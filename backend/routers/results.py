from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Dict, Optional
import uuid
import json
from datetime import datetime
from database.db import get_db
from routers.auth import get_current_user
from ml.inference import run_inference
from routers.tests import load_questions
from security import assert_owns_result
import csv
import os

router = APIRouter()

DATASETS_DIR = os.path.join(os.path.dirname(__file__), "../datasets")

VALID_TESTS = [
    # Tier A (ML pipeline)
    "hexaco", "sixteenpf", "darktriad", "attachment", "riasec", "aesthetic",
    "hsq", "kims", "fti", "dass", "npi", "ambi", "gcbs",
    # Tier B (LLM clustering)
    "pvq", "bpnss", "who5", "pid5",
]

DATASET_FOLDER_MAP = {
    "hexaco":     "HEXACO",
    "sixteenpf":  "16PF",
    "darktriad":  "SD3",
    "attachment": "ECR-data-1March2018",
    "riasec":     "RIASEC_data12Dec2018",
    "aesthetic":  "APS_data",
    "hsq":        "HSQ",
    "kims":       "KIMS",
    "fti":        "FTI",
    "dass":       "DASS_data_21.02.19",
    "npi":        "NPI",
    "ambi":       "AMBI_data_Nov2019",
    "gcbs":       "GCBS",
    # Tier B has no dataset folder
}


class SubmitTestRequest(BaseModel):
    test_type: str
    responses: Dict[str, int]
    consent_to_dataset: bool = False
    question_contexts: Optional[Dict[str, str]] = None


