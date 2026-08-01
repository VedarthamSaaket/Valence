# backend/ml/psych_layer.py
"""
Psychology model augmentation layer for Valence.

Two layers, mirroring the proven Lumina architecture:

Layer A , small HuggingFace Inference API classifiers (free serverless tier).
    Used to classify the user's volunteered context notes (emotion / mental
    state spectrum) so the heavier models receive an affect signal alongside
    the raw trait profile.

Layer B , specialty psychology LLMs (too heavy for the serverless tier),
    hosted on a dedicated Hugging Face Space (Docker, llama.cpp, GGUF quants,
    static *.hf.space URL). The Space sleeps when unused and wakes on any
    HTTP request , no public backend, no callbacks, no Kaggle quota:

        Instrument family        | Model                    | Spec
        -------------------------|--------------------------|-----------------------------------------
        mood/clinical (dass,who5)| MentaLLaMA-chat-7B       | interpretable mental-health justification
        trait-clinical (pid5,...)| PsychoLexLLaMA-8B        | academic psych terminology enrichment
        relational (attachment,..)| PsychoCounsel-Llama3    | therapist decision-alignment
        broad personality (rest) | PsyLLM-8B                | DSM-5/ICD-11 + CBT/ACT frameworks

Warm-while-testing contract
---------------------------
The frontend pings /api/psych/warmup/{test_id} the moment a questionnaire
opens and keeps pinging while the test is in progress. That keeps Layer A
models out of cold storage, wakes the Space if it was sleeping, and tells it
to hold this test's specialty model resident in RAM, so enrichment after
submit runs against a hot worker.

Enrich + monitor + fine-tuning corpus
-------------------------------------
Every enrichment call is logged as a JSONL record (input profile, prompt,
model output, latency) under ml/finetune_data/{test_id}.jsonl. That corpus is
the monitored fine-tuning dataset for the specialty models.

Fail-soft semantics everywhere: any failure returns None / leaves the result
untouched. A user submit never hard-fails because a model was unreachable.
"""

from __future__ import annotations

import asyncio
import hashlib
import json
import os
import threading
import time
from collections import OrderedDict
from typing import Dict, List, Optional

import httpx

# ─── Config (env-driven, mirrors the Lumina layer) ───────────────────────────

HF_API_KEY = os.getenv("HF_API_KEY", "")
ENABLE_PSYCH_AUGMENT = os.getenv("ENABLE_PSYCH_AUGMENT", "true").lower() in ("1", "true", "yes")
ENABLE_SPECIALTY_PSYCH = os.getenv("ENABLE_SPECIALTY_PSYCH", "true").lower() in ("1", "true", "yes")

# Layer A classifiers , per-signal pins, env-overridable.
PSYCH_MODEL_NOTES     = os.getenv("PSYCH_MODEL_NOTES",     "mental/mental-bert-base-uncased")
PSYCH_MODEL_EMOTION   = os.getenv("PSYCH_MODEL_EMOTION",   "SamLowe/roberta-base-go_emotions")
PSYCH_MODEL_SENTIMENT = os.getenv("PSYCH_MODEL_SENTIMENT", "cardiffnlp/twitter-roberta-base-sentiment-latest")

HF_MODELS = [PSYCH_MODEL_NOTES, PSYCH_MODEL_EMOTION, PSYCH_MODEL_SENTIMENT]

# Layer B manual fallback URLs (paste a Colab/ngrok URL to pin a worker).
COLAB_URL_PSYLLM        = os.getenv("COLAB_URL_PSYLLM", "")
COLAB_URL_PSYCHOCOUNSEL = os.getenv("COLAB_URL_PSYCHOCOUNSEL", "")
COLAB_URL_PSYCHOLEX     = os.getenv("COLAB_URL_PSYCHOLEX", "")
COLAB_URL_MENTALLAMA    = os.getenv("COLAB_URL_MENTALLAMA", "")

SPECIALTY_REGISTRY_SECRET = os.getenv("SPECIALTY_REGISTRY_SECRET", "")

