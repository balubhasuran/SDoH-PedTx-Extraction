#!/usr/bin/env python3
"""
Generate a small, fully-synthetic sample dataset that mirrors the file
formats used by the SDoH-PedTx-Extraction pipeline (1.tag/, 2.label/),
without containing any real patient data.

All patients, names, dates, addresses, and notes below are fictional.
"""
import csv
import json
import os
import re

OUT_ROOT = os.path.dirname(os.path.abspath(__file__))

# ---------------------------------------------------------------------------
# Category name maps
#   - "l1" name = the name used in the raw UIMA export (SDoHLevel1.SDoHlv1),
#     2.label ground truth / LLM-output JSON keys, and 2.label/config schemas.
#     Two-word categories keep a space here ("Mental Health", "Substance Use"),
#     matching the real repo's 2.label/config/sdoh_kw_dict.json keys.
#   - "ner" name = the BIO tag suffix used in 1.tag (train_data / splitted_data),
#     which the real repo's data-prep strips spaces from ("MentalHealth",
#     "SubstanceUse"). This mismatch is real and intentional -- Part I and
#     Part II of the pipeline use slightly different spellings for the same
#     two categories.
CATS = {
    "Healthcare": "Healthcare",
    "Living": "Living",
    "Smoke": "Smoke",
    "Employment": "Employment",
    "Social": "Social",
    "Education": "Education",
    "Transportation": "Transportation",
    "Mental Health": "MentalHealth",
    "Insurance": "Insurance",
    "Financial": "Financial",
    "Substance Use": "SubstanceUse",
    "Trauma": "Trauma",
    "Adherence": "Adherence",
    "Literacy": "Literacy",
    "Recommendation": "Recommendation",
    "Concern": "Concern",
}

# Required fields per category (mirrors 2.label/config/sdoh_kw_dict.json)
REQUIRED_FIELDS = {
    "Healthcare": ["Experiencer", "HealthcareType"],
    "Living": ["Experiencer", "LivingStatus", "LivingType", "ResidentType"],
    "Smoke": ["Experiencer", "SmokeStatus"],
    "Employment": ["EmploymentStatus", "Experiencer"],
    "Social": ["Experiencer", "SocialActivity", "SocialType"],
    "Education": ["EducationStatus", "EducationType", "Experiencer"],
    "Transportation": ["Experiencer", "TransportationConvenienceLevel", "TransportationType"],
    "Mental Health": ["Experiencer", "MentalHealthStatus", "MentalHealthType"],
    "Insurance": ["Experiencer", "InsuranceType"],
    "Financial": ["Experiencer", "FinancialStatus"],
    "Substance Use": ["Experiencer", "SubstanceUseStatus"],
    "Trauma": ["Experiencer", "TraumaStatus", "TraumaType"],
    "Adherence": ["AdherenceLevel", "AdherenceType", "Experiencer"],
    "Literacy": ["Experiencer", "LiteracyLevel", "LiteracyType"],
    "Recommendation": ["RecommendationType"],
    "Concern": ["ConcernLevel"],
}


def S(text, spans=None):
    """A sentence: text plus zero or more SDoH spans.
    Each span: (trigger_substring, category, fields_dict)
    """
    return {"text": text, "spans": spans or []}


