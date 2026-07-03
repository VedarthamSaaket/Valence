# Kaggle entrypoint: bootstrap deps + run the specialty host, all in one file.
#
# Kaggle "script" kernels only push the single file named in kernel-metadata.json's
# code_file — a second local file (valence_psych_host.py) never reaches the kernel,
# so everything must live here.
#
# This file gets `kaggle kernels push`-ed by the backend's wake controller.
# Each push triggers a new GPU kernel run.
#
# Kaggle secrets that must be configured under the kernel:
#   VALENCE_BACKEND_URL         https://<your-deployed-backend>
#   SPECIALTY_REGISTRY_SECRET  <same as backend .env>
#   HF_TOKEN                   (optional, for gated repos)
#
# Settings → Accelerator: GPU T4 x2
# Settings → Internet:    On

# ── Bootstrap: install deps + cloudflared ────────────────────────────────────
import os
import subprocess
import sys
import urllib.request

subprocess.check_call([
    sys.executable, "-m", "pip", "install", "-q", "--upgrade",
    "fastapi", "uvicorn", "transformers", "accelerate",
    "bitsandbytes", "nest_asyncio", "requests", "pydantic",
])

CF_BIN = "/usr/local/bin/cloudflared"
if not os.path.exists(CF_BIN):
    urllib.request.urlretrieve(
        "https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64",
        CF_BIN,
    )
    os.chmod(CF_BIN, 0o755)

# ── Host: preload models, expose /infer, tunnel + self-register ─────────────
import re
import time
import threading
from collections import OrderedDict
from typing import Optional

import requests
import torch
import nest_asyncio
from fastapi import FastAPI
from pydantic import BaseModel
import uvicorn
from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig


# Kaggle Secrets
try:
    from kaggle_secrets import UserSecretsClient
    _sec = UserSecretsClient()
    def _s(name: str, default: str = "") -> str:
        try:    return _sec.get_secret(name) or default
        except Exception: return os.getenv(name, default)
except Exception:
    def _s(name: str, default: str = "") -> str:
        return os.getenv(name, default)


VALENCE_BACKEND_URL = _s("VALENCE_BACKEND_URL").rstrip("/")
SPECIALTY_SECRET   = _s("SPECIALTY_REGISTRY_SECRET")
HF_TOKEN           = _s("HF_TOKEN")
PROVIDER_NAME      = os.getenv("SPECIALTY_PROVIDER", "kaggle")
PORT               = int(os.getenv("PORT", "8000"))
# Self-terminate after this many seconds without any /infer hit.
IDLE_SHUTDOWN_SEC  = int(_s("SPECIALTY_WORKER_IDLE_SECONDS", "1200"))


MODEL_REGISTRY: dict[str, str] = {
    "psyllm":        "GMLHUHE/PsyLLM-8B",
    "psychocounsel": "Psychotherapy-LLM/PsyCoPref-Llama3-8B",
    "psycholex":     "aminabbasi/PsychoLexLLaMA-8B",  # gated — needs HF_TOKEN + accepted access
    "mentallama":    "klyang/MentaLLaMA-chat-7B-hf",
}

# One-time boot self-test: sequentially load+evict every model to prove each
# one actually works on whatever GPU Kaggle handed out, before opening the
# tunnel. Off by default (adds several minutes to every cold boot); set the
# Kaggle secret SELFTEST_ALL_MODELS=true for a one-off verification run.
SELFTEST_ALL = _s("SELFTEST_ALL_MODELS", "false").lower() in ("1", "true", "yes")


# ── Idle tracking ────────────────────────────────────────────────────────────
_boot_time = time.time()
_last_request_time = time.time()


# ── GPU capability detection ─────────────────────────────────────────────────
# bitsandbytes 4-bit (NF4) kernels aren't built for pre-Turing cards. Kaggle's
# "GPU T4 x2" setting is a request, not a guarantee — when the T4 pool is full
# it silently hands out an older P100 (capability 6.0) instead, which crashes
# bnb with "named symbol not found" mid weight-load. Detect and degrade instead.
def _bnb_capable() -> bool:
    if not torch.cuda.is_available():
        return False
    return torch.cuda.get_device_capability(0) >= (7, 5)


BNB_CAPABLE = _bnb_capable()
# T4 x2 (32GB combined) fits all three 4-bit 8B models at once. Anything else
# (e.g. a single 16GB P100) can only hold one fp16 8B model at a time.
MAX_RESIDENT = len(MODEL_REGISTRY) if BNB_CAPABLE else 1