# The dedicated Hugging Face Space hosting the specialty models. Static URL,
# reachable from anywhere, wakes from sleep on any HTTP request , the local
# backend never needs to be publicly reachable. Deploy with deploy_space.py.
SPECIALTY_SPACE_URL = os.getenv(
    "SPECIALTY_SPACE_URL", "https://vaedarth-valence-psych-host.hf.space"
)
# CPU inference on the free Space tier is slow (tens of seconds); enrichment
# runs in a background thread after submit, so a long timeout costs nothing.
SPECIALTY_INFER_TIMEOUT = float(os.getenv("SPECIALTY_INFER_TIMEOUT", "240"))

FINETUNE_DIR = os.path.join(os.path.dirname(__file__), "finetune_data")

HF_BASE = "https://api-inference.huggingface.co/models"
# Fallback endpoint. HF migrated many hosted classifiers to router.hf.co in
# 2024, on Windows resolvers where api-inference.huggingface.co DNS drops
# (getaddrinfo failed), the .hf.space wildcard usually still resolves, and
# router.huggingface.co is on the same edge network.
HF_ROUTER_BASE = "https://router.huggingface.co/hf-inference/models"

MODEL_KEYS = ("psyllm", "psychocounsel", "psycholex", "mentallama")
PRIORITY = ("lightning", "space", "kaggle", "colab")

# Human-facing labels for the "Deep Dive" panel , which specialty psychology
# model produced the enrichment, and what it specialises in.
MODEL_LABELS = {
    "psyllm":        "PsyLLM , personality-science model (trait theory + DSM-5 dimensional framing)",
    "psychocounsel": "PsychoCounsel , psychotherapist-aligned relational model",
    "psycholex":     "PsychoLex , academic psychology model",
    "mentallama":    "MentaLLaMA , interpretable mental-health model",
}

# Which specialty model owns which instrument.
TEST_SPECIALTY_MAP: Dict[str, str] = {
    # mood / clinical state
    "dass": "mentallama", "who5": "mentallama",
    # clinical-adjacent trait instruments
    "pid5": "psycholex", "darktriad": "psycholex", "npi": "psycholex", "gcbs": "psycholex",
    # relational / needs / values
    "attachment": "psychocounsel", "hsq": "psychocounsel",
    "bpnss": "psychocounsel", "pvq": "psychocounsel",
    # broad personality
    "hexaco": "psyllm", "sixteenpf": "psyllm", "ambi": "psyllm", "fti": "psyllm",
    "kims": "psyllm", "aesthetic": "psyllm", "riasec": "psyllm",
}


def _augment_enabled() -> bool:
    return ENABLE_PSYCH_AUGMENT and bool(HF_API_KEY)


def _specialty_enabled() -> bool:
    return ENABLE_SPECIALTY_PSYCH


def specialty_model_for(test_id: str) -> str:
    return TEST_SPECIALTY_MAP.get(test_id, "psyllm")


# ─── Layer A: HuggingFace Inference API (async, cached, fail-soft) ───────────

_CACHE: "OrderedDict[str, list]" = OrderedDict()
_CACHE_MAX = 1024
_cache_lock = threading.Lock()


def _cache_key(model: str, text: str) -> str:
    return hashlib.sha256(f"{model}::{text}".encode("utf-8")).hexdigest()


def _cache_get(key: str):
    with _cache_lock:
        if key in _CACHE:
            _CACHE.move_to_end(key)
            return _CACHE[key]
    return None


def _cache_put(key: str, value) -> None:
    with _cache_lock:
        _CACHE[key] = value
        _CACHE.move_to_end(key)
        while len(_CACHE) > _CACHE_MAX:
            _CACHE.popitem(last=False)


# Session-level circuit breaker for Layer A. When both the primary
# api-inference.huggingface.co host and the router.hf.co fallback fail with
# DNS or connect errors this many times in a row, further calls short-circuit
# to None immediately instead of hammering an unreachable host. State resets
# whenever any classifier call succeeds.
_HF_LAYERA_FAIL_STREAK = {"count": 0}
_HF_LAYERA_CIRCUIT_OPEN_AT = 5


def _layer_a_disabled() -> bool:
    return _HF_LAYERA_FAIL_STREAK["count"] >= _HF_LAYERA_CIRCUIT_OPEN_AT