# ---------------------------------------------------------------------------
# Synthetic documents. Every name/date/address/organization below is invented.
# ---------------------------------------------------------------------------
DOCS = [
    {
        "doc_id": "9001_synthetic",
        "title": "9001_Column_2.txt",
        "sw_name": "Jamie Ostrander, LCSW",
        "sentences": [
            S("9001\tPt, Avery Coleman, is a 5 year old female with a history of dilated "
              "cardiomyopathy referred by Dana Whitfield, RN, Transplant Coordinator, for "
              "Heart Transplant Psychosocial Assessment.",
              [("dilated cardiomyopathy referred by Dana Whitfield, RN, Transplant Coordinator, for Heart Transplant Psychosocial Assessment",
                "Healthcare", {"Experiencer": "patients", "HealthcareType": "assessment"})]),
            S("Information for this assessment was obtained through an interview with the "
              "parents and review of the medical records."),
            S("SW spent 50 minutes of face to face time with the family."),
            S("Living situation: Avery lives with her mother and father in Millbrook Hollow, Rivendale.",
              [("lives with her mother and father in Millbrook Hollow, Rivendale",
                "Living", {"Experiencer": "patients", "LivingStatus": "current",
                            "LivingType": "with both parents", "ResidentType": "home"})]),
            S("They reside in a two bedroom apartment with central heat and air conditioning.",
              [("reside in a two bedroom apartment with central heat and air conditioning",
                "Living", {"Experiencer": "parents/caregiver", "LivingStatus": "current",
                            "LivingType": "with both parents", "ResidentType": "home"})]),
            S("There is no smoking in the home.",
              [("no smoking in the home", "Smoke", {"Experiencer": "patients", "SmokeStatus": "none"})]),
            S("Support systems: the mother and father report leaning on each other and on "
              "extended family for support.",
              [("mother and father report leaning on each other and on extended family for support",
                "Social", {"Experiencer": "parents/caregiver", "SocialActivity": "high", "SocialType": "family"})]),
            S("Avery is enrolled in kindergarten and the school has been notified of her "
              "medical condition.",
              [("enrolled in kindergarten and the school has been notified of her medical condition",
                "Education", {"EducationStatus": "current", "EducationType": "childhood", "Experiencer": "patients"})]),
            S("Avery is covered by Rivendale State Medicaid.",
              [("covered by Rivendale State Medicaid", "Insurance", {"Experiencer": "patients", "InsuranceType": "public"})]),
            S("The family owns a reliable vehicle and reports no difficulty getting Avery to appointments.",
              [("owns a reliable vehicle and reports no difficulty getting Avery to appointments",
                "Transportation", {"Experiencer": "parents/caregiver",
                                     "TransportationConvenienceLevel": "easy",
                                     "TransportationType": "vehicle access"})]),
            S("The family lives approximately four hours from the transplant center, which "
              "adds to travel cost for appointments.",
              [("adds to travel cost for appointments",
                "Transportation", {"Experiencer": "patients and caregivers",
                                     "TransportationConvenienceLevel": "hard",
                                     "TransportationType": "transportation cost"})]),
            S("Course of illness: Avery was diagnosed with dilated cardiomyopathy after a "
              "routine well-child visit revealed an irregular heartbeat."),
            S("She was started on standard heart failure medications and has since been "
              "listed for transplant evaluation."),
            S("Financial situation: the family reports finances are tight due to the cost "
              "of frequent travel for appointments.",
              [("finances are tight due to the cost of frequent travel for appointments",
                "Financial", {"Experiencer": "parents/caregiver", "FinancialStatus": "constrain"})]),
            S("The father continues to work full time and the mother has reduced her hours "
              "to manage caregiving."),
            S("Assessment and recommendations: the family demonstrates a good understanding "
              "of the transplant process and appears well bonded with Avery."),
            S("Recommendations: continue to monitor the family's travel-related financial "
              "burden and connect them with the hospital's travel assistance fund.",
              [("connect them with the hospital's travel assistance fund",
                "Recommendation", {"RecommendationType": "increase financial support"})]),
        ],
    },
    {
        "doc_id": "9002_synthetic",
        "title": "9002_Column_2.txt",
        "sw_name": "Priya Nandakumar, LCSW",
        "sentences": [
            S("9002\tPt, Micah Torres, is a 12 year old male with a history of focal "
              "segmental glomerulosclerosis referred for Kidney Transplant Psychosocial "
              "Assessment.",
              [("focal segmental glomerulosclerosis referred for Kidney Transplant Psychosocial Assessment",
                "Healthcare", {"Experiencer": "patients", "HealthcareType": "assessment"})]),
            S("Information for this assessment was obtained through interviews with the "
              "patient and his mother, and review of the medical record."),
            S("SW spent 60 minutes of face to face time with patient and family."),
            S("Family history: the family reports a prior Department of Child and Family "
              "involvement approximately five years ago related to housing instability, "
              "which has since been resolved.",
              [("prior Department of Child and Family involvement approximately five years ago related to housing instability, which has since been resolved",
                "Trauma", {"Experiencer": "patients", "TraumaStatus": "past", "TraumaType": "DCF"})]),
            S("The family denies any current involvement with child protective services.",
              [("denies any current involvement with child protective services",
                "Trauma", {"Experiencer": "Family", "TraumaStatus": "none", "TraumaType": "DCF"})]),
            S("Mental health: Micah's mother reports a history of generalized anxiety, "
              "currently managed with outpatient counseling.",
              [("history of generalized anxiety, currently managed with outpatient counseling",
                "Mental Health", {"Experiencer": "Mother", "MentalHealthStatus": "current", "MentalHealthType": "anxiety"})]),
            S("Micah himself denies any mental health concerns at this time.",
              [("denies any mental health concerns at this time",
                "Mental Health", {"Experiencer": "patients", "MentalHealthStatus": "none"})]),
            S("Substance use: the family denies any current or past substance use in the home.",
              [("denies any current or past substance use in the home",
                "Substance Use", {"Experiencer": "Family", "SubstanceUseStatus": "none"})]),
            S("Adherence: the family reports occasional missed doses of Micah's "
              "immunosuppressant medication due to a hectic school schedule.",
              [("occasional missed doses of Micah's immunosuppressant medication due to a hectic school schedule",
                "Adherence", {"AdherenceLevel": "Low", "AdherenceType": "medication", "Experiencer": "patients"})]),
            S("The mother verbalizes a strong understanding of the medication regimen and "
              "transplant process.",
              [("strong understanding of the medication regimen and transplant process",
                "Adherence", {"AdherenceLevel": "High", "AdherenceType": "medication", "Experiencer": "Mother"})]),
            S("Assessment and recommendations: the primary psychosocial concern is "
              "moderate medication non-adherence related to scheduling conflicts.",
              [("moderate medication non-adherence related to scheduling conflicts",
                "Concern", {"ConcernLevel": "moderate"})]),
            S("The family appears otherwise well supported and engaged in Micah's care."),
            S("Recommendations: refer the family to the adherence support program and "
              "provide a pill organizer with alarm reminders.",
              [("refer the family to the adherence support program and provide a pill organizer with alarm reminders",
                "Recommendation", {"RecommendationType": "Help with Adherence"})]),
            S("Continue routine psychosocial follow-up at each clinic visit."),
        ],
    },
    {
        "doc_id": "9003_synthetic",
        "title": "9003_Column_2.txt",
        "sw_name": "Owen Whitfield, LCSW",
        "sentences": [
            S("9003\tPt, Naomi Ferraro, is a 16 year old female with a history of "
              "autoimmune hepatitis referred for Liver Transplant Psychosocial Assessment.",
              [("autoimmune hepatitis referred for Liver Transplant Psychosocial Assessment",
                "Healthcare", {"Experiencer": "patients", "HealthcareType": "assessment"})]),
            S("Information for this assessment was obtained through an interview with the "
              "patient and her father, and review of the medical record."),
            S("SW spent 45 minutes of face to face time with the family."),
            S("Employment: the father was recently laid off from his position at a "
              "local warehouse and is currently seeking new employment.",
              [("recently laid off from his position at a local warehouse and is currently seeking new employment",
                "Employment", {"EmploymentStatus": "Looking for", "Experiencer": "Father"})]),
            S("The mother works part time as a home health aide.",
              [("works part time as a home health aide", "Employment", {"EmploymentStatus": "part-time", "Experiencer": "Mother"})]),
            S("Financial situation: the family reports significant financial strain "
              "related to the father's recent job loss.",
              [("significant financial strain related to the father's recent job loss",
                "Financial", {"Experiencer": "Family", "FinancialStatus": "constrain"})]),
            S("Naomi is currently covered by a combination of private insurance through "
              "her mother's employer and state Medicaid.",
              [("covered by a combination of private insurance through her mother's employer and state Medicaid",
                "Insurance", {"Experiencer": "patients", "InsuranceType": "both"})]),
            S("Transportation: the family's only vehicle is unreliable, which has caused "
              "difficulty attending clinic appointments.",
              [("family's only vehicle is unreliable, which has caused difficulty attending clinic appointments",
                "Transportation", {"Experiencer": "Family",
                                     "TransportationConvenienceLevel": "hard",
                                     "TransportationType": "vehicle access"})]),
            S("Support systems: the family is active in their church community, which "
              "provides both emotional and occasional financial support.",
              [("active in their church community, which provides both emotional and occasional financial support",
                "Social", {"Experiencer": "Family", "SocialActivity": "high", "SocialType": "church"})]),
            S("There is no smoking or vaping in the home; the father reports quitting "
              "smoking two years ago.",
              [("father reports quitting smoking two years ago", "Smoke", {"Experiencer": "Father", "SmokeStatus": "past"})]),
            S("Health literacy: the father verbalizes some difficulty understanding the "
              "post-transplant medication schedule and would benefit from additional teaching.",
              [("some difficulty understanding the post-transplant medication schedule and would benefit from additional teaching",
                "Literacy", {"Experiencer": "Father", "LiteracyLevel": "Low", "LiteracyType": "medication knowledge"})]),
            S("Assessment and recommendations: the family is motivated and engaged despite "
              "current financial stressors."),
            S("Recommendations: connect the family with the hospital's financial "
              "counseling office and the transportation assistance program.",
              [("connect the family with the hospital's financial counseling office and the transportation assistance program",
                "Recommendation", {"RecommendationType": "increase financial support"})]),
            S("Provide additional one-on-one medication education for the father prior "
              "to discharge.",
              [("Provide additional one-on-one medication education for the father prior to discharge",
                "Recommendation", {"RecommendationType": "increase literacy"})]),
        ],
    },
    {
        "doc_id": "9004_synthetic",
        "title": "9004_Column_2.txt",
        "sw_name": "Dana Whitfield, LCSW",
        "sentences": [
            S("9004\tPt, Elias Byrne, is an 8 year old male with a history of cystic "
              "fibrosis referred for Lung Transplant Psychosocial Assessment.",
              [("cystic fibrosis referred for Lung Transplant Psychosocial Assessment",
                "Healthcare", {"Experiencer": "patients", "HealthcareType": "assessment"})]),
            S("Information for this assessment was obtained through an interview with the "
              "parents and review of the medical record."),
            S("SW spent 55 minutes of face to face time with the family."),
            S("Education: Elias is currently enrolled in a hospital homebound schooling "
              "program due to frequent admissions.",
              [("currently enrolled in a hospital homebound schooling program due to frequent admissions",
                "Education", {"EducationStatus": "current", "EducationType": "childhood", "Experiencer": "patients"})]),
            S("Family history: the mother reports a past episode of postpartum depression "
              "that was treated and has since resolved.",
              [("past episode of postpartum depression that was treated and has since resolved",
                "Mental Health", {"Experiencer": "Mother", "MentalHealthStatus": "past", "MentalHealthType": "depression"})]),
            S("The family denies any history of domestic violence or other trauma.",
              [("denies any history of domestic violence or other trauma",
                "Trauma", {"Experiencer": "Family", "TraumaStatus": "none", "TraumaType": "domestic violence"})]),
            S("Adherence: the parents report consistent adherence to Elias's airway "
              "clearance therapy and enzyme regimen.",
              [("consistent adherence to Elias's airway clearance therapy and enzyme regimen",
                "Adherence", {"AdherenceLevel": "High", "AdherenceType": "medication", "Experiencer": "parents/caregiver"})]),
            S("Health literacy: both parents demonstrate a strong understanding of Elias's "
              "illness and the transplant listing process.",
              [("strong understanding of Elias's illness and the transplant listing process",
                "Literacy", {"Experiencer": "parents/caregiver", "LiteracyLevel": "High", "LiteracyType": "transplant knowledge"})]),
            S("Assessment and recommendations: the family's primary concern is the "
              "emotional toll of Elias's frequent hospitalizations on his siblings.",
              [("emotional toll of Elias's frequent hospitalizations on his siblings",
                "Concern", {"ConcernLevel": "moderate"})]),
            S("The parents appear well informed, engaged, and appropriately bonded with "
              "Elias."),
            S("Recommendations: offer a referral to sibling support group services "
              "through the hospital's family resource center.",
              [("offer a referral to sibling support group services through the hospital's family resource center",
                "Recommendation", {"RecommendationType": "increase social support"})]),
            S("Continue routine psychosocial follow-up prior to transplant listing."),
        ],
    },
]

