"""
Streamlit GUI for two-level SDoH extraction.

Level 1: a fine-tuned transformer NER model (BERT / BioBERT / RoBERTa,
trained via 1.tag/ner_code/run_ner.py) finds SDoH trigger words + category.

Level 2: for each trigger, the OpenAI API (forced function/tool calling
against the strict per-category schemas in 2.label/config/) extracts
structured detail fields, following the same pattern as
2.label/notebooks/LLM_label_prediction.ipynb.

Input modes:
  - Sentence / paragraph: run the pipeline on the whole pasted text.
  - Full EHR note: sectionize with medspacy (regex fallback), pre-select
    SDoH-relevant sections (Social History, HPI, ...), and run the
    pipeline only on the sections you keep checked.

All results can be downloaded as a sentence-number-keyed JSON file
(see results_export.py for the exact format).

Run with:
    cd gui
    streamlit run app.py
"""

import html
import json
import os
import re
import sys
from datetime import datetime

import streamlit as st
from dotenv import load_dotenv

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from ner_inference import get_extractor  # noqa: E402
from llm_extraction import DetailExtractor, DEFAULT_MODEL  # noqa: E402
from ehr_sections import sectionize, section_for_offset  # noqa: E402
from results_export import build_results_json, results_to_json_str  # noqa: E402

load_dotenv()

THIS_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_DIR = os.path.join(THIS_DIR, "..", "1.tag", "output")
PERF_PATH = os.path.join(OUTPUT_DIR, "model_performance.json")

MODEL_DIR_RE = re.compile(r"^(BERT|BioBERT|roberta)_fold_(\d+)_lr_([\d.eE\-]+)$")
FAMILY_DISPLAY = {"BERT": "BERT", "BioBERT": "BioBERT", "roberta": "RoBERTa"}

CATEGORY_COLORS = {
    "Adherence": "#FFD6A5",
    "Concern": "#FDFFB6",
    "Education": "#CAFFBF",
    "Employment": "#9BF6FF",
    "Financial": "#A0C4FF",
    "Healthcare": "#BDB2FF",
    "Insurance": "#FFC6FF",
    "Literacy": "#FFADAD",
    "Living": "#D0F4DE",
    "MentalHealth": "#E2C2FF",
    "Recommendation": "#FFE5B4",
    "Smoke": "#C9C9C9",
    "Social": "#B5EAD7",
    "SubstanceUse": "#FF9AA2",
    "Transportation": "#C7CEEA",
    "Trauma": "#F7A1A1",
}


@st.cache_data(show_spinner=False)
def discover_models():
    options = {}
    if os.path.isdir(OUTPUT_DIR):
        for name in sorted(os.listdir(OUTPUT_DIR)):
            full = os.path.join(OUTPUT_DIR, name)
            match = MODEL_DIR_RE.match(name)
            if match and os.path.isfile(os.path.join(full, "config.json")):
                family, fold, lr = match.groups()
                label = f"{FAMILY_DISPLAY.get(family, family)} — fold {fold} (lr {lr})"
                options[label] = {"path": full, "family": family, "fold": int(fold), "lr": lr}
    return options


@st.cache_data(show_spinner=False)
def load_performance():
    if os.path.isfile(PERF_PATH):
        with open(PERF_PATH, "r") as f:
            return json.load(f)
    return {}


@st.cache_data(show_spinner=False)
def cached_sectionize(text):
    return sectionize(text)


# Sentence boundaries:
#   1. after .!? (guarding common clinical abbreviations and initials),
#   2. at blank lines,
#   3. at a single newline only when the next line clearly starts a new item
#      (bullet, numbered item, "Header:", or an ALL-CAPS header) — EHR notes
#      often omit end-of-line punctuation, but plain hard-wrapped prose
#      should not be split mid-sentence.
_SENT_BOUNDARY_RE = re.compile(
    r"(?<=[.!?])(?<!\bMr\.)(?<!\bMrs\.)(?<!\bMs\.)(?<!\bDr\.)(?<!\bSt\.)"
    r"(?<!\bvs\.)(?<!\be\.g\.)(?<!\bi\.e\.)(?<!\b[A-Z]\.)\s+"
    r"|\n{2,}"
    r"|\n(?=[ \t]*(?:[-*•]|\d+[.)]\s|[A-Za-z][A-Za-z0-9 /&'()\-]{0,60}:|[A-Z]{3,}))"
)