def _record_layer_a(success: bool) -> None:
    if success:
        _HF_LAYERA_FAIL_STREAK["count"] = 0
    else:
        _HF_LAYERA_FAIL_STREAK["count"] += 1


async def hf_classify(model: str, text: str, timeout: float = 3.0,
                      wait_for_model: bool = False) -> Optional[list]:
    """Full [{label, score}, ...] distribution. None on any failure.

    Tries the legacy api-inference.huggingface.co endpoint first, then
    router.huggingface.co/hf-inference as a fallback for DNS setups where
    only the router subdomain resolves. The classifier is optional
    enrichment (affect spectrum of user-volunteered notes), any failure is
    fail-soft and never blocks base results or the deep dive."""
    if not _augment_enabled():
        return None
    if _layer_a_disabled():
        return None
    text = (text or "").strip()
    if not text:
        return None
    payload_text = text[:1500]

    key = _cache_key(model, payload_text)
    cached = _cache_get(key)
    if cached is not None:
        return cached

    headers = {"Authorization": f"Bearer {HF_API_KEY}"}
    body = {"inputs": payload_text, "options": {"use_cache": True, "wait_for_model": wait_for_model}}
    effective_timeout = 25.0 if wait_for_model else timeout

    async def _try_base(base: str) -> Optional[list]:
        try:
            async with httpx.AsyncClient(timeout=effective_timeout) as client:
                resp = await client.post(f"{base}/{model}", json=body, headers=headers)
            if resp.status_code == 503 and not wait_for_model:
                body["options"]["wait_for_model"] = True
                async with httpx.AsyncClient(timeout=25.0) as client:
                    resp = await client.post(f"{base}/{model}", json=body, headers=headers)
            if resp.status_code == 429:
                print(f"[HF {model}] rate limited (429). Skipping augmentation.")
                return None
            resp.raise_for_status()
            data = resp.json()
        except Exception as e:
            raise e

        if isinstance(data, dict) and "error" in data:
            print(f"[HF {model}] {data.get('error')}")
            return None
        if isinstance(data, list) and data:
            result = data[0] if isinstance(data[0], list) else data
            if all(isinstance(i, dict) and "label" in i and "score" in i for i in result):
                _cache_put(key, result)
                return result
        return None

    first_err = None
    try:
        out = await _try_base(HF_BASE)
        if out is not None:
            _record_layer_a(True)
            return out
    except Exception as e:
        first_err = e

    # DNS drops on the legacy endpoint are common on some Windows resolvers.
    # Retry the same call against the newer router.hf.co edge before giving up.
    try:
        out = await _try_base(HF_ROUTER_BASE)
        if out is not None:
            _record_layer_a(True)
            return out
    except Exception as e:
        second_err = e
        print(f"[HF {model} unreachable] primary={type(first_err).__name__ if first_err else 'ok'} "
              f"router={type(second_err).__name__}. Skipping optional affect enrichment.")
        _record_layer_a(False)
        return None

    if first_err is not None:
        # Primary raised, fallback returned None cleanly.
        _record_layer_a(False)
    return None


async def hf_warmup(model: str) -> bool:
    result = await hf_classify(model, "warming up the classifier model now please",
                               wait_for_model=True)
    return result is not None


async def _network_reachable() -> bool:
    """Probe api-inference.huggingface.co with GET and a small retry budget.
    HEAD on the bare /models path returns spuriously (or DNS drops), so we
    hit the API root and accept any HTTP response as evidence the host is
    reachable, only network/DNS errors count as unreachable."""
    for attempt in range(2):
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                r = await client.get("https://api-inference.huggingface.co/",
                                      headers={"User-Agent": "valence-warmup"})
            return r.status_code < 600
        except Exception:
            if attempt == 0:
                await asyncio.sleep(1.5)
                continue
            return False
    return False