# ---------------------------------------------------------------------------
# Tokenizer: words/numbers (incl. simple contractions) or single punctuation
# chars, mirroring the coarse tokenization style seen in the real data.
# ---------------------------------------------------------------------------
TOKEN_RE = re.compile(r"[A-Za-z0-9]+(?:['/][A-Za-z0-9]+)*|[^\sA-Za-z0-9]")


def tokenize_with_offsets(text):
    return [(m.group(0), m.start(), m.end()) for m in TOKEN_RE.finditer(text)]


def bio_tags_for_sentence(text, spans):
    """spans: list of (trigger_substring, l1_category, fields). Returns
    (tokens, ner_tags) using the no-space NER category name."""
    tokens = tokenize_with_offsets(text)
    tags = ["O"] * len(tokens)
    for trigger, cat, _fields in spans:
        start = text.find(trigger)
        if start == -1:
            raise ValueError(f"trigger not found: {trigger!r} in {text!r}")
        end = start + len(trigger)
        ner_cat = CATS[cat]
        first = True
        for i, (_tok, ts, te) in enumerate(tokens):
            if ts >= start and te <= end:
                tags[i] = ("B-" if first else "I-") + ner_cat
                first = False
    return [t[0] for t in tokens], tags


def build_document_text(doc):
    """Builds the full note text and per-sentence (begin, end) offsets,
    joining sentences the way the real sofaString does (two spaces between
    sentences, matching the exported annotation format)."""
    parts = []
    offsets = []
    cursor = 0
    for i, sent in enumerate(doc["sentences"]):
        if i > 0:
            sep = "  "
            parts.append(sep)
            cursor += len(sep)
        start = cursor
        parts.append(sent["text"])
        cursor += len(sent["text"])
        offsets.append((start, cursor))
    footer = f"\n\n{doc['sw_name']}\nPediatric Transplant Team\n(000) 000-0000"
    parts.append(footer)
    full_text = "".join(parts)
    return full_text, offsets


