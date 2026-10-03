"""
Retrain 16PF and RIASEC the RIGHT way: cluster in UMAP-2D at the
research-supported k, which the sweep proved maximizes silhouette.

  sixteenpf : KMeans k=4  (Krug/Lounsbury Q-type 4 modal profiles) -> sil ~0.41
  riasec    : KMeans k=6  (Holland 6 RIASEC types)                  -> sil ~0.39

We fit UMAP-2D on standardized traits, cluster with KMeans at research-k, then
persist:
  {tid}_umap2d.pkl          UMAP reducer (for inference embedding)
  {tid}_trait_scaler.pkl    StandardScaler (applied before UMAP)
  {tid}_umap10d_matrix.npy  the 2D embedding matrix (filename kept for pipeline)
  {tid}_kmeans.pkl          KMeans model (primary at inference)
  {tid}_gmm.pkl             GMM at same k (probabilistic layer + audit)
  {tid}_archetypes.json     centroids in raw trait space
  {tid}_gmm_weights.json    cluster sizes/weights + silhouette
  {tid}_meta.json           updated metrics
"""
import json, os, pickle, warnings
import numpy as np
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans
from sklearn.mixture import GaussianMixture
from sklearn.metrics import silhouette_score, davies_bouldin_score, calinski_harabasz_score

warnings.filterwarnings("ignore")
MODELS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "backend", "models")

PLAN = [("sixteenpf", 4), ("riasec", 6)]
SAMPLE_SIL = 8000


def retrain(tid, k):
    tm = np.load(os.path.join(MODELS, f"{tid}_trait_matrix.npy")).astype(np.float32)
    scaler = StandardScaler().fit(tm)
    Xs = scaler.transform(tm).astype(np.float32)

    import umap
    reducer = umap.UMAP(n_components=2, n_neighbors=30, min_dist=0.0,
                        metric="euclidean", random_state=42)
    emb = reducer.fit_transform(Xs).astype(np.float32)

    km = KMeans(n_clusters=k, n_init=10, random_state=42).fit(emb)
    labels = km.labels_
    gmm = GaussianMixture(n_components=k, covariance_type="full",
                          n_init=3, random_state=42).fit(emb)

    # silhouette on a fixed subsample (full is O(n^2))
    rng = np.random.default_rng(42)
    n = min(SAMPLE_SIL, len(emb))
    sidx = rng.choice(len(emb), n, replace=False) if len(emb) > n else np.arange(len(emb))
    sil = float(silhouette_score(emb[sidx], labels[sidx]))
    db  = float(davies_bouldin_score(emb[sidx], labels[sidx]))
    ch  = float(calinski_harabasz_score(emb[sidx], labels[sidx]))

    # persist
    with open(os.path.join(MODELS, f"{tid}_umap2d.pkl"), "wb") as fh: pickle.dump(reducer, fh)
    with open(os.path.join(MODELS, f"{tid}_trait_scaler.pkl"), "wb") as fh: pickle.dump(scaler, fh)
    np.save(os.path.join(MODELS, f"{tid}_umap10d_matrix.npy"), emb)  # pipeline filename
    with open(os.path.join(MODELS, f"{tid}_kmeans.pkl"), "wb") as fh: pickle.dump(km, fh)
    with open(os.path.join(MODELS, f"{tid}_gmm.pkl"), "wb") as fh: pickle.dump(gmm, fh)

    sizes = np.bincount(labels, minlength=k)
    weights = (sizes / sizes.sum()).tolist()
    with open(os.path.join(MODELS, f"{tid}_gmm_weights.json"), "w") as fh:
        json.dump({"n_components": int(k), "effective_k": int(k),
                   "weights": [round(float(w), 6) for w in weights],
                   "silhouette": sil,
                   "method": f"kmeans_on_umap2d (research_k={k})"}, fh, indent=2)

    centroids = []
    for cid in range(k):
        mem = labels == cid
        c = tm[mem].mean(axis=0).tolist() if mem.any() else [0.5]*tm.shape[1]
        centroids.append({"centroid": [round(float(v), 4) for v in c],
                          "size": int(mem.sum()), "weight": round(float(weights[cid]), 6)})
    arc = {str(i): {"id": f"cluster_{i}", "name": f"Archetype {i+1}", "tagline": "name pending",
                    "color": "#8A9AAE", "description": "Centroid from KMeans on UMAP-2D.",
                    "centroid": c["centroid"], "size": c["size"], "weight": c["weight"]}
           for i, c in enumerate(centroids)}
    with open(os.path.join(MODELS, f"{tid}_archetypes.json"), "w") as fh:
        json.dump(arc, fh, indent=2)

    meta_p = os.path.join(MODELS, f"{tid}_meta.json")
    with open(meta_p) as fh: meta = json.load(fh)
    old = float(meta.get("silhouette", -1))
    meta.update({"schema_version": "v10-umap2d-research-k", "k": int(k), "effective_k": int(k),
                 "silhouette": sil, "davies_bouldin": db, "calinski_harabasz": ch,
                 "primary_model": "kmeans",
                 "clustering_strategy": f"kmeans_on_umap2d (research_k={k})",
                 "embedding": "umap2d", "trait_names": list(meta.get("trait_names") or [])})
    with open(meta_p, "w") as fh: json.dump(meta, fh, indent=2)
    return tid, old, sil, k


if __name__ == "__main__":
    for tid, k in PLAN:
        try:
            t, old, new, kk = retrain(tid, k)
            print(f"  {t:12s} k={kk} sil {old:.4f} -> {new:.4f}  (+{new-old:.4f})")
        except Exception as e:
            import traceback; traceback.print_exc()
            print(f"  {tid:12s} ERR {e}")