def split_sentences_with_offsets(text):
    """Lightweight sentence splitter that keeps character offsets."""
    spans = []
    start = 0
    for m in _SENT_BOUNDARY_RE.finditer(text):
        end = m.start()
        if text[start:end].strip():
            spans.append((text[start:end], start, end))
        start = m.end()
    if text[start:].strip():
        spans.append((text[start:], start, len(text)))
    return spans or [(text, 0, len(text))]


def render_highlighted_html(text, triggers, skipped_ranges=None):
    """Highlight triggers; grey out skipped (unprocessed) sections."""
    boundaries = []
    for t in sorted(triggers, key=lambda t: t["start"]):
        boundaries.append(("trig", t))
    skipped_ranges = sorted(skipped_ranges or [])

    def esc(s):
        return html.escape(s).replace("\n", "<br>")

    def grey_out(segment_html):
        return f'<span style="opacity:0.45;">{segment_html}</span>'

    # Render plain segments with skipped ranges greyed out.
    def render_plain(seg_start, seg_end):
        out, cursor = [], seg_start
        for s, e in skipped_ranges:
            s, e = max(s, seg_start), min(e, seg_end)
            if s >= e:
                continue
            if cursor < s:
                out.append(esc(text[cursor:s]))
            out.append(grey_out(esc(text[s:e])))
            cursor = e
        if cursor < seg_end:
            out.append(esc(text[cursor:seg_end]))
        return "".join(out)

    parts, cursor = [], 0
    for kind, t in boundaries:
        if t["start"] < cursor:
            continue  # skip any overlapping span defensively
        parts.append(render_plain(cursor, t["start"]))
        color = CATEGORY_COLORS.get(t["category"], "#eeeeee")
        span_text = html.escape(text[t["start"]:t["end"]])
        parts.append(
            f'<mark style="background-color:{color};border-radius:4px;padding:1px 4px;" '
            f'title="{t["category"]}">{span_text}'
            f'<sup style="font-size:0.65em;opacity:0.75;">&nbsp;{t["category"]}</sup></mark>'
        )
        cursor = t["end"]
    parts.append(render_plain(cursor, len(text)))
    return "<div style='line-height:2.4; font-size:1.05rem;'>" + "".join(parts) + "</div>"


def section_label(i, sec):
    title = sec["title"] or "(untitled preamble)"
    return f"{i + 1}. {title}  [{sec['category']}]"


st.set_page_config(page_title="SDoH Extraction", layout="wide")
st.title("SDoH Trigger & Detail Extraction")
st.caption(
    "Level 1 runs your fine-tuned transformer NER model to find SDoH trigger words. "
    "Level 2 sends each trigger's sentence to an OpenAI model for structured detail extraction. "
    "Paste a whole EHR note to sectionize it first and only process SDoH-relevant sections."
)

model_options = discover_models()
perf = load_performance()

with st.sidebar:
    st.header("Settings")

    if not model_options:
        st.error(f"No model checkpoints found under:\n{OUTPUT_DIR}")
        st.stop()

    labels = list(model_options.keys())
    default_label = next(
        (
            l for l in labels
            if model_options[l]["family"] == "roberta"
            and model_options[l]["fold"] == 1
            and model_options[l]["lr"] == "2e-5"
        ),
        labels[0],
    )
    model_label = st.selectbox(
        "Trigger-word (Level 1) model",
        labels,
        index=labels.index(default_label),
    )
    chosen = model_options[model_label]

    family_perf = perf.get(FAMILY_DISPLAY.get(chosen["family"], chosen["family"]))
    if family_perf:
        f1 = family_perf.get("overall", {}).get("sentence-level", {}).get("f-1")
        if f1 is not None:
            st.caption(
                f"{FAMILY_DISPLAY.get(chosen['family'])} overall sentence-level F1 "
                f"(cross-validated, all folds): {f1:.3f}"
            )

    st.divider()
    llm_model = st.text_input("OpenAI model (Level 2)", value=DEFAULT_MODEL)
    api_key_input = st.text_input(
        "OpenAI API key (optional — leave blank to use OPENAI_API_KEY from .env)",
        type="password",
    )
    run_level2 = st.checkbox("Run Level 2 (LLM detail extraction)", value=True)

    st.divider()
    with st.expander("Category legend"):
        legend_html = " ".join(
            f'<span style="background-color:{color};padding:2px 8px;border-radius:4px;'
            f'margin:2px;display:inline-block;">{cat}</span>'
            for cat, color in CATEGORY_COLORS.items()
        )
        st.markdown(legend_html, unsafe_allow_html=True)

