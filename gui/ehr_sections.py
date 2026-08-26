"""
EHR sectionizing for the SDoH GUI.

When the user pastes a whole electronic health record note, this module
splits it into clinical sections so the pipeline can focus on the parts
that are likely to contain SDoH information (Social History, HPI, etc.).

Primary engine: medspacy's `medspacy_sectionizer` (rule-based detection of
section headers like "Social History:", "HPI:", "Assessment/Plan:").
Fallback engine: a lightweight regex header detector used automatically if
medspacy is not installed or fails to load, so the app still works.

Every section is returned as a plain dict with *global character offsets*
into the original text:

    {
        "title":    str,   # header text as it appears in the note ("" if none)
        "category": str,   # normalized category, e.g. "social_history"
        "start":    int,   # section start (including header) in the full text
        "end":      int,   # section end in the full text
        "body_start": int, # first char after the header
        "relevant": bool,  # True if the category is SDoH-relevant by default
    }
"""

import re
from functools import lru_cache

# Section categories that are checked by default because they commonly
# contain SDoH content (employment, housing, substance use, adherence,
# recommendations, ...). Everything else is still shown and can be toggled on.
SDOH_RELEVANT_CATEGORIES = {
    "social_history",
    "sexual_and_social_history",
    "history_of_present_illness",
    "chief_complaint",
    "hospital_course",
    "observation_and_plan",
    "patient_instructions",
    "patient_education",
    "preamble",  # untitled text before the first header
    "other",     # unrecognized headers — err on the side of inclusion
}


# --------------------------------------------------------------------------
# medspacy engine
# --------------------------------------------------------------------------

@lru_cache(maxsize=1)
def _load_medspacy_nlp():
    """Build a minimal spaCy pipeline with medspacy's sectionizer."""
    import spacy
    import medspacy  # noqa: F401  (registers the medspacy_* factories)

    nlp = spacy.blank("en")
    nlp.max_length = 2_000_000
    nlp.add_pipe("medspacy_sectionizer")
    return nlp


def _sectionize_medspacy(text):
    nlp = _load_medspacy_nlp()
    doc = nlp(text)

    sections = []
    for sec in doc._.sections:
        category = getattr(sec, "category", None)
        title_span = getattr(sec, "title_span", None)
        body_span = getattr(sec, "body_span", None)
        section_span = getattr(sec, "section_span", None)
        if section_span is None:
            continue

        title = title_span.text.strip() if title_span is not None and len(title_span) else ""
        body_start = body_span.start_char if body_span is not None and len(body_span) else section_span.start_char
        category = category or ("preamble" if not title else "other")

        sections.append({
            "title": title,
            "category": category,
            "start": section_span.start_char,
            "end": section_span.end_char,
            "body_start": body_start,
            "relevant": category in SDOH_RELEVANT_CATEGORIES,
        })
    return sections


# --------------------------------------------------------------------------
# regex fallback engine
# --------------------------------------------------------------------------

