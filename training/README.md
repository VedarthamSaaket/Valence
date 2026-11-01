# Training

train_paper_pipeline.py is the clustering pipeline behind the paper.
The parameters are in backend/research/paper_results.json.

Each instrument is cleaned and scored with the published keys, then sampled to at most 15000 rows.
UMAP reduces the traits to 10 dimensions with n_neighbors 30, min_dist 0.0 and seed 42.
A variational Bayesian Gaussian mixture with a Dirichlet process prior is fitted at k_max 2 to 8, and the best silhouette is kept.
Components under 0.02 weight are treated as pruned.
K-means, Ward and Gaussian mixtures on the raw traits are the robustness comparison at k 2 to 5.

Run it with backend/.venv/bin/python training/train_paper_pipeline.py hexaco riasec.
With no names it runs all eleven instruments.
Results go to backend/models/_paper_pipeline_rerun, so the app's models are not touched.

The AMBI scorer gives five traits where the paper used seven.
The Ward comparison is limited to 5000 rows.

The app's own models come from backend/ml/train_offline.py and name_archetypes.py.