@router.post("/submit")
def submit_test(body: SubmitTestRequest, current_user=Depends(get_current_user)):
    try:
        if body.test_type not in VALID_TESTS:
            raise HTTPException(status_code=400, detail=f"Invalid test type: '{body.test_type}'")

        if len(body.responses) == 0:
            raise HTTPException(status_code=400, detail="No responses provided")

        print("[DEBUG] Step 1: Running inference")
        context_notes = _build_context_notes(body.test_type, body.question_contexts)
        result = run_inference(body.test_type, body.responses, context_notes=context_notes)

        print("[DEBUG] Step 2: Preparing archetype")
        archetype = result.get("archetype") or {}

        result_id = str(uuid.uuid4())
        db        = get_db()

        print("[DEBUG] Step 3: Inserting into DB")
        db.execute("""
            INSERT INTO test_results
            (id, user_id, test_type, raw_responses, trait_scores, percentiles,
             archetype_id, archetype_name, archetype_description,
             umap_x, umap_y, similarity_pct, rarity_pct, neighborhood_traits, consented_to_dataset, taken_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            result_id,
            current_user["id"],
            body.test_type,
            json.dumps(body.responses),
            json.dumps(result["trait_scores"]),
            json.dumps(result["percentiles"]),
            archetype.get("id"),
            archetype.get("name"),
            archetype.get("tagline"),
            result["umap_x"],
            result["umap_y"],
            result["similarity_pct"],
            result["rarity_pct"],
            json.dumps(result["neighborhood"]),
            1 if body.consent_to_dataset else 0,
            datetime.utcnow().isoformat(),
        ))

        print("[DEBUG] Step 4: Updating profile")
        profile = db.execute(
            "SELECT * FROM unified_profiles WHERE user_id = ?",
            (current_user["id"],)
        ).fetchone()

        completed = json.loads(profile["completed_tests"] or "[]") if profile else []
        if body.test_type not in completed:
            completed.append(body.test_type)

        db.execute("""
            INSERT OR REPLACE INTO unified_profiles (user_id, completed_tests, last_updated)
            VALUES (?, ?, ?)
        """, (current_user["id"], json.dumps(completed), datetime.utcnow().isoformat()))

        db.commit()
        db.close()

        print("[DEBUG] Step 5: Dataset write")
        if body.consent_to_dataset:
            try:
                _append_to_dataset(body.test_type, body.responses)
            except Exception as e:
                print("[dataset crash]", e)

        print("[DEBUG] SUCCESS")

        return {
            "result_id":     result_id,
            "test_type":     body.test_type,
            "trait_scores":  result["trait_scores"],
            "percentiles":   result["percentiles"],
            "archetype":     result["archetype"],
            "umap_x":        result["umap_x"],
            "umap_y":        result["umap_y"],
            "similarity_pct": result["similarity_pct"],
            "rarity_pct":    result["rarity_pct"],
            "neighborhood":  result["neighborhood"],
            "insights":      result["insights"],
        }

    except HTTPException:
        raise
    except Exception as e:
        print("BACKEND CRASH:", str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/my")
def get_my_results(current_user=Depends(get_current_user)):
    """Returns ONLY the authenticated user's own results – never another user's."""
    db   = get_db()
    rows = db.execute(
        "SELECT * FROM test_results WHERE user_id = ? ORDER BY taken_at DESC",
        (current_user["id"],)
    ).fetchall()
    db.close()

    results = []
    for row in rows:
        r = dict(row)
        # Ownership enforced by the WHERE clause above; double-check for safety
        assert_owns_result(r, current_user["id"], "result")
        r["trait_scores"]        = json.loads(r["trait_scores"])
        r["percentiles"]         = json.loads(r["percentiles"])
        r["neighborhood_traits"] = json.loads(r["neighborhood_traits"] or "{}")
        r["raw_responses"]       = None  # never expose raw responses in list endpoint
        results.append(r)
    return results


@router.get("/my/{test_type}/latest")
def get_latest_result(test_type: str, current_user=Depends(get_current_user)):
    """Returns the latest result for the given test type for the authenticated user only."""
    db  = get_db()
    row = db.execute(
        "SELECT * FROM test_results WHERE user_id = ? AND test_type = ? ORDER BY taken_at DESC LIMIT 1",
        (current_user["id"], test_type)
    ).fetchone()
    db.close()

    if not row:
        raise HTTPException(status_code=404, detail="No result found")

    r = dict(row)
    # IDOR guard: the WHERE clause already filters by user_id, but we enforce explicitly
    assert_owns_result(r, current_user["id"], "result")

    r["trait_scores"]        = json.loads(r["trait_scores"])
    r["percentiles"]         = json.loads(r["percentiles"])
    r["neighborhood_traits"] = json.loads(r["neighborhood_traits"] or "{}")
    return r


@router.get("/map/{test_type}")
def get_map_coords(test_type: str, current_user=Depends(get_current_user)):
    """Map coordinates are aggregate/anonymous – no per-user data leaked here."""
    coords_path = os.path.join(
        os.path.dirname(__file__), f"../models/{test_type}_map_coords.json"
    )
    if not os.path.exists(coords_path):
        import random
        random.seed(42)
        coords = [[random.gauss(0, 3), random.gauss(0, 3)] for _ in range(500)]
        return {"coords": coords, "is_synthetic": True}
    with open(coords_path, encoding="utf-8") as f:
        coords = json.load(f)
    return {"coords": coords[:2000], "is_synthetic": False}


@router.get("/{result_id}")
def get_result(result_id: str, current_user=Depends(get_current_user)):
    """
    Returns a single result by ID.
    IDOR protection: user_id is checked in SQL AND via assert_owns_result.
    A user who guesses another user's result UUID gets a 404, not a 403,
    so the existence of the record is not disclosed.
    """
    db  = get_db()
    row = db.execute(
        # Deliberately filter by user_id in SQL as first line of defence
        "SELECT * FROM test_results WHERE id = ? AND user_id = ?",
        (result_id, current_user["id"])
    ).fetchone()
    db.close()

    # Second line of defence: ownership helper raises 404 if mismatch
    assert_owns_result(dict(row) if row else None, current_user["id"], "result")

    r = dict(row)
    r["trait_scores"]        = json.loads(r["trait_scores"])
    r["percentiles"]         = json.loads(r["percentiles"])
    r["neighborhood_traits"] = json.loads(r["neighborhood_traits"] or "{}")
    return r


# ---------------------------------------------------------------------------
# Optional context helper
# ---------------------------------------------------------------------------

def _build_context_notes(test_id: str, question_contexts: Optional[Dict[str, str]]):
    """
    Resolve user-supplied per-question notes into a list of
    {question, note} pairs, attaching the question text so the
    refinement layer can interpret each note in context.

    Returns None when no usable notes were provided.
    """
    if not question_contexts:
        return None

    cleaned = {
        qid: note.strip()
        for qid, note in question_contexts.items()
        if isinstance(note, str) and note.strip()
    }
    if not cleaned:
        return None

    text_by_id = {}
    try:
        data = load_questions(test_id)
        for q in (data.get("questions", []) if isinstance(data, dict) else data):
            text_by_id[q.get("id")] = q.get("text", "")
    except Exception as e:
        print(f"[context] could not load question text for {test_id}: {e}")

    notes = []
    for qid, note in cleaned.items():
        notes.append({
            "question_id": qid,
            "question": text_by_id.get(qid, ""),
            "note": note,
        })
    return notes or None


# ---------------------------------------------------------------------------
# Archetype compatibility
# ---------------------------------------------------------------------------

MODELS_DIR = os.path.join(os.path.dirname(__file__), "../models")

# Display names for cross-test compatibility rows.
TEST_DISPLAY_NAMES = {
    "hexaco": "Six-Trait Personality", "sixteenpf": "Sixteen Personality Traits",
    "darktriad": "Dark Traits", "fti": "Temperament Type",
    "npi": "How You See Yourself", "ambi": "Broad Personality Scan",
    "pid5": "Five Trait Styles", "hsq": "Humor Style",
    "kims": "Mindfulness Skills", "gcbs": "Conspiracy Beliefs",
    "aesthetic": "Aesthetic Taste", "riasec": "Career Type",
    "attachment": "Attachment Style", "pvq": "Core Values",
    "bpnss": "Inner Needs", "dass": "Mood and Stress", "who5": "Wellbeing Check",
}

_arch_cache: Dict[str, Optional[dict]] = {}


def _load_archetypes(test_id: str) -> Optional[dict]:
    if test_id in _arch_cache:
        return _arch_cache[test_id]
    path = os.path.join(MODELS_DIR, f"{test_id}_archetypes.json")
    data = None
    if os.path.exists(path):
        try:
            with open(path, encoding="utf-8") as f:
                data = json.load(f)
        except Exception as e:
            print(f"[compat] failed loading {test_id} archetypes: {e}")
    _arch_cache[test_id] = data
    return data


def _shape_vector(centroid):
    """Normalize a cluster centroid to a zero-mean, unit-variance shape
    vector. Compatibility compares profile SHAPES, so tests whose raw trait
    scales differ still land on a common footing."""
    import numpy as np
    v = np.asarray(centroid, dtype=np.float64)
    if v.size == 0:
        return None
    sd = v.std()
    if sd < 1e-9:
        return np.zeros_like(v)
    return (v - v.mean()) / sd


def _cosine(a, b) -> float:
    import numpy as np
    na, nb = np.linalg.norm(a), np.linalg.norm(b)
    if na < 1e-9 or nb < 1e-9:
        return 0.0
    return float(np.dot(a, b) / (na * nb))


def _signature(shape, points: int = 6):
    """Resample a sorted shape profile onto a fixed number of points so
    clusters from tests with different trait counts become comparable.
    Captures how peaked vs flat, and how skewed, a profile is."""
    import numpy as np
    s = np.sort(shape)[::-1]
    if s.size == 1:
        return np.full(points, float(s[0]))
    xs = np.linspace(0, s.size - 1, points)
    return np.interp(xs, np.arange(s.size), s)


def _to_score(cos: float) -> int:
    """Map cosine similarity [-1, 1] to a compatibility score out of 100."""
    return int(round(max(0.0, min(100.0, 50.0 + 50.0 * cos))))


@router.get("/compatibility/{result_id}")
def get_compatibility(result_id: str, current_user=Depends(get_current_user)):
    """Compatibility of the user's archetype with every other archetype of
    the same test (within-test) and with the archetypes of all other tests
    (cross-test), scored out of 100."""
    db  = get_db()
    row = db.execute(
        "SELECT * FROM test_results WHERE id = ? AND user_id = ?",
        (result_id, current_user["id"])
    ).fetchone()
    db.close()
    assert_owns_result(dict(row) if row else None, current_user["id"], "result")

    r         = dict(row)
    test_type = r["test_type"]
    arch_id   = r["archetype_id"] or ""
    arch_name = r["archetype_name"] or ""

    archetypes = _load_archetypes(test_type)
    if not archetypes:
        return {"available": False, "reason": "No archetype model for this test."}

    # Locate the user's cluster: by id ("cluster_3"), then by exact name.
    user_key = None
    for cid, info in archetypes.items():
        if info.get("id") == arch_id or cid == arch_id:
            user_key = cid
            break
    if user_key is None:
        for cid, info in archetypes.items():
            if (info.get("name") or "").strip().lower() == arch_name.strip().lower():
                user_key = cid
                break
    if user_key is None:
        user_key = next(iter(archetypes))

    user_info  = archetypes[user_key]
    user_shape = _shape_vector(user_info.get("centroid") or [])
    if user_shape is None:
        return {"available": False, "reason": "User cluster has no centroid."}
    user_sig = _signature(user_shape)

    # Within-test: same trait space, direct shape comparison.
    same_test = []
    for cid, info in archetypes.items():
        if cid == user_key:
            continue
        shape = _shape_vector(info.get("centroid") or [])
        if shape is None or shape.shape != user_shape.shape:
            continue
        score = _to_score(_cosine(user_shape, shape))
        same_test.append({
            "test_id":   test_type,
            "test_name": TEST_DISPLAY_NAMES.get(test_type, test_type),
            "name":      info.get("name"),
            "tagline":   info.get("tagline"),
            "color":     info.get("color"),
            "score":     score,
            "kind":      "within",
        })
    same_test.sort(key=lambda x: -x["score"])

    # Cross-test: compare fixed-length profile signatures.
    cross_test = []
    for other_id, display in TEST_DISPLAY_NAMES.items():
        if other_id == test_type:
            continue
        other = _load_archetypes(other_id)
        if not other:
            continue
        best = None
        for cid, info in other.items():
            shape = _shape_vector(info.get("centroid") or [])
            if shape is None:
                continue
            score = _to_score(_cosine(user_sig, _signature(shape)))
            entry = {
                "test_id":   other_id,
                "test_name": display,
                "name":      info.get("name"),
                "tagline":   info.get("tagline"),
                "color":     info.get("color"),
                "score":     score,
                "kind":      "cross",
            }
            if best is None or score > best["score"]:
                best = entry
        if best:
            cross_test.append(best)
    cross_test.sort(key=lambda x: -x["score"])

    combined = sorted(same_test + cross_test, key=lambda x: -x["score"])

    return {
        "available":  True,
        "user": {
            "test_id":   test_type,
            "test_name": TEST_DISPLAY_NAMES.get(test_type, test_type),
            "name":      user_info.get("name") or arch_name,
            "tagline":   user_info.get("tagline"),
        },
        "same_test":  same_test,
        "cross_test": cross_test[:8],
        "top5":       combined[:5],
        "all_names":  [v.get("name") for v in archetypes.values()],
    }


# ---------------------------------------------------------------------------
# Dataset helpers (unchanged logic, kept intact)
# ---------------------------------------------------------------------------

def _get_dataset_path(test_id: str) -> Optional[str]:
    folder_name = DATASET_FOLDER_MAP.get(test_id)
    if folder_name:
        subfolder_path = os.path.join(DATASETS_DIR, folder_name, "data.csv")
        if os.path.exists(os.path.dirname(subfolder_path)):
            return subfolder_path
    return os.path.join(DATASETS_DIR, f"{test_id}.csv")


def _append_to_dataset(test_id: str, responses: Dict[str, int]):
    path = _get_dataset_path(test_id)
    if not path:
        return

    os.makedirs(os.path.dirname(path), exist_ok=True)

    try:
        file_exists = os.path.isfile(path) and os.path.getsize(path) > 0

        if file_exists:
            with open(path, "r", newline="", encoding="utf-8") as f:
                reader  = csv.reader(f, delimiter="\t")
                headers = next(reader, None)
            if not headers:
                file_exists = False
                headers     = sorted(responses.keys())
        else:
            headers = sorted(responses.keys())

        row    = {col: responses.get(col, "") for col in headers}
        filled = sum(1 for v in row.values() if v != "")

        if filled < len(headers) * 0.8:
            print(f"[dataset] Skipping {test_id}: only {filled}/{len(headers)} columns filled")
            return

        with open(path, "a", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=headers, delimiter="\t", extrasaction="ignore")
            if not file_exists:
                writer.writeheader()
            writer.writerow(row)

        print(f"[dataset] Appended row to {path} ({filled}/{len(headers)} cols)")

    except Exception as e:
        print(f"[dataset] Failed to append {test_id}: {e}")