import numpy as np
import json
import os
import pickle
from typing import Dict, List, Any, Optional

from ml.scoring_keys import (
    HEXACO_FACETS, HEXACO_REVERSED_ITEMS, HSQ_SCALES, HSQ_REVERSED,
    ECR_AVOIDANCE, ECR_ANXIETY, ECR_REVERSED, AMBI_NEO_FACETS,
)

MODELS_DIR   = os.path.join(os.path.dirname(__file__), "../models")
DATASETS_DIR = os.path.join(os.path.dirname(__file__), "../datasets")

def score_hexaco(responses: Dict[str, int]) -> Dict[str, float]:
    def item(key):
        v = responses.get(key, 4)
        return 8 - v if key in HEXACO_REVERSED_ITEMS else v
    result = {}
    for trait, prefixes in HEXACO_FACETS.items():
        items = [item(f"{p}{i}") for p in prefixes for i in range(1, 11)]
        result[trait] = round((float(np.mean(items)) - 1) / 6, 4)
    return result


def score_darktriad(responses: Dict[str, int]) -> Dict[str, float]:
    def safe(key): return responses.get(key, 3)
    def r(x): return 6 - x

    mach = np.mean([safe(f"M{i}") for i in range(1, 10)])
    narc = np.mean([safe("N1"), r(safe("N2")), safe("N3"), safe("N4"),
                    safe("N5"), r(safe("N6")), safe("N7"), r(safe("N8")), safe("N9")])
    psyc = np.mean([safe("P1"), r(safe("P2")), safe("P3"), safe("P4"),
                    safe("P5"), safe("P6"), r(safe("P7")), safe("P8"), safe("P9")])

    def norm(x): return round((x - 1) / 4, 4)
    return {
        "Machiavellianism": norm(mach),
        "Narcissism":       norm(narc),
        "Psychopathy":      norm(psyc),
    }


def score_dass(responses: Dict[str, int]) -> Dict[str, float]:
    def safe(key): return responses.get(key, 1)

    depression_keys = [f"D{i}" for i in range(1, 15)]
    anxiety_keys    = [f"A{i}" for i in range(1, 15)]
    stress_keys     = [f"S{i}" for i in range(1, 15)]

    dep_raw = sum(safe(k) - 1 for k in depression_keys)
    anx_raw = sum(safe(k) - 1 for k in anxiety_keys)
    str_raw = sum(safe(k) - 1 for k in stress_keys)

    return {
        "Depression": round(min(dep_raw / 42, 1.0), 4),
        "Anxiety":    round(min(anx_raw / 42, 1.0), 4),
        "Stress":     round(min(str_raw / 42, 1.0), 4),
    }


def score_hsq(responses: Dict[str, int]) -> Dict[str, float]:
    def item(q):
        v = responses.get(f"Q{q}", 3)
        return 6 - v if q in HSQ_REVERSED else v
    return {
        scale: round((float(np.mean([item(q) for q in qs])) - 1) / 4, 4)
        for scale, qs in HSQ_SCALES.items()
    }


def score_kims(responses: Dict[str, int]) -> Dict[str, float]:
    """Kentucky Inventory of Mindfulness Skills (Baer et al. 2004), 4 facets."""
    def safe(key): return responses.get(key, 3)
    def r(x): return 6 - x
    observing  = float(np.mean([safe(f"Q{i}") for i in [1, 5, 9, 13, 17, 21, 25, 29, 33, 37, 39]]))
    describing = float(np.mean([
        safe("Q2"), safe("Q6"), safe("Q10"),
        r(safe("Q14")), r(safe("Q18")), r(safe("Q22")),
        safe("Q26"), safe("Q30"), safe("Q34"),
    ]))
    acting = float(np.mean([
        r(safe("Q3")), safe("Q7"), r(safe("Q11")), safe("Q15"), safe("Q19"),
        r(safe("Q23")), r(safe("Q27")), r(safe("Q31")), r(safe("Q35")), safe("Q38"),
    ]))
    accepting = float(np.mean([
        r(safe("Q4")), r(safe("Q8")), r(safe("Q12")), r(safe("Q16")),
        r(safe("Q20")), r(safe("Q24")), r(safe("Q28")), r(safe("Q32")), r(safe("Q36")),
    ]))
    norm = lambda x: round((x - 1) / 4, 4)
    return {
        "Observing":                  norm(observing),
        "Describing":                 norm(describing),
        "Acting with Awareness":      norm(acting),
        "Accepting without Judgment": norm(accepting),
    }


