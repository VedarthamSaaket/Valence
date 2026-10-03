"""
Grand audit: every model, every metric, every persona, every archetype.

Coverage: all 17 tests.
- 13 clustered tests (Tier A): full UL metrics, archetype quality, sample persona test
- 4 LLM-only tests   (Tier B): STATIC_NORMS quality, fallback archetype audit, persona check

Outputs:
- console table
- backend/models/_grand_audit_report.json with full per-test breakdown
"""
import json
import os
import pickle
import sys
from typing import Dict, List, Optional, Tuple

import numpy as np
from sklearn.metrics import silhouette_score, calinski_harabasz_score, davies_bouldin_score

ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(ROOT, "backend"))
from ml.inference import (  # noqa: E402
    SCORERS, calc_percentiles, assign_archetype,
    STATIC_NORMS, get_fallback_archetype,
)

MODELS_DIR = os.path.join(ROOT, "backend", "models")

TIER_A = ["hexaco", "sixteenpf", "darktriad", "fti", "npi", "ambi", "pid5_skip",
          "hsq", "kims", "gcbs", "aesthetic", "riasec", "attachment", "dass"]
TIER_A_REAL = [t for t in TIER_A if t != "pid5_skip"]  # pid5 is Tier B
TIER_B = ["pvq", "bpnss", "who5", "pid5"]

SILHOUETTE_FLOOR = 0.25
SILHOUETTE_STRONG = 0.40

RESEARCH_K = {
    "hexaco":     (3, 5, "Gerlach 2018 Nat Hum Behav: 4 types"),
    "sixteenpf":  (2, 6, "Cattell types; LPA studies"),
    "darktriad":  (2, 4, "Jones & Paulhus 2014: 3 dim ~ 2-4 profiles"),
    "fti":        (4, 4, "Fisher 2013: 4 temperaments (theoretical)"),
    "npi":        (3, 5, "Wallace & Baumeister 2002: 3-4 facets"),
    "ambi":       (4, 7, "Yarkoni 2010 Big-Five-like"),
    "hsq":        (3, 5, "Galloway 2010: 3-4 humor profiles"),
    "kims":       (3, 5, "Pearson 2015: 4 mindfulness profiles"),
    "gcbs":       (3, 6, "Brotherton 2013: 5-factor structure"),
    "aesthetic":  (3, 5, "APS factor structure"),
    "riasec":     (3, 6, "Holland's 6 codes"),
    "attachment": (3, 4, "Bartholomew 1991: 4-style model"),
    "dass":       (3, 5, "Lovibond 1995: severity bands"),
}


# ---------------------------------------------------------------------------
# Persona suite for sample-output verification
# ---------------------------------------------------------------------------
def import_personas():
    """Lazy import to avoid circulars."""
    sys.path.insert(0, ROOT)
    import importlib.util
    spec = importlib.util.spec_from_file_location("verify_archetypes", os.path.join(ROOT, "verify_archetypes.py"))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return {
        "hexaco":     mod.hexaco_personas(),
        "sixteenpf":  mod.sixteenpf_personas(),
        "darktriad":  mod.darktriad_personas(),
        "fti":        mod.fti_personas(),
        "npi":        mod.npi_personas(),
        "ambi":       mod.ambi_personas(),
        "hsq":        mod.hsq_personas(),
        "kims":       mod.kims_personas(),
        "gcbs":       mod.gcbs_personas(),
        "aesthetic":  mod.aesthetic_personas(),
        "riasec":     mod.riasec_personas(),
        "attachment": mod.attachment_personas(),
        "dass":       mod.dass_personas(),
    }


# Tier B personas, synthetic, score-targeted
def tier_b_personas():
    """For LLM-only tests, build personas at score extremes."""
    return {
        "pvq":   {"low values":   {f"Q{i}": 6 for i in range(1, 22)},
                  "high values":  {f"Q{i}": 1 for i in range(1, 22)}},
        "bpnss": {"needs unmet":  {f"Q{i}": 1 for i in range(1, 22)},
                  "needs full":   {f"Q{i}": 7 for i in range(1, 22)}},
        "who5":  {"low wellbeing":  {f"Q{i}": 0 for i in range(1, 6)},
                  "high wellbeing": {f"Q{i}": 5 for i in range(1, 6)}},
        "pid5":  {"low maladaptive":  {f"Q{i}": 0 for i in range(1, 26)},
                  "high maladaptive": {f"Q{i}": 3 for i in range(1, 26)}},
    }