if torch.cuda.is_available():
    print(
        f"[gpu] {torch.cuda.get_device_name(0)} "
        f"capability={torch.cuda.get_device_capability(0)} → "
        f"{'4-bit eager preload' if BNB_CAPABLE else 'fp16 lazy single-model mode'}",
        flush=True,
    )


# ── Model cache: eager-preloaded on capable hardware, lazy + LRU-evicted
# otherwise. Access serialized by _infer_lock so eviction can never free a
# model tensor while another request is mid-generate() on it. ────────────────
_cache: "OrderedDict[str, dict]" = OrderedDict()
_infer_lock = threading.Lock()


def _bnb_4bit() -> BitsAndBytesConfig:
    return BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_quant_type="nf4",
        bnb_4bit_compute_dtype=torch.float16,
        bnb_4bit_use_double_quant=True,
    )


def _load_one(model_key: str):
    if model_key in _cache:
        _cache.move_to_end(model_key)
        return _cache[model_key]["tok"], _cache[model_key]["model"]

    while len(_cache) >= MAX_RESIDENT:
        evict_key, evicted = _cache.popitem(last=False)
        del evicted["model"]
        del evicted["tok"]
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
        print(f"[evict] {evict_key} (resident cap={MAX_RESIDENT})", flush=True)

    repo = MODEL_REGISTRY[model_key]
    print(f"[load] {model_key} ← {repo}", flush=True)
    t0 = time.time()
    tok = AutoTokenizer.from_pretrained(repo, token=HF_TOKEN or None)
    if tok.pad_token_id is None:
        tok.pad_token = tok.eos_token
    if BNB_CAPABLE:
        mdl = AutoModelForCausalLM.from_pretrained(
            repo,
            token=HF_TOKEN or None,
            quantization_config=_bnb_4bit(),
            device_map="auto",
        )
    else:
        mdl = AutoModelForCausalLM.from_pretrained(
            repo,
            token=HF_TOKEN or None,
            torch_dtype=torch.float16,
            device_map="auto",
        )
    mdl.eval()
    _cache[model_key] = {"tok": tok, "model": mdl}
    print(f"[load] {model_key} ready in {time.time() - t0:.1f}s", flush=True)
    return tok, mdl


def _preload_all():
    if not BNB_CAPABLE:
        print("[preload] skipped — lazy single-model mode (low-VRAM GPU)", flush=True)
        return
    for k in MODEL_REGISTRY:
        try:
            _load_one(k)
        except Exception as e:
            print(f"[preload] {k} FAILED {type(e).__name__}: {e}", flush=True)


def _selftest_all():
    print(f"[selftest] verifying all {len(MODEL_REGISTRY)} models load (resident cap={MAX_RESIDENT})...", flush=True)
    for k in MODEL_REGISTRY:
        try:
            with _infer_lock:
                _load_one(k)
            print(f"[selftest] {k} OK", flush=True)
        except Exception as e:
            print(f"[selftest] {k} FAILED {type(e).__name__}: {e}", flush=True)


# ── FastAPI ──────────────────────────────────────────────────────────────────
app = FastAPI(title=f"Valence specialty host ({PROVIDER_NAME})")


class InferBody(BaseModel):
    prompt: str
    max_new_tokens: int = 256
    temperature: float = 0.7
    model_key: Optional[str] = None


@app.post("/infer")
async def infer(body: InferBody, model: Optional[str] = None):
    global _last_request_time
    _last_request_time = time.time()
    model_key = model or body.model_key or "psyllm"
    if model_key not in MODEL_REGISTRY:
        return {"text": "", "error": f"unknown model {model_key}"}
    with _infer_lock:
        tok, mdl = _load_one(model_key)
        inputs = tok(body.prompt, return_tensors="pt", truncation=True, max_length=4096).to(mdl.device)
        with torch.no_grad():
            out = mdl.generate(
                **inputs,
                max_new_tokens=int(body.max_new_tokens),
                temperature=float(max(0.01, body.temperature)),
                do_sample=body.temperature > 0.01,
                pad_token_id=tok.pad_token_id,
            )
        text = tok.decode(out[0][inputs["input_ids"].shape[1]:], skip_special_tokens=True).strip()
    return {"text": text, "model": MODEL_REGISTRY[model_key]}