# ---------------------------------------------------------------------------
# 1. UIMA CAS-JSON raw annotation export (1.tag/data/annotation_data,
#    2.label/data/annotation_data)
# ---------------------------------------------------------------------------
def build_uima_export(doc):
    full_text, sent_offsets = build_document_text(doc)

    sentence_fs = []
    token_fs = []
    level1_fs = []
    level2_fs = []

    for (sent, (s_begin, s_end)) in zip(doc["sentences"], sent_offsets):
        if s_begin == 0:
            sentence_fs.append({"sofa": 1, "end": s_end})
        else:
            sentence_fs.append({"sofa": 1, "begin": s_begin, "end": s_end})

        for tok, ts, te in tokenize_with_offsets(sent["text"]):
            abs_ts, abs_te = s_begin + ts, s_begin + te
            if abs_ts == 0:
                token_fs.append({"sofa": 1, "end": abs_te})
            else:
                token_fs.append({"sofa": 1, "begin": abs_ts, "end": abs_te})

        for trigger, cat, fields in sent["spans"]:
            local_start = sent["text"].find(trigger)
            abs_begin = s_begin + local_start
            abs_end = abs_begin + len(trigger)
            level1_fs.append({"sofa": 1, "begin": abs_begin, "end": abs_end, "SDoHlv1": cat})
            level2_entry = {"sofa": 1, "begin": abs_begin, "end": abs_end}
            level2_entry.update(fields)
            level2_fs.append(level2_entry)

    export = {
        "_context": {
            "_types": {
                "DocumentMetaData": {"_feature_types": {"sofa": "_ref"}},
                "SDoHLevel1": {"_feature_types": {"sofa": "_ref"}},
                "SDoHlevel2": {"_feature_types": {"sofa": "_ref"}},
                "Sentence": {"_feature_types": {"sofa": "_ref"}},
                "Sofa": {"_feature_types": {"sofaArray": "_ref"}},
                "Token": {"_feature_types": {"sofa": "_ref"}},
            }
        },
        "_views": {
            "_InitialView": {
                "DocumentMetaData": [
                    {
                        "sofa": 1,
                        "end": len(full_text),
                        "language": "x-unspecified",
                        "documentTitle": doc["title"],
                        "documentId": "CURATION_USER",
                        "isLastSegment": False,
                    }
                ],
                "Sentence": sentence_fs,
                "Token": token_fs,
                "SDoHLevel1": level1_fs,
                "SDoHlevel2": level2_fs,
            }
        },
        "_referenced_fss": {
            "1": {
                "_type": "Sofa",
                "sofaNum": 1,
                "sofaID": "_InitialView",
                "mimeType": "text",
                "sofaString": full_text,
            }
        },
    }
    return export


