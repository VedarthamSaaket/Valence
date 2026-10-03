import os
import re
import threading
from typing import List, Optional

MODEL_NAME = os.getenv("MEANING_CHECK_MODEL", "MoritzLaurer/DeBERTa-v3-base-mnli-fever-anli")
ENABLED = os.getenv("ENABLE_MEANING_CHECK", "true").lower() in ("1", "true", "yes")
CONTRADICTION_THRESHOLD = float(os.getenv("MEANING_CONTRADICTION_THRESHOLD", "0.9"))
ENTAILMENT_THRESHOLD = float(os.getenv("MEANING_ENTAILMENT_THRESHOLD", "0.5"))

_lock = threading.Lock()
_state = {"tokenizer": None, "model": None, "labels": None, "failed": False}


def load() -> bool:
    if not ENABLED or _state["failed"]:
        return False
    if _state["model"] is not None:
        return True
    with _lock:
        if _state["model"] is not None:
            return True
        try:
            from transformers import AutoModelForSequenceClassification, AutoTokenizer
            tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
            model = AutoModelForSequenceClassification.from_pretrained(MODEL_NAME).eval()
            _state["labels"] = {v.lower(): k for k, v in model.config.id2label.items()}
            _state["tokenizer"], _state["model"] = tokenizer, model
            print("[meaning] entailment checker ready")
            return True
        except Exception as e:
            _state["failed"] = True
            print(f"[meaning] entailment checker unavailable: {type(e).__name__}: {e}")
            return False


def split_sentences(text: str) -> List[str]:
    parts = re.split(r"(?<=[.!?])\s+(?=[A-Z])", text.strip())
    return [p.strip() for p in parts if len(p.strip()) > 15]


def check(text: str, premises: List[str]) -> Optional[dict]:
    if not premises or not load():
        return None
    import torch
    sentences = split_sentences(text)
    if not sentences:
        return None
    pairs = [(p, s) for s in sentences for p in premises]
    with _lock:
        encoded = _state["tokenizer"]([p for p, _ in pairs], [s for _, s in pairs],
                                      return_tensors="pt", truncation=True, padding=True, max_length=256)
        with torch.no_grad():
            probs = torch.softmax(_state["model"](**encoded).logits, dim=-1)
    c_idx, e_idx = _state["labels"]["contradiction"], _state["labels"]["entailment"]
    n = len(premises)
    contradicted, supported = [], 0
    for i, sentence in enumerate(sentences):
        block = probs[i * n:(i + 1) * n]
        if float(block[:, c_idx].max()) >= CONTRADICTION_THRESHOLD:
            contradicted.append(sentence)
        elif float(block[:, e_idx].max()) >= ENTAILMENT_THRESHOLD:
            supported += 1
    return {"sentences": len(sentences), "supported": supported, "contradicted": contradicted}
