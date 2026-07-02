"""
Valence Unified Training Script
================================
One script. Trains percentile distributions, UMAP embeddings, and Bayesian Gaussian
Mixture clusters for all ML-pipeline tests. No KMeans. No hand-picked k.

Pipeline per test:
  1. load dataset
  2. clean (drop invalid rows, fill medians)
  3. score (population-level scorer -> trait matrix, N x D, all in 0..1)
  4. save distributions.json  (per-trait sorted arrays for percentile lookup)
  5. UMAP -> 10D embedding (preserves manifold for clustering)
  6. Bayesian Gaussian Mixture with Dirichlet Process prior on the 10D embedding,
     max_components = 12, data picks the actual k via variational Bayes
  7. UMAP -> 2D for the personality map visualization
  8. write archetype placeholders (centroids in raw trait space, LLM refines later)
  9. write meta.json (k, effective_k, silhouette, schema_version, timestamps)

Why Bayesian GMM with DP prior:
  - Auto-discovers k from the data (no silhouette grid-search)
  - Soft probabilistic membership (every person is a blend, never a binary label)
  - Predicts cluster for new respondents (.predict / .predict_proba on the model)
  - Combined with UMAP-10D, handles non-convex personality clusters cleanly
  - Latent Profile Analysis is the gold standard in personality psych research;
    BGM-DP is its principled "auto k" extension.

Usage:
    python backend/ml/train_offline.py                  # train missing
    FORCE_RETRAIN=1 python backend/ml/train_offline.py  # retrain everything
    python backend/ml/train_offline.py hexaco hsq       # only the listed ones

Observable progress (you can tail these without interrupting training):
    backend/models/train_offline.log         (line-by-line log)
    backend/models/_training_status.json     (current test, step, percent)
"""

from __future__ import annotations

import json
import logging
import os
import pickle
import sys
import time
import traceback
from datetime import datetime
from typing import Dict, List, Optional

import numpy as np
import pandas as pd
from sklearn.mixture import BayesianGaussianMixture
from sklearn.metrics import silhouette_score

try:
    import umap
    UMAP_AVAILABLE = True
except ImportError:
    print("WARNING: umap-learn not installed. Run: pip install umap-learn")
    UMAP_AVAILABLE = False


# ---------------------------------------------------------------------------
# Paths and logging
# ---------------------------------------------------------------------------
SCRIPT_DIR   = os.path.dirname(os.path.abspath(__file__))
DATASETS_DIR = os.path.join(SCRIPT_DIR, "..", "datasets")
MODELS_DIR   = os.path.join(SCRIPT_DIR, "..", "models")
os.makedirs(MODELS_DIR, exist_ok=True)

LOG_PATH    = os.path.join(MODELS_DIR, "train_offline.log")
STATUS_PATH = os.path.join(MODELS_DIR, "_training_status.json")

SCHEMA_VERSION = "v6-bgm-research-tuned"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)s  %(message)s",
    handlers=[
        logging.FileHandler(LOG_PATH, mode="a", encoding="utf-8"),
        logging.StreamHandler(sys.stdout),
    ],
)
log = logging.getLogger("train")


def write_status(state: Dict):
    state["updated_at"] = datetime.utcnow().isoformat(timespec="seconds") + "Z"
    with open(STATUS_PATH, "w", encoding="utf-8") as fh:
        json.dump(state, fh, indent=2)


def stage(test_id: str, step: str, percent: int, extra: Optional[Dict] = None):
    state = {
        "schema_version": SCHEMA_VERSION,
        "current_test":   test_id,
        "step":           step,
        "percent":        percent,
    }
    if extra:
        state.update(extra)
    write_status(state)
    log.info(f"[{test_id}] {step} ({percent}%)")


