# Synthetic sample data

Everything under `sample_data/` is **fully synthetic** — invented patients,
names, dates, addresses, and note text. Nothing here is derived from, or
copied from, any real clinical record. It exists so the repository has a
safe, public, runnable example of every file format used by the pipeline
without needing access to the real (sensitive/de-identified) notes that
normally live under `1.tag/data/`, `2.label/data/`, and `2.label/output/`.

Four fictional pediatric transplant "psychosocial assessment" notes
(`9001_synthetic` .. `9004_synthetic`, heart/kidney/liver/lung) are encoded
once as structured sentences + SDoH annotations, then rendered into every
downstream format the real pipeline consumes/produces, so the numbers,
tokens, and labels are consistent across files for the same document.
Between the four notes, all 16 SDoH categories (`Adherence`, `Concern`,
`Education`, `Employment`, `Financial`, `Healthcare`, `Insurance`,
`Literacy`, `Living`, `Mental Health`, `Recommendation`, `Smoke`, `Social`,
`Substance Use`, `Transportation`, `Trauma`) appear at least once.

## Layout (mirrors the real data layout)

```
sample_data/
├── 1.tag/
│   ├── data/
│   │   ├── annotation_data/        # raw UIMA CAS-JSON export (INCEpTION-style), one per doc
│   │   ├── train_data/             # tokens + BIO ner_tags, one per doc
│   │   └── splitted_data/fold_1/   # a single train/test fold (.iob, .txt, .json), 3 docs train / 1 doc test
│   └── output/
│       └── GPT-4o-trigger.csv      # Sentence / True / predict trigger-word CSV
└── 2.label/
    ├── data/
    │   ├── annotation_data/        # same raw export as 1.tag/data/annotation_data
    │   └── processed_data/         # ground-truth structured SDoH extraction, one per doc
    ├── output/
    │   ├── gpt4o_type/                       # LLM extraction output, full Experiencer values
    │   └── gpt55_type_simple_experiencer/    # same, with Experiencer collapsed to patient/caregiver/family
    └── eval/
        └── sdoh_error_analysis.csv # doc_id/sentence/category/true_label/predicted_label/status
```

## Known simplifications vs. the real data

- **Category naming split is intentional, not a bug.** The raw export,
  `processed_data`, and LLM outputs use the two-word category names
  (`"Mental Health"`, `"Substance Use"`), matching
  `2.label/config/sdoh_kw_dict.json`. The NER token-classification files
  (`train_data`, `splitted_data`) use the no-space BIO tag names
  (`MentalHealth`, `SubstanceUse`). The real repo has this same split.
- The raw UIMA export here only includes the fields actually consumed
  downstream (`DocumentMetaData`, `Sentence`, `Token`, `SDoHLevel1`,
  `SDoHlevel2`, and the `Sofa` text) — it omits POS/lemma/dependency layers
  present in a genuine INCEpTION/WebAnno export, since nothing in this
  pipeline reads them.
- LLM-output field names follow the primary documented schema
  (`2.label/config/llm_category_schema.json` / `sdoh_kw_dict.json`). Some
  real experimental runs used alternate per-run schema variants with
  different field names (e.g. lowercase `healthcare_type`, or
  `num_of_caregivers` instead of `LivingType`/`ResidentType` for `Living`,
  as seen in `sdoh_extraction_schema_strict_type.json`) — this sample keeps
  one consistent field naming for clarity/testability rather than
  reproducing every variant.
- `GPT-4o-trigger.csv` and `sdoh_error_analysis.csv` predictions are
  synthetic and deterministic (seeded off document/sentence content), not
  the output of an actual model call — they're constructed to exercise all
  five real evaluation statuses (`Exact Match (TP)`, `Partial Match
  (FP/FN)`, `Missed (FN)`, `Hallucination (FP)`, `Complete Mismatch
  (FP/FN)`) and both trigger-detection failure modes (missed category,
  hallucinated category).
- Only one 5-fold split (`fold_1`) is provided, with 3 of the 4 synthetic
  docs in train and 1 in test — enough to smoke-test the NER training
  scripts, not a statistically meaningful split.

## Regenerating

```bash
python sample_data/generate_sample_data.py
```

`generate_sample_data.py` defines each synthetic note once as sentences +
SDoH spans (`DOCS` near the top of the file) and derives every file format
below from that shared source, so offsets/tokens/labels stay consistent
across formats. Add or edit an entry in `DOCS` and re-run the script to
regenerate all outputs.
