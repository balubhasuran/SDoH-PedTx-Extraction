# SDoH: Annotation and Information Extraction of Social Determinants of Health from Social Worker Notes of Pediatric Transplantation

**eHealth Lab, School of Information (iSchool), Florida State University**

This repository contains the code, annotation configuration, and models for a
two-stage pipeline that identifies mentions of **Social Determinants of
Health (SDoH)** in clinical/social-worker notes (pediatric transplantation
population) and then extracts structured, detailed information about each
mention. A Streamlit demo GUI ties both stages together into an
end-to-end, interactive tool.

## Pipeline overview

The project is organized around two sequential stages plus a demo app:

| Stage | Folder | What it does |
|---|---|---|
| **Part I — Tagging** | [`1.tag/`](1.tag) | Traditional NLP / NER approach: fine-tunes transformer token-classification models (BERT, BioBERT, RoBERTa) to find the **trigger word/span** for each SDoH category in a sentence. |
| **Part II — Labeling** | [`2.label/`](2.label) | LLM approach: given a sentence and the trigger/category found in Part I, calls an LLM (OpenAI function/tool-calling) with a strict per-category JSON schema to extract deeper, structured detail (e.g., Experiencer, sub-type, polarity) for that mention. |
| **Demo GUI** | [`gui/`](gui) | Streamlit app that chains Part I (NER) and Part II (LLM extraction) together over pasted text or a full EHR note, with section-aware filtering and JSON export. |

