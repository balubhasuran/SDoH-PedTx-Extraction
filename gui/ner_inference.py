"""
Level-1 SDoH extraction: load a fine-tuned token-classification model
(BERT / BioBERT / RoBERTa, trained via 1.tag/ner_code/run_ner.py) and run
inference on raw free text to find SDoH "trigger word" spans + categories.

The training pipeline tokenized sentences into INCEpTION-derived word-level
tokens, then used `tokenizer(..., is_split_into_words=True)` + `word_ids()`
to align labels to subwords (see run_ner.py: tokenize_and_align_labels).
At inference time there is no INCEpTION tokenizer available, so this module
approximates it with a regex word tokenizer that splits on whitespace while
keeping punctuation as separate tokens (close to how the training data looks
in 1.tag/data/splitted_data/**/test.json). This mirrors the *shape* of
training-time tokenization closely enough for a fine-tuned subword model to
generalize, even though it won't be byte-for-byte identical to INCEpTION's
own segmentation rules.
"""

import re
from functools import lru_cache

import torch
from transformers import AutoModelForTokenClassification, AutoTokenizer

# Word-ish tokens (letters/digits/underscore, optionally hyphenated) OR a
# single punctuation/symbol character. Keeps contractions like "doesn't"
# together-ish while still splitting trailing punctuation.
_TOKEN_RE = re.compile(r"[A-Za-z0-9]+(?:[-'][A-Za-z0-9]+)*|[^\sA-Za-z0-9]")


def tokenize_with_offsets(text: str):
    """Split text into word-level tokens, keeping (token, start, end) offsets."""
    return [(m.group(), m.start(), m.end()) for m in _TOKEN_RE.finditer(text)]


class TriggerExtractor:
    """Loads one fine-tuned NER checkpoint and extracts SDoH trigger spans."""

    def __init__(self, model_dir: str, device: str = "cpu"):
        self.model_dir = model_dir
        self.tokenizer = AutoTokenizer.from_pretrained(model_dir)
        self.model = AutoModelForTokenClassification.from_pretrained(model_dir)
        self.model.to(device)
        self.model.eval()
        self.device = device
        self.id2label = self.model.config.id2label

    @torch.no_grad()
    def extract(self, text: str):
        """
        Returns a list of trigger dicts:
            {"category": str, "text": str, "start": int, "end": int}
        `start`/`end` are character offsets into `text`.
        """
        spans = tokenize_with_offsets(text)
        if not spans:
            return []

        words = [w for w, _, _ in spans]
        encoding = self.tokenizer(
            words,
            is_split_into_words=True,
            truncation=True,
            max_length=512,
            return_tensors="pt",
        )
        word_ids = encoding.word_ids(batch_index=0)
        encoding = {k: v.to(self.device) for k, v in encoding.items()}

        logits = self.model(**encoding).logits[0]
        pred_ids = logits.argmax(dim=-1).tolist()

        # Keep only the label of the *first* subtoken of each word, matching
        # how labels were assigned during training (label_all_tokens=False).
        word_label = {}
        for tok_idx, w_id in enumerate(word_ids):
            if w_id is None or w_id in word_label:
                continue
            word_label[w_id] = self.id2label[pred_ids[tok_idx]]

        return self._decode_bio(text, spans, word_label)

    @staticmethod
    def _decode_bio(text, spans, word_label):
        triggers = []
        current = None

        for i, (_, start, end) in enumerate(spans):
            label = word_label.get(i, "O")
            if label == "O" or "-" not in label:
                if current:
                    triggers.append(current)
                    current = None
                continue

            tag, category = label.split("-", 1)
            if tag == "B" or current is None or current["category"] != category:
                if current:
                    triggers.append(current)
                current = {"category": category, "start": start, "end": end}
            else:  # tag == "I" continuing the same category span
                current["end"] = end

        if current:
            triggers.append(current)

        for t in triggers:
            t["text"] = text[t["start"]:t["end"]]
        return triggers


@lru_cache(maxsize=8)
def _cached_extractor(model_dir: str) -> TriggerExtractor:
    return TriggerExtractor(model_dir)


def get_extractor(model_dir: str) -> TriggerExtractor:
    """Process-wide cache so each model checkpoint is only loaded once."""
    return _cached_extractor(model_dir)