# ---------------------------------------------------------------------------
# Dataset loader
# ---------------------------------------------------------------------------
def load_dataset(folder: str) -> pd.DataFrame:
    candidates = [
        os.path.join(DATASETS_DIR, folder, folder, "data.csv"),
        os.path.join(DATASETS_DIR, folder, "data.csv"),
    ]
    for path in candidates:
        if not os.path.exists(path):
            continue
        for sep in (",", "\t"):
            try:
                df = pd.read_csv(path, sep=sep, low_memory=False)
                if df.shape[1] > 1:
                    log.info(f"  loaded {path}  sep={sep!r}  shape={df.shape}")
                    return df
            except Exception:
                continue
        raise ValueError(f"Could not parse {path} with comma or tab delimiter")
    raise FileNotFoundError(f"Dataset not found for folder: {folder}")


# ---------------------------------------------------------------------------
# Population scorers (df -> DataFrame of normalized 0..1 trait scores)
# ---------------------------------------------------------------------------
def score_sixteenpf_df(df):
    factor_map = {
        "Warmth":             [f"A{i}" for i in range(1,11)],
        "Reasoning":          [f"B{i}" for i in range(1,14)],
        "Stability":          [f"C{i}" for i in range(1,11)],
        "Dominance":          [f"D{i}" for i in range(1,11)],
        "Liveliness":         [f"E{i}" for i in range(1,11)],
        "Rule-Consciousness": [f"F{i}" for i in range(1,11)],
        "Social-Boldness":    [f"G{i}" for i in range(1,11)],
        "Sensitivity":        [f"H{i}" for i in range(1,11)],
        "Vigilance":          [f"I{i}" for i in range(1,11)],
        "Abstractedness":     [f"J{i}" for i in range(1,11)],
        "Privateness":        [f"K{i}" for i in range(1,11)],
        "Apprehension":       [f"L{i}" for i in range(1,11)],
        "Openness-to-Change": [f"M{i}" for i in range(1,11)],
        "Self-Reliance":      [f"N{i}" for i in range(1,11)],
        "Perfectionism":      [f"O{i}" for i in range(1,11)],
        "Tension":            [f"P{i}" for i in range(1,11)],
    }
    out = {}
    for trait, cols in factor_map.items():
        avail = [c for c in cols if c in df.columns]
        out[trait] = ((df[avail].mean(axis=1) - 1) / 4).clip(0, 1)
    return pd.DataFrame(out)


def score_darktriad_df(df):
    def r(c): return 6 - df[c]
    m = df[[f"M{i}" for i in range(1,10)]].mean(axis=1)
    n = pd.concat([df["N1"], r("N2"), df["N3"], df["N4"], df["N5"], r("N6"),
                   df["N7"], r("N8"), df["N9"]], axis=1).mean(axis=1)
    p = pd.concat([df["P1"], r("P2"), df["P3"], df["P4"], df["P5"], df["P6"],
                   r("P7"), df["P8"], df["P9"]], axis=1).mean(axis=1)
    return pd.DataFrame({
        "Machiavellianism": ((m - 1) / 4).clip(0, 1),
        "Narcissism":       ((n - 1) / 4).clip(0, 1),
        "Psychopathy":      ((p - 1) / 4).clip(0, 1),
    })


def score_dass_df(df):
    dep_nums = [3, 5, 10, 13, 16, 17, 21, 24, 26, 31, 34, 37, 38, 42]
    anx_nums = [2, 4, 7, 9, 15, 19, 20, 23, 25, 28, 30, 36, 40, 41]
    str_nums = [1, 6, 8, 11, 12, 14, 18, 22, 27, 29, 32, 33, 35, 39]

    def col(n): return f"Q{n}A"

    def avg(nums):
        cols = [col(n) for n in nums if col(n) in df.columns]
        return ((df[cols].mean(axis=1) - 1) / 3).clip(0, 1)

    return pd.DataFrame({
        "Depression": avg(dep_nums),
        "Anxiety":    avg(anx_nums),
        "Stress":     avg(str_nums),
    })


def score_aesthetic_df(df):
    def avg(prefix, end):
        cols = [f"{prefix}{i}A" for i in range(1, end + 1) if f"{prefix}{i}A" in df.columns]
        return ((df[cols].mean(axis=1) - 1) / 4).clip(0, 1)
    return pd.DataFrame({
        "Intense":     avg("RA", 8),
        "Mainstream":  avg("LP", 8),
        "Traditional": avg("MF", 8),
        "Visual":      avg("V",  6),
    })


