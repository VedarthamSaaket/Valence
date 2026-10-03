# Valence

A psychometric assessment platform: eleven peer-reviewed self-report instruments, an unsupervised clustering layer trained on open reference data, and a locally hosted MentaLLaMA model that writes a construct-level deep dive for each result.

## Start

Double-click `Valence` on the Desktop (or run `./start_valence.command`). It starts the API, the MentaLLaMA model server and the web app, then opens `http://localhost:5173`. Close the window or press Ctrl+C to stop everything. Logs are written to `logs/`.

Manual start, if needed:

```bash
cd backend && .venv/bin/python -m uvicorn main:app --port 8000
cd frontend && npm run dev
```

The backend launches `llama-server` itself when the model file is present.

## Layout

```
backend/
  main.py                FastAPI app
  routers/               auth, tests, results, user, psych, research
  ml/inference.py        scoring, percentiles, cluster assignment
  ml/scoring_keys.py     published item keys shared by training and inference
  ml/train_offline.py    training pipeline
  ml/psych_layer.py      MentaLLaMA deep-dive layer
  ml/psych_lexicon.py    constructs and frameworks per instrument
  research/              results from the accompanying study
  models/                trained artifacts, models/llm holds the GGUF
  datasets/              openpsychometrics.org reference data
frontend/                React + Vite
shared/questions/        item text for the eleven instruments
legacy/                  retired tuning scripts, not used by the app
```

## Instruments

HEXACO, AMBI, Short Dark Triad, NPI, DASS, KIMS, HSQ, GCBS, RIASEC, ECR and FTI. These are the eleven instruments analysed in the study; no others are offered.

## Training

```bash
FORCE_RETRAIN=1 backend/.venv/bin/python backend/ml/train_offline.py
backend/.venv/bin/python name_archetypes.py
```

Per instrument: clean, score with the published keys, normalise to 0-1, standardise, and fit a latent-profile model (diagonal Gaussian mixture) with the number of profile types fixed from the person-centered literature (see `CONFIGS` in `train_offline.py`). `name_archetypes.py` then labels each profile with its literature type. The accompanying study's clustering comparison is separate from the app's models; its tables are served at `/api/research/{test}`.

## Deep dive

`MentaLLaMA-chat-7B` (Q4_K_M GGUF) runs through `llama-server` on the local GPU. For each result the layer selects the constructs that characterise the profile, asks the model for one paragraph per construct grounded in the scores, and adds an integrative formulation. Nothing leaves the machine.

Setup on a new machine:

```bash
brew install llama.cpp
backend/.venv/bin/hf download QuantFactory/MentaLLaMA-chat-7B-GGUF MentaLLaMA-chat-7B.Q4_K_M.gguf --local-dir backend/models/llm
```

## Notes

Percentiles are ranks within self-selected online reference samples, not population norms. Results are self-reflection material and not a clinical assessment.