def score_fti(responses: Dict[str, int]) -> Dict[str, float]:
    """Fisher Temperament Inventory (Brown, Acevedo & Fisher 2013), 4 temperaments x 14 items."""
    def safe(key): return responses.get(key, 2.5)
    explorer   = float(np.mean([safe(f"Q{i}") for i in range(1, 15)]))
    builder    = float(np.mean([safe(f"Q{i}") for i in range(15, 29)]))
    director   = float(np.mean([safe(f"Q{i}") for i in range(29, 43)]))
    negotiator = float(np.mean([safe(f"Q{i}") for i in range(43, 57)]))
    norm = lambda x: round((x - 1) / 3, 4)
    return {
        "Explorer":   norm(explorer),
        "Builder":    norm(builder),
        "Director":   norm(director),
        "Negotiator": norm(negotiator),
    }


# NPI scoring keys (Raskin & Terry 1988). Value-per-Q that scores as narcissistic.
_NPI_NARC_KEY = {
    1: 1, 2: 1, 3: 1, 4: 2, 5: 2, 6: 1, 7: 2, 8: 1, 9: 2, 10: 2,
    11: 1, 12: 1, 13: 1, 14: 1, 15: 2, 16: 1, 17: 2, 18: 2, 19: 2, 20: 2,
    21: 1, 22: 2, 23: 2, 24: 1, 25: 1, 26: 2, 27: 1, 28: 2, 29: 1, 30: 1,
    31: 1, 32: 2, 33: 1, 34: 1, 35: 2, 36: 1, 37: 1, 38: 1, 39: 1, 40: 2,
}
_NPI_FACETS = {
    "Authority":        [1, 8, 10, 11, 12, 32, 33, 36],
    "Self-Sufficiency": [17, 21, 22, 31, 34, 39],
    "Superiority":      [4, 9, 26, 37, 40],
    "Exhibitionism":    [2, 3, 7, 20, 28, 30, 38],
    "Exploitativeness": [6, 13, 16, 23, 35],
    "Vanity":           [15, 19, 29],
    "Entitlement":      [5, 14, 18, 24, 25, 27],
}


def score_npi(responses: Dict[str, int]) -> Dict[str, float]:
    """Narcissistic Personality Inventory (Raskin & Terry 1988), 7 facets, forced-choice."""
    def safe(key): return responses.get(key, 0)
    result = {}
    for facet, qnums in _NPI_FACETS.items():
        score = sum(1 for q in qnums if safe(f"Q{q}") == _NPI_NARC_KEY[q])
        result[facet] = round(score / len(qnums), 4)
    return result


def score_ambi(responses: Dict[str, int]) -> Dict[str, float]:
    def item(q, sign):
        v = responses.get(f"Q{q}", 4)
        return v if sign > 0 else 8 - v
    result = {}
    for domain, facets in AMBI_NEO_FACETS.items():
        facet_means = [float(np.mean([item(q, sign) for q, sign in keyed])) for keyed in facets.values()]
        result[domain] = round((float(np.mean(facet_means)) - 1) / 6, 4)
    return result


def score_gcbs(responses: Dict[str, int]) -> Dict[str, float]:
    """Generic Conspiracist Beliefs Scale (Brotherton, French & Pickering 2013), 5 factors x 3 items."""
    def safe(key): return responses.get(key, 3)
    factors = {
        "Government Malfeasance":     [1, 6, 11],
        "Malevolent Global":          [2, 7, 12],
        "Extraterrestrial Coverup":   [3, 8, 13],
        "Personal Wellbeing Threats": [4, 9, 14],
        "Control of Information":     [5, 10, 15],
    }
    norm = lambda x: round((x - 1) / 4, 4)
    return {f: norm(float(np.mean([safe(f"Q{i}") for i in qs]))) for f, qs in factors.items()}