async def warmup_all_hf() -> None:
    """Concurrent warmup for every Layer A model. Fire-and-forget at boot and
    on every test-open ping. Layer A is optional enrichment (affect spectrum
    of user-volunteered notes), base results and the deep dive do NOT depend
    on it, any failure is fail-soft. Once the session-level circuit breaker
    trips after repeated failures, further warmups are skipped silently until
    the process restarts."""
    if not _augment_enabled():
        print("[psych] Layer A augmentation disabled or HF_API_KEY missing, skipping HF warmup.")
        return
    if _layer_a_disabled():
        # Circuit already open, quiet skip. No log spam.
        return
    results = await asyncio.gather(*[hf_warmup(m) for m in HF_MODELS], return_exceptions=True)
    ok_count = sum(1 for ok in results if ok is True)
    if ok_count == len(HF_MODELS):
        print(f"[psych] Layer A classifiers ready ({ok_count}/{len(HF_MODELS)}).")
    elif ok_count == 0:
        if _layer_a_disabled():
            print("[psych] Layer A classifiers unreachable. Circuit opened, further Layer A warmup pings suppressed. "
                  "Base results and Deep Dive are unaffected.")
        else:
            print(f"[psych] Layer A classifiers all failed this round (streak {_HF_LAYERA_FAIL_STREAK['count']}"
                  f"/{_HF_LAYERA_CIRCUIT_OPEN_AT}). Base results and Deep Dive are unaffected.")
    else:
        print(f"[psych] Layer A partial: {ok_count}/{len(HF_MODELS)} ready.")


def format_spectrum(scores: Optional[list], min_score: float = 0.05) -> str:
    if not scores:
        return ""
    ordered = sorted(scores, key=lambda d: d.get("score", 0), reverse=True)
    return ", ".join(
        f"{d['label']}: {float(d['score']):.2f}" for d in ordered
        if float(d.get("score", 0)) >= min_score
    )


# ─── Layer B: worker registry (self-reporting URLs) ──────────────────────────

_reg_lock = threading.Lock()
_reg_table: Dict[str, Dict[str, dict]] = {k: {} for k in MODEL_KEYS}


def registry_register(provider: str, model_key: str, url: str) -> None:
    if provider not in PRIORITY:
        raise ValueError(f"unknown provider {provider!r}")
    if model_key not in MODEL_KEYS:
        raise ValueError(f"unknown model_key {model_key!r}")
    url = url.strip().rstrip("/")
    if not url.startswith("http"):
        raise ValueError("url must be http(s)")
    with _reg_lock:
        _reg_table[model_key][provider] = {"url": url, "ts": time.time()}


def registry_unregister(provider: str, model_key: str) -> None:
    with _reg_lock:
        _reg_table.get(model_key, {}).pop(provider, None)


def _env_fallback(model_key: str) -> str:
    """Manual Colab pin wins if set; otherwise the dedicated HF Space serves
    every model key from its single static URL."""
    manual = {
        "psyllm": COLAB_URL_PSYLLM,
        "psychocounsel": COLAB_URL_PSYCHOCOUNSEL,
        "psycholex": COLAB_URL_PSYCHOLEX,
        "mentallama": COLAB_URL_MENTALLAMA,
    }.get(model_key, "")
    return manual or SPECIALTY_SPACE_URL


def _secret_headers() -> dict:
    if SPECIALTY_REGISTRY_SECRET:
        return {"X-Specialty-Secret": SPECIALTY_REGISTRY_SECRET}
    return {}


def registry_resolve(model_key: str) -> Optional[str]:
    with _reg_lock:
        providers = _reg_table.get(model_key, {})
        for p in PRIORITY:
            entry = providers.get(p)
            if entry and entry["url"]:
                return entry["url"]
    return _env_fallback(model_key) or None


def registry_snapshot() -> dict:
    with _reg_lock:
        return {k: {p: dict(v) for p, v in prov.items()} for k, prov in _reg_table.items()}


# ─── Layer B: Space wake-on-demand ────────────────────────────────────────────
# A sleeping HF Space restarts on ANY incoming HTTP request; while it boots,
# requests get non-200 responses. Wake = probe /health with patience. No
# quota tracking needed , the free CPU tier is not metered.

_wake_lock = threading.Lock()
_wake_state = {"in_flight_until": 0.0, "last_attempt": 0.0}
_WAKE_GRACE_SEC = 3 * 60  # container restart + first model download