# ---------------------------------------------------------------------------
# 2. NER token-classification format (1.tag/data/train_data,
#    1.tag/data/splitted_data/*/*.json|iob|txt)
# ---------------------------------------------------------------------------
def build_ner_records(doc):
    records = []
    for i, sent in enumerate(doc["sentences"]):
        spans = [(t, c, f) for (t, c, f) in sent["spans"]]
        tokens, tags = bio_tags_for_sentence(sent["text"], spans)
        records.append({"id": i, "tokens": tokens, "ner_tags": tags})
    return records


def write_iob(records, path):
    with open(path, "w", encoding="utf-8") as f:
        for rec in records:
            toks = " ".join(["BOS"] + rec["tokens"] + ["EOS"])
            tags = " ".join(["O"] + rec["ner_tags"] + ["O"])
            f.write(f"{toks}\t{tags}\n")


def write_txt(records, path):
    with open(path, "w", encoding="utf-8") as f:
        for rec in records:
            line = " ".join(f"{tok}/{tag}" for tok, tag in zip(rec["tokens"], rec["ner_tags"]))
            f.write(line + "\n")


def write_split_json(records, doc_id, path):
    out = [{"id": f"{doc_id}-{r['id']}", "tokens": r["tokens"], "ner_tags": r["ner_tags"]} for r in records]
    with open(path, "w", encoding="utf-8") as f:
        json.dump(out, f, indent=2)


