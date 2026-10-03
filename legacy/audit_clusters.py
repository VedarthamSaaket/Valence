"""
Comprehensive unsupervised-learning audit of all trained BGM clustering models.

Metrics computed per test (all on the UMAP-10D embedding the model was trained on):
  - silhouette         higher better (range -1 to 1)
  - calinski_harabasz  higher better (variance ratio)
  - davies_bouldin     lower  better (avg similarity to nearest cluster)
  - aic, bic           lower  better (model selection penalties)
  - log_likelihood     higher better (per sample)
  - effective_k        BGM components with weight >= 2%
  - max_cluster_pct    largest cluster as % of n (high = unbalanced)
  - balance_entropy    Shannon entropy of cluster sizes, normalized 0-1

Composite quality score: rank-normalized average of sil + CH + (-DB).
"""
import json
import os
import pickle
import sys
from math import log
from typing import Dict, List

import numpy as np
from sklearn.metrics import silhouette_score, calinski_harabasz_score, davies_bouldin_score

MODELS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "backend", "models")
TESTS = ["hexaco", "hsq", "kims", "fti", "npi", "ambi", "gcbs"]


def cluster_balance(labels: np.ndarray) -> Dict:
    _, counts = np.unique(labels, return_counts=True)
    pct = counts / counts.sum()
    nz = pct[pct > 0]
    entropy = float(-np.sum(nz * np.log(nz)) / log(len(nz))) if len(nz) > 1 else 0.0
    return {
        "max_cluster_pct":   round(float(counts.max() / counts.sum() * 100), 2),
        "balance_entropy":   round(entropy, 4),
        "n_nonempty":        int(len(nz)),
        "smallest_size_pct": round(float(counts.min() / counts.sum() * 100), 2),
    }


def audit_one(test_id: str) -> Dict:
    gmm_path  = os.path.join(MODELS_DIR, f"{test_id}_gmm.pkl")
    emb_path  = os.path.join(MODELS_DIR, f"{test_id}_umap10d_matrix.npy")
    meta_path = os.path.join(MODELS_DIR, f"{test_id}_meta.json")

    if not (os.path.exists(gmm_path) and os.path.exists(emb_path) and os.path.exists(meta_path)):
        return {"test_id": test_id, "error": "artifacts missing"}

    with open(gmm_path, "rb") as fh:
        bgm = pickle.load(fh)
    emb = np.load(emb_path).astype(np.float32)
    with open(meta_path) as fh:
        meta = json.load(fh)

    sample_size = min(15000, len(emb))
    rng = np.random.default_rng(42)
    idx = rng.choice(len(emb), sample_size, replace=False) if len(emb) > sample_size else np.arange(len(emb))
    X = emb[idx]

    labels = bgm.predict(X)
    nonzero_clusters = sorted(set(labels))

    weights = np.array(bgm.weights_)
    eff_k = int(np.sum(weights >= 0.02))

    sil = float(silhouette_score(X, labels)) if len(nonzero_clusters) > 1 else 0.0
    ch  = float(calinski_harabasz_score(X, labels)) if len(nonzero_clusters) > 1 else 0.0
    db  = float(davies_bouldin_score(X, labels)) if len(nonzero_clusters) > 1 else float("inf")
    ll  = float(bgm.score(X))
    bic = float(bgm.bic(X)) if hasattr(bgm, "bic") else None
    aic = float(bgm.aic(X)) if hasattr(bgm, "aic") else None

    balance = cluster_balance(labels)

    return {
        "test_id":      test_id,
        "n_samples":    int(len(emb)),
        "n_traits":     int(meta.get("n_traits", 0)),
        "k_max":        int(bgm.n_components),
        "effective_k":  eff_k,
        "silhouette":   round(sil, 4),
        "calinski_harabasz": round(ch, 2),
        "davies_bouldin":    round(db, 4),
        "log_likelihood":    round(ll, 4),
        "aic":          round(aic, 2) if aic is not None else None,
        "bic":          round(bic, 2) if bic is not None else None,
        **balance,
    }


def rank_models(results: List[Dict]) -> List[Dict]:
    """Composite quality score = mean rank of sil + CH + (-DB).
    Lower composite_rank = better."""
    valid = [r for r in results if "silhouette" in r]
    sil_rank = {r["test_id"]: i for i, r in enumerate(sorted(valid, key=lambda x: -x["silhouette"]))}
    ch_rank  = {r["test_id"]: i for i, r in enumerate(sorted(valid, key=lambda x: -x["calinski_harabasz"]))}
    db_rank  = {r["test_id"]: i for i, r in enumerate(sorted(valid, key=lambda x:  x["davies_bouldin"]))}
    for r in valid:
        r["composite_rank"] = round((sil_rank[r["test_id"]] + ch_rank[r["test_id"]] + db_rank[r["test_id"]]) / 3, 2)
    return sorted(valid, key=lambda x: x["composite_rank"])


if __name__ == "__main__":
    results = [audit_one(t) for t in TESTS]
    ranked  = rank_models(results)

    print(f"{'rank':<5} {'test':<10} {'n':<6} {'k':<4} {'sil':>7} {'CH':>10} {'DB':>7} {'ll':>9} {'BIC':>11} {'max%':>6} {'entropy':>8}")
    print("-" * 100)
    for i, r in enumerate(ranked, 1):
        bic_str = f"{r['bic']:>11.0f}" if r.get('bic') is not None else f"{'n/a':>11}"
        print(f"{i:<5} {r['test_id']:<10} {r['n_samples']:<6} {r['effective_k']:<4} "
              f"{r['silhouette']:>7.3f} {r['calinski_harabasz']:>10.1f} "
              f"{r['davies_bouldin']:>7.3f} {r['log_likelihood']:>9.2f} "
              f"{bic_str} {r['max_cluster_pct']:>5.1f}% {r['balance_entropy']:>8.3f}")

    print()
    print("Composite quality flag (sil + CH + 1/DB):")
    for r in ranked:
        flag = "OK"
        if r["silhouette"] < 0.25:
            flag = "WEAK_SEPARATION"
        if r["davies_bouldin"] > 1.5:
            flag = "WEAK_SEPARATION"
        if r["max_cluster_pct"] > 60:
            flag = "DOMINANT_CLUSTER"
        if r["effective_k"] == r["k_max"]:
            flag = "NO_PRUNING" if flag == "OK" else flag + "+NO_PRUNING"
        print(f"  {r['test_id']:<10} {flag}")

    with open(os.path.join(MODELS_DIR, "_audit_report.json"), "w") as fh:
        json.dump({"ranked": ranked}, fh, indent=2)
    print(f"\nFull audit saved to backend/models/_audit_report.json")