input_mode = st.radio(
    "Input type",
    ["Sentence / paragraph", "Full EHR note (auto-sectionize)"],
    horizontal=True,
)
is_ehr = input_mode.startswith("Full EHR")

text = st.text_area(
    "Enter text" if not is_ehr else "Paste the full EHR note",
    height=160 if not is_ehr else 320,
    placeholder=(
        "e.g. The patient's mother lost her job last month and the family has "
        "been struggling to pay rent. The patient also missed several clinic visits."
        if not is_ehr else
        "Paste the whole note — sections like Social History, HPI, Assessment/Plan "
        "will be detected automatically."
    ),
)

# --- EHR sectionizing (live, before extraction) ---------------------------
sections, section_engine, selected_section_idx = None, None, None
if is_ehr and text.strip():
    sections, section_engine = cached_sectionize(text)
    engine_note = (
        "medspacy sectionizer" if section_engine == "medspacy"
        else "built-in regex sectionizer (install `medspacy` for better detection)"
    )
    st.markdown(f"**Detected sections** ({len(sections)}, via {engine_note})")

    all_labels = [section_label(i, sec) for i, sec in enumerate(sections)]
    default_labels = [section_label(i, sec) for i, sec in enumerate(sections) if sec["relevant"]]
    chosen_labels = st.multiselect(
        "Sections to process (SDoH-relevant ones are pre-selected)",
        all_labels,
        default=default_labels,
    )
    selected_section_idx = {all_labels.index(l) for l in chosen_labels}

