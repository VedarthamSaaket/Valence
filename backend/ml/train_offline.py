"""
Valence training script.

Per instrument: load the reference dataset, clean, score with the published keys,
save the empirical distributions used for percentiles, fit a latent-profile model
(Gaussian mixture on standardized trait scores) with the number of profiles fixed
from the person-centered literature, and fit a 2D UMAP for the personality map.

Usage:
    FORCE_RETRAIN=1 python backend/ml/train_offline.py
    python backend/ml/train_offline.py hexaco hsq
"""

from __future__ import annotations

import io
import json
import logging
import os
import pickle
import re
import sys
import time
import traceback
from datetime import datetime
from typing import Dict, List, Optional

import numpy as np
import pandas as pd
from sklearn.mixture import GaussianMixture
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import silhouette_score

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from scoring_keys import (
    HEXACO_FACETS, HEXACO_REVERSED_ITEMS, HSQ_SCALES, HSQ_REVERSED,
    ECR_AVOIDANCE, ECR_ANXIETY, ECR_REVERSED, AMBI_NEO_FACETS,
)

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

SCHEMA_VERSION = "v12-literature-profiles"

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
APP_ROW = re.compile(r"20\d\d-\d\d-\d\dT\d\d:\d\d:\d\d")


def load_dataset(folder: str) -> pd.DataFrame:
    candidates = [
        os.path.join(DATASETS_DIR, folder, folder, "data.csv"),
        os.path.join(DATASETS_DIR, folder, "data.csv"),
    ]
    for path in candidates:
        if not os.path.exists(path):
            continue
        with open(path, encoding="latin-1") as fh:
            lines = fh.read().splitlines()
        if APP_ROW.search(lines[0]) or lines[0].lower().startswith("timestamp"):
            continue
        kept = [lines[0]] + [ln for ln in lines[1:] if not APP_ROW.search(ln)]
        if len(kept) != len(lines):
            log.info(f"  ignored {len(lines) - len(kept)} app-appended rows in {path}")
        text = "\n".join(kept)
        for sep in (",", "\t"):
            try:
                df = pd.read_csv(io.StringIO(text), sep=sep, low_memory=False)
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
    def keyed(nums):
        cols = [(6 - df[f"Q{q}"]) if q in ECR_REVERSED else df[f"Q{q}"] for q in nums if f"Q{q}" in df.columns]
        return (pd.concat(cols, axis=1).mean(axis=1) - 1) / 4
    anx = keyed(ECR_ANXIETY)
    avo = keyed(ECR_AVOIDANCE)
    return pd.DataFrame({
        "Anxious":  anx.clip(0, 1),
        "Avoidant": avo.clip(0, 1),
        "Secure":   (1 - (anx + avo) / 2).clip(0, 1),
    })


def score_hexaco_df(df):
    out = {}
    for trait, facets in HEXACO_FACETS.items():
        cols = []
        for f in facets:
            for i in range(1, 11):
                name = f"{f}{i}"
                if name in df.columns:
                    cols.append((8 - df[name]) if name in HEXACO_REVERSED_ITEMS else df[name])
        out[trait] = ((pd.concat(cols, axis=1).mean(axis=1) - 1) / 6).clip(0, 1)
    return pd.DataFrame(out)


