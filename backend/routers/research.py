import json
import os

from fastapi import APIRouter, HTTPException

router = APIRouter()

BASE_DIR = os.path.dirname(__file__)
PAPER_PATH = os.path.join(BASE_DIR, "..", "research", "paper_results.json")
MODELS_DIR = os.path.join(BASE_DIR, "..", "models")


def _paper() -> dict:
    with open(PAPER_PATH, encoding="utf-8") as f:
        return json.load(f)


def _silhouette_band(value, bands) -> str:
    if value is None:
        return "unknown"
    if value >= bands["strong"]:
        return "strong"
    if value >= bands["reasonable"]:
        return "reasonable"
    return "weak"


def _trained(test_id: str, bands: dict):
    path = os.path.join(MODELS_DIR, f"{test_id}_meta.json")
    if not os.path.exists(path):
        return None
    with open(path, encoding="utf-8") as f:
        meta = json.load(f)
    sil = meta.get("silhouette")
    return {
        "n_samples": meta.get("n_samples"),
        "profiles": meta.get("k"),
        "profile_basis": meta.get("k_basis"),
        "silhouette": round(sil, 4) if sil is not None else None,
        "silhouette_band": _silhouette_band(sil, bands),
        "strategy": meta.get("clustering_strategy"),
        "trained_at": meta.get("trained_at"),
        "schema_version": meta.get("schema_version"),
    }


def _instrument(test_id: str, paper: dict) -> dict:
    bands = paper["pipeline"]["silhouette_bands"]
    return {
        "test_id": test_id,
        **paper["instruments"][test_id],
        "trained_model": _trained(test_id, bands),
        "robustness": paper["robustness"].get(test_id, []),
        "comparators": paper["comparators"].get(test_id, []),
    }


@router.get("/summary")
def research_summary():
    paper = _paper()
    return {
        "title": paper["title"],
        "pipeline": paper["pipeline"],
        "caveats": paper["caveats"],
        "instruments": [_instrument(t, paper) for t in paper["instruments"]],
    }


@router.get("/acknowledgements")
def acknowledgements():
    from ml.psych_bibliography import all_authors
    paper = _paper()
    authors = all_authors()
    return [
        {"test_id": test_id, "code": info["code"], "domain": info["domain"], "authors": authors.get(test_id, [])}
        for test_id, info in paper["instruments"].items()
    ]


@router.get("/{test_id}")
def research_for_test(test_id: str):
    paper = _paper()
    if test_id not in paper["instruments"]:
        raise HTTPException(status_code=404, detail="Instrument not found")
    return {
        "pipeline": paper["pipeline"],
        "caveats": paper["caveats"],
        **_instrument(test_id, paper),
    }