def score_riasec(responses: Dict[str, int]) -> Dict[str, float]:
    def safe(key): return responses.get(key, 3)

    groups = {
        "Realistic":     [f"R{i}" for i in range(1, 9)],
        "Investigative": [f"I{i}" for i in range(1, 9)],
        "Artistic":      [f"A{i}" for i in range(1, 9)],
        "Social":        [f"S{i}" for i in range(1, 9)],
        "Enterprising":  [f"E{i}" for i in range(1, 9)],
        "Conventional":  [f"C{i}" for i in range(1, 9)],
    }
    return {
        t: round((np.mean([safe(k) for k in keys]) - 1) / 4, 4)
        for t, keys in groups.items()
    }


def score_attachment(responses: Dict[str, int]) -> Dict[str, float]:
    def item(q):
        v = responses.get(f"ECR{q}", 3)
        return 6 - v if q in ECR_REVERSED else v
    anxiety   = (float(np.mean([item(q) for q in ECR_ANXIETY])) - 1) / 4
    avoidance = (float(np.mean([item(q) for q in ECR_AVOIDANCE])) - 1) / 4
    return {
        "Anxious":  round(anxiety, 4),
        "Avoidant": round(avoidance, 4),
        "Secure":   round(max(0.0, 1.0 - (anxiety + avoidance) / 2), 4),
    }


SCORERS = {
    "hexaco":     score_hexaco,
    "ambi":       score_ambi,
    "darktriad":  score_darktriad,
    "npi":        score_npi,
    "dass":       score_dass,
    "kims":       score_kims,
    "hsq":        score_hsq,
    "gcbs":       score_gcbs,
    "riasec":     score_riasec,
    "attachment": score_attachment,
    "fti":        score_fti,
}

# ---------------------------------------------------------------------------
# Model helpers
# ---------------------------------------------------------------------------

def load_model(test_id: str, model_type: str):
    path = os.path.join(MODELS_DIR, f"{test_id}_{model_type}.pkl")
    if not os.path.exists(path):
        return None
    with open(path, "rb") as f:
        return pickle.load(f)


def load_json(test_id: str, name: str):
    path = os.path.join(MODELS_DIR, f"{test_id}_{name}.json")
    if not os.path.exists(path):
        return None
    with open(path, encoding="utf-8") as f:
        return json.load(f)

def calc_percentiles(test_id: str, trait_scores: Dict[str, float]) -> Dict[str, int]:
    distributions = load_json(test_id, "distributions")
    percentiles: Dict[str, int] = {}
    for trait, score in trait_scores.items():
        if distributions and trait in distributions:
            arr = np.sort(np.array(distributions[trait]))
            pct = int(np.searchsorted(arr, score) / len(arr) * 100)
            percentiles[trait] = max(1, min(99, pct))
        else:
            percentiles[trait] = 50
    return percentiles