def score_riasec_df(df):
    def avg(letter):
        cols = [f"{letter}{i}" for i in range(1, 9) if f"{letter}{i}" in df.columns]
        return ((df[cols].mean(axis=1) - 1) / 4).clip(0, 1)
    return pd.DataFrame({
        "Realistic":     avg("R"),
        "Investigative": avg("I"),
        "Artistic":      avg("A"),
        "Social":        avg("S"),
        "Enterprising":  avg("E"),
        "Conventional":  avg("C"),
    })


def score_attachment_df(df):
    anx_cols = [f"Q{i}" for i in range(1, 19) if f"Q{i}" in df.columns]
    avo_cols = [f"Q{i}" for i in range(19, 37) if f"Q{i}" in df.columns]
    anx = (df[anx_cols].mean(axis=1) - 1) / 6
    avo = (df[avo_cols].mean(axis=1) - 1) / 6
    return pd.DataFrame({
        "Anxious":  anx.clip(0, 1),
        "Avoidant": avo.clip(0, 1),
        "Secure":   (1 - (anx + avo) / 2).clip(0, 1),
    })


# --- the 7 new tests ---

HEXACO_FACETS = {
    "Honesty-Humility":  ["HSinc", "HFair", "HGree", "HMode"],
    "Emotionality":      ["EFear", "EAnxi", "EDepe", "ESent"],
    "Extraversion":      ["XExpr", "XSoci", "XSocB", "XLive"],
    "Agreeableness":     ["AForg", "AGent", "AFlex", "APati"],
    "Conscientiousness": ["COrga", "CDili", "CPerf", "CPrud"],
    "Openness":          ["OAesA", "OInqu", "OCrea", "OUnco"],
}


def score_hexaco_df(df):
    out = {}
    for trait, facets in HEXACO_FACETS.items():
        cols = []
        for f in facets:
            cols += [f"{f}{i}" for i in range(1, 11) if f"{f}{i}" in df.columns]
        out[trait] = ((df[cols].mean(axis=1) - 1) / 6).clip(0, 1)
    return pd.DataFrame(out)


def score_hsq_df(df):
    def r(c): return 6 - df[c]
    aff = pd.concat([r("Q1"),  df["Q5"],  r("Q9"),  df["Q13"],
                     r("Q17"), df["Q21"], r("Q25"), r("Q29")], axis=1).mean(axis=1)
    sen = df[[f"Q{i}" for i in [2, 6, 10, 14, 18, 22, 26, 30] if f"Q{i}" in df.columns]].mean(axis=1)
    agg = df[[f"Q{i}" for i in [3, 7, 11, 15, 19, 23, 27, 31] if f"Q{i}" in df.columns]].mean(axis=1)
    sdf = df[[f"Q{i}" for i in [4, 8, 12, 16, 20, 24, 28, 32] if f"Q{i}" in df.columns]].mean(axis=1)
    return pd.DataFrame({
        "Affiliative":    ((aff - 1) / 4).clip(0, 1),
        "Self-Enhancing": ((sen - 1) / 4).clip(0, 1),
        "Aggressive":     ((agg - 1) / 4).clip(0, 1),
        "Self-Defeating": ((sdf - 1) / 4).clip(0, 1),
    })


def score_kims_df(df):
    def r(c): return 6 - df[c]
    obs = df[[f"Q{i}" for i in [1, 5, 9, 13, 17, 21, 25, 29, 33, 37, 39] if f"Q{i}" in df.columns]].mean(axis=1)
    des = pd.concat([df["Q2"],  df["Q6"],  df["Q10"],
                     r("Q14"),  r("Q18"),  r("Q22"),
                     df["Q26"], df["Q30"], df["Q34"]], axis=1).mean(axis=1)
    act = pd.concat([r("Q3"),  df["Q7"],  r("Q11"), df["Q15"], df["Q19"],
                     r("Q23"), r("Q27"), r("Q31"), r("Q35"), df["Q38"]], axis=1).mean(axis=1)
    acc = pd.concat([r("Q4"),  r("Q8"),  r("Q12"), r("Q16"),
                     r("Q20"), r("Q24"), r("Q28"), r("Q32"), r("Q36")], axis=1).mean(axis=1)
    return pd.DataFrame({
        "Observing":                  ((obs - 1) / 4).clip(0, 1),
        "Describing":                 ((des - 1) / 4).clip(0, 1),
        "Acting with Awareness":      ((act - 1) / 4).clip(0, 1),
        "Accepting without Judgment": ((acc - 1) / 4).clip(0, 1),
    })


