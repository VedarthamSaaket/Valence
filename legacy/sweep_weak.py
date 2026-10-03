"""
Algorithm + k sweep for weak tests (16PF, RIASEC).

For each test we sweep:
  spaces:      standardized raw traits, UMAP-10D, UMAP-2D
  algorithms:  KMeans, GaussianMixture(full), BayesianGMM(dp), Agglomerative(ward)
  k:           2..8

We report the silhouette for every (space, algo, k) and flag the research-k row,
so we can SEE whether matching the psychology-paper cluster count maximizes the
silhouette. Output: console table + JSON.

Research cluster counts (person-typologies, not factor counts):
  sixteenpf : 4  (Krug & Johns Q-type modal profiles -> 4 types)
  riasec    : 6  (Holland RIASEC types; circular structure, weak separation)
"""
import json, os, warnings
import numpy as np
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans, AgglomerativeClustering
from sklearn.mixture import GaussianMixture, BayesianGaussianMixture
from sklearn.metrics import silhouette_score, davies_bouldin_score, calinski_harabasz_score

warnings.filterwarnings("ignore")
MODELS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "backend", "models")

RESEARCH_K = {"sixteenpf": 4, "riasec": 6}
KS = [2, 3, 4, 5, 6, 7, 8]
SAMPLE = 8000  # silhouette is O(n^2); subsample for speed, fixed seed


def build_spaces(tid):
    tm = np.load(os.path.join(MODELS, f"{tid}_trait_matrix.npy")).astype(np.float32)
    Xs = StandardScaler().fit_transform(tm).astype(np.float32)
    spaces = {"traits_scaled": Xs}
    try:
        import umap
        for d, key in [(10, "umap10d"), (2, "umap2d")]:
            reducer = umap.UMAP(n_components=d, n_neighbors=30, min_dist=0.0,
                                metric="euclidean", random_state=42)
            # fit on a sample for speed, transform sample only (we cluster the sample)
            spaces[key] = None  # filled per-sample below to keep alignment
        spaces["_umap_cfg"] = True
    except Exception as e:
        spaces["_umap_err"] = str(e)
    return tm, Xs, spaces


def cluster_and_score(X, algo, k):
    if algo == "kmeans":
        labels = KMeans(n_clusters=k, n_init=10, random_state=42).fit_predict(X)
    elif algo == "gmm":
        labels = GaussianMixture(n_components=k, covariance_type="full",
                                 n_init=3, random_state=42).fit_predict(X)
    elif algo == "bgm":
        bgm = BayesianGaussianMixture(n_components=k, covariance_type="full",
              weight_concentration_prior_type="dirichlet_process",
              weight_concentration_prior=0.01, max_iter=300, n_init=2,
              init_params="kmeans", reg_covar=1e-4, random_state=42).fit(X)
        labels = bgm.predict(X)
    elif algo == "ward":
        labels = AgglomerativeClustering(n_clusters=k, linkage="ward").fit_predict(X)
    else:
        return None
    if len(set(labels)) < 2:
        return None
    return {
        "k_eff": int(len(set(labels))),
        "sil": float(silhouette_score(X, labels)),
        "db":  float(davies_bouldin_score(X, labels)),
        "ch":  float(calinski_harabasz_score(X, labels)),
    }


def sweep(tid):
    tm, Xs, spaces = build_spaces(tid)
    rng = np.random.default_rng(42)
    n = min(SAMPLE, len(Xs))
    idx = rng.choice(len(Xs), n, replace=False) if len(Xs) > n else np.arange(len(Xs))

    sample_spaces = {"traits_scaled": Xs[idx]}
    # build UMAP on the sample directly (clustering done on sample)
    if spaces.get("_umap_cfg"):
        import umap
        for d, key in [(10, "umap10d"), (2, "umap2d")]:
            try:
                emb = umap.UMAP(n_components=d, n_neighbors=30, min_dist=0.0,
                                metric="euclidean", random_state=42).fit_transform(Xs[idx])
                sample_spaces[key] = emb.astype(np.float32)
            except Exception as e:
                print(f"  [umap {key}] err {e}")

    rows = []
    for space_name, X in sample_spaces.items():
        for algo in ["kmeans", "gmm", "bgm", "ward"]:
            for k in KS:
                try:
                    r = cluster_and_score(X, algo, k)
                except Exception:
                    r = None
                if r:
                    rows.append({"space": space_name, "algo": algo, "k": k, **r})
    return rows


def main():
    all_out = {}
    for tid in ["sixteenpf", "riasec"]:
        rk = RESEARCH_K[tid]
        print(f"\n{'='*92}\n{tid.upper()}  (research k = {rk})\n{'='*92}")
        rows = sweep(tid)
        rows.sort(key=lambda r: -r["sil"])
        print(f"{'space':<14}{'algo':<9}{'k':>3}{'k_eff':>6}{'sil':>9}{'DB':>7}{'CH':>9}  note")
        print("-" * 92)
        # top 12 overall
        for r in rows[:12]:
            note = "<<< RESEARCH K" if r["k"] == rk else ""
            print(f"{r['space']:<14}{r['algo']:<9}{r['k']:>3}{r['k_eff']:>6}"
                  f"{r['sil']:>9.4f}{r['db']:>7.2f}{r['ch']:>9.0f}  {note}")
        # best at research k
        rk_rows = [r for r in rows if r["k"] == rk]
        best_rk = max(rk_rows, key=lambda r: r["sil"]) if rk_rows else None
        best_any = rows[0] if rows else None
        print("-" * 92)
        if best_rk:
            print(f"BEST @ research k={rk}: {best_rk['space']}/{best_rk['algo']} sil={best_rk['sil']:.4f}")
        if best_any:
            print(f"BEST overall:         {best_any['space']}/{best_any['algo']} k={best_any['k']} sil={best_any['sil']:.4f}")
        all_out[tid] = {"research_k": rk, "best_research_k": best_rk,
                        "best_overall": best_any, "all_rows": rows}
    with open(os.path.join(MODELS, "_sweep_weak.json"), "w") as fh:
        json.dump(all_out, fh, indent=2)
    print(f"\nReport -> {os.path.join(MODELS, '_sweep_weak.json')}")


if __name__ == "__main__":
    main()
