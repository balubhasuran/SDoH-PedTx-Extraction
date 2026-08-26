"""
Build the downloadable JSON results file for the SDoH GUI.

Format (sentence-number-keyed, as discussed):

{
  "metadata": {
    "created": "...",                # ISO timestamp
    "input_mode": "ehr" | "plain",
    "section_engine": "medspacy" | "regex" | null,
    "level1_model": "...",
    "level2_model": "..." | null,    # null when Level 2 was not run
    "num_sentences": N,
    "sections": [ {title, category, start, end, processed}, ... ]  # ehr mode
  },
  "sentences": {
    "1": {
      "sentence": "...",
      "start": 0, "end": 57,         # char offsets into the full input text
      "section": "social_history",   # null in plain mode
      "processed": true,             # false = sentence was in a skipped section
      "level1": [                    # trigger words from the NER model
        {"category": "Employment", "trigger": "lost her job",
         "start": 21, "end": 33}     # global char offsets
      ],
      "level2": [                    # structured details from the LLM
        {"category": "Employment", "trigger": "lost her job",
         "extracted_conditions": [ ... ]}   # or {"error": "..."}
      ]
    },
    ...
  }
}

Every sentence of the input appears (even ones with no findings, which get
empty lists), so sentence numbers are stable references into the note.
"""

import json
from datetime import datetime


def build_results_json(
    text,
    sentences,          # list of dicts: {"num", "text", "start", "end", "section", "processed"}
    triggers,           # list of dicts: {"sentence_num", "category", "text", "start", "end"}
    level2_results,     # list of dicts: {"sentence_num", "category", "trigger", "result"}
    input_mode="plain",
    section_engine=None,
    sections=None,      # section dicts from ehr_sections + "processed" flag
    level1_model=None,
    level2_model=None,
):
    sentence_rows = {}
    for s in sentences:
        sentence_rows[str(s["num"])] = {
            "sentence": s["text"],
            "start": s["start"],
            "end": s["end"],
            "section": s.get("section"),
            "processed": bool(s.get("processed", True)),
            "level1": [],
            "level2": [],
        }

    for t in triggers:
        row = sentence_rows.get(str(t["sentence_num"]))
        if row is not None:
            row["level1"].append({
                "category": t["category"],
                "trigger": t["text"],
                "start": t["start"],
                "end": t["end"],
            })

    for r in level2_results:
        row = sentence_rows.get(str(r["sentence_num"]))
        if row is not None:
            entry = {"category": r["category"], "trigger": r["trigger"]}
            entry.update(r["result"] if isinstance(r["result"], dict) else {"raw": r["result"]})
            row["level2"].append(entry)

    metadata = {
        "created": datetime.now().isoformat(timespec="seconds"),
        "input_mode": input_mode,
        "section_engine": section_engine,
        "level1_model": level1_model,
        "level2_model": level2_model,
        "num_sentences": len(sentence_rows),
    }
    if sections is not None:
        metadata["sections"] = [
            {
                "title": sec.get("title", ""),
                "category": sec.get("category"),
                "start": sec["start"],
                "end": sec["end"],
                "processed": bool(sec.get("processed", False)),
            }
            for sec in sections
        ]

    return {"metadata": metadata, "sentences": sentence_rows}


def results_to_json_str(results):
    return json.dumps(results, indent=2, ensure_ascii=False)