def _wake_in_progress() -> bool:
    return time.time() < _wake_state["in_flight_until"]


def _health_ok_sync(base_url: str, timeout: float = 6.0) -> bool:
    try:
        r = httpx.get(f"{base_url.rstrip('/')}/health",
                      headers=_secret_headers(), timeout=timeout)
        return r.status_code == 200
    except Exception:
        return False


async def ensure_warm(model_key: str) -> dict:
    """Best-effort wake of the Space worker. Never raises. The health probe
    itself is what triggers a sleeping Space to restart."""
    base_url = registry_resolve(model_key)
    if not base_url:
        return {"action": "refused", "reason": "no worker URL configured"}
    try:
        async with httpx.AsyncClient(timeout=6.0) as client:
            r = await client.get(f"{base_url.rstrip('/')}/health",
                                 headers=_secret_headers())
        if r.status_code == 200:
            return {"action": "noop", "reason": "alive"}
    except Exception:
        pass
    if _wake_in_progress():
        return {"action": "noop", "reason": "wake-in-flight"}
    with _wake_lock:
        if _wake_in_progress():
            return {"action": "noop", "reason": "wake-in-flight"}
        _wake_state["in_flight_until"] = time.time() + _WAKE_GRACE_SEC
        _wake_state["last_attempt"] = time.time()
    # One patient probe: the request has already queued the restart; this
    # just reports whether it came up within the grace window.
    try:
        async with httpx.AsyncClient(timeout=_WAKE_GRACE_SEC) as client:
            r = await client.get(f"{base_url.rstrip('/')}/health",
                                 headers=_secret_headers())
        ok = r.status_code == 200
    except Exception:
        ok = False
    with _wake_lock:
        _wake_state["in_flight_until"] = 0.0 if ok else time.time() + 30
    return {"action": "wake", "ok": ok}


def lifecycle_snapshot() -> dict:
    return {
        "space_url": SPECIALTY_SPACE_URL,
        "wake": {
            "in_flight": _wake_in_progress(),
            "last_attempt_ts": _wake_state["last_attempt"],
        },
    }


# ─── Layer B: worker calls ────────────────────────────────────────────────────

async def warm_worker(model_key: str, timeout: float = 8.0) -> Optional[dict]:
    """Tell the worker to load model_key into RAM now (non-blocking on its
    side). If the Space is asleep, this very request triggers its restart;
    the questionnaire's periodic re-ping finishes the job."""
    if not _specialty_enabled():
        return None
    base_url = registry_resolve(model_key)
    if not base_url:
        return {"action": "refused", "reason": "no worker URL configured"}
    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            resp = await client.post(f"{base_url.rstrip('/')}/warm",
                                     json={"model_key": model_key},
                                     params={"model": model_key},
                                     headers=_secret_headers())
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        print(f"[psych warm {model_key} @ {base_url}] {type(e).__name__}: {e}")
        # The failed request still queued a restart of a sleeping Space.
        asyncio.create_task(ensure_warm(model_key))
        return {"action": "waking"}


async def health_check(model_key: str, timeout: float = 5.0) -> bool:
    if not _specialty_enabled():
        return False
    base_url = registry_resolve(model_key)
    if not base_url:
        return False
    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            resp = await client.get(f"{base_url.rstrip('/')}/health",
                                    headers=_secret_headers())
        return resp.status_code == 200
    except Exception:
        return False


async def specialty_health_snapshot() -> dict:
    if not _specialty_enabled():
        return {"enabled": False}
    results = await asyncio.gather(*[health_check(k) for k in MODEL_KEYS])
    return {
        "enabled": True,
        "alive": {k: ok for k, ok in zip(MODEL_KEYS, results)},
        "registry": registry_snapshot(),
        "lifecycle": lifecycle_snapshot(),
    }