def get_fallback_archetype(test_id: str, trait_vector: List[float]) -> Dict:
    fallbacks = {
        "hexaco": [
            {"id": "principled_steward",   "name": "The Principled Steward",     "tagline": "Honesty as the through-line",          "color": "#6B8CAE"},
            {"id": "warm_connector",       "name": "The Warm Connector",         "tagline": "Energy that lifts a room",             "color": "#AE8A6B"},
            {"id": "thoughtful_observer",  "name": "The Thoughtful Observer",    "tagline": "Inner depth, careful presence",        "color": "#6AAE8A"},
            {"id": "open_explorer",        "name": "The Open Explorer",          "tagline": "Curiosity as a way of life",           "color": "#8A6BAE"},
        ],
        "darktriad": [
            {"id": "strategic_pragmatist", "name": "The Strategic Pragmatist",   "tagline": "Calculated, clear-eyed, effective",   "color": "#8A7A9A"},
            {"id": "grounded_empath",      "name": "The Grounded Empath",        "tagline": "Warmth over strategy",                "color": "#7A9A8A"},
        ],
        "fti": [
            {"id": "the_explorer",         "name": "The Explorer",                "tagline": "Novelty, energy, curiosity",          "color": "#9A7AAE"},
            {"id": "the_builder",          "name": "The Builder",                 "tagline": "Order, loyalty, steady hands",        "color": "#6AAE8A"},
            {"id": "the_director",         "name": "The Director",                "tagline": "Decisive, analytical, ambitious",     "color": "#AE7A6B"},
            {"id": "the_negotiator",       "name": "The Negotiator",              "tagline": "Empathy, imagination, big picture",   "color": "#7A9AAE"},
        ],
        "npi": [
            {"id": "self_assured_lead",    "name": "The Self-Assured Lead",      "tagline": "Confident, visible, takes charge",    "color": "#AE7A8A"},
            {"id": "modest_collaborator",  "name": "The Modest Collaborator",    "tagline": "Quiet, deferential, team-first",      "color": "#7AAE8A"},
            {"id": "balanced_self_view",   "name": "The Balanced Self-View",     "tagline": "Confident without inflation",         "color": "#8A8AAE"},
        ],
        "ambi": [
            {"id": "energized_organizer",  "name": "The Energized Organizer",    "tagline": "Drive meets discipline",              "color": "#6B6B8A"},
            {"id": "reflective_artisan",   "name": "The Reflective Artisan",     "tagline": "Inner world, careful craft",          "color": "#8A6BAE"},
            {"id": "warm_companion",       "name": "The Warm Companion",         "tagline": "Connection as a default state",       "color": "#AE8A6B"},
            {"id": "freewheeling_seeker",  "name": "The Freewheeling Seeker",    "tagline": "Open, mobile, low-attachment",        "color": "#6BAE9A"},
        ],
        "hsq": [
            {"id": "warm_humorist",        "name": "The Warm Humorist",          "tagline": "Humor that brings people in",         "color": "#AE9A6B"},
            {"id": "inner_resilient",      "name": "The Inner Resilient",        "tagline": "Self-amusement as a coping tool",     "color": "#6BAE9A"},
            {"id": "edgy_jester",          "name": "The Edgy Jester",            "tagline": "Sharp, sometimes cutting",            "color": "#8A6BAE"},
            {"id": "self_deprecator",      "name": "The Self-Deprecator",        "tagline": "Laughs at self to keep others close", "color": "#AE6B8A"},
        ],
        "kims": [
            {"id": "embodied_noticer",     "name": "The Embodied Noticer",       "tagline": "Aware of the body and senses",        "color": "#8AAE8A"},
            {"id": "articulate_observer",  "name": "The Articulate Observer",    "tagline": "Words come easily for inner states",  "color": "#7AAE9A"},
            {"id": "present_actor",        "name": "The Present Actor",          "tagline": "Fully in what you are doing",         "color": "#6BAE7A"},
            {"id": "accepting_witness",    "name": "The Accepting Witness",      "tagline": "Lets experience be what it is",       "color": "#9AAE6B"},
        ],
        "gcbs": [
            {"id": "low_skeptic",          "name": "The Trusting View",          "tagline": "Mostly takes official accounts at face value", "color": "#AE8A6B"},
            {"id": "selective_skeptic",    "name": "The Selective Skeptic",      "tagline": "Questions some, accepts others",      "color": "#9AAE6B"},
            {"id": "deep_skeptic",         "name": "The Deep Skeptic",           "tagline": "Sees hidden hands behind big events", "color": "#8A6B6B"},
        ],
        "riasec": [
            {"id": "creative_investigator","name": "The Creative Investigator",  "tagline": "Curiosity meets craft",               "color": "#8A6BAE"},
            {"id": "social_builder",       "name": "The Social Builder",         "tagline": "People and purpose together",         "color": "#6BAE8A"},
            {"id": "enterprising_mind",    "name": "The Enterprising Mind",      "tagline": "Leading, persuading, creating",       "color": "#AE8A6B"},
        ],
        "attachment": [
            {"id": "secure_connector",     "name": "The Secure Connector",       "tagline": "Trust as a foundation",              "color": "#6BAE8A"},
            {"id": "anxious_heart",        "name": "The Anxious Heart",          "tagline": "Love felt deeply, held tightly",     "color": "#AE8A6B"},
            {"id": "independent_spirit",   "name": "The Independent Spirit",     "tagline": "Space as a love language",           "color": "#6B8AAE"},
        ],
        "dass": [
            {"id": "resilient_navigator",  "name": "The Resilient Navigator",    "tagline": "Steady through the storm",            "color": "#6A8A7A"},
            {"id": "sensitive_processor",  "name": "The Sensitive Processor",    "tagline": "Depth through feeling",               "color": "#8A7A6A"},
            {"id": "calm_center",          "name": "The Calm Center",            "tagline": "Equanimity as a practice",            "color": "#7A8A9A"},
        ],
    }
    options = fallbacks.get(test_id, [{"id": "explorer", "name": "The Explorer", "tagline": "Charting unknown territory", "color": "#8A9AAE"}])
    idx = int(sum(trait_vector) * len(options)) % len(options)
    return options[idx]

