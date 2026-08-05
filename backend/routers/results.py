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
import threading

router = APIRouter()


def _enrich_result_async(result_id: str, test_type: str, trait_scores: Dict,
                         percentiles: Dict, archetype: Optional[Dict],
                         insights: Dict, context_notes) -> None:
    """Background enrichment: call the specialty psychology model (waiting
    out a Space wake-up if needed), persist the enriched insights, and flip
    enrichment_status so the results page can stop polling. Fail-soft , on
    any error the row keeps its base insights with status 'failed'."""
    status = "failed"
    try:
        from ml.psych_layer import enrich_result
        enriched = enrich_result(test_type, trait_scores, percentiles,
                                 archetype or {}, dict(insights),
                                 context_notes=context_notes)
        insights = enriched or insights
        status = "done"
    except Exception as e:
        print(f"[psych] background enrichment failed for {result_id}: {e}")
    try:
        db = get_db()
        db.execute(
            "UPDATE test_results SET insights = ?, enrichment_status = ? WHERE id = ?",
            (json.dumps(insights), status, result_id),
        )
        db.commit()
        db.close()
    except Exception as e:
        print(f"[psych] could not persist enrichment for {result_id}: {e}")

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
             umap_x, umap_y, similarity_pct, rarity_pct, neighborhood_traits,
             consented_to_dataset, taken_at, insights, enrichment_status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
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
            json.dumps(result["insights"]),
            "pending",
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

        # Step 6: specialty psychology-model enrichment in the background.
        # The worker was pre-warmed while the user answered, but even a slow
        # or waking worker costs the user nothing , this response returns
        # NOW with the base insights; the enriched version lands in the row
        # and the results page picks it up when it's ready.
        threading.Thread(
            target=_enrich_result_async,
            args=(result_id, body.test_type, result["trait_scores"],
                  result["percentiles"], result["archetype"],
                  result["insights"], context_notes),
            daemon=True,
        ).start()

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
    """Returns ONLY the authenticated user's own results - never another user's."""
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
    r["insights"]            = json.loads(r["insights"]) if r.get("insights") else None
    return r


@router.get("/map/{test_type}")
def get_map_coords(test_type: str, current_user=Depends(get_current_user)):
    """Map coordinates are aggregate/anonymous - no per-user data leaked here."""
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
    r["insights"]            = json.loads(r["insights"]) if r.get("insights") else None

    # Older rows may carry placeholder names from before the archetype
    # models were named ("Archetype 2" / "LLM enrichment pending").
    # Refresh them from the current archetype catalogue by cluster id.
    import re as _re
    name = r.get("archetype_name") or ""
    tag  = r.get("archetype_description") or ""
    if _re.match(r"^Archetype \d+$", name) or "enrichment pending" in tag.lower():
        catalogue = _load_archetypes(r["test_type"]) or {}
        for cid, info in catalogue.items():
            if info.get("id") == r.get("archetype_id") or cid == r.get("archetype_id"):
                r["archetype_name"]        = info.get("name") or name
                r["archetype_description"] = info.get("tagline") or tag
                break
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


# Scoring model grounded in peer-reviewed findings:
#   1. Profile similarity as the base signal: actual similarity predicts
#      attraction (Byrne, 1971, "The Attraction Paradigm"; Montoya, Horton &
#      Kirchner, 2008, meta-analysis, J. of Social and Personal Relationships).
#      Profiles are compared as population z-score vectors per Furr (2008,
#      J. of Personality) so normativeness does not inflate similarity.
#   2. Interpersonal circumplex: SIMILARITY on warmth/communion but
#      COMPLEMENTARITY on dominance/agency predicts smoother interactions
#      (Sadler & Woody, 2003, JPSP; Markey & Markey, 2007).
#   3. Partner effects: a partner's low negative-affect and high
#      steadiness/conscientiousness predict relationship satisfaction
#      regardless of similarity (Malouff et al., 2010, J. of Research in
#      Personality; Dyrenforth et al., 2010, JPSP).

WARMTH_KEYS = ("agreeable", "warmth", "affiliat", "social", "relatedness",
               "benevolence", "secure", "empath", "warm", "helper")
AGENCY_KEYS = ("dominance", "assertive", "authority", "enterprising",
               "director", "power", "exhibition", "superiority", "energy",
               "liveliness", "boldness")
NEGAFF_KEYS = ("neurotic", "emotionality", "anxiety", "anxious", "depress",
               "stress", "tension", "apprehension", "negative",
               "self-defeating", "vigilance", "avoidant")
STEADY_KEYS = ("conscientious", "stability", "wellbeing", "accepting",
               "affect regulation", "mindful", "observ", "awareness",
               "self-enhancing")