def score_fti_df(df):
    def avg(rng):
        cols = [f"Q{i}A" for i in rng if f"Q{i}A" in df.columns]
        if not cols:
            cols = [f"Q{i}" for i in rng if f"Q{i}" in df.columns]
        return ((df[cols].mean(axis=1) - 1) / 3).clip(0, 1)
    return pd.DataFrame({
        "Explorer":   avg(range(1, 15)),
        "Builder":    avg(range(15, 29)),
        "Director":   avg(range(29, 43)),
        "Negotiator": avg(range(43, 57)),
    })


NPI_NARC_KEY = {
    1:1, 2:1, 3:1, 4:2, 5:2, 6:1, 7:2, 8:1, 9:2, 10:2,
    11:1, 12:1, 13:1, 14:1, 15:2, 16:1, 17:2, 18:2, 19:2, 20:2,
    21:1, 22:2, 23:2, 24:1, 25:1, 26:2, 27:1, 28:2, 29:1, 30:1,
    31:1, 32:2, 33:1, 34:1, 35:2, 36:1, 37:1, 38:1, 39:1, 40:2,
}
NPI_FACETS = {
    "Authority":        [1, 8, 10, 11, 12, 32, 33, 36],
    "Self-Sufficiency": [17, 21, 22, 31, 34, 39],
    "Superiority":      [4, 9, 26, 37, 40],
    "Exhibitionism":    [2, 3, 7, 20, 28, 30, 38],
    "Exploitativeness": [6, 13, 16, 23, 35],
    "Vanity":           [15, 19, 29],
    "Entitlement":      [5, 14, 18, 24, 25, 27],
}


def score_npi_df(df):
    out = {}
    for facet, qnums in NPI_FACETS.items():
        cols = []
        for q in qnums:
            col = f"Q{q}"
            if col in df.columns:
                cols.append((df[col] == NPI_NARC_KEY[q]).astype(int))
        if cols:
            out[facet] = pd.concat(cols, axis=1).mean(axis=1).clip(0, 1)
        else:
            out[facet] = pd.Series(0.0, index=df.index)
    return pd.DataFrame(out)


def score_ambi_df(df):
    def avg(rng):
        cols = [f"Q{i}A" for i in rng if f"Q{i}A" in df.columns]
        if not cols:
            cols = [f"Q{i}" for i in rng if f"Q{i}" in df.columns]
        return ((df[cols].mean(axis=1) - 1) / 6).clip(0, 1)
    return pd.DataFrame({
        "Affect Regulation":  avg(range(1, 27)),
        "Social Drive":       avg(range(27, 53)),
        "Conscientiousness":  avg(range(53, 79)),
        "Openness":           avg(range(79, 105)),
        "Agreeableness":      avg(range(105, 131)),
        "Energy Drive":       avg(range(131, 157)),
        "Identity Coherence": avg(range(157, 182)),
    })


def score_gcbs_df(df):
    factors = {
        "Government Malfeasance":     [1, 6, 11],
        "Malevolent Global":          [2, 7, 12],
        "Extraterrestrial Coverup":   [3, 8, 13],
        "Personal Wellbeing Threats": [4, 9, 14],
        "Control of Information":     [5, 10, 15],
    }
    out = {}
    for fname, qs in factors.items():
        cols = [f"Q{i}" for i in qs if f"Q{i}" in df.columns]
        out[fname] = ((df[cols].mean(axis=1) - 1) / 4).clip(0, 1)
    return pd.DataFrame(out)


