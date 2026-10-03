import threading

from fastapi import APIRouter

from ml import psych_layer

router = APIRouter()


def _wake() -> None:
    threading.Thread(target=psych_layer.ensure_server, daemon=True).start()


@router.get("/warmup")
def warmup_all():
    _wake()
    return psych_layer.status()


@router.get("/warmup/{test_id}")
def warmup_test(test_id: str):
    _wake()
    return {"test_id": test_id, **psych_layer.status()}


@router.get("/health")
def psych_health():
    return psych_layer.status()