def score_hsq_df(df):
    out = {}
    for scale, qs in HSQ_SCALES.items():
        cols = [(6 - df[f"Q{q}"]) if q in HSQ_REVERSED else df[f"Q{q}"] for q in qs if f"Q{q}" in df.columns]
        out[scale] = ((pd.concat(cols, axis=1).mean(axis=1) - 1) / 4).clip(0, 1)
    return pd.DataFrame(out)


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
    def col(q):
        return f"Q{q}A" if f"Q{q}A" in df.columns else f"Q{q}"
    out = {}
    for domain, facets in AMBI_NEO_FACETS.items():
        facet_means = []
        for keyed in facets.values():
            cols = [df[col(q)] if sign > 0 else (8 - df[col(q)]) for q, sign in keyed if col(q) in df.columns]
            facet_means.append(pd.concat(cols, axis=1).mean(axis=1))
        out[domain] = ((pd.concat(facet_means, axis=1).mean(axis=1) - 1) / 6).clip(0, 1)
    return pd.DataFrame(out)


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
    "hexaco":     {"folder": "HEXACO",               "scorer": score_hexaco_df,     "k": 5,
                   "basis": "Espinoza, Daljeet & Meyer (2020, Nature Human Behaviour): five replicated HEXACO-PI-R profiles in about 90,000 respondents; Daljeet et al. (2017) also found five"},
    "ambi":       {"folder": "AMBI_data_Nov2019",    "scorer": score_ambi_df,       "k": 4,
                   "basis": "Gerlach, Farb, Revelle & Amaral (2018, Nature Human Behaviour): four personality types (average, reserved, self-centred, role model) in Big-Five trait space across more than 1.5 million respondents"},
    "darktriad":  {"folder": "SD3",                  "scorer": score_darktriad_df,  "k": 4,
                   "basis": "Dark Triad latent-profile studies report four or five profiles running from low to high; four follows the four-profile solutions (e.g. the person-centered work-behaviour study, 2020)"},
    "npi":        {"folder": "NPI",                  "scorer": score_npi_df,        "k": 4,
                   "basis": "Wetzel, Leckelt, Gerlach & Back (2016, European Journal of Personality): four narcissism subgroups replicated in German and US samples"},
    "dass":       {"folder": "DASS_data_21.02.19",   "scorer": score_dass_df,       "k": 4,
                   "basis": "A latent-profile study of depression, anxiety and stress found four profiles (low, moderate, high, very high), in an adolescent sample; no adult DASS profile study was located"},
    "kims":       {"folder": "KIMS",                 "scorer": score_kims_df,       "k": 4,
                   "basis": "Pearson, Lawless, Brown & Bravo (2015, Personality and Individual Differences): four mindfulness subgroups (high, low, judgmentally observing, non-judgmentally aware), found with the related FFMQ"},
    "hsq":        {"folder": "HSQ",                  "scorer": score_hsq_df,        "k": 4,
                   "basis": "Galloway (2010, Personality and Individual Differences): four humor clusters on the HSQ (high on all, low on all, positive styles, negative styles); Leist & Mueller (2013) found three"},
    "gcbs":       {"folder": "GCBS",                 "scorer": score_gcbs_df,       "k": 5,
                   "basis": "Frenken & Imhoff (2021, International Review of Social Psychology): latent profiles that differ mainly in degree of belief; five graded profiles follow the comparison in the accompanying study"},
    "riasec":     {"folder": "RIASEC_data12Dec2018", "scorer": score_riasec_df,     "k": 6, "ipsatize": True, "assignment": "dominant",
                   "basis": "Holland (1959): six vocational personality types, each person classified by their dominant interest area; Perera & McIlveen (2018) also report six interest profiles"},
    "attachment": {"folder": "ECR-data-1March2018",  "scorer": score_attachment_df, "k": 4,
                   "cluster_traits": ["Anxious", "Avoidant"],
                   "basis": "Bartholomew & Horowitz (1991): four attachment styles; Vaillancourt-Morel et al. (2022): latent profile analysis of ECR scores found the same four in a community sample"},
    "fti":        {"folder": "FTI",                  "scorer": score_fti_df,        "k": 4, "ipsatize": True, "assignment": "dominant",
                   "basis": "Brown, Acevedo & Fisher (2013); Fisher et al. (2015): four temperament types, each person classified by their dominant temperament scale"},
}


# ---------------------------------------------------------------------------
# Clustering: latent-profile model with a literature-fixed number of profiles
# ---------------------------------------------------------------------------
def profile_features(z: np.ndarray, ipsatize: bool) -> np.ndarray:
    if ipsatize:
        return z - z.mean(axis=1, keepdims=True)
    return z


