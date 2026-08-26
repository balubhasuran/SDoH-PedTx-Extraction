"""
Standalone logic tests for the GUI modules that don't require torch/
transformers/openai to actually be installed (this sandbox has no network
access to PyPI). Run with fake torch/transformers/openai stubs on the
PYTHONPATH so the real import statements in ner_inference.py / llm_extraction.py
succeed, then exercise the pure-Python logic (regex tokenizer, BIO decoding,
schema loading/resolution, prompt + response parsing) directly.

This file is scratch/dev-only -- delete it once you've installed the real
dependencies and verified the app runs end-to-end with real models + API key.
"""

import json
import sys

import ner_inference
import llm_extraction


def check(label, cond):
    status = "PASS" if cond else "FAIL"
    print(f"[{status}] {label}")
    if not cond:
        FAILURES.append(label)


FAILURES = []

# ---------------------------------------------------------------------------
# tokenize_with_offsets
# ---------------------------------------------------------------------------
text = "The patient's mother lost her job; family can't pay rent (urgent)."
spans = ner_inference.tokenize_with_offsets(text)
check("tokenize_with_offsets: non-empty", len(spans) > 0)
check(
    "tokenize_with_offsets: offsets reconstruct tokens",
    all(text[s:e] == w for w, s, e in spans),
)
check(
    "tokenize_with_offsets: splits punctuation as separate tokens",
    any(w == ";" for w, _, _ in spans) and any(w == "(" for w, _, _ in spans),
)
check(
    "tokenize_with_offsets: keeps contraction together",
    any(w == "patient's" for w, _, _ in spans) or any(w == "can't" for w, _, _ in spans),
)

# ---------------------------------------------------------------------------
# _decode_bio
# ---------------------------------------------------------------------------
sample = "mother lost her job and can not pay rent today"
sample_spans = ner_inference.tokenize_with_offsets(sample)
words = [w for w, _, _ in sample_spans]
print("words:", words)

# Simulate two trigger spans: "lost her job" (Employment, B-I-I) and
# "pay rent" (Financial, B-I), with an O gap and a non-trigger word between.
word_label = {
    1: "B-Employment",  # lost
    2: "I-Employment",  # her
    3: "I-Employment",  # job
    7: "B-Financial",   # pay
    8: "I-Financial",   # rent
}
triggers = ner_inference.TriggerExtractor._decode_bio(sample, sample_spans, word_label)
check("decode_bio: finds 2 spans", len(triggers) == 2)
check(
    "decode_bio: first span text/category correct",
    triggers and triggers[0]["category"] == "Employment" and triggers[0]["text"] == "lost her job",
)
check(
    "decode_bio: second span text/category correct",
    len(triggers) > 1 and triggers[1]["category"] == "Financial" and triggers[1]["text"] == "pay rent",
)

# B immediately after B of a *different* category with no O between -> 2 spans
word_label_adjacent = {1: "B-Employment", 2: "B-Financial"}
triggers_adj = ner_inference.TriggerExtractor._decode_bio(sample, sample_spans, word_label_adjacent)
check("decode_bio: adjacent different-category B- tags split into 2 spans", len(triggers_adj) == 2)

# ---------------------------------------------------------------------------
# llm_extraction: schema loading + category-name resolution
# ---------------------------------------------------------------------------
schemas = llm_extraction.load_category_schemas()
check("load_category_schemas: loaded 16 categories", len(schemas) == 16)

check(
    "resolve_schema_key: direct match (Healthcare)",
    llm_extraction.resolve_schema_key("Healthcare", schemas) == "Healthcare",
)
check(
    "resolve_schema_key: MentalHealth -> 'Mental Health'",
    llm_extraction.resolve_schema_key("MentalHealth", schemas) == "Mental Health",
)
check(
    "resolve_schema_key: SubstanceUse -> 'Substance Use'",
    llm_extraction.resolve_schema_key("SubstanceUse", schemas) == "Substance Use",
)
check(
    "resolve_schema_key: unknown category -> None",
    llm_extraction.resolve_schema_key("NotARealCategory", schemas) is None,
)

# all 16 NER label categories must resolve to a schema (no silent gaps)
ner_categories = [
    "Adherence", "Concern", "Education", "Employment", "Financial", "Healthcare",
    "Insurance", "Literacy", "Living", "MentalHealth", "Recommendation", "Smoke",
    "Social", "SubstanceUse", "Transportation", "Trauma",
]
unresolved = [c for c in ner_categories if llm_extraction.resolve_schema_key(c, schemas) is None]
check(f"resolve_schema_key: all 16 NER categories resolve (unresolved={unresolved})", not unresolved)

# ---------------------------------------------------------------------------
# DetailExtractor.extract() full round trip against the fake OpenAI client
# ---------------------------------------------------------------------------
extractor = llm_extraction.DetailExtractor(model="gpt-4o-2024-08-06", api_key="fake-key", schemas=schemas)

canned = {
    "category": "Financial",
    "Experiencer": "caregivers",
    "financial_status": "constrain",
}
extractor.client._completions.canned_args_by_func["extract_financial_info"] = json.dumps(
    {"extracted_conditions": [canned]}
)

result = extractor.extract(
    "The family can not pay rent this month.", "Financial", context="Mother lost her job."
)
check("DetailExtractor.extract: no error", "error" not in result)
check(
    "DetailExtractor.extract: parsed extracted_conditions",
    result.get("extracted_conditions") == [canned],
)

last_kwargs = extractor.client._completions.last_kwargs
check(
    "DetailExtractor.extract: forced tool_choice to extract_financial_info",
    last_kwargs["tool_choice"]["function"]["name"] == "extract_financial_info",
)
check(
    "DetailExtractor.extract: tools[0] schema name matches",
    last_kwargs["tools"][0]["function"]["name"] == "extract_financial_info",
)

# malformed JSON from the model -> graceful error, not an exception
extractor.client._completions.canned_args_by_func["extract_financial_info"] = "{not valid json"
bad_result = extractor.extract("x", "Financial")
check("DetailExtractor.extract: malformed JSON reported as error", "error" in bad_result)
check("DetailExtractor.extract: malformed JSON keeps raw_output", "raw_output" in bad_result)

# unmapped category -> error dict, no exception
none_result = extractor.extract("x", "NotARealCategory")
check("DetailExtractor.extract: unknown category -> error dict", "error" in none_result)

# ---------------------------------------------------------------------------
print()
if FAILURES:
    print(f"{len(FAILURES)} check(s) FAILED:")
    for f in FAILURES:
        print(" -", f)
    sys.exit(1)
else:
    print("All checks passed.")
