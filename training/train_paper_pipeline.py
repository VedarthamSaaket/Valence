import argparse
import json
import os
import pickle
import sys
from datetime import datetime

import numpy as np
import pandas as pd
import umap
from sklearn.cluster import AgglomerativeClustering, KMeans
from sklearn.metrics import silhouette_score
from sklearn.mixture import BayesianGaussianMixture, GaussianMixture

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT_DIR, "backend", "ml"))
from train_offline import CONFIGS, load_dataset

OUT_DIR = os.path.join(ROOT_DIR, "backend", "models", "_paper_pipeline_rerun")
SCHEMA_VERSION = "v11-paper-pipeline"
SAMPLE_SIZE = 15000
SEED = 42
K_MAX_SWEEP = range(2, 9)
WEIGHT_THRESHOLD = 0.02
ROBUSTNESS_K = range(2, 6)
WARD_LIMIT = 5000


def trait_table(test_id):
    cfg = CONFIGS[test_id]
    df = load_dataset(cfg["folder"]).apply(pd.to_numeric, errors="coerce").replace(0, np.nan)
    df = df.dropna(thresh=int(df.shape[1] * 0.8))
    df = df.fillna(df.median(numeric_only=True))
    return cfg["scorer"](df).dropna()


def sample_rows(matrix, limit):
    if len(matrix) <= limit:
        return matrix
    return matrix[np.random.default_rng(SEED).choice(len(matrix), limit, replace=False)]


def fit_bgm(embedding, k_max):
    model = BayesianGaussianMixture(
        n_components=k_max,
        covariance_type="full",
        weight_concentration_prior_type="dirichlet_process",
        weight_concentration_prior=0.01,
        max_iter=300,
        n_init=3,
        init_params="kmeans",
        reg_covar=1e-4,
        random_state=SEED,
    )
    return model.fit(embedding)


def sweep(embedding):
    rows, best, best_model = [], None, None
    for k_max in K_MAX_SWEEP:
        model = fit_bgm(embedding, k_max)
        labels = model.predict(embedding)
        effective = int(np.sum(model.weights_ >= WEIGHT_THRESHOLD))
        silhouette = float(silhouette_score(embedding, labels)) if len(set(labels)) > 1 else -1.0
        row = {"k_max": k_max, "effective_k": effective, "silhouette": round(silhouette, 4)}
        rows.append(row)
        print(test_label, row, flush=True)
        if best is None or silhouette > best["silhouette"]:
            best, best_model = {**row, "silhouette": silhouette}, model
    return rows, best, best_model


def robustness(sample):
    ward_rows = sample_rows(sample, WARD_LIMIT)
    fitters = {
        "kmeans": lambda k: (sample, KMeans(n_clusters=k, n_init=10, random_state=SEED).fit_predict(sample)),
        "ward": lambda k: (ward_rows, AgglomerativeClustering(n_clusters=k, linkage="ward").fit_predict(ward_rows)),
        "gmm_full": lambda k: (sample, GaussianMixture(k, covariance_type="full", n_init=3, random_state=SEED).fit_predict(sample)),
        "gmm_diag": lambda k: (sample, GaussianMixture(k, covariance_type="diag", n_init=3, random_state=SEED).fit_predict(sample)),
    }
    table = {}
    for name, fit in fitters.items():
        table[name] = {}
        for k in ROBUSTNESS_K:
            rows, labels = fit(k)
            table[name][str(k)] = round(float(silhouette_score(rows, labels)), 4)
    return table


def train(test_id):
    traits = trait_table(test_id)
    matrix = traits.values.astype(np.float32)
    sample = sample_rows(matrix, SAMPLE_SIZE)

    reducer = umap.UMAP(n_components=10, n_neighbors=30, min_dist=0.0, metric="euclidean", random_state=SEED).fit(sample)
    embedding = reducer.transform(sample)
    rows, best, model = sweep(embedding)
    map_reducer = umap.UMAP(n_components=2, n_neighbors=15, min_dist=0.1, random_state=SEED).fit(sample)

    for name, artifact in (("umap10d", reducer), ("bgm", model), ("umap", map_reducer)):
        with open(os.path.join(OUT_DIR, f"{test_id}_{name}.pkl"), "wb") as fh:
            pickle.dump(artifact, fh)

    meta = {
        "schema_version": SCHEMA_VERSION,
        "test_id": test_id,
        "trained_at": datetime.utcnow().isoformat(timespec="seconds") + "Z",
        "n_samples": int(len(matrix)),
        "n_traits": int(matrix.shape[1]),
        "trait_names": list(traits.columns),
        "k": best["k_max"],
        "effective_k": best["effective_k"],
        "silhouette": best["silhouette"],
        "sweep": rows,
        "weight_threshold": WEIGHT_THRESHOLD,
        "clustering_strategy": "bayesian_gmm_dp_on_umap10d",
        "umap_dims_cluster": 10,
        "umap_dims_map": 2,
        "sample_size": int(len(sample)),
        "robustness_silhouette": robustness(sample),
    }
    with open(os.path.join(OUT_DIR, f"{test_id}_meta.json"), "w", encoding="utf-8") as fh:
        json.dump(meta, fh, indent=2)
    print(test_id, "best", best, flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("tests", nargs="*", default=list(CONFIGS))
    args = parser.parse_args()
    os.makedirs(OUT_DIR, exist_ok=True)
    for test_label in args.tests:
        train(test_label)