# ---------------------------------------------------------------------------
# 3. Ground-truth structured extraction (2.label/data/processed_data)
# ---------------------------------------------------------------------------
def build_processed_data(doc):
    out = {}
    for i, sent in enumerate(doc["sentences"]):
        entry = {"sentence": sent["text"]}
        if sent["spans"]:
            sdoh = []
            for _trigger, cat, fields in sent["spans"]:
                ordered = {k: fields[k] for k in REQUIRED_FIELDS[cat] if k in fields}
                sdoh.append({cat: ordered})
            entry["SDoH"] = sdoh
        out[str(i)] = entry
    return out


# ---------------------------------------------------------------------------
# 4. LLM extraction output (2.label/output/gpt4o_type,
#    2.label/output/gpt55_type_simple_experiencer)
#    gpt55_type_simple_experiencer collapses Experiencer down to a coarser
#    "patient" / "caregiver" / "family" bucket, matching the real run's
#    "simple experiencer" schema variant.
# ---------------------------------------------------------------------------
def simplify_experiencer(value):
    if value is None:
        return value
    v = value.lower()
    if v == "patients":
        return "patient"
    if "caregiver" in v or v in ("mother", "father", "parents/caregiver"):
        return "caregiver"
    return "family"


def build_llm_output(doc, simple_experiencer=False):
    out = []
    for sent in doc["sentences"]:
        categories = sorted({cat for (_t, cat, _f) in sent["spans"]}, key=lambda c: [t for t in sent["spans"] if t[1] == c][0][0])
        entry = {"sentence": sent["text"], "categories": [c for _t, c, _f in sent["spans"]] if False else [], "extracted_predictions": {}}
        # preserve first-seen order of categories
        seen = []
        for _t, cat, _f in sent["spans"]:
            if cat not in seen:
                seen.append(cat)
        entry["categories"] = seen
        preds = {}
        for cat in seen:
            conditions = []
            for trigger, c, fields in sent["spans"]:
                if c != cat:
                    continue
                cond = {"category": cat}
                for k in REQUIRED_FIELDS[cat]:
                    if k not in fields:
                        continue
                    v = fields[k]
                    if simple_experiencer and k == "Experiencer":
                        v = simplify_experiencer(v)
                    cond[k] = v
                conditions.append(cond)
            preds[cat] = {"extracted_conditions": conditions}
        entry["extracted_predictions"] = preds
        out.append(entry)
    return out


