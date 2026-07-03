# backend/routers/psych.py
"""
Warmup-on-demand + worker self-registration endpoints.

The frontend hits /api/psych/warmup/{test_id} the moment a questionnaire
opens, and keeps pinging while the user answers. By submit time the Layer A
classifiers are warm and the Layer B specialty worker has this test's model
resident in VRAM, so "Analyze results" pays no cold-start latency.

Endpoints are idempotent and cheap — spamming them is fine.

The /internal/specialty/* endpoints are how GPU workers (Kaggle kernel,
manual Colab) self-report their public URL, and how idle workers report
burned uptime for the rolling weekly GPU quota. Auth: shared secret in the
X-Specialty-Secret header (SPECIALTY_REGISTRY_SECRET in backend/.env).
"""

import asyncio
from typing import Optional

from fastapi import APIRouter, Header, HTTPException
from pydantic import BaseModel, Field

from ml import psych_layer

router = APIRouter()
internal_router = APIRouter(prefix="/internal/specialty", tags=["specialty-internal"])


def _ensure_refiner() -> dict:
    """Nudge the general-purpose archetype refiner out of cold storage and
    report its readiness, so a single questionnaire ping keeps BOTH the
    refiner and the psychology models hot. Idempotent and fail-soft: the
    refiner loads once in a background thread, so repeated calls just report
    status. Never raises — a warmup ping must never error."""
    try:
        from ml.archetype_refiner import ArchetypeRefiner
        refiner = ArchetypeRefiner.instance()
        refiner.warm_up(background=True)  # no-op once loading has started
        return refiner.status()
    except Exception as e:
        print(f"[warmup] refiner nudge failed: {e}")
        return {"started": False, "ready": False, "available": False}


# ─── Warmup (public, hit by the questionnaire page) ───────────────────────────

@router.get("/warmup")
async def warmup_all():
    """Warm the general refiner + every Layer A classifier + probe the
    specialty layer, so nothing the results page depends on is cold at submit."""
    refiner = _ensure_refiner()
    asyncio.create_task(psych_layer.warmup_all_hf())
    snapshot = await psych_layer.specialty_health_snapshot()
    return {
        "refiner": refiner,
        "hf_warmup_scheduled": len(psych_layer.HF_MODELS),
        "specialty": snapshot,
    }


@router.get("/warmup/{test_id}")
async def warmup_test(test_id: str):
    """Warm every model this specific instrument needs at "Analyze results":
    the general-purpose refiner is nudged awake and its readiness reported,
    Layer A classifiers get a wait_for_model ping, and the Layer B worker is
    told to hold this test's specialty model resident (waking a worker if
    none is live)."""
    refiner = _ensure_refiner()
    asyncio.create_task(psych_layer.warmup_all_hf())

    model_key = psych_layer.specialty_model_for(test_id)
    specialty_ready = bool(psych_layer.registry_resolve(model_key))
    specialty_action = await psych_layer.warm_worker(model_key)

    return {
        "test_id": test_id,
        "refiner": refiner,
        "hf_warmup_scheduled": True,
        "specialty_model": model_key,
        "specialty_ready": specialty_ready,
        "specialty_warm_action": specialty_action,
    }


@router.get("/health")
async def psych_health():
    return {
        "refiner": _ensure_refiner(),
        "augmentation_enabled": psych_layer._augment_enabled(),
        "hf_models": psych_layer.HF_MODELS,
        "specialty": await psych_layer.specialty_health_snapshot(),
    }


# ─── Internal worker registry (secret-gated) ──────────────────────────────────

class RegisterBody(BaseModel):
    provider:  str = Field(..., pattern=r"^(lightning|space|kaggle|colab)$")
    model_key: str = Field(..., pattern=r"^(psyllm|psychocounsel|psycholex|mentallama)$")
    url:       str


class UnregisterBody(BaseModel):
    provider:  str
    model_key: str


class ShutdownBody(BaseModel):
    provider:       str
    uptime_seconds: float


def _check(secret_header: Optional[str]) -> None:
    expected = psych_layer.SPECIALTY_REGISTRY_SECRET
    if not expected:
        raise HTTPException(503, "registry secret not configured")
    if not secret_header or secret_header != expected:
        raise HTTPException(401, "bad secret")


@internal_router.post("/register")
def register(body: RegisterBody, x_specialty_secret: Optional[str] = Header(default=None)):
    _check(x_specialty_secret)
    try:
        psych_layer.registry_register(body.provider, body.model_key, body.url)
    except ValueError as e:
        raise HTTPException(400, str(e))
    return {"ok": True, "provider": body.provider, "model_key": body.model_key}


@internal_router.post("/unregister")
def unregister(body: UnregisterBody, x_specialty_secret: Optional[str] = Header(default=None)):
    _check(x_specialty_secret)
    psych_layer.registry_unregister(body.provider, body.model_key)
    return {"ok": True}


@internal_router.post("/shutdown")
def shutdown(body: ShutdownBody, x_specialty_secret: Optional[str] = Header(default=None)):
    """Worker calls this right before shutting down: clear its registry
    entries so resolution falls back to the static Space URL."""
    _check(x_specialty_secret)
    for model_key in psych_layer.MODEL_KEYS:
        psych_layer.registry_unregister(body.provider, model_key)
    return {"ok": True, "uptime_seconds": body.uptime_seconds}


@internal_router.get("/snapshot")
def snapshot(x_specialty_secret: Optional[str] = Header(default=None)):
    _check(x_specialty_secret)
    return {
        "registry": psych_layer.registry_snapshot(),
        "lifecycle": psych_layer.lifecycle_snapshot(),
    }