# ---------------------------------------------------------------------------
# UL metrics per Tier A test
# ---------------------------------------------------------------------------
def audit_tier_a(test_id: str) -> Dict:
    gmm_path  = os.path.join(MODELS_DIR, f"{test_id}_gmm.pkl")
    emb_path  = os.path.join(MODELS_DIR, f"{test_id}_umap10d_matrix.npy")
    meta_path = os.path.join(MODELS_DIR, f"{test_id}_meta.json")
    arc_path  = os.path.join(MODELS_DIR, f"{test_id}_archetypes.json")
    dist_path = os.path.join(MODELS_DIR, f"{test_id}_distributions.json")

    if not all(os.path.exists(p) for p in (emb_path, meta_path)):
        return {"test_id": test_id, "tier": "A", "error": "missing artifacts"}

    with open(meta_path) as fh:
        meta = json.load(fh)

    # Use the model that inference actually uses: KMeans if primary_model says so,
    # otherwise the (Bayesian) GMM.
    km_path = os.path.join(MODELS_DIR, f"{test_id}_kmeans.pkl")
    use_kmeans = meta.get("primary_model") == "kmeans" and os.path.exists(km_path)
    model_path = km_path if use_kmeans else gmm_path
    if not os.path.exists(model_path):
        return {"test_id": test_id, "tier": "A", "error": "missing model"}
    with open(model_path, "rb") as fh:
        bgm = pickle.load(fh)
    emb = np.load(emb_path).astype(np.float32)

    rng = np.random.default_rng(42)
    n_sample = min(15000, len(emb))
    idx = rng.choice(len(emb), n_sample, replace=False) if len(emb) > n_sample else np.arange(len(emb))
    X = emb[idx]
    labels = bgm.predict(X)

    if use_kmeans:
        _, cnts = np.unique(labels, return_counts=True)
        weights = cnts / cnts.sum()
    else:
        weights = np.array(bgm.weights_)
    eff_k = int(np.sum(weights >= 0.02))
    sil = float(silhouette_score(X, labels)) if len(set(labels)) > 1 else 0.0
    ch  = float(calinski_harabasz_score(X, labels)) if len(set(labels)) > 1 else 0.0
    db  = float(davies_bouldin_score(X, labels)) if len(set(labels)) > 1 else float("inf")
    ll  = float(bgm.score(X))

    # Cluster balance
    _, counts = np.unique(labels, return_counts=True)
    pct = counts / counts.sum()
    nz = pct[pct > 0]
    entropy = float(-np.sum(nz * np.log(nz)) / np.log(max(len(nz), 2))) if len(nz) > 1 else 0.0
    max_pct = float(counts.max() / counts.sum() * 100)

    # Archetype quality: distinct names, reasonable centroid spread
    archetypes = {}
    if os.path.exists(arc_path):
        with open(arc_path) as fh:
            archetypes = json.load(fh)
    arc_names = [a.get("name", "") for a in archetypes.values()]
    arc_distinct = len(set(arc_names))

    # Verdict
    research_lo, research_hi, _ = RESEARCH_K.get(test_id, (2, 8, ""))
    in_research_range = research_lo <= eff_k <= research_hi
    if sil >= SILHOUETTE_STRONG:
        quality = "STRONG"
    elif sil >= SILHOUETTE_FLOOR:
        quality = "PRODUCTION"
    elif sil >= 0.10:
        quality = "WEAK"
    else:
        quality = "POOR"

    return {
        "test_id":        test_id,
        "tier":           "A",
        "schema_version": meta.get("schema_version"),
        "n_samples":      int(len(emb)),
        "n_traits":       int(meta.get("n_traits", 0)),
        "k_max":          int(getattr(bgm, "n_components", getattr(bgm, "n_clusters", len(weights)))),
        "effective_k":    eff_k,
        "silhouette":     round(sil, 4),
        "ch":             round(ch, 1),
        "db":             round(db, 4),
        "log_likelihood": round(ll, 3),
        "max_cluster_pct": round(max_pct, 1),
        "balance_entropy": round(entropy, 3),
        "in_research_k":  in_research_range,
        "research_k":     f"{research_lo}-{research_hi}",
        "n_archetypes":   len(archetypes),
        "n_distinct_archetype_names": arc_distinct,
        "quality":        quality,
    }


# ---------------------------------------------------------------------------
# Audit for Tier B (LLM-only)
# ---------------------------------------------------------------------------
def audit_tier_b(test_id: str) -> Dict:
    has_norms = test_id in STATIC_NORMS
    norms = STATIC_NORMS.get(test_id, {})
    fallback_options = get_fallback_archetype.__wrapped__ if False else None  # noqa
    # Get fallback archetype options
    try:
        # quick eval
        sample_vec = [0.5] * 5
        arc = get_fallback_archetype(test_id, sample_vec)
        n_fallback = 0
        # Re-import fallback dict
        from ml.inference import get_fallback_archetype as gfa
        import inspect
        src = inspect.getsource(gfa)
        # Count options in test_id's block
        import re
        match = re.search(rf'"{test_id}":\s*\[(.*?)\]', src, re.DOTALL)
        n_fallback = len(re.findall(r'\{"id"', match.group(1))) if match else 0
    except Exception:
        n_fallback = 0

    return {
        "test_id":          test_id,
        "tier":             "B",
        "has_static_norms": has_norms,
        "n_norm_dims":      len(norms),
        "norm_traits":      list(norms.keys()),
        "n_fallback_archetypes": n_fallback,
        "quality":          "PRODUCTION (LLM-only)" if has_norms and n_fallback >= 3 else "NEEDS_FIX",
    }


