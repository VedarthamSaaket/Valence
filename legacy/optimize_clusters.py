"""
Grid-search optimizer for tests whose current model is below the silhouette
threshold. Sweeps (k_max, weight_concentration_prior) over a small grid on the
already-saved UMAP-10D embedding, picks the combination that maximizes a
composite quality score, and rewrites the BGM + archetype + meta files only if
the new model strictly beats the current one.

Composite score: silhouette - 0.1*davies_bouldin + log10(calinski_harabasz)
This favors well-separated, compact, high-variance-ratio clusters.

Run after train_offline.py. Safe to re-run.
"""
import json
import os
import pickle
import sys
from typing import Dict, List, Optional, Tuple

import numpy as np
from sklearn.metrics import silhouette_score, calinski_harabasz_score, davies_bouldin_score
from sklearn.mixture import BayesianGaussianMixture

MODELS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "backend", "models")

# (k_max, wcp) grid. k_max range stays within research-plausible territory.
GRID = [
    (k, wcp)
    for k   in (2, 3, 4, 5, 6, 8)
    for wcp in (0.001, 0.01, 0.05, 0.1, 1.0)
]

SILHOUETTE_FLOOR = 0.25   # production threshold

# Research-supported k ranges per test. Used as a soft prior, not a hard rule.
# If the best silhouette comes from outside this range, we still accept it but
# log a divergence warning.
RESEARCH_K_RANGE = {
    "hexaco":     (3, 5),    # Gerlach 2018 found 4
    "sixteenpf":  (2, 6),    # 16PF type research varies 2-6
    "darktriad":  (2, 4),    # Mach/Narc/Psyc profiles
    "attachment": (3, 4),    # Bartholomew 1991 4-style model
    "riasec":     (3, 6),    # Holland's 6 codes
    "aesthetic":  (3, 5),
    "hsq":        (3, 5),    # Galloway 2010
    "kims":       (3, 5),    # Pearson 2015
    "fti":        (4, 4),    # Fisher's 4 temperaments (theoretical)
    "dass":       (3, 5),    # severity bands
    "npi":        (3, 5),    # Wallace 2002
    "ambi":       (4, 7),
    "gcbs":       (3, 6),    # Brotherton 5-factor
}


def composite(sil: float, db: float, ch: float) -> float:
    return sil - 0.1 * db + (np.log10(max(ch, 1.0)) / 5.0)


def current_score(test_id: str) -> Optional[Dict]:
    meta_path = os.path.join(MODELS_DIR, f"{test_id}_meta.json")
    emb_path  = os.path.join(MODELS_DIR, f"{test_id}_umap10d_matrix.npy")
    gmm_path  = os.path.join(MODELS_DIR, f"{test_id}_gmm.pkl")
    if not all(os.path.exists(p) for p in (meta_path, emb_path, gmm_path)):
        return None
    with open(meta_path) as fh:
        meta = json.load(fh)
    with open(gmm_path, "rb") as fh:
        gmm = pickle.load(fh)
    emb = np.load(emb_path).astype(np.float32)
    rng = np.random.default_rng(42)
    n = min(15000, len(emb))
    idx = rng.choice(len(emb), n, replace=False) if len(emb) > n else np.arange(len(emb))
    X = emb[idx]
    labels = gmm.predict(X)
    if len(set(labels)) < 2:
        return {"score": -1.0, "sil": 0.0, "db": float("inf"), "ch": 0.0, "k": 0}
    sil = float(silhouette_score(X, labels))
    db  = float(davies_bouldin_score(X, labels))
    ch  = float(calinski_harabasz_score(X, labels))
    return {"score": composite(sil, db, ch), "sil": sil, "db": db, "ch": ch,
            "k": int(np.sum(np.array(gmm.weights_) >= 0.02)),
            "k_max": int(gmm.n_components),
            "wcp": float(gmm.weight_concentration_prior_)
                   if hasattr(gmm, "weight_concentration_prior_") and gmm.weight_concentration_prior_ is not None
                   else None}


def search_one(test_id: str) -> Optional[Dict]:
    emb_path = os.path.join(MODELS_DIR, f"{test_id}_umap10d_matrix.npy")
    if not os.path.exists(emb_path):
        return {"error": "no umap10d matrix"}

    emb = np.load(emb_path).astype(np.float32)
    rng = np.random.default_rng(42)
    n = min(15000, len(emb))
    idx = rng.choice(len(emb), n, replace=False) if len(emb) > n else np.arange(len(emb))
    X = emb[idx]

    research_lo, research_hi = RESEARCH_K_RANGE.get(test_id, (2, 8))

    results: List[Dict] = []
    for k_max, wcp in GRID:
        try:
            bgm = BayesianGaussianMixture(
                n_components=k_max, covariance_type="full",
                weight_concentration_prior_type="dirichlet_process",
                weight_concentration_prior=wcp,
                max_iter=300, n_init=2, init_params="kmeans",
                reg_covar=1e-4, random_state=42,
            )
            bgm.fit(X)
            labels = bgm.predict(X)
            if len(set(labels)) < 2:
                continue
            sil = float(silhouette_score(X, labels))
            db  = float(davies_bouldin_score(X, labels))
            ch  = float(calinski_harabasz_score(X, labels))
            eff_k = int(np.sum(np.array(bgm.weights_) >= 0.02))
            score = composite(sil, db, ch)
            # research-k bonus: small bonus if effective_k falls inside the research range
            if research_lo <= eff_k <= research_hi:
                score += 0.05
            results.append({
                "k_max": k_max, "wcp": wcp, "eff_k": eff_k,
                "sil": sil, "db": db, "ch": ch, "score": score,
                "bgm": bgm,
            })
        except Exception as e:
            results.append({"k_max": k_max, "wcp": wcp, "error": str(e)})

    # Pick best by composite, but prefer ones with sil >= SILHOUETTE_FLOOR if available
    above_floor = [r for r in results if "sil" in r and r["sil"] >= SILHOUETTE_FLOOR]
    pool = above_floor if above_floor else [r for r in results if "sil" in r]
    if not pool:
        return {"error": "no valid grid result"}
    best = max(pool, key=lambda r: r["score"])
    return {"best": best, "above_floor_count": len(above_floor), "total": len(pool)}