def fit_profiles(features: np.ndarray, k: int) -> GaussianMixture:
    model = GaussianMixture(
        n_components=k,
        covariance_type="diag",
        n_init=10,
        max_iter=500,
        init_params="kmeans",
        reg_covar=1e-3,
        random_state=42,
    )
    model.fit(features)
    return model


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

    stage(test_id, "latent profile fit", 50)
    trait_names = list(trait_df.columns)
    cluster_traits = cfg.get("cluster_traits") or trait_names
    cluster_idx = [trait_names.index(t) for t in cluster_traits]
    ipsatize = bool(cfg.get("ipsatize", False))
    k = int(cfg["k"])

    scaler = StandardScaler().fit(trait_matrix[:, cluster_idx])
    features = profile_features(scaler.transform(trait_matrix[:, cluster_idx]), ipsatize)
    fit_idx = np.random.default_rng(42).choice(n, min(50000, n), replace=False) if n > 50000 else np.arange(n)
    dominant = cfg.get("assignment") == "dominant"
    if dominant:
        bgm = None
        all_labels = features.argmax(axis=1)
    else:
        bgm = fit_profiles(features[fit_idx], k)
        all_labels = bgm.predict(features)
    labels = all_labels[sample_idx]
    weights = [float(np.mean(all_labels == c)) for c in range(k)]
    k_eff = int(len(set(all_labels.tolist())))
    try:
        sil = float(silhouette_score(features[sample_idx], labels))
    except Exception:
        sil = 0.0
    log.info(f"  profiles k={k}, shares={[round(w, 3) for w in weights]}, silhouette={sil:.4f}")

    if bgm is not None:
        with open(os.path.join(MODELS_DIR, f"{test_id}_gmm.pkl"), "wb") as fh:
            pickle.dump(bgm, fh)
    with open(os.path.join(MODELS_DIR, f"{test_id}_trait_scaler.pkl"), "wb") as fh:
        pickle.dump(scaler, fh)

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
    for cid in range(k):
        members = all_labels == cid
        centroid = trait_matrix[members].mean(axis=0).tolist() if members.any() else [0.5] * trait_matrix.shape[1]
        centroids.append({
            "cluster":  int(cid),
            "weight":   round(float(weights[cid]), 6),
            "size":     int(members.sum()),
            "centroid": [round(float(v), 4) for v in centroid],
        })

    arc_path = os.path.join(MODELS_DIR, f"{test_id}_archetypes.json")
    kept = [c for c in centroids if c["size"] > 0]
    placeholder = {
        str(c["cluster"]): {
            "id":          f"cluster_{c['cluster']}",
            "name":        f"Archetype {c['cluster'] + 1}",
            "tagline":     "",
            "color":       "#8A9AAE",
            "description": "",
            "centroid":    c["centroid"],
            "size":        c["size"],
            "weight":      c["weight"],
        }
        for c in kept
    }
    with open(arc_path, "w", encoding="utf-8") as fh:
        json.dump(placeholder, fh, indent=2)
    log.info(f"  archetype seeds written ({len(kept)} profiles)")

    meta = {
        "schema_version":      SCHEMA_VERSION,
        "test_id":             test_id,
        "trained_at":          datetime.utcnow().isoformat(timespec="seconds") + "Z",
        "n_samples":           int(n),
        "n_traits":            int(trait_matrix.shape[1]),
        "trait_names":         trait_names,
        "cluster_traits":      cluster_traits,
        "ipsatize":            ipsatize,
        "assignment":          "dominant" if dominant else "mixture",
        "k":                   k,
        "effective_k":         k_eff,
        "k_basis":             cfg.get("basis"),
        "silhouette":          sil,
        "clustering_strategy": "dominant_type_on_standardized_traits" if dominant else "latent_profile_gmm_on_standardized_traits",
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