Annotation was performed in the [INCEpTION](https://inception-project.github.io/)
tool against a shared
[annotation guideline](https://docs.google.com/document/d/1s9TIPULfy8k63ELmHUbQrI85llH2OCQyy92W8kmOqPQ/edit?usp=sharing),
then exported as JSON and stored (zipped) under each stage's `data/annotation_data_zip`.

## SDoH categories

Sentences/spans are labeled into one or more of the following categories
(see `1.tag/prompts/Trigger_word.txt` and `2.label/config/llm_category_schema.json`
for full definitions and edge cases):

`Adherence`, `Concern`, `Education`, `Employment`, `Financial`, `Healthcare`,
`Insurance`, `Literacy`, `Living`, `MentalHealth`, `Recommendation`, `Smoke`,
`Social`, `SubstanceUse`, `Transportation`, `Trauma`

Part II further extracts category-specific structured fields (e.g.
`Experiencer`: patient / caregivers / others; healthcare sub-type; etc.) using
the strict JSON schemas in `2.label/config/`.

## Repository structure

```
SDoH-main/
├── 1.tag/                  # Part I: NER trigger-word tagging
│   ├── ner_code/            #   HuggingFace token-classification training scripts
│   │                        #   (run_ner.py / run_ner_no_trainer.py, adapted from
│   │                        #   the transformers examples repo)
│   ├── util/                 #   data prep: 5-fold split, sentence split, format transform
│   ├── config/               #   LLM tagging config (LLM_SDoH_tag.json)
│   ├── prompts/               #   LLM trigger-word prompt (Trigger_word.txt)
│   ├── data/                  #   annotation_data, annotation_data_zip, splitted_data, train_data
│   ├── annotations/            #   raw INCEpTION exports
│   ├── output/                  #   trained model checkpoints & model_performance.json
│   ├── results/, eval/, logs/, notebooks/
│   ├── train_*.sh, predict_*.sh    # per-model (BERT/BioBERT/RoBERTa) and
│   │                                 5-fold-CV train/predict scripts
│   ├── copy_and_process_data.sh, split.sh, sample_train.sh, test.sh
│   └── README.md
│
├── 2.label/                 # Part II: LLM-based structured extraction
│   ├── config/                #   per-category strict extraction JSON schemas +
│   │                           #   sdoh_kw_dict.json
│   ├── util/                   #   transform_data.py, unzip.py
│   ├── data/                   #   annotation_data, annotation_data_zip, curation, processed_data
│   ├── output/                  #   LLM extraction runs (gpt4o_type, gpt55_type_*),
│   │                            #   manual_labeled_dataset.csv, MIMIC-III run outputs
│   ├── eval/                    #   error analysis CSVs
│   ├── notebooks/                #   LLM_label_prediction.ipynb, evaluation/formatting notebooks
│   ├── copy_and_process_data.sh
│   └── README.md
│
├── gui/                     # Streamlit demo app combining Part I + Part II
│   ├── app.py                 #   UI + orchestration
│   ├── ner_inference.py        #   loads a fine-tuned checkpoint, decodes BIO tags into triggers
│   ├── llm_extraction.py        #   Level-2 OpenAI tool-calling extraction
│   ├── ehr_sections.py          #   EHR note sectionizing (medspacy + regex fallback)
│   ├── results_export.py        #   builds the sentence-keyed JSON export
│   ├── requirements.txt
│   └── README.md
│
└── README.md                 # (this file)
```

## Getting started

### 1. Clone and set up an environment

```bash
git clone https://github.com/drizzle98/SDoH.git
cd SDoH
conda create -n SDoH python=3.11
conda activate SDoH
pip install -r 1.tag/ner_code/requirements.txt
```

Install a [PyTorch](https://pytorch.org/) build compatible with your hardware
(CPU/GPU) if it isn't pulled in automatically.

### 2. Part I — train/predict the NER tagger

```bash
cd 1.tag
./copy_and_process_data.sh
./split.sh
./train_bert.sh         # or train_biobert.sh / train_roberta.sh
                         # *_5_folder.sh variants run 5-fold cross-validation
./predict_bert.sh        # run inference with a trained checkpoint
```

See [`1.tag/README.md`](1.tag/README.md) for details, and `1.tag/ner_code/README.md`
for the underlying HuggingFace token-classification script options.

### 3. Part II — LLM structured extraction

```bash
cd 2.label
./copy_and_process_data.sh
```

Then run `2.label/notebooks/LLM_label_prediction.ipynb` (or the MIMIC-III
variant) to call the LLM with the strict function-calling schemas in
`2.label/config/` against the trigger words found in Part I. Evaluation /
formatting notebooks (`evaluate.ipynb`, `dataset_eval.ipynb`,
`json_evaluation.ipynb`, etc.) are also in `2.label/notebooks/`.

See [`2.label/README.md`](2.label/README.md) for details.

### 4. Run the interactive demo

```bash
cd gui
pip install -r requirements.txt
streamlit run app.py
```

The GUI auto-discovers trained checkpoints from `1.tag/output/`, runs Level-1
trigger detection, then (optionally) calls an LLM for Level-2 detail
extraction, and exports results as JSON. It also supports pasting a full EHR
note, which is automatically split into sections (Social History, HPI,
Assessment/Plan, etc.) so you can choose which sections to process. See
[`gui/README.md`](gui/README.md) for the full walkthrough, output JSON
schema, and design notes.

## Evaluation

- **Part I (NER):** strict span match, relaxed/overlapping match, and
  sentence-level match are used to score trigger-word detection (see
  `1.tag/README.md`); per-fold metrics are written to
  `1.tag/output/model_performance.json`.
- **Part II (LLM extraction):** error analysis and label-agreement notebooks
  live in `2.label/notebooks/` and `2.label/eval/` (e.g.
  `sdoh_error_analysis.csv`, `level_2_error.csv`).

## Data and privacy note

The annotated notes are derived from pediatric transplantation social-worker
notes. Raw/annotated data files under `1.tag/data/`, `2.label/data/`, and
`2.label/output/` may contain sensitive or de-identified clinical text — do
not commit new data files or credentials, and treat any local copies
according to your institution's data-use agreement. GUI users must supply
their own OpenAI API key (see `gui/README.md`); never commit `.env` files or
keys.

## Status / next steps

- Part I evaluation (strict / relaxed / sentence-level match scoring) is
  still under active development — see `1.tag/README.md` for the current
  plan.
- Longer-term direction: since NER is primarily a supporting step to locate
  SDoH-relevant sentences, an LLM-only (encoder+decoder or decoder-only)
  approach to the whole pipeline is being explored as an alternative to the
  fine-tuned NER + LLM two-stage design.