def _call_worker_sync(model_key: str, prompt: str, max_new_tokens: int = 420,
                      temperature: float = 0.5,
                      timeout: Optional[float] = None) -> Optional[str]:
    """Synchronous inference call , runs in the post-submit enrichment
    thread, so it can afford to wait out a Space wake-up. Fail-soft: None
    on any failure."""
    if not _specialty_enabled():
        return None
    base_url = registry_resolve(model_key)
    if not base_url:
        return None
    timeout = timeout or SPECIALTY_INFER_TIMEOUT

    def _infer() -> Optional[dict]:
        resp = httpx.post(
            f"{base_url.rstrip('/')}/infer",
            json={"prompt": prompt, "max_new_tokens": max_new_tokens,
                  "temperature": temperature, "model_key": model_key},
            params={"model": model_key},
            headers=_secret_headers(),
            timeout=timeout,
        )
        resp.raise_for_status()
        return resp.json()

    try:
        data = _infer()
    except Exception as first_err:
        # Space was likely asleep , the failed request queued its restart.
        # Wait for /health to come back (bounded), then retry once.
        print(f"[psych {model_key} @ {base_url}] {type(first_err).__name__}: "
              f"{first_err} , waiting for worker to wake")
        deadline = time.time() + 180
        while time.time() < deadline:
            if _health_ok_sync(base_url):
                break
            time.sleep(10)
        else:
            return None
        try:
            data = _infer()
        except Exception as e:
            print(f"[psych {model_key} retry] {type(e).__name__}: {e}")
            return None
    if isinstance(data, dict):
        for key in ("text", "response", "output", "generated_text"):
            v = data.get(key)
            if isinstance(v, str) and v.strip():
                return v.strip()
    return None


def _classify_notes_sync(context_notes: Optional[List[Dict]]) -> str:
    """Layer A spectrum of the user's volunteered notes, rendered as a compact
    prompt block. Empty string when unavailable. Silently skipped when the
    Layer A circuit breaker has opened for this session."""
    if not context_notes or not _augment_enabled() or _layer_a_disabled():
        return ""
    text = " ".join((n.get("note") or "").strip() for n in context_notes if n.get("note"))
    if not text.strip():
        return ""
    try:
        emotion = asyncio.run(hf_classify(PSYCH_MODEL_EMOTION, text, timeout=6.0))
    except Exception:
        emotion = None
    spectrum = format_spectrum(emotion)
    if not spectrum:
        return ""
    return f"Affect spectrum of their volunteered notes (classifier): {spectrum}\n"


# ─── Enrichment + monitoring / fine-tuning corpus ─────────────────────────────

def _log_finetune(test_id: str, record: dict) -> None:
    """Append one monitored enrichment record to the fine-tuning corpus."""
    try:
        os.makedirs(FINETUNE_DIR, exist_ok=True)
        path = os.path.join(FINETUNE_DIR, f"{test_id}.jsonl")
        with open(path, "a", encoding="utf-8") as f:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")
    except Exception as e:
        print(f"[psych finetune-log] {e}")