# normalized header text -> category (mirrors medspacy's default categories)
_HEADER_CATEGORY_MAP = {
    "chief complaint": "chief_complaint",
    "cc": "chief_complaint",
    "history of present illness": "history_of_present_illness",
    "hpi": "history_of_present_illness",
    "history": "history_of_present_illness",
    "social history": "social_history",
    "psychosocial history": "social_history",
    "social hx": "social_history",
    "sh": "social_history",
    "sexual and social history": "sexual_and_social_history",
    "past medical history": "past_medical_history",
    "pmh": "past_medical_history",
    "past medical hx": "past_medical_history",
    "past surgical history": "surgical_history",
    "surgical history": "surgical_history",
    "family history": "family_history",
    "fh": "family_history",
    "medications": "medications",
    "current medications": "medications",
    "medications on admission": "medications",
    "discharge medications": "medications",
    "allergies": "allergies",
    "review of systems": "review_of_systems",
    "ros": "review_of_systems",
    "physical exam": "physical_exam",
    "physical examination": "physical_exam",
    "exam": "physical_exam",
    "vital signs": "vital_signs",
    "vitals": "vital_signs",
    "labs": "labs_and_studies",
    "laboratory data": "labs_and_studies",
    "laboratory studies": "labs_and_studies",
    "lab results": "labs_and_studies",
    "imaging": "imaging",
    "radiology": "imaging",
    "assessment": "observation_and_plan",
    "assessment and plan": "observation_and_plan",
    "assessment/plan": "observation_and_plan",
    "impression": "observation_and_plan",
    "impression and plan": "observation_and_plan",
    "plan": "observation_and_plan",
    "hospital course": "hospital_course",
    "brief hospital course": "hospital_course",
    "discharge instructions": "patient_instructions",
    "patient instructions": "patient_instructions",
    "followup instructions": "patient_instructions",
    "follow-up instructions": "patient_instructions",
    "patient education": "patient_education",
    "problem list": "problem_list",
    "diagnosis": "diagnoses",
    "diagnoses": "diagnoses",
    "discharge diagnosis": "diagnoses",
    "admitting diagnosis": "diagnoses",
    "immunizations": "immunizations",
    "signature": "signature",
}

# A header is a short line-initial phrase ending with ":" (e.g. "Social History:")
# or an ALL-CAPS line (e.g. "SOCIAL HISTORY").
_HEADER_RE = re.compile(
    r"^[ \t]*(?P<title>[A-Za-z][A-Za-z0-9 /&'().\-]{0,60}?)[ \t]*:",
    re.MULTILINE,
)
_CAPS_LINE_RE = re.compile(r"^[ \t]*(?P<title>[A-Z][A-Z0-9 /&'().\-]{2,60})[ \t]*$", re.MULTILINE)


def _normalize_header(title):
    return re.sub(r"\s+", " ", title).strip().lower()


def _sectionize_regex(text):
    headers = []
    seen_starts = set()
    for regex, mapped_only in ((_HEADER_RE, False), (_CAPS_LINE_RE, True)):
        for m in regex.finditer(text):
            title = m.group("title").strip()
            norm = _normalize_header(title)
            category = _HEADER_CATEGORY_MAP.get(norm)
            # For plain "Word:" headers accept unknown ones (as "other") only
            # if reasonably short; for bare ALL-CAPS lines require a known name
            # to avoid treating shouted sentences as headers.
            if category is None:
                if mapped_only or len(norm.split()) > 5:
                    continue
                category = "other"
            if m.start() in seen_starts:
                continue
            seen_starts.add(m.start())
            headers.append({
                "title": title,
                "category": category,
                "start": m.start(),
                "body_start": m.end(),
            })

    headers.sort(key=lambda h: h["start"])

    sections = []
    if not headers or headers[0]["start"] > 0:
        end = headers[0]["start"] if headers else len(text)
        if text[:end].strip():
            sections.append({
                "title": "",
                "category": "preamble",
                "start": 0,
                "end": end,
                "body_start": 0,
                "relevant": True,
            })

    for i, h in enumerate(headers):
        end = headers[i + 1]["start"] if i + 1 < len(headers) else len(text)
        sections.append({
            "title": h["title"],
            "category": h["category"],
            "start": h["start"],
            "end": end,
            "body_start": h["body_start"],
            "relevant": h["category"] in SDOH_RELEVANT_CATEGORIES,
        })
    return sections


# --------------------------------------------------------------------------
# public API
# --------------------------------------------------------------------------

def sectionize(text):
    """
    Split an EHR note into sections.

    Returns (sections, engine) where engine is "medspacy" or "regex".
    Falls back to the regex engine if medspacy is unavailable or errors.
    """
    try:
        sections = _sectionize_medspacy(text)
        if sections:
            return sections, "medspacy"
    except Exception:
        pass
    return _sectionize_regex(text), "regex"


def section_for_offset(sections, offset):
    """Return the section dict containing a character offset (or None)."""
    for sec in sections:
        if sec["start"] <= offset < sec["end"]:
            return sec
    return None