_popstats_cache: Dict[str, Optional[dict]] = {}
_traitnames_cache: Dict[str, Optional[list]] = {}


def _trait_names(test_id: str) -> Optional[list]:
    """Trait names in centroid order: prefer the model meta file, fall back
    to the distributions file's key order."""
    if test_id in _traitnames_cache:
        return _traitnames_cache[test_id]
    names = None
    meta_path = os.path.join(MODELS_DIR, f"{test_id}_meta.json")
    if os.path.exists(meta_path):
        try:
            with open(meta_path, encoding="utf-8") as f:
                names = json.load(f).get("trait_names")
        except Exception:
            names = None
    if not names:
        dist_path = os.path.join(MODELS_DIR, f"{test_id}_distributions.json")
        if os.path.exists(dist_path):
            try:
                with open(dist_path, encoding="utf-8") as f:
                    names = list(json.load(f).keys())
            except Exception:
                names = None
    _traitnames_cache[test_id] = names
    return names


def _cluster_avg_profile(test_id: str, info: dict) -> Optional[list]:
    """Trait scores + population percentiles of the AVERAGE member of a
    cluster (its centroid). Gives the user the concrete profile behind each
    compatible archetype instead of just a name and a score."""
    centroid = info.get("centroid")
    names = _trait_names(test_id)
    if not centroid or not names or len(names) != len(centroid):
        return None
    try:
        from ml.inference import calc_percentiles
        scores = {n: float(c) for n, c in zip(names, centroid)}
        pcts = calc_percentiles(test_id, scores)
        return [
            {"trait": n, "score": round(scores[n], 3), "percentile": pcts.get(n, 50)}
            for n in names
        ]
    except Exception as e:
        print(f"[compat] avg profile for {test_id}: {e}")
        return None


def _cluster_definition(info: dict) -> str:
    """One-line definition of a cluster , the centroid description generated
    at training time (which traits sit above/below the population and by how
    much), falling back to the tagline."""
    return (info.get("description") or info.get("tagline") or "").strip()


def _pop_stats(test_id: str) -> Optional[dict]:
    """Population mean/std per trait, from the training distributions."""
    if test_id in _popstats_cache:
        return _popstats_cache[test_id]
    import numpy as np
    path = os.path.join(MODELS_DIR, f"{test_id}_distributions.json")
    stats = None
    if os.path.exists(path):
        try:
            with open(path, encoding="utf-8") as f:
                d = json.load(f)
            stats = {k: (float(np.mean(v)), float(np.std(v)) + 1e-8)
                     for k, v in d.items()}
        except Exception as e:
            print(f"[compat] distributions for {test_id}: {e}")
    _popstats_cache[test_id] = stats
    return stats


def _z_profile(test_id: str, centroid):
    """Cluster centroid as z-scores against the test's population
    (Furr, 2008). Falls back to within-centroid standardisation when no
    distribution data exists."""
    import numpy as np
    stats = _pop_stats(test_id)
    if stats and len(stats) == len(centroid):
        traits = list(stats.keys())
        z = np.array([(c - stats[t][0]) / stats[t][1]
                      for t, c in zip(traits, centroid)])
        return traits, z
    v = np.asarray(centroid, dtype=np.float64)
    sd = v.std()
    z = (v - v.mean()) / sd if sd > 1e-9 else np.zeros_like(v)
    return [f"t{i}" for i in range(len(v))], z


def _class_means(traits, z) -> dict:
    import numpy as np
    out = {}
    for name, keys in (("warmth", WARMTH_KEYS), ("agency", AGENCY_KEYS),
                       ("negaff", NEGAFF_KEYS), ("steady", STEADY_KEYS)):
        vals = [zz for tr, zz in zip(traits, z)
                if any(k in tr.lower() for k in keys)]
        out[name] = float(np.mean(vals)) if vals else 0.0
    return out


def _pearson(a, b) -> float:
    import numpy as np
    if len(a) < 2 or len(b) < 2 or np.std(a) < 1e-9 or np.std(b) < 1e-9:
        return 0.0
    return float(np.corrcoef(a, b)[0, 1])


def _signature(z, points: int = 8):
    """Sorted z-profile resampled to a fixed length so clusters from tests
    with different trait counts become comparable (profile elevation and
    scatter, after Furr, 2008)."""
    import numpy as np
    s = np.sort(z)[::-1]
    if s.size == 1:
        return np.full(points, float(s[0]))
    xs = np.linspace(0, s.size - 1, points)
    return np.interp(xs, np.arange(s.size), s)