# ---------------------------------------------------------------------------
# 5. Trigger-word CSV (1.tag/output/GPT-4o-trigger.csv)
# ---------------------------------------------------------------------------
def build_trigger_rows(all_docs):
    rows = []
    idx = 0
    for doc in all_docs:
        for sent in doc["sentences"]:
            true_cats = []
            for _t, cat, _f in sent["spans"]:
                if cat not in true_cats:
                    true_cats.append(cat)
            # Simulate a realistic, mostly-correct but imperfect predictor:
            # every 5th labeled sentence "misses" one category, and every
            # 7th sentence overall produces a harmless extra (hallucinated)
            # category call, so this sample CSV exercises both failure modes.
            predict = list(true_cats)
            if true_cats and idx % 5 == 0:
                predict = predict[1:]
            if not true_cats and idx % 7 == 0:
                predict = ["Concern"]
            rows.append({"": idx, "Sentence": sent["text"], "True": str(true_cats), "predict": str(predict)})
            idx += 1
    return rows


# ---------------------------------------------------------------------------
# 6. Error-analysis eval CSV (2.label/eval/sdoh_error_analysis.csv)
# ---------------------------------------------------------------------------
def build_eval_rows(all_docs):
    rows = []
    for doc in all_docs:
        for sent in doc["sentences"]:
            if not sent["spans"]:
                continue
            for trigger, cat, fields in sent["spans"]:
                true_tuple = tuple(fields.get(k) for k in REQUIRED_FIELDS[cat])
                # Vary the outcome deterministically so the sample shows all
                # five status categories used by the real evaluation notebook.
                bucket = (hash((doc["doc_id"], trigger)) % 5)
                if bucket == 0:
                    pred_tuple, status = true_tuple, "Exact Match (TP)"
                elif bucket == 1:
                    altered = list(true_tuple)
                    if altered:
                        altered[0] = "unspecified"
                    pred_tuple, status = tuple(altered), "Partial Match (FP/FN)"
                elif bucket == 2:
                    pred_tuple, status = (), "Missed (FN)"
                elif bucket == 3:
                    pred_tuple, status = ("other",), "Hallucination (FP)"
                else:
                    pred_tuple, status = tuple(reversed(true_tuple)), "Complete Mismatch (FP/FN)"
                rows.append({
                    "doc_id": doc["doc_id"],
                    "sentence": sent["text"],
                    "category": cat,
                    "true_label": str(true_tuple),
                    "predicted_label": str(pred_tuple),
                    "status": status,
                })
    return rows


# ---------------------------------------------------------------------------
# Write everything out
# ---------------------------------------------------------------------------
def ensure_dir(path):
    os.makedirs(path, exist_ok=True)