# ---------------------------------------------------------------------------
# Persona verification
# ---------------------------------------------------------------------------
def persona_check(test_id: str, personas: Dict) -> Dict:
    rows = []
    for label, resp in personas.items():
        try:
            scores = SCORERS[test_id](resp)
            pcts   = calc_percentiles(test_id, scores)
            trait_vec = list(scores.values())
            arc = assign_archetype(test_id, trait_vec, trait_scores=scores, percentiles=pcts) or {}
            rows.append({
                "persona":   label,
                "cluster":   arc.get("id", "?"),
                "archetype": arc.get("name", "?"),
                "top_pct":   sorted(pcts.items(), key=lambda kv: -kv[1])[:2],
            })
        except Exception as e:
            rows.append({"persona": label, "error": str(e)})
    distinct_clusters = len(set(r.get("cluster") for r in rows if "cluster" in r))
    return {
        "n_personas":        len(rows),
        "distinct_clusters": distinct_clusters,
        "discriminative":    distinct_clusters >= len(rows) - 1,
        "personas":          rows,
    }


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main():
    print("=" * 100)
    print("GRAND AUDIT, 17 models")
    print("=" * 100)

    report = {"tier_a": [], "tier_b": [], "ranked": []}

    # Personas
    try:
        personas_a = import_personas()
    except Exception as e:
        print(f"persona loader failed: {e}")
        personas_a = {}
    personas_b = tier_b_personas()

    # Tier A
    for tid in TIER_A_REAL:
        r = audit_tier_a(tid)
        if "error" not in r:
            pc = persona_check(tid, personas_a.get(tid, {}))
            r["persona_check"] = pc
        report["tier_a"].append(r)

    # Tier B
    for tid in TIER_B:
        r = audit_tier_b(tid)
        pc = persona_check(tid, personas_b.get(tid, {}))
        r["persona_check"] = pc
        report["tier_b"].append(r)

    # Print Tier A
    print("\nTier A (clustered, BGM/UMAP)")
    print(f"{'rank':<5} {'test':<11} {'qual':<11} {'sil':>7} {'CH':>9} {'DB':>6} {'k':>3} {'res-k':<6} {'in-k':<5} {'disc':<5}")
    print("-" * 85)
    tier_a_sorted = sorted([r for r in report["tier_a"] if "silhouette" in r],
                           key=lambda x: -x["silhouette"])
    for i, r in enumerate(tier_a_sorted, 1):
        pc = r.get("persona_check", {})
        disc = "Y" if pc.get("discriminative") else "N"
        print(f"{i:<5} {r['test_id']:<11} {r['quality']:<11} {r['silhouette']:>7.3f} "
              f"{r['ch']:>9.0f} {r['db']:>6.2f} {r['effective_k']:>3} "
              f"{r['research_k']:<6} {'Y' if r['in_research_k'] else 'N':<5} {disc:<5}")

    # Print Tier B
    print("\nTier B (LLM-only, STATIC_NORMS + fallback archetypes)")
    print(f"{'test':<11} {'norms':<7} {'dims':>5} {'fallback':<10} {'disc':<5} {'quality':<20}")
    print("-" * 75)
    for r in report["tier_b"]:
        pc = r.get("persona_check", {})
        disc = "Y" if pc.get("discriminative") else "N"
        print(f"{r['test_id']:<11} {'Y' if r['has_static_norms'] else 'N':<7} "
              f"{r['n_norm_dims']:>5} {r['n_fallback_archetypes']:>10} {disc:<5} {r['quality']}")

    # Action items
    print("\nAction items")
    print("-" * 60)
    weak_count = 0
    for r in tier_a_sorted:
        if r["quality"] in ("WEAK", "POOR"):
            print(f"  {r['test_id']:<11} sil={r['silhouette']} k={r['effective_k']} -> grid_search")
            weak_count += 1
        elif not r["in_research_k"]:
            print(f"  {r['test_id']:<11} sil={r['silhouette']} k={r['effective_k']} outside research k={r['research_k']} -> review")
    for r in report["tier_b"]:
        if r["quality"] == "NEEDS_FIX":
            print(f"  {r['test_id']:<11} fix STATIC_NORMS or fallback archetypes")
    if weak_count == 0:
        print("  none.")

    out_path = os.path.join(MODELS_DIR, "_grand_audit_report.json")
    with open(out_path, "w") as fh:
        json.dump(report, fh, indent=2, default=str)
    print(f"\nFull report -> {out_path}")


if __name__ == "__main__":
    main()