# ---------------------------------------------------------------------------
# Config table
# ---------------------------------------------------------------------------
CONFIGS = {
    # already-trained tests, retrained under the new BGM pipeline for consistency
    "sixteenpf":  {"folder": "16PF",                 "scorer": score_sixteenpf_df,  "k_max": 6, "wcp": 0.01},
    "darktriad":  {"folder": "SD3",                  "scorer": score_darktriad_df,  "k_max": 4, "wcp": 0.01},
    "dass":       {"folder": "DASS_data_21.02.19",   "scorer": score_dass_df,       "k_max": 5, "wcp": 0.01},
    "aesthetic":  {"folder": "APS_data",             "scorer": score_aesthetic_df,  "k_max": 5, "wcp": 0.01},
    "riasec":     {"folder": "RIASEC_data12Dec2018", "scorer": score_riasec_df,     "k_max": 6, "wcp": 0.01},
    "attachment": {"folder": "ECR-data-1March2018",  "scorer": score_attachment_df, "k_max": 4, "wcp": 0.01},
    # the 7 new tests, k_max chosen per research literature, see README/docstring
    "hexaco": {"folder": "HEXACO",            "scorer": score_hexaco_df, "k_max": 4, "wcp": 0.01},  # Gerlach 2018: 4 types
    "hsq":    {"folder": "HSQ",               "scorer": score_hsq_df,    "k_max": 4, "wcp": 0.01},  # Galloway 2010
    "kims":   {"folder": "KIMS",              "scorer": score_kims_df,   "k_max": 4, "wcp": 0.01},  # Pearson 2015
    "fti":    {"folder": "FTI",               "scorer": score_fti_df,    "k_max": 4, "wcp": 0.01},  # Fisher 2013 (4 temperaments)
    "npi":    {"folder": "NPI",               "scorer": score_npi_df,    "k_max": 4, "wcp": 0.01},  # Wallace 2002
    "ambi":   {"folder": "AMBI_data_Nov2019", "scorer": score_ambi_df,   "k_max": 5, "wcp": 0.01},  # Big Five mapping
    "gcbs":   {"folder": "GCBS",              "scorer": score_gcbs_df,   "k_max": 5, "wcp": 0.01},  # Brotherton 2013
}


# ---------------------------------------------------------------------------
# Clustering: Bayesian GMM with Dirichlet Process prior
# ---------------------------------------------------------------------------
def fit_bgm(embeddings: np.ndarray, max_components: int = 12,
            weight_concentration_prior: float = 0.01) -> BayesianGaussianMixture:
    """
    Variational Bayesian Gaussian Mixture with Dirichlet Process weight prior.
    weight_concentration_prior smaller -> sparser mixture (more aggressive pruning).
    Default 0.01 follows LPA-style sparse mixture practice in personality research.
    """
    bgm = BayesianGaussianMixture(
        n_components=max_components,
        covariance_type="full",
        weight_concentration_prior_type="dirichlet_process",
        weight_concentration_prior=weight_concentration_prior,
        max_iter=300,
        n_init=3,
        init_params="kmeans",
        reg_covar=1e-4,
        random_state=42,
    )
    bgm.fit(embeddings)
    return bgm


def effective_k(weights: np.ndarray, threshold: float = 0.02) -> int:
    """Components with non-trivial weight."""
    return int(np.sum(np.array(weights) >= threshold))


