# SDoH Extraction GUI

Streamlit app for the two-level SDoH pipeline:

1. **Level 1 (trigger words):** runs one of your fine-tuned NER checkpoints
   from `1.tag/output/` (BERT / BioBERT / RoBERTa) on the input text and
   highlights each detected SDoH trigger word with its category.
2. **Level 2 (details):** for each trigger, calls the OpenAI API with the
   strict per-category function schema from
   `2.label/config/sdoh_extraction_schema_strict_type_simple_experiencer.json`
   (same forced tool-calling pattern as
   `2.label/notebooks/LLM_label_prediction.ipynb`) to extract structured
   detail fields.

Two input modes:

- **Sentence / paragraph:** the whole pasted text is processed.
- **Full EHR note:** the note is sectionized (medspacy's
  `medspacy_sectionizer`, with a built-in regex fallback if medspacy isn't
  installed). SDoH-relevant sections (Social History, HPI, Chief Complaint,
  Assessment/Plan, Hospital Course, Patient Instructions/Education, and any
  untitled/unrecognized text) are pre-selected; you can toggle any detected
  section on/off before extracting. Skipped sections are greyed out in the
  highlighted output.

All results can be downloaded as JSON (button below the results).

## Setup

```bash
cd gui
pip install -r requirements.txt
```

Create a `.env` file in this folder with your OpenAI key (never commit this
file):

```
OPENAI_API_KEY=sk-...
```

Alternatively, paste a key directly into the sidebar at runtime — it is only
kept in memory for that session.

## Run

```bash
streamlit run app.py
```

The sidebar lets you pick which trained checkpoint to use for Level 1 (it
auto-discovers every `*_fold_*_lr_*` directory under `1.tag/output/`, and
shows that model family's cross-validated overall sentence-level F1 from
`1.tag/output/model_performance.json`), and which OpenAI model to use for
Level 2. You can also turn Level 2 off to only see trigger words.

## Output JSON format

One row per sentence of the input (sentence number is the key), so numbers
are stable references into the note. Level-1 tags and Level-2 labels are
lists of dictionaries; sentences with no findings have empty lists. All
`start`/`end` values are character offsets into the full input text.

```json
{
  "metadata": {
    "created": "2026-07-15T10:30:00",
    "input_mode": "ehr",
    "section_engine": "medspacy",
    "level1_model": "RoBERTa — fold 1 (lr 2e-5)",
    "level2_model": "gpt-4o-2024-08-06",
    "num_sentences": 17,
    "sections": [
      {"title": "Social History", "category": "social_history",
       "start": 360, "end": 580, "processed": true}
    ]
  },
  "sentences": {
    "5": {
      "sentence": "He reports he could not afford the copay.",
      "start": 137, "end": 226,
      "section": "history_of_present_illness",
      "processed": true,
      "level1": [
        {"category": "Financial", "trigger": "could not afford",
         "start": 199, "end": 215}
      ],
      "level2": [
        {"category": "Financial", "trigger": "could not afford",
         "extracted_conditions": [{"...": "..."}]}
      ]
    }
  }
}
```

`"processed": false` marks sentences in sections you chose to skip (their
`level1`/`level2` lists are empty because they were not run, not because
nothing was found).

## Notes / design choices

- **Tokenization:** the NER models were trained on INCEpTION's own word-level
  tokens. There's no standalone "raw text → INCEpTION tokens" utility in this
  repo (training/prediction both go through `run_ner.py` on pre-tokenized
  JSON), so `ner_inference.py` uses a regex word tokenizer (splits on
  whitespace, keeps punctuation as separate tokens, keeps simple
  hyphenated/contraction words together) as a practical approximation. It
  reproduces the *shape* of training-time tokenization closely enough for the
  fine-tuned subword tokenizer to generalize, but it is not a byte-for-byte
  match to INCEpTION's segmentation rules.
- **Category name mismatch:** the NER labels have no spaces (`MentalHealth`,
  `SubstanceUse`); two of the Level-2 schema keys do (`"Mental Health"`,
  `"Substance Use"`). `llm_extraction.py` reconciles this via
  `NER_TO_SCHEMA_CATEGORY`.
- **Sentence/context window for Level 2:** each trigger's containing sentence
  is sent as the "current sentence"; the previous + next sentence are
  included as context only to help resolve pronouns/Experiencer, mirroring
  the notebook's 3-sentence window — the model is instructed not to pull
  events from the context sentences themselves.
- Only the BERT / BioBERT / RoBERTa checkpoints are exposed as options.
  `model_performance.json` shows `BiLSTM-CRF` with several precision/F1
  values above 1.0 (likely an evaluation bug for that model), so it's
  excluded from the GUI's model picker.

- **Per-sentence NER:** the input is sentence-split (with global character
  offsets, guarding common clinical abbreviations and hard-wrapped lines)
  and the Level-1 model runs sentence by sentence — matching how the models
  were trained and avoiding the 512-token truncation limit on long notes.
- **medspacy is optional:** if it isn't installed (or fails to load), a
  regex sectionizer with the common clinical header names is used instead,
  and the UI tells you which engine produced the sections.
- **Results survive reruns:** extraction results are kept in
  `st.session_state`, so clicking the JSON download button doesn't clear
  them.

## Files

- `app.py` — Streamlit UI and orchestration.
- `ner_inference.py` — Level-1 model loading + BIO decoding into trigger
  spans.
- `llm_extraction.py` — Level-2 OpenAI tool-calling extraction.
- `ehr_sections.py` — EHR sectionizing (medspacy sectionizer + regex
  fallback) and the SDoH-relevant section defaults.
- `results_export.py` — builds the sentence-number-keyed JSON results file.