# --- Extraction ------------------------------------------------------------
if st.button("Extract", type="primary") and text.strip():
    if is_ehr and not selected_section_idx:
        st.warning("Select at least one section to process.")
        st.stop()

    with st.spinner(f"Loading {model_label}..."):
        try:
            extractor = get_extractor(chosen["path"])
        except Exception as e:
            st.error(f"Failed to load the Level 1 model: {e}")
            st.stop()

    # 1) Sentence-split the whole note with global offsets, tag each sentence
    #    with its section and whether it falls in a selected section.
    raw_sentences = split_sentences_with_offsets(text)
    sentences = []
    for num, (sent_text, s, e) in enumerate(raw_sentences, start=1):
        sec = section_for_offset(sections, s) if sections else None
        processed = True
        if is_ehr:
            processed = sec is not None and sections.index(sec) in selected_section_idx
        sentences.append({
            "num": num,
            "text": sent_text.strip(),
            "start": s,
            "end": e,
            "section": sec["category"] if sec else None,
            "processed": processed,
        })

    # 2) Level 1: run the NER model sentence by sentence (matches how the
    #    models were trained) on processed sentences only.
    triggers = []
    to_process = [s for s in sentences if s["processed"]]
    progress = st.progress(0.0, text="Level 1 — finding trigger words...")
    try:
        for i, s in enumerate(to_process):
            offset = s["start"] + (len(text[s["start"]:s["end"]]) - len(text[s["start"]:s["end"]].lstrip()))
            for t in extractor.extract(s["text"]):
                triggers.append({
                    "sentence_num": s["num"],
                    "category": t["category"],
                    "text": t["text"],
                    "start": offset + t["start"],
                    "end": offset + t["end"],
                })
            progress.progress((i + 1) / len(to_process), text="Level 1 — finding trigger words...")
    except Exception as e:
        st.error(f"Failed to run the Level 1 model: {e}")
        st.stop()
    finally:
        progress.empty()

    # 3) Level 2: LLM detail extraction per trigger.
    level2_results = []
    level2_ran = False
    if run_level2 and triggers:
        api_key = api_key_input.strip() or None
        try:
            detail_extractor = DetailExtractor(model=llm_model, api_key=api_key)
            level2_ran = True
        except Exception as e:
            st.error(
                f"Could not initialize the OpenAI client: {e}\n\n"
                "Set OPENAI_API_KEY in a .env file next to app.py, or paste a key "
                "in the sidebar. Showing Level 1 results only."
            )

        if level2_ran:
            by_num = {s["num"]: s for s in sentences}
            progress = st.progress(0.0, text="Level 2 — calling OpenAI...")
            for i, trig in enumerate(triggers):
                s = by_num[trig["sentence_num"]]
                context = " ".join(
                    by_num[n]["text"] for n in (s["num"] - 1, s["num"], s["num"] + 1) if n in by_num
                )
                result = detail_extractor.extract(s["text"], trig["category"], context=context)
                level2_results.append({
                    "sentence_num": trig["sentence_num"],
                    "category": trig["category"],
                    "trigger": trig["text"],
                    "result": result,
                })
                progress.progress((i + 1) / len(triggers), text="Level 2 — calling OpenAI...")
            progress.empty()

    # 4) Build the exportable JSON and stash everything in session_state so
    #    the results (and the download button) survive Streamlit reruns.
    processed_sections = None
    if sections is not None:
        processed_sections = [
            {**sec, "processed": i in selected_section_idx}
            for i, sec in enumerate(sections)
        ]

    results = build_results_json(
        text,
        sentences,
        triggers,
        level2_results,
        input_mode="ehr" if is_ehr else "plain",
        section_engine=section_engine,
        sections=processed_sections,
        level1_model=model_label,
        level2_model=llm_model if level2_ran else None,
    )

    st.session_state["run"] = {
        "text": text,
        "is_ehr": is_ehr,
        "sentences": sentences,
        "triggers": triggers,
        "level2_results": level2_results,
        "level2_ran": level2_ran,
        "sections": processed_sections,
        "json_str": results_to_json_str(results),
    }

# --- Render results (from session_state, so downloads don't clear them) ----
run = st.session_state.get("run")
if run:
    st.divider()
    st.subheader("Level 1 — Trigger words")

    if not run["triggers"]:
        st.info("No SDoH trigger words detected in the processed text.")
    else:
        skipped = [
            (sec["start"], sec["end"])
            for sec in (run["sections"] or [])
            if not sec["processed"]
        ]
        st.markdown(
            render_highlighted_html(run["text"], run["triggers"], skipped_ranges=skipped),
            unsafe_allow_html=True,
        )
        n_proc = sum(1 for s in run["sentences"] if s["processed"])
        st.caption(
            f"{len(run['triggers'])} trigger word(s) across "
            f"{len(set(t['category'] for t in run['triggers']))} categories, "
            f"from {n_proc} processed sentence(s)."
            + (" Greyed-out text belongs to skipped sections." if skipped else "")
        )

    if run["level2_ran"] and run["level2_results"]:
        st.subheader("Level 2 — Detailed extraction (LLM)")
        by_num = {s["num"]: s for s in run["sentences"]}
        for i, r in enumerate(run["level2_results"]):
            sent = by_num[r["sentence_num"]]["text"]
            with st.expander(
                f'Sentence {r["sentence_num"]} — {r["category"]} — “{r["trigger"]}”',
                expanded=(i == 0),
            ):
                st.caption(f"Sentence: {sent}")
                result = r["result"]
                if "error" in result:
                    st.error(result["error"])
                    if "raw_output" in result:
                        st.code(result["raw_output"])
                elif not result.get("extracted_conditions"):
                    st.info("LLM found no structured detail for this category in this sentence.")
                else:
                    st.json(result)

    st.divider()
    st.download_button(
        "⬇️ Download results JSON",
        data=run["json_str"],
        file_name=f"sdoh_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
        mime="application/json",
    )
    with st.expander("Preview JSON"):
        st.code(run["json_str"], language="json")