# ---------------------------------------------------------------------------
# Per-test trainer
# ---------------------------------------------------------------------------
def train_one(test_id: str, cfg: Dict) -> Dict:
    stage(test_id, "loading dataset", 5, {"folder": cfg["folder"]})
    df_raw = load_dataset(cfg["folder"])

    stage(test_id, "cleaning", 12)
    df = df_raw.apply(pd.to_numeric, errors="coerce").replace(0, np.nan)
    df = df.dropna(thresh=int(df.shape[1] * 0.8))
    df = df.fillna(df.median(numeric_only=True))
    log.info(f"  clean rows: {len(df)}")

    stage(test_id, "scoring", 22)
    trait_df = cfg["scorer"](df).dropna()
    trait_matrix = trait_df.values.astype(np.float32)
    log.info(f"  trait matrix: {trait_matrix.shape}")

    np.save(os.path.join(MODELS_DIR, f"{test_id}_trait_matrix.npy"), trait_matrix)
    with open(os.path.join(MODELS_DIR, f"{test_id}_distributions.json"), "w", encoding="utf-8") as fh:
        json.dump({c: trait_df[c].tolist() for c in trait_df.columns}, fh)
    log.info("  distributions saved (for percentiles)")

    n = len(trait_matrix)
    sample_size = min(15000, n)
    sample_idx = np.random.default_rng(42).choice(n, sample_size, replace=False) if n > sample_size else np.arange(n)
    sample = trait_matrix[sample_idx]

    # UMAP 10D for clustering input
    stage(test_id, "umap 10d", 38)
    if UMAP_AVAILABLE:
        reducer10 = umap.UMAP(n_components=10, n_neighbors=30, min_dist=0.0,
                              random_state=42, metric="euclidean")
        reducer10.fit(sample)
        with open(os.path.join(MODELS_DIR, f"{test_id}_umap10d.pkl"), "wb") as fh:
            pickle.dump(reducer10, fh)
        emb10_full = reducer10.transform(trait_matrix).astype(np.float32)
        np.save(os.path.join(MODELS_DIR, f"{test_id}_umap10d_matrix.npy"), emb10_full)
        cluster_input = emb10_full[sample_idx]
    else:
        log.warning("  umap unavailable, clustering on raw trait space")
        cluster_input = sample

    # Bayesian GMM with DP prior on the embedding (per-test k_max + Dirichlet prior)
    stage(test_id, "bayesian gmm fit", 60)
    k_max = int(cfg.get("k_max", 12))
    wcp   = float(cfg.get("wcp", 0.01))
    bgm   = fit_bgm(cluster_input, max_components=k_max, weight_concentration_prior=wcp)
    weights = bgm.weights_.tolist()
    k_eff = effective_k(weights)
    labels = bgm.predict(cluster_input)
    try:
        sil = float(silhouette_score(cluster_input, labels))
    except Exception:
        sil = 0.0
    log.info(f"  BGM converged, effective_k={k_eff}, silhouette={sil:.4f}")

    with open(os.path.join(MODELS_DIR, f"{test_id}_gmm.pkl"), "wb") as fh:
        pickle.dump(bgm, fh)
    with open(os.path.join(MODELS_DIR, f"{test_id}_gmm_weights.json"), "w", encoding="utf-8") as fh:
        json.dump({
            "n_components": int(bgm.n_components),
            "effective_k":  int(k_eff),
            "weights":      [round(float(w), 6) for w in weights],
            "silhouette":   sil,
            "method":       "bayesian_gmm_dirichlet_process",
        }, fh, indent=2)

    # UMAP 2D for the visualization map
    stage(test_id, "umap 2d for map", 80)
    if UMAP_AVAILABLE:
        reducer2 = umap.UMAP(n_components=2, n_neighbors=15, min_dist=0.1, random_state=42)
        reducer2.fit(sample)
        with open(os.path.join(MODELS_DIR, f"{test_id}_umap.pkl"), "wb") as fh:
            pickle.dump(reducer2, fh)
        coords = reducer2.transform(trait_matrix[:10000]).tolist()
        with open(os.path.join(MODELS_DIR, f"{test_id}_map_coords.json"), "w", encoding="utf-8") as fh:
            json.dump(coords, fh)
        log.info(f"  map_coords: {len(coords)} points")

    # Archetype centroid seeds (in raw trait space). LLM names them at inference.
    stage(test_id, "archetype seeds", 90)
    centroids = []
    for cid in range(bgm.n_components):
        members = sample_idx[labels == cid]
        if len(members) > 0:
            centroid = trait_matrix[members].mean(axis=0).tolist()
        else:
            centroid = [0.5] * trait_matrix.shape[1]
        centroids.append({
            "cluster":  int(cid),
            "weight":   round(float(weights[cid]), 6),
            "size":     int(len(members)),
            "centroid": [round(float(v), 4) for v in centroid],
        })

    arc_path = os.path.join(MODELS_DIR, f"{test_id}_archetypes.json")
    if not os.path.exists(arc_path) or os.getenv("FORCE_RETRAIN") == "1":
        # Only emit archetypes for effective components (weight above threshold)
        kept = [c for c in centroids if c["weight"] >= 0.02]
        placeholder = {
            str(i): {
                "id":          f"cluster_{i}",
                "name":        f"Archetype {i + 1}",
                "tagline":     "LLM enrichment pending",
                "color":       "#8A9AAE",
                "description": "Seeded from BGM centroid. LLM rewrites at inference time.",
                "centroid":    c["centroid"],
                "size":        c["size"],
                "weight":      c["weight"],
            }
            for i, c in enumerate(kept)
        }
        with open(arc_path, "w", encoding="utf-8") as fh:
            json.dump(placeholder, fh, indent=2)
        log.info(f"  archetype placeholders written ({len(kept)} non-trivial clusters)")

    meta = {
        "schema_version":      SCHEMA_VERSION,
        "test_id":             test_id,
        "trained_at":          datetime.utcnow().isoformat(timespec="seconds") + "Z",
        "n_samples":           int(n),
        "n_traits":            int(trait_matrix.shape[1]),
        "trait_names":         list(trait_df.columns),
        "k":                   int(bgm.n_components),
        "effective_k":         int(k_eff),
        "silhouette":          sil,
        "clustering_strategy": "bayesian_gmm_dp_on_umap10d",
        "umap_dims_cluster":   10,
        "umap_dims_map":       2,
        "sample_size":         int(sample_size),
    }
    with open(os.path.join(MODELS_DIR, f"{test_id}_meta.json"), "w", encoding="utf-8") as fh:
        json.dump(meta, fh, indent=2)
    return meta


