# Training

train_paper_pipeline.py rebuilds the clustering run behind the paper.
The original script for that run was not kept, so this is a reconstruction.
It was written from the parameters in backend/research/paper_results.json, the archived results in backend/models/_archive_paper_pipeline, and the earlier pipeline in git history.
It has not been run, so its output has not been compared with the archived results.

Each instrument is cleaned and scored with the published keys, then sampled to at most 15000 rows.
UMAP reduces the traits to 10 dimensions with n_neighbors 30, min_dist 0.0 and seed 42.
A variational Bayesian Gaussian mixture with a Dirichlet process prior is fitted at k_max 2 to 8, and the best silhouette is kept.
Components under 0.02 weight are treated as pruned.
K-means, Ward and Gaussian mixtures on the raw traits are the robustness comparison at k 2 to 5.

Run it with backend/.venv/bin/python training/train_paper_pipeline.py hexaco riasec.
With no names it runs all eleven instruments.
Results go to backend/models/_paper_pipeline_rerun, so the app's models are not touched.

The archived AMBI run used seven traits and the current scorer gives five, so AMBI will differ.
The Ward sample limit of 5000 is an assumption.

The app's own models come from backend/ml/train_offline.py and name_archetypes.py.
