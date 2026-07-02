"""
Refit BGM on the 10D UMAP matrix for tests whose current BGM was trained on raw
trait space (2-3 features), these can't discriminate personas.

Also refit NPI and GCBS with tighter k_max + lower wcp to drop effective_k toward
the research-supported range without losing silhouette quality.
"""
import json, os, pickle, warnings
import numpy as np
from sklearn.mixture import BayesianGaussianMixture
from sklearn.metrics import silhouette_score, davies_bouldin_score, calinski_harabasz_score

warnings.filterwarnings("ignore")

MODELS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "backend", "models")

# (test_id, k_max, wcp)
PLAN = [
    ("npi",        5, 0.005, True),   # force: research k=5
]

def refit(tid, k_max, wcp, force_arg=False):
    emb_p = os.path.join(MODELS, f"{tid}_umap10d_matrix.npy")
    tm_p  = os.path.join(MODELS, f"{tid}_trait_matrix.npy")
    meta_p= os.path.join(MODELS, f"{tid}_meta.json")
    gmm_p = os.path.join(MODELS, f"{tid}_gmm.pkl")
    arc_p = os.path.join(MODELS, f"{tid}_archetypes.json")
    w_p   = os.path.join(MODELS, f"{tid}_gmm_weights.json")

    if not all(os.path.exists(p) for p in (emb_p, tm_p, meta_p)):
        return tid, "skip-missing"
    emb = np.load(emb_p).astype(np.float32)
    trait_m = np.load(tm_p)
    rng = np.random.default_rng(42)
    n = min(15000, len(emb))
    idx = rng.choice(len(emb), n, replace=False) if len(emb)>n else np.arange(len(emb))
    X = emb[idx]

    bgm = BayesianGaussianMixture(
        n_components=k_max, covariance_type="full",
        weight_concentration_prior_type="dirichlet_process",
        weight_concentration_prior=wcp,
        max_iter=500, n_init=3, init_params="kmeans",
        reg_covar=1e-4, random_state=42,
    )
    bgm.fit(X)
    labels = bgm.predict(X)
    if len(set(labels))<2:
        return tid, "single-cluster"
    sil = float(silhouette_score(X, labels))
    db  = float(davies_bouldin_score(X, labels))
    ch  = float(calinski_harabasz_score(X, labels))
    eff_k = int(np.sum(np.array(bgm.weights_) >= 0.02))

    # Load current sil
    with open(meta_p) as fh: meta = json.load(fh)
    cur_sil = float(meta.get("silhouette", -1))

    # Need to refit BGM if current is on wrong features regardless of sil
    with open(gmm_p, "rb") as fh:
        cur = pickle.load(fh)
    cur_features = cur.means_.shape[1]
    force = cur_features != 10 or force_arg

    if not force and sil < cur_sil + 0.01:
        return tid, f"kept cur_sil={cur_sil:.4f} new_sil={sil:.4f} cur_k={cur.n_components}"

    # Persist
    with open(gmm_p, "wb") as fh: pickle.dump(bgm, fh)
    with open(w_p, "w") as fh:
        json.dump({"n_components": int(bgm.n_components), "effective_k": eff_k,
                   "weights":[round(float(x),6) for x in bgm.weights_.tolist()],
                   "silhouette": sil,
                   "method": f"bayesian_gmm_dp_refit10d (wcp={wcp})"}, fh, indent=2)
    # Centroids in raw trait space
    centroids=[]
    for cid in range(bgm.n_components):
        members = idx[labels==cid]
        c = trait_m[members].mean(axis=0).tolist() if len(members)>0 else [0.5]*trait_m.shape[1]
        centroids.append({"cluster":int(cid),"weight":round(float(bgm.weights_[cid]),6),
                          "size":int(len(members)),"centroid":[round(float(v),4) for v in c]})
    kept = [c for c in centroids if c["weight"]>=0.02]
    arc = {str(i):{"id":f"cluster_{i}","name":f"Archetype {i+1}","tagline":"name pending",
                   "color":"#8A9AAE","description":"Centroid from refit BGM.",
                   "centroid":c["centroid"],"size":c["size"],"weight":c["weight"]}
           for i,c in enumerate(kept)}
    with open(arc_p,"w") as fh: json.dump(arc, fh, indent=2)
    meta.update({"schema_version":"v8-refit10d","k":int(bgm.n_components),"effective_k":eff_k,
                 "silhouette":sil,"davies_bouldin":db,"calinski_harabasz":ch,
                 "clustering_strategy":f"bayesian_gmm_dp_refit10d (k_max={k_max}, wcp={wcp})"})
    with open(meta_p,"w") as fh: json.dump(meta, fh, indent=2)
    return tid, f"REFIT sil={sil:.4f} eff_k={eff_k} (was sil={cur_sil:.4f} feats={cur_features})"

if __name__=="__main__":
    for entry in PLAN:
        tid,k,w = entry[0],entry[1],entry[2]
        force = entry[3] if len(entry)>3 else False
        try:
            r = refit(tid,k,w,force)
            print(f"  {r[0]:12s} {r[1]}")
        except Exception as e:
            print(f"  {tid:12s} ERR {e}")