def already_trained(test_id: str) -> bool:
    meta_path = os.path.join(MODELS_DIR, f"{test_id}_meta.json")
    if not os.path.exists(meta_path):
        return False
    try:
        with open(meta_path, encoding="utf-8") as fh:
            meta = json.load(fh)
        return meta.get("schema_version") == SCHEMA_VERSION
    except Exception:
        return False


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main():
    requested = [a for a in sys.argv[1:] if not a.startswith("-")]
    targets = requested if requested else list(CONFIGS.keys())
    force = os.getenv("FORCE_RETRAIN") == "1"

    write_status({
        "schema_version": SCHEMA_VERSION,
        "phase":          "starting",
        "targets":        targets,
        "force":          force,
        "started_at":     datetime.utcnow().isoformat(timespec="seconds") + "Z",
    })

    trained: List[str] = []
    skipped: List[str] = []
    failed:  List[str] = []

    for i, tid in enumerate(targets):
        if tid not in CONFIGS:
            log.warning(f"unknown test '{tid}', skipping")
            continue
        if not force and already_trained(tid):
            log.info(f"[{tid}] already trained (schema {SCHEMA_VERSION}); skipping. FORCE_RETRAIN=1 to redo.")
            skipped.append(tid)
            continue

        try:
            stage(tid, "starting", 0, {"progress": f"{i + 1}/{len(targets)}"})
            t0 = time.time()
            meta = train_one(tid, CONFIGS[tid])
            elapsed = time.time() - t0
            stage(tid, "completed", 100, {
                "effective_k": meta.get("effective_k"),
                "silhouette":  meta.get("silhouette"),
                "elapsed_s":   round(elapsed, 2),
            })
            trained.append(tid)
        except FileNotFoundError as e:
            log.error(f"[{tid}] dataset missing: {e}")
            skipped.append(tid)
        except Exception as e:
            log.error(f"[{tid}] failed: {e}\n{traceback.format_exc()}")
            failed.append(tid)

    write_status({
        "schema_version": SCHEMA_VERSION,
        "phase":          "done",
        "trained":        trained,
        "skipped":        skipped,
        "failed":         failed,
        "finished_at":    datetime.utcnow().isoformat(timespec="seconds") + "Z",
    })
    log.info(f"trained: {trained}")
    log.info(f"skipped: {skipped}")
    log.info(f"failed:  {failed}")


if __name__ == "__main__":
    main()