def project_umap(test_id: str, trait_vector: List[float]):
    coords_path = os.path.join(MODELS_DIR, f"{test_id}_map_coords.json")
    matrix_path = os.path.join(MODELS_DIR, f"{test_id}_trait_matrix.npy")

    if not os.path.exists(coords_path) or not os.path.exists(matrix_path):
        x = float(np.mean(trait_vector[:2]) * 10 - 5)
        y = float(np.mean(trait_vector[2:]) * 10 - 5) if len(trait_vector) > 2 else 0.0
        return round(x, 3), round(y, 3)

    try:
        matrix = np.load(matrix_path)
        with open(coords_path, encoding="utf-8") as f:
            coords = np.array(json.load(f))

        n = min(len(matrix), len(coords))
        matrix = matrix[:n]
        coords = coords[:n]

        vec = np.array(trait_vector, dtype=np.float32)
        dim = matrix.shape[1]
        if vec.shape[0] >= dim:
            vec_aligned = vec[:dim]
        else:
            vec_aligned = np.pad(vec, (0, dim - vec.shape[0]))

        dists = np.linalg.norm(matrix - vec_aligned, axis=1)
        k = min(5, n)
        top_k = np.argsort(dists)[:k]
        weights = 1.0 / (dists[top_k] + 1e-8)
        weights /= weights.sum()

        x = float(np.dot(weights, coords[top_k, 0]))
        y = float(np.dot(weights, coords[top_k, 1]))
        return round(x, 3), round(y, 3)

    except Exception as e:
        print(f"[umap] neighbor interpolation failed ({e}), using fallback")
        x = float(np.mean(trait_vector[:2]) * 10 - 5)
        y = float(np.mean(trait_vector[2:]) * 10 - 5) if len(trait_vector) > 2 else 0.0
        return round(x, 3), round(y, 3)


def _profile_features(test_id: str, trait_scores: Dict[str, float]) -> Optional[np.ndarray]:
    meta = load_json(test_id, "meta")
    scaler = load_model(test_id, "trait_scaler")
    if not meta or scaler is None:
        return None
    names = meta.get("cluster_traits") or meta.get("trait_names") or list(trait_scores.keys())
    raw = np.array([[float(trait_scores[n]) for n in names]], dtype=np.float64)
    z = scaler.transform(raw)
    if meta.get("ipsatize"):
        z = z - z.mean(axis=1, keepdims=True)
    return z


def assign_archetype(test_id: str, trait_scores: Dict[str, float]) -> Optional[Dict]:
    archetypes = load_json(test_id, "archetypes")
    meta = load_json(test_id, "meta") or {}
    if archetypes:
        try:
            features = _profile_features(test_id, trait_scores)
            if features is not None:
                if meta.get("assignment") == "dominant":
                    logits = 2.0 * features[0]
                    proba = np.exp(logits - logits.max())
                    proba = proba / proba.sum()
                else:
                    gmm = load_model(test_id, "gmm")
                    proba = gmm.predict_proba(features)[0]
                for cid in np.argsort(proba)[::-1]:
                    base = archetypes.get(str(int(cid)))
                    if base:
                        result = dict(base)
                        result["membership_probability"] = round(float(proba[cid]), 4)
                        return result
        except Exception as e:
            print(f"[archetype] failed ({e}), using fallback")
    return get_fallback_archetype(test_id, list(trait_scores.values()))