def _build_prompt(test_id: str, model_key: str, trait_scores: Dict[str, float],
                  percentiles: Dict[str, int], archetype: dict,
                  notes_block: str) -> str:
    trait_lines = "\n".join(
        f"  {name}: {score:.2f} ({percentiles.get(name, 50)}th percentile)"
        for name, score in trait_scores.items()
    )
    arch_name = (archetype or {}).get("name", "")
    arch_tag = (archetype or {}).get("tagline", "")
    test_label = test_id.replace("_", " ")

    if model_key == "mentallama":
        return (
            "You are MentaLLaMA. A person completed the "
            f"{test_label} self-report instrument.\n\n"
            f"Scored profile:\n{trait_lines}\n\n{notes_block}"
            "Give 6 short lines, each starting with 'BECAUSE:', that justify one "
            "observation about their current affective pattern with a specific "
            "score and connect it to a recognised mental-health construct. "
            "Neutral tone, no diagnosis, no alarmism. Each line must be one "
            "complete sentence, distinct from the others.\n\nJustifications:"
        )
    if model_key == "psychocounsel":
        return (
            "You are PsychoCounsel, aligned with professional psychotherapist "
            f"norms. A person completed the {test_label} assessment and was "
            f"assigned the profile '{arch_name}' ({arch_tag}).\n\n"
            f"Scored profile:\n{trait_lines}\n\n{notes_block}"
            "Write 6 one-sentence observations about how this relational/needs "
            "profile likely shows up in close relationships, work, and everyday "
            "self-regulation, phrased warmly and without diagnostic claims. "
            "Cover at least three different life domains across the six lines.\n\nObservations:"
        )
    if model_key == "psycholex":
        return (
            "You are PsychoLexLLaMA. A person completed the "
            f"{test_label} instrument and was assigned '{arch_name}' ({arch_tag}).\n\n"
            f"Scored profile:\n{trait_lines}\n\n{notes_block}"
            "Drawing on academic psychological literature, write 6 one-sentence "
            "notes: two naming the theoretical constructs most relevant to this "
            "profile, two describing well-supported behavioural implications, "
            "and two connecting the most distinctive scores to concrete life "
            "situations. No diagnoses, no repetition.\n\nNotes:"
        )
    # psyllm default
    return (
        "You are PsyLLM. Apply established personality-science framing "
        f"(trait theory, DSM-5 dimensional models where relevant) to a person's "
        f"{test_label} results, assigned '{arch_name}' ({arch_tag}).\n\n"
        f"Scored profile:\n{trait_lines}\n\n{notes_block}"
        "Write 6 one-sentence, personalised observations that connect their "
        "most distinctive scores to concrete day-to-day tendencies across work, "
        "relationships, and self-regulation. No diagnoses, no repetition of the "
        "archetype tagline, each line must stand alone.\n\nObservations:"
    )


def _extract_lines(response: str, limit: int = 6) -> List[str]:
    out = []
    seen = set()
    for line in (response or "").split("\n"):
        line = line.strip().lstrip("-•· 0123456789.)")
        line = line.strip()
        if not line or len(line) <= 20 or len(line) >= 320:
            continue
        # Deduplicate near-identical sentences.
        key = line.lower()[:80]
        if key in seen:
            continue
        seen.add(key)
        out.append(line)
        if len(out) >= limit:
            break
    return out


def enrich_result(test_id: str, trait_scores: Dict[str, float],
                  percentiles: Dict[str, int], archetype: dict,
                  insights: Dict, context_notes: Optional[List[Dict]] = None) -> Dict:
    """Specialty-model enrichment of a scored test result. Appends up to 2
    observations to insights['insights'], logs the monitored record, and
    returns the (possibly updated) insights dict. Fail-soft."""
    if not _specialty_enabled():
        return insights
    model_key = specialty_model_for(test_id)
    notes_block = _classify_notes_sync(context_notes)
    prompt = _build_prompt(test_id, model_key, trait_scores, percentiles,
                           archetype or {}, notes_block)

    t0 = time.time()
    response = _call_worker_sync(model_key, prompt)
    latency = round(time.time() - t0, 2)

    record = {
        "ts": time.time(),
        "test_id": test_id,
        "model_key": model_key,
        "trait_scores": trait_scores,
        "percentiles": percentiles,
        "archetype": {k: (archetype or {}).get(k) for k in ("id", "name", "tagline")},
        "notes_spectrum": notes_block.strip() or None,
        "prompt": prompt,
        "output": response,
        "latency_s": latency,
        "status": "ok" if response else "unavailable",
    }
    _log_finetune(test_id, record)

    # The specialty-model output is NOT merged into the base insights. It is
    # held in a separate `deep_dive` block so the results page can show base
    # results instantly and reveal this richer psychology-model analysis only
    # when the user opts into "Deep Dive Mode".
    lines = _extract_lines(response) if response else []
    insights["deep_dive"] = {
        "model_key":      model_key,
        "model_label":    MODEL_LABELS.get(model_key, model_key),
        "insights":       lines,
        # Layer-A affect classification of the user's volunteered notes , bonus
        # context shown only in the deep dive. None when no notes were given.
        "affect_context": (notes_block.strip() or None),
        "latency_s":      latency,
        "status":         "ok" if lines else "unavailable",
    }
    if lines:
        print(f"[psych] {model_key} deep-dive for {test_id} (+{len(lines)} lines, {latency}s)")
    return insights
