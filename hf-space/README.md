---
title: Valence Psych Host
emoji: "\U0001F9E0"
colorFrom: gray
colorTo: indigo
sdk: docker
app_port: 7860
pinned: false
---

# Valence Psych Host

Specialty psychology LLM worker for the Valence platform (Layer B).

Serves four model keys over a tiny FastAPI contract, running GGUF quants via
llama.cpp on the free CPU tier:

| key           | served weights                                            |
|---------------|-----------------------------------------------------------|
| psyllm        | PsyLLM-8B Q4_K_M (eeleexx/PsyLLM-Q4_K_M-GGUF)             |
| psychocounsel | PsychoCounsel-Llama3-8B i1-IQ3_M (mradermacher)           |
| psycholex     | PsyLLM-4B Q4_K_M (mradermacher) — PsychoLex is gated/no GGUF, nearest open substitute |
| mentallama    | MentaLLaMA-chat-7B Q4_K_M (QuantFactory)                  |

Contract:

- `POST /infer`  `{prompt, max_new_tokens, temperature, model_key}` → `{text}`
- `POST /warm`   `{model_key}` → schedules a background load into RAM
- `GET  /health` → `{ok, loaded, available}`

All endpoints require the `X-Specialty-Secret` header matching the
`SPECIALTY_REGISTRY_SECRET` Space secret (health is exempt so wake probes work).

The Space sleeps when idle and wakes on any request — the Valence backend
(running on localhost) probes and warms it while a user is taking a test.