def calc_similarity(test_id: str, trait_vector: List[float]) -> float:
    dataset_path = os.path.join(MODELS_DIR, f"{test_id}_trait_matrix.npy")
    if not os.path.exists(dataset_path):
        return round(np.random.uniform(2.0, 8.0), 1)

    matrix = np.load(dataset_path)
    vec = np.array(trait_vector, dtype=np.float32)

    dim = matrix.shape[1]
    if vec.shape[0] >= dim:
        vec_aligned = vec[:dim]
    else:
        vec_aligned = np.pad(vec, (0, dim - vec.shape[0]))

    dists = np.linalg.norm(matrix - vec_aligned, axis=1)

    n_dims = matrix.shape[1]
    threshold = 0.12 * np.sqrt(n_dims)

    similar_count = np.sum(dists < threshold)
    pct = round((similar_count / len(matrix)) * 100, 1)
    return max(0.1, min(99.9, pct))

def get_neighborhood_traits(test_id: str, trait_vector: List[float], trait_names: List[str]) -> Dict:
    dataset_path = os.path.join(MODELS_DIR, f"{test_id}_trait_matrix.npy")
    if not os.path.exists(dataset_path):
        return {"description": "People with similar profiles share your depth of curiosity and reflective thinking."}
    matrix      = np.load(dataset_path)
    dists       = np.linalg.norm(matrix - np.array(trait_vector), axis=1)
    top_k       = min(100, len(matrix))
    nearest_idx = np.argsort(dists)[:top_k]
    neighbors   = matrix[nearest_idx]
    top_traits  = sorted(zip(trait_names, np.mean(neighbors, axis=0)), key=lambda x: -x[1])[:3]
    return {"top_traits": [{"trait": t, "score": round(float(s), 3)} for t, s in top_traits]}


# ---------------------------------------------------------------------------
# Main inference entry point
# ---------------------------------------------------------------------------

def run_inference(test_id: str, raw_responses: Dict[str, int],
                  context_notes: Optional[List[Dict]] = None) -> Dict[str, Any]:
    scorer = SCORERS.get(test_id)
    if not scorer:
        raise ValueError(f"No scorer for test_id: {test_id}")

    trait_scores    = scorer(raw_responses)
    trait_names     = list(trait_scores.keys())
    trait_vector    = list(trait_scores.values())

    percentiles     = calc_percentiles(test_id, trait_scores)
    archetype       = assign_archetype(test_id, trait_scores)
    umap_x, umap_y  = project_umap(test_id, trait_vector)
    similarity_pct  = calc_similarity(test_id, trait_vector)
    neighborhood    = get_neighborhood_traits(test_id, trait_vector, trait_names)
    rarity_pct      = round(100 - similarity_pct, 1)
    insights        = generate_insights(test_id, trait_scores, percentiles, archetype)

    return {
        "trait_scores":   trait_scores,
        "percentiles":    percentiles,
        "archetype":      archetype,
        "umap_x":         umap_x,
        "umap_y":         umap_y,
        "similarity_pct": similarity_pct,
        "rarity_pct":     rarity_pct,
        "neighborhood":   neighborhood,
        "insights":       insights,
    }


# ---------------------------------------------------------------------------
# Insight generation
# ---------------------------------------------------------------------------