@app.get("/health")
def health():
    return {
        "ok":        True,
        "provider":  PROVIDER_NAME,
        "loaded":    list(_cache.keys()),
        "available": list(MODEL_REGISTRY.keys()),
    }


class WarmBody(BaseModel):
    model_key: Optional[str] = None


@app.post("/warm")
async def warm(body: WarmBody, model: Optional[str] = None):
    """Kick off a background load for one model without blocking on it — lets
    the backend say 'start loading psycholex' the moment a user opens the
    screening test, so it's resident by the time they submit, instead of
    paying the full load latency on the real /infer call."""
    global _last_request_time
    _last_request_time = time.time()
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


# ── Cloudflared tunnel + URL detection ───────────────────────────────────────
_TUNNEL_RE = re.compile(r"https://[a-zA-Z0-9-]+\.trycloudflare\.com")


def _spawn_tunnel(port: int) -> Optional[str]:
    p = subprocess.Popen(
        ["cloudflared", "tunnel", "--url", f"http://localhost:{port}",
         "--no-autoupdate", "--metrics", "localhost:0"],
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1,
    )
    deadline = time.time() + 60
    while time.time() < deadline:
        line = p.stdout.readline()
        if not line:
            time.sleep(0.2)
            continue
        print("[cf]", line.rstrip(), flush=True)
        m = _TUNNEL_RE.search(line)
        if m:
            return m.group(0)
    return None


def _register(public_url: str):
    if not (VALENCE_BACKEND_URL and SPECIALTY_SECRET):
        print("[register] missing VALENCE_BACKEND_URL or secret — skipping", flush=True)
        return
    endpoint = f"{VALENCE_BACKEND_URL}/internal/specialty/register"
    for model_key in MODEL_REGISTRY:
        try:
            r = requests.post(
                endpoint,
                json={"provider": PROVIDER_NAME, "model_key": model_key, "url": public_url},
                headers={"X-Specialty-Secret": SPECIALTY_SECRET},
                timeout=10,
            )
            print(f"[register] {model_key} → {r.status_code}", flush=True)
        except Exception as e:
            print(f"[register] {model_key} FAILED {type(e).__name__}: {e}", flush=True)


def _bootstrap():
    # 1. preload models so first user request doesn't pay load latency
    _preload_all()
    if SELFTEST_ALL:
        _selftest_all()
    # 2. spawn tunnel
    url = _spawn_tunnel(PORT)
    if not url:
        print("[bootstrap] tunnel URL not detected within timeout", flush=True)
        return
    print(f"[bootstrap] PUBLIC URL = {url}", flush=True)
    # 3. report
    _register(url)


def _report_shutdown_and_exit():
    """Notify backend so it can deduct uptime from the weekly quota counter
    and clear stale registry entries, then hard-exit so Kaggle releases the
    GPU and stops the quota meter."""
    uptime = max(0.0, time.time() - _boot_time)
    if VALENCE_BACKEND_URL and SPECIALTY_SECRET:
        try:
            requests.post(
                f"{VALENCE_BACKEND_URL}/internal/specialty/shutdown",
                json={"provider": PROVIDER_NAME, "uptime_seconds": uptime},
                headers={"X-Specialty-Secret": SPECIALTY_SECRET},
                timeout=10,
            )
        except Exception as e:
            print(f"[shutdown] notify failed {type(e).__name__}: {e}", flush=True)
    print(f"[shutdown] idle exit after {uptime:.0f}s uptime", flush=True)
    # Hard-exit the kernel — releases the GPU and stops quota meter.
    os._exit(0)


def _idle_watchdog():
    """Background loop. If no /infer in IDLE_SHUTDOWN_SEC, kill the kernel."""
    while True:
        time.sleep(30)
        if time.time() - _last_request_time > IDLE_SHUTDOWN_SEC:
            _report_shutdown_and_exit()


# ── Entrypoint ───────────────────────────────────────────────────────────────
if __name__ == "__main__" or "ipykernel" in sys.modules:
    if not torch.cuda.is_available():
        print("WARNING: no CUDA. Make sure Kaggle accelerator = GPU T4 x2.", file=sys.stderr)
    nest_asyncio.apply()
    threading.Thread(target=_bootstrap, daemon=True).start()
    threading.Thread(target=_idle_watchdog, daemon=True).start()
    uvicorn.run(app, host="0.0.0.0", port=PORT, log_level="info")
