# Valence specialty psych host — HF Space (Docker, CPU, llama.cpp).
#
# Same /infer /warm /health contract as the previous GPU worker, but:
#   - static URL (https://<owner>-valence-psych-host.hf.space), no tunnel
#   - no self-registration callback (the backend polls; it can stay on localhost)
#   - GGUF quants via llama.cpp instead of transformers+CUDA
#   - auth via X-Specialty-Secret header (Space secret SPECIALTY_REGISTRY_SECRET)
#
# Free CPU tier = 2 vCPU / 16 GB RAM: one resident model at a time, LRU-evicted.
# Generation is slow (tens of seconds) — callers run enrichment in a
# background thread and tolerate that.

import os
import threading
import time
from collections import OrderedDict
from typing import Optional

import uvicorn
from fastapi import FastAPI, Header, HTTPException
from huggingface_hub import hf_hub_download
from pydantic import BaseModel

SECRET = os.getenv("SPECIALTY_REGISTRY_SECRET", "")
PORT = int(os.getenv("PORT", "7860"))

# model_key -> (gguf repo, gguf filename)
MODEL_REGISTRY = {
    "psyllm":        ("eeleexx/PsyLLM-Q4_K_M-GGUF", "psyllm-q4_k_m.gguf"),
    "psychocounsel": ("mradermacher/PsychoCounsel-Llama3-8B-i1-GGUF",
                      "PsychoCounsel-Llama3-8B.i1-IQ3_M.gguf"),
    # PsychoLexLLaMA is gated with no public GGUF; PsyLLM-4B is the nearest
    # open academically-trained substitute and much faster on CPU.
    "psycholex":     ("mradermacher/PsyLLM-4B-GGUF", "PsyLLM-4B.Q4_K_M.gguf"),
    "mentallama":    ("QuantFactory/MentaLLaMA-chat-7B-GGUF",
                      "MentaLLaMA-chat-7B.Q4_K_M.gguf"),
}

MAX_RESIDENT = 1  # 16 GB RAM; one Q4 7-8B resident at a time is the safe cap


def _usable_cpus() -> int:
    """Threads llama.cpp should actually use.

    os.cpu_count() reports the HOST's core count (16-32) on a shared Space,
    but the free CPU-basic container only gets 2 vCPU. Spawning host-count
    threads oversubscribes those 2 cores and collapses throughput to seconds
    per token. Respect the cgroup where possible, else fall back to the free
    tier's real allotment. Override with N_THREADS if you upgrade hardware.
    """
    env = os.getenv("N_THREADS")
    if env and env.isdigit() and int(env) > 0:
        return int(env)
    try:
        # Honors CPU affinity / cgroup limits on Linux; not host core count.
        n = len(os.sched_getaffinity(0))
        if n > 0:
            return min(n, 2)
    except (AttributeError, OSError):
        pass
    return 2


N_THREADS = _usable_cpus()
print(f"[boot] N_THREADS={N_THREADS} host_cpu_count={os.cpu_count()}", flush=True)

_cache: "OrderedDict[str, object]" = OrderedDict()
_infer_lock = threading.Lock()
_boot_time = time.time()


def _check_secret(header: Optional[str]) -> None:
    if SECRET and header != SECRET:
        raise HTTPException(401, "bad secret")


def _load_one(model_key: str):
    from llama_cpp import Llama

    if model_key in _cache:
        _cache.move_to_end(model_key)
        return _cache[model_key]

    while len(_cache) >= MAX_RESIDENT:
        evict_key, _ = _cache.popitem(last=False)
        print(f"[evict] {evict_key}", flush=True)

    repo, fname = MODEL_REGISTRY[model_key]
    print(f"[load] {model_key} ← {repo}/{fname}", flush=True)
    t0 = time.time()
    path = hf_hub_download(repo_id=repo, filename=fname)
    llm = Llama(
        model_path=path,
        n_ctx=2048,
        n_threads=N_THREADS,
        n_batch=256,
        verbose=False,
    )
    _cache[model_key] = llm
    print(f"[load] {model_key} ready in {time.time() - t0:.1f}s", flush=True)
    return llm


app = FastAPI(title="Valence specialty psych host (space)")


class InferBody(BaseModel):
    prompt: str
    max_new_tokens: int = 160
    temperature: float = 0.4
    model_key: Optional[str] = None


@app.post("/infer")
def infer(body: InferBody, model: Optional[str] = None,
          x_specialty_secret: Optional[str] = Header(default=None)):
    _check_secret(x_specialty_secret)
    model_key = model or body.model_key or "psyllm"
    if model_key not in MODEL_REGISTRY:
        return {"text": "", "error": f"unknown model {model_key}"}
    with _infer_lock:
        llm = _load_one(model_key)
        t0 = time.time()
        out = llm.create_completion(
            prompt=body.prompt[:6000],
            max_tokens=int(body.max_new_tokens),
            temperature=float(max(0.01, body.temperature)),
            stop=["\n\n\n"],
        )
    text = (out.get("choices") or [{}])[0].get("text", "").strip()
    print(f"[infer] {model_key} {time.time() - t0:.1f}s "
          f"({out.get('usage', {})})", flush=True)
    return {"text": text, "model": MODEL_REGISTRY[model_key][0]}


class WarmBody(BaseModel):
    model_key: Optional[str] = None


@app.post("/warm")
def warm(body: WarmBody, model: Optional[str] = None,
         x_specialty_secret: Optional[str] = Header(default=None)):
    """Background-load one model so it is resident before the real /infer.
    Called repeatedly while a user is taking the matching test."""
    _check_secret(x_specialty_secret)
    model_key = model or body.model_key or "psyllm"
    if model_key not in MODEL_REGISTRY:
        return {"scheduled": False, "error": f"unknown model {model_key}"}
    if model_key in _cache:
        return {"scheduled": False, "already_loaded": True}

    def _bg():
        with _infer_lock:
            try:
                _load_one(model_key)
            except Exception as e:
                print(f"[warm] {model_key} FAILED {type(e).__name__}: {e}", flush=True)

    threading.Thread(target=_bg, daemon=True).start()
    return {"scheduled": True, "model_key": model_key}


@app.get("/health")
def health():
    # Unauthenticated on purpose: wake probes must work before the caller
    # can prove anything, and this leaks nothing sensitive.
    return {
        "ok": True,
        "provider": "space",
        "uptime_s": round(time.time() - _boot_time, 1),
        "n_threads": N_THREADS,
        "host_cpu_count": os.cpu_count(),
        "loaded": list(_cache.keys()),
        "available": list(MODEL_REGISTRY.keys()),
    }


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=PORT, log_level="info")