def generate_insights(test_id: str, scores: Dict, percentiles: Dict, archetype: Dict) -> Dict:
    insights  = []
    strengths = []

    if test_id == "hexaco":
        if percentiles.get("Honesty-Humility", 50) > 70:
            insights.append("Your high Honesty-Humility suggests sincerity, fairness, and an aversion to manipulation or exploitation, even when bending the rules would benefit you.")
            strengths.append("Honesty and humility")
        if percentiles.get("Openness", 50) > 70:
            insights.append("Your high openness suggests strong intellectual curiosity and a genuine appetite for new experiences and ideas.")
            strengths.append("Intellectual curiosity")
        if percentiles.get("Conscientiousness", 50) > 70:
            insights.append("Your conscientiousness indicates you are organized, dependable, and goal-oriented in how you approach your responsibilities.")
            strengths.append("Disciplined work ethic")
        if percentiles.get("Agreeableness", 50) > 70:
            insights.append("Your agreeableness reflects forgiveness, patience, and a cooperative style that others tend to notice and trust.")
            strengths.append("Empathy and warmth")
        if percentiles.get("Extraversion", 50) < 35:
            insights.append("Your lower extraversion suggests you prefer depth over breadth in social interaction, and that solitude tends to restore rather than drain you.")
        if percentiles.get("Emotionality", 50) > 70:
            insights.append("Your high emotionality means you feel things strongly, both your own emotions and the emotions of people close to you.")
        if not insights:
            insights.append("Your HEXACO profile shows a balanced distribution across all six dimensions, without strong peaks or troughs in any single area.")

    elif test_id == "darktriad":
        if all(percentiles.get(t, 50) < 40 for t in ["Machiavellianism", "Narcissism", "Psychopathy"]):
            insights.append("Your profile shows low dark triad traits. You tend to be cooperative, empathic, and transparent in how you deal with others.")
            strengths.append("Ethical consistency")
        if percentiles.get("Machiavellianism", 50) > 60:
            insights.append("You tend toward strategic thinking and long-term planning, often calculating the likely consequences of a move before committing to it.")
        if percentiles.get("Narcissism", 50) > 60:
            insights.append("You have a strong sense of self-worth and carry a natural leadership confidence that others can find either compelling or demanding.")
        if percentiles.get("Psychopathy", 50) > 60:
            insights.append("Your psychopathy score is elevated, suggesting a tendency toward risk tolerance, emotional detachment under pressure, and directness that can unsettle others.")

    elif test_id == "dass":
        if percentiles.get("Stress", 50) < 35:
            insights.append("Your stress levels are low relative to others. You manage demands and uncertainty well without becoming easily overwhelmed.")
            strengths.append("Stress tolerance")
        if percentiles.get("Anxiety", 50) > 65:
            insights.append("Your anxiety score is elevated this week. If this pattern persists, it may be worth paying attention to the physical and cognitive signals your body is sending.")
        if percentiles.get("Depression", 50) > 65:
            insights.append("Your depression score is elevated. A persistent flatness, lack of anticipation, or difficulty seeing meaning are worth taking seriously rather than pushing through.")
        if percentiles.get("Depression", 50) < 30:
            insights.append("Your mood scores reflect a generally positive emotional baseline, things land, anticipation is present, and motivation feels accessible.")
            strengths.append("Positive affect")
        if not insights:
            insights.append("Your emotional scores fall within a moderate range across all three dimensions this week.")

    elif test_id == "riasec":
        top  = sorted(percentiles.items(), key=lambda x: -x[1])[:2]
        code = "".join(t[0] for t, _ in top)
        insights.append(f"Your Holland code begins with {code}. Work environments that match this profile tend to bring out your strongest performance and sustain your motivation over time.")
        for t, p in top:
            if p > 65:
                strengths.append(t)
        bottom = sorted(percentiles.items(), key=lambda x: x[1])[:1]
        if bottom:
            t, p = bottom[0]
            if p < 30:
                insights.append(f"Your lowest area is {t}. Roles that demand this as a core function are likely to drain rather than energize you.")

    elif test_id == "attachment":
        if percentiles.get("Secure", 50) > 65:
            insights.append("Your attachment profile leans secure. You tend to feel comfortable with both intimacy and independence, without needing one to crowd out the other.")
            strengths.append("Secure base")
        if percentiles.get("Anxious", 50) > 65:
            insights.append("You show elevated attachment anxiety. You may find yourself wanting more closeness than you are currently getting, and reading small signals from a partner as evidence of withdrawal.")
        if percentiles.get("Avoidant", 50) > 65:
            insights.append("Your avoidant score is high. Emotional distance tends to feel safer or more comfortable than full vulnerability, which can create patterns of pulling back precisely when closeness becomes available.")
        if not insights:
            insights.append("Your attachment profile is moderate across all three dimensions, suggesting a flexible rather than strongly patterned relational style.")

    elif test_id == "fti":
        top = sorted(percentiles.items(), key=lambda x: -x[1])[:2]
        if top:
            primary, p = top[0]
            insights.append(f"Your strongest temperament is the {primary}. This is the cognitive and emotional rhythm that shows up most consistently in how you move through life.")
            strengths.append(primary)
            if len(top) > 1 and top[1][1] > 55:
                insights.append(f"Your secondary temperament is the {top[1][0]}. You blend both rhythms rather than running entirely on one.")
        if not insights:
            insights.append("Your temperament blend is balanced across all four styles, with no single rhythm dominating.")

    elif test_id == "hsq":
        if percentiles.get("Affiliative", 50) > 65:
            insights.append("You use humor as a way of bringing people together. Easy banter, shared laughter, and light moments with friends are part of how you build closeness.")
            strengths.append("Warm humor")
        if percentiles.get("Self-Enhancing", 50) > 65:
            insights.append("You use humor as a coping resource. When something hits hard, finding the absurd or funny angle is often what helps you metabolize it.")
            strengths.append("Humor as resilience")
        if percentiles.get("Aggressive", 50) > 65:
            insights.append("Your humor sometimes has a sharper edge, used to put others on the back foot or score points. It can land well or wound, depending on the room.")
        if percentiles.get("Self-Defeating", 50) > 65:
            insights.append("You often make yourself the punchline. It can earn affection in the short term but tends to wear on self-worth over time.")
        if not insights:
            insights.append("Your humor styles are balanced rather than dominated by any single mode.")

    elif test_id == "kims":
        if percentiles.get("Observing", 50) > 65:
            insights.append("You notice the texture of present-moment experience, sensations in the body, sounds, shifts in mood, more than most people do.")
            strengths.append("Inner noticing")
        if percentiles.get("Describing", 50) > 65:
            insights.append("You can put inner states into words easily. This makes you a useful thinking partner for people who struggle to name what they feel.")
            strengths.append("Articulating experience")
        if percentiles.get("Acting with Awareness", 50) > 65:
            insights.append("You stay present with what you are doing rather than going through it on autopilot. Distractions and rumination have less hold on you.")
            strengths.append("Present focus")
        if percentiles.get("Accepting without Judgment", 50) > 65:
            insights.append("You let experience be what it is rather than fighting or grading it. This is the mindfulness facet most associated with reduced anxiety over time.")
            strengths.append("Non-reactivity")
        if not insights:
            insights.append("Your mindfulness profile is moderate across all four skills, with room to grow in any of them.")

    elif test_id == "npi":
        top = sorted(percentiles.items(), key=lambda x: -x[1])[:2]
        if top and top[0][1] > 65:
            insights.append(f"Your most prominent self-view facet is {top[0][0]}. This is the lens through which you most readily understand your own worth and place.")
            strengths.append(top[0][0])
        if percentiles.get("Authority", 50) > 70:
            insights.append("You see yourself as a natural leader. Taking charge feels comfortable rather than effortful.")
        if percentiles.get("Entitlement", 50) > 70:
            insights.append("You hold a strong sense of what you deserve from others. This can fuel confidence in negotiations, but can also strain relationships when expectations go unmet.")
        if all(percentiles.get(t, 50) < 40 for t in ["Authority", "Superiority", "Entitlement", "Exploitativeness"]):
            insights.append("Your self-view is humble and other-focused. You don't lean on grandiosity as a default mode.")
            strengths.append("Humility")
        if not insights:
            insights.append("Your self-view profile is moderately balanced across all seven facets.")

    elif test_id == "ambi":
        top = sorted(percentiles.items(), key=lambda x: -x[1])[:3]
        if top:
            primaries = ", ".join(t for t, _ in top[:2])
            insights.append(f"Across the broad personality scan, your strongest signals show up in {primaries}. These shape the personality silhouette others most notice in you.")
            for t, p in top[:2]:
                if p > 60:
                    strengths.append(t)
        if not insights:
            insights.append("Your broad personality scan is unusually balanced, without a single dominant signal across the seven domains.")

    elif test_id == "gcbs":
        avg = sum(percentiles.values()) / max(len(percentiles), 1) if percentiles else 50
        if avg > 65:
            insights.append("You tend to hold a strongly skeptical view of official narratives and powerful institutions. You see hidden hands more readily than most.")
        elif avg < 35:
            insights.append("You tend to take official accounts at close to face value. Your default is trust unless there is clear reason otherwise.")
            strengths.append("Default trust")
        else:
            insights.append("Your skepticism is selective. Some claims you take at face value, others you examine more carefully.")
            strengths.append("Selective skepticism")

    summary = f"{archetype.get('name', 'Your profile')}: {archetype.get('tagline', '')}".rstrip(": ")

    return {
        "summary":   summary,
        "insights":  insights[:5],
        "strengths": strengths[:4],
    }