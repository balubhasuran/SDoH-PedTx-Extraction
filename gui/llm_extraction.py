"""
Level-2 SDoH extraction: given a sentence and the SDoH category found by the
Level-1 NER model, call the OpenAI API (forced function/tool calling, strict
JSON schema) to pull out structured detail fields.

Mirrors the pattern used in 2.label/notebooks/LLM_label_prediction.ipynb
(process_document): one strict function schema per category, loaded from
2.label/config/sdoh_extraction_schema_strict_type_simple_experiencer.json,
forced via tool_choice, response parsed from the tool call arguments.
"""

import json
import os
from typing import Optional

from openai import OpenAI

_THIS_DIR = os.path.dirname(os.path.abspath(__file__))
SCHEMA_PATH = os.path.join(
    _THIS_DIR, "..", "2.label", "config",
    "sdoh_extraction_schema_strict_type_simple_experiencer.json",
)

# The NER model's BIO labels have no spaces (MentalHealth, SubstanceUse);
# the Level-2 schema file keys a couple of categories with spaces.
NER_TO_SCHEMA_CATEGORY = {
    "MentalHealth": "Mental Health",
    "SubstanceUse": "Substance Use",
}

DEFAULT_MODEL = "gpt-4o-2024-08-06"


def load_category_schemas(path: str = SCHEMA_PATH) -> dict:
    with open(path, "r") as f:
        return json.load(f)


def resolve_schema_key(category: str, schemas: dict) -> Optional[str]:
    if category in schemas:
        return category
    mapped = NER_TO_SCHEMA_CATEGORY.get(category)
    if mapped in schemas:
        return mapped
    return None


class DetailExtractor:
    """Calls OpenAI to extract Level-2 structured detail for one category."""

    def __init__(self, model: str = DEFAULT_MODEL, api_key: Optional[str] = None,
                 schemas: Optional[dict] = None):
        self.model = model
        self.client = OpenAI(api_key=api_key) if api_key else OpenAI()
        self.schemas = schemas if schemas is not None else load_category_schemas()

    def extract(self, sentence: str, category: str, context: str = "") -> dict:
        """
        sentence: the sentence containing the trigger word (current sentence).
        category: Level-1 category name as produced by the NER model
                   (e.g. "MentalHealth", "Financial").
        context:  optional surrounding text (e.g. neighboring sentences) used
                   only to resolve pronouns / the Experiencer, per the
                   notebook's prompt convention.
        """
        schema_key = resolve_schema_key(category, self.schemas)
        if schema_key is None:
            return {"error": f"No Level-2 schema found for category '{category}'"}

        func_schema = self.schemas[schema_key]
        tool = {"type": "function", "function": func_schema}

        prompt = (
            f'Context sentences for reference: "{context}"\n\n'
            f'Current sentence to process: "{sentence}"\n\n'
            f"Target category: {schema_key}\n\n"
            "Task: Extract structured information strictly for the current "
            "sentence.\n"
            "Rules:\n"
            "1. Use the context sentences only to resolve pronouns or identify "
            "the Experiencer, never to pull in events that only occurred in "
            "the context.\n"
            "2. Only use enum values defined in the schema.\n"
            "3. If no valid information for this category appears in the "
            'current sentence, return {"extracted_conditions": []}.\n'
        )

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "You are a clinical social-determinants-of-health "
                            "information extraction assistant. Call the "
                            "provided tool and follow its schema exactly."
                        ),
                    },
                    {"role": "user", "content": prompt},
                ],
                tools=[tool],
                tool_choice={"type": "function", "function": {"name": func_schema["name"]}},
                temperature=0,
            )
        except Exception as e:  # network/auth/rate-limit errors, etc.
            return {"error": f"OpenAI API error: {e}"}

        tool_calls = response.choices[0].message.tool_calls
        if not tool_calls:
            return {"error": "Model did not return a tool call"}

        args_str = tool_calls[0].function.arguments
        try:
            return json.loads(args_str)
        except json.JSONDecodeError:
            return {"error": "Could not parse model output as JSON", "raw_output": args_str}
