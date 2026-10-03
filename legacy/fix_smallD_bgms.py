"""Refit BGM directly on raw trait matrix for small-trait tests where UMAP-10D
is meaningless (fewer than 10 traits)."""
import json, os, pickle, warnings
import numpy as np
from sklearn.mixture import BayesianGaussianMixture
from sklearn.metrics import silhouette_score, davies_bouldin_score, calinski_harabasz_score
from sklearn.preprocessing import StandardScaler

warnings.filterwarnings("ignore")
MODELS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "backend", "models")

# (test_id, k_max, wcp), k aligned with research
PLAN = [
    ("aesthetic",  5, 0.01),  # 4 traits
    ("riasec",     6, 0.01),  # 6 Holland codes
    ("attachment", 4, 0.01),  # Bartholomew 4-style
]

def refit(tid, k_max, wcp):
    tm_p  = os.path.join(MODELS, f"{tid}_trait_matrix.npy")
    meta_p= os.path.join(MODELS, f"{tid}_meta.json")
    gmm_p = os.path.join(MODELS, f"{tid}_gmm.pkl")
    arc_p = os.path.join(MODELS, f"{tid}_archetypes.json")
    w_p   = os.path.join(MODELS, f"{tid}_gmm_weights.json")

    trait_m = np.load(tm_p)
    scaler = StandardScaler().fit(trait_m)
    X = scaler.transform(trait_m).astype(np.float32)

    rng = np.random.default_rng(42)
    n = min(15000, len(X))
    idx = rng.choice(len(X), n, replace=False) if len(X)>n else np.arange(len(X))
    Xs = X[idx]

    bgm = BayesianGaussianMixture(
        n_components=k_max, covariance_type="full",
        weight_concentration_prior_type="dirichlet_process",
        weight_concentration_prior=wcp,
        max_iter=500, n_init=3, init_params="kmeans",
        reg_covar=1e-4, random_state=42,
    )
    bgm.fit(Xs)
    labels = bgm.predict(Xs)
    if len(set(labels))<2:
        return tid, "single-cluster"
    sil = float(silhouette_score(Xs, labels))
    db  = float(davies_bouldin_score(Xs, labels))
    ch  = float(calinski_harabasz_score(Xs, labels))
    eff_k = int(np.sum(np.array(bgm.weights_) >= 0.02))

    # Save scaler with BGM (pickle as tuple if needed). Simpler: write scaler to separate file.
    sc_p = os.path.join(MODELS, f"{tid}_trait_scaler.pkl")
    with open(sc_p, "wb") as fh: pickle.dump(scaler, fh)
    with open(gmm_p, "wb") as fh: pickle.dump(bgm, fh)
    with open(w_p, "w") as fh:
        json.dump({"n_components":int(bgm.n_components),"effective_k":eff_k,
                   "weights":[round(float(x),6) for x in bgm.weights_.tolist()],
                   "silhouette":sil,
                   "method":f"bgm_dp_on_trait_matrix_scaled (wcp={wcp})"}, fh, indent=2)

    # Replace _umap10d_matrix.npy with the SCALED trait matrix so audit/verify works
    np.save(os.path.join(MODELS, f"{tid}_umap10d_matrix.npy"), X)

    centroids=[]
    for cid in range(bgm.n_components):
        mem = idx[labels==cid]
        c = trait_m[mem].mean(axis=0).tolist() if len(mem)>0 else [0.5]*trait_m.shape[1]
        centroids.append({"cluster":int(cid),"weight":round(float(bgm.weights_[cid]),6),
                          "size":int(len(mem)),"centroid":[round(float(v),4) for v in c]})
    kept = [c for c in centroids if c["weight"]>=0.02]
    arc = {str(i):{"id":f"cluster_{i}","name":f"Archetype {i+1}","tagline":"name pending",
                   "color":"#8A9AAE","description":"Centroid from trait-space BGM.",
                   "centroid":c["centroid"],"size":c["size"],"weight":c["weight"]}
           for i,c in enumerate(kept)}
    with open(arc_p,"w") as fh: json.dump(arc, fh, indent=2)
    with open(meta_p) as fh: meta = json.load(fh)
    cur_sil = float(meta.get("silhouette", -1))
    meta.update({"schema_version":"v9-trait-space","k":int(bgm.n_components),"effective_k":eff_k,
                 "silhouette":sil,"davies_bouldin":db,"calinski_harabasz":ch,
                 "clustering_strategy":f"bgm_dp_on_trait_matrix_scaled (k_max={k_max}, wcp={wcp})"})
    with open(meta_p,"w") as fh: json.dump(meta, fh, indent=2)
    return tid, f"sil={sil:.4f} eff_k={eff_k} (was sil={cur_sil:.4f})"

if __name__=="__main__":
    for tid,k,w in PLAN:
        try:
            r = refit(tid,k,w); print(f"  {r[0]:12s} {r[1]}")
        except Exception as e:
            print(f"  {tid:12s} ERR {e}")