def _compat_score(user_traits, user_z, other_traits, other_z, same_space: bool) -> int:
    """Composite compatibility score out of 100."""
    base = (_pearson(user_z, other_z) if same_space
            else _pearson(_signature(user_z), _signature(other_z)))
    u = _class_means(user_traits, user_z)
    o = _class_means(other_traits, other_z)
    # Similarity on warmth/communion (Sadler & Woody, 2003)
    warmth_sim = 1.0 - min(abs(u["warmth"] - o["warmth"]) / 2.0, 1.0)
    # Complementarity on dominance/agency (Sadler & Woody, 2003; Markey 2007)
    agency_comp = max(-1.0, min(1.0, -u["agency"] * o["agency"]))
    # Partner effects (Malouff et al., 2010; Dyrenforth et al., 2010)
    partner = max(-1.0, min(1.0, 0.5 * o["steady"] - 0.8 * o["negaff"]))
    raw = (0.50 * base
           + 0.18 * (2.0 * warmth_sim - 1.0)
           + 0.12 * agency_comp
           + 0.20 * partner)
    return int(round(max(5.0, min(98.0, 50.0 + 50.0 * raw))))


COMPAT_METHOD = {
    "summary": ("Scores blend profile similarity (Byrne, 1971; Montoya, "
                "Horton & Kirchner, 2008; profile metrics after Furr, 2008), "
                "warmth similarity with dominance complementarity (Sadler & "
                "Woody, 2003; Markey & Markey, 2007), and partner effects of "
                "low negative affect and high steadiness (Malouff et al., "
                "2010; Dyrenforth et al., 2010)."),
    "weights": {"profile_similarity": 0.50, "warmth_similarity": 0.18,
                "dominance_complementarity": 0.12, "partner_effects": 0.20},
}


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

    user_info = archetypes[user_key]
    if not user_info.get("centroid"):
        return {"available": False, "reason": "User cluster has no centroid."}
    user_traits, user_z = _z_profile(test_type, user_info["centroid"])

    # Within-test: same trait space, direct z-profile comparison.
    same_test = []
    for cid, info in archetypes.items():
        if cid == user_key or not info.get("centroid"):
            continue
        o_traits, o_z = _z_profile(test_type, info["centroid"])
        same_space = len(o_z) == len(user_z)
        score = _compat_score(user_traits, user_z, o_traits, o_z, same_space)
        same_test.append({
            "test_id":     test_type,
            "test_name":   TEST_DISPLAY_NAMES.get(test_type, test_type),
            "name":        info.get("name"),
            "tagline":     info.get("tagline"),
            "definition":  _cluster_definition(info),
            "avg_profile": _cluster_avg_profile(test_type, info),
            "color":       info.get("color"),
            "score":       score,
            "kind":        "within",
        })
    same_test.sort(key=lambda x: -x["score"])

    # Cross-test: fixed-length z-profile signatures + partner effects.
    cross_test = []
    for other_id, display in TEST_DISPLAY_NAMES.items():
        if other_id == test_type:
            continue
        other = _load_archetypes(other_id)
        if not other:
            continue
        best = None
        for cid, info in other.items():
            if not info.get("centroid"):
                continue
            o_traits, o_z = _z_profile(other_id, info["centroid"])
            score = _compat_score(user_traits, user_z, o_traits, o_z, False)
            entry = {
                "test_id":     other_id,
                "test_name":   display,
                "name":        info.get("name"),
                "tagline":     info.get("tagline"),
                "definition":  _cluster_definition(info),
                "avg_profile": _cluster_avg_profile(other_id, info),
                "color":       info.get("color"),
                "score":       score,
                "kind":        "cross",
            }
            if best is None or score > best["score"]:
                best = entry
        if best:
            cross_test.append(best)
    cross_test.sort(key=lambda x: -x["score"])

    combined = sorted(same_test + cross_test, key=lambda x: -x["score"])

    # Bottom 5 = the LEAST compatible clusters, presented worst-first. combined
    # is sorted best-first, so the tail holds the lowest scorers; reverse it so
    # index 0 is the single least-compatible archetype.
    bottom5 = list(reversed(combined[-5:])) if len(combined) >= 5 else \
        list(reversed(combined))

    return {
        "available":  True,
        "user": {
            "test_id":     test_type,
            "test_name":   TEST_DISPLAY_NAMES.get(test_type, test_type),
            "name":        user_info.get("name") or arch_name,
            "tagline":     user_info.get("tagline"),
            "definition":  _cluster_definition(user_info),
            "avg_profile": _cluster_avg_profile(test_type, user_info),
        },
        "same_test":  same_test,
        "cross_test": cross_test[:8],
        "top5":       combined[:5],
        "bottom5":    bottom5,
        "all_names":  [v.get("name") for v in archetypes.values()],
        "method":     COMPAT_METHOD,
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