def main():
    tag_annotation_dir = os.path.join(OUT_ROOT, "1.tag", "data", "annotation_data")
    tag_train_data_dir = os.path.join(OUT_ROOT, "1.tag", "data", "train_data")
    split_fold_dir = os.path.join(OUT_ROOT, "1.tag", "data", "splitted_data", "fold_1")
    tag_output_dir = os.path.join(OUT_ROOT, "1.tag", "output")

    label_annotation_dir = os.path.join(OUT_ROOT, "2.label", "data", "annotation_data")
    label_processed_dir = os.path.join(OUT_ROOT, "2.label", "data", "processed_data")
    label_output_4o_dir = os.path.join(OUT_ROOT, "2.label", "output", "gpt4o_type")
    label_output_55_dir = os.path.join(OUT_ROOT, "2.label", "output", "gpt55_type_simple_experiencer")
    label_eval_dir = os.path.join(OUT_ROOT, "2.label", "eval")

    for d in [tag_annotation_dir, tag_train_data_dir, split_fold_dir, tag_output_dir,
              label_annotation_dir, label_processed_dir, label_output_4o_dir,
              label_output_55_dir, label_eval_dir]:
        ensure_dir(d)

    all_train_records = []  # (doc_id, records)
    for doc in DOCS:
        doc_id = doc["doc_id"]

        # 1) Raw UIMA CAS-JSON export -- identical content published under
        #    both 1.tag and 2.label, mirroring the real repo's layout.
        export = build_uima_export(doc)
        for target_dir in (tag_annotation_dir, label_annotation_dir):
            with open(os.path.join(target_dir, f"{doc_id}.xmi.zip.json"), "w", encoding="utf-8") as f:
                json.dump(export, f, indent=2)

        # 2) NER tokens/ner_tags training format
        records = build_ner_records(doc)
        with open(os.path.join(tag_train_data_dir, f"{doc_id}.xmi.zip.json"), "w", encoding="utf-8") as f:
            json.dump(records, f, indent=2)
        all_train_records.append((doc_id, records))

        # 3) Ground-truth structured SDoH extraction
        processed = build_processed_data(doc)
        with open(os.path.join(label_processed_dir, f"{doc_id}.json"), "w", encoding="utf-8") as f:
            json.dump(processed, f, indent=2)

        # 4) LLM extraction outputs
        gpt4o = build_llm_output(doc, simple_experiencer=False)
        with open(os.path.join(label_output_4o_dir, f"{doc_id}_extracted.json"), "w", encoding="utf-8") as f:
            json.dump(gpt4o, f, indent=2)

        gpt55 = build_llm_output(doc, simple_experiencer=True)
        with open(os.path.join(label_output_55_dir, f"{doc_id}_extracted.json"), "w", encoding="utf-8") as f:
            json.dump(gpt55, f, indent=2)

    # 5) 5-fold-style split: last doc is "test", rest are "train" (fold_1 sample)
    train_docs = all_train_records[:-1]
    test_docs = all_train_records[-1:]

    def flatten(doc_records):
        out = []
        for doc_id, records in doc_records:
            out.extend(records)
        return out

    train_flat = flatten(train_docs)
    test_flat = flatten(test_docs)

    write_iob(train_flat, os.path.join(split_fold_dir, "train.iob"))
    write_txt(train_flat, os.path.join(split_fold_dir, "train.txt"))
    write_split_json(train_flat, "train", os.path.join(split_fold_dir, "train.json"))

    write_iob(test_flat, os.path.join(split_fold_dir, "test.iob"))
    write_txt(test_flat, os.path.join(split_fold_dir, "test.txt"))
    write_split_json(test_flat, "test", os.path.join(split_fold_dir, "test.json"))

    # 6) Trigger-word CSV
    trigger_rows = build_trigger_rows(DOCS)
    with open(os.path.join(tag_output_dir, "GPT-4o-trigger.csv"), "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["", "Sentence", "True", "predict"])
        writer.writeheader()
        writer.writerows(trigger_rows)

    # 7) Error-analysis eval CSV
    eval_rows = build_eval_rows(DOCS)
    with open(os.path.join(label_eval_dir, "sdoh_error_analysis.csv"), "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["doc_id", "sentence", "category", "true_label", "predicted_label", "status"])
        writer.writeheader()
        writer.writerows(eval_rows)

    print("Synthetic sample data written to:", OUT_ROOT)
    print("Docs:", [d["doc_id"] for d in DOCS])
    print("Train sentences:", len(train_flat), "Test sentences:", len(test_flat))
    print("Trigger CSV rows:", len(trigger_rows))
    print("Eval CSV rows:", len(eval_rows))


if __name__ == "__main__":
    main()