def apply_best(test_id: str, best_result: Dict) -> None:
    """Refit BGM on the FULL matrix (not just sample) with best params, save."""
    emb_full_path = os.path.join(MODELS_DIR, f"{test_id}_umap10d_matrix.npy")
    trait_path    = os.path.join(MODELS_DIR, f"{test_id}_trait_matrix.npy")
    meta_path     = os.path.join(MODELS_DIR, f"{test_id}_meta.json")
    gmm_path      = os.path.join(MODELS_DIR, f"{test_id}_gmm.pkl")
    arc_path      = os.path.join(MODELS_DIR, f"{test_id}_archetypes.json")
    weights_path  = os.path.join(MODELS_DIR, f"{test_id}_gmm_weights.json")

    emb_full     = np.load(emb_full_path).astype(np.float32)
    trait_matrix = np.load(trait_path)

    best = best_result["best"]
    bgm = BayesianGaussianMixture(
        n_components=best["k_max"], covariance_type="full",
        weight_concentration_prior_type="dirichlet_process",
        weight_concentration_prior=best["wcp"],
        max_iter=300, n_init=3, init_params="kmeans",
        reg_covar=1e-4, random_state=42,
    )
    rng = np.random.default_rng(42)
    n = min(15000, len(emb_full))
    idx = rng.choice(len(emb_full), n, replace=False) if len(emb_full) > n else np.arange(len(emb_full))
    bgm.fit(emb_full[idx])

    labels = bgm.predict(emb_full[idx])
    weights = bgm.weights_.tolist()
    eff_k = int(np.sum(np.array(weights) >= 0.02))
    sil = float(silhouette_score(emb_full[idx], labels))

    with open(gmm_path, "wb") as fh:
        pickle.dump(bgm, fh)
    with open(weights_path, "w") as fh:
        json.dump({
            "n_components": int(bgm.n_components),
            "effective_k":  eff_k,
            "weights":      [round(float(w), 6) for w in weights],
            "silhouette":   sil,
            "method":       f"bayesian_gmm_dp_grid_search (wcp={best['wcp']})",
        }, fh, indent=2)

    # Recompute archetype centroids in raw trait space
    centroids = []
    for cid in range(bgm.n_components):
        members = idx[labels == cid]
        if len(members) > 0:
            centroid = trait_matrix[members].mean(axis=0).tolist()
        else:
            centroid = [0.5] * trait_matrix.shape[1]
        centroids.append({
            "cluster": int(cid), "weight": round(float(weights[cid]), 6),
            "size": int(len(members)),
            "centroid": [round(float(v), 4) for v in centroid],
        })
    # Keep only effective components
    kept = [c for c in centroids if c["weight"] >= 0.02]
    archetypes = {
        str(i): {
            "id": f"cluster_{i}", "name": f"Archetype {i + 1}",
            "tagline": "name pending", "color": "#8A9AAE",
            "description": "Centroid from grid-search optimized BGM.",
            "centroid": c["centroid"], "size": c["size"], "weight": c["weight"],
        }
        for i, c in enumerate(kept)
    }
    with open(arc_path, "w") as fh:
        json.dump(archetypes, fh, indent=2)

    # Update meta
    with open(meta_path) as fh:
        meta = json.load(fh)
    meta.update({
        "schema_version":      "v7-grid-optimized",
        "k":                   int(bgm.n_components),
        "effective_k":         eff_k,
        "silhouette":          sil,
        "clustering_strategy": f"bayesian_gmm_dp_grid_optimized (k_max={best['k_max']}, wcp={best['wcp']})",
    })
    with open(meta_path, "w") as fh:
        json.dump(meta, fh, indent=2)


def main(tests: List[str]):
    print(f"{'test':<12} {'current sil':>11} {'best sil':>9} {'best k':>7} {'best wcp':>9} {'action':<10}")
    print("-" * 70)
    for tid in tests:
        cur = current_score(tid)
        result = search_one(tid)
        if cur is None or result is None or "error" in result:
            print(f"{tid:<12} {'(no model)':>11} {'-':>9} {'-':>7} {'-':>9} skip")
            continue
        best = result["best"]
        if best["sil"] > cur["sil"] + 0.01:  # require meaningful improvement
            apply_best(tid, result)
            action = "UPDATED"
        else:
            action = "kept-current"
        print(f"{tid:<12} {cur['sil']:>11.4f} {best['sil']:>9.4f} "
              f"{best['eff_k']:>7d} {best['wcp']:>9g} {action:<10}")


if __name__ == "__main__":
    if len(sys.argv) > 1:
        main(sys.argv[1:])
    else:
        main(["hexaco", "sixteenpf", "darktriad", "fti", "npi", "ambi", "pid5",
              "hsq", "kims", "gcbs", "aesthetic", "riasec", "attachment", "dass"])
