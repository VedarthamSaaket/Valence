# Valence — Model vs. Research Audit (all 17 instruments)

**Generated 2026-06-15.** Our k + silhouette from `backend/models/_grand_audit_report.json`
(silhouette measured on the embedding the model clusters in, 15k subsample, seed 42).

## Important caveat on "research silhouette"
Silhouette is a **machine-learning** cluster-separation metric. Psychology papers
**almost never report it.** They report (a) the number of types/factors/profiles and
(b) their *own* fit metrics — for Latent Profile Analysis: BIC / aBIC / entropy /
% classified; for factor analysis: % variance explained, eigenvalues, fit indices.
So the "research silhouette" column is **n/r (not reported)** for every instrument —
this is expected, not a gap in the search. Compare on **k** and on **method**, not
on silhouette-vs-silhouette.

Also note: many of these instruments are **dimensional** (subscales/factors), not
**person-typologies**. For those, "research k" = number of subscales/factors, which is
a *dimension* count, not a *cluster-of-people* count. Flagged in the Type column.

---

## TIER A — clustered models (we run unsupervised clustering)

| # | Test (instrument) | Type | Research k | Research method / fit | Our k | Our silhouette | k match | Notes |
|---|---|---|---|---|---|---|---|---|
| 1 | **HEXACO** (HEXACO-PI-R) | person-types (debated) | **5** (LPA); 6 spectral; 7 (JP); **0** (Ashton&Lee) | LPA: BIC/entropy; Ashton&Lee: variance vs random → *no clear types* | 2 | 0.415 | ✗ (we<research) | Literature itself contests existence of types. Our k=2 = a low/high split; high silhouette but coarse |
| 2 | **16PF** (16PF-5) | person-types | **4** | Krug/Lounsbury Q-type factor analysis; 4 modal profiles classify ~⅔ subjects | **4** | 0.403 | ✓ | Retrained on UMAP-2D; research-k=4 was global silhouette max |
| 3 | **Dark Traits** (Dark Triad) | person-profiles | **4** (also 5) | LPA / LCA; AIC/BIC/CAIC | **4** | 0.457 | ✓ | benevolent → trait-specific → malevolent continuum |
| 4 | **Temperament** (FTI) | typology (theory) | **4** | Fisher neurochemical theory; MRI + large-sample distribution | **4** | 0.286 | ✓ | Explorer/Builder/Director/Negotiator |
| 5 | **Narcissism** (NPI-40) | factors (not clusters) | **3** (also 2/4/7) | PCA / parallel analysis; % variance | 3 | 0.641 | ✓ (vs 3-factor) | Ackerman 3-factor is modern standard; NPI is dimensional, our clusters approximate it |
| 6 | **Ambiversion** (AMBI, 7-trait) | Big-Five-derived | ~**5** | no canonical person-cluster paper (derived from FFM) | 2 | 0.397 | ✗ | No literature typology to comply with; treat as dimensional |
| 7 | **Humor Styles** (HSQ) | factors | **4** | Martin 2003 EFA/CFA; 4 humor-style factors | **4** | 0.363 | ✓ | Affiliative/Self-enhancing/Aggressive/Self-defeating |
| 8 | **Mindfulness** (KIMS) | factors | **4** | Baer 2004 EFA; 4 facets | **4** | 0.316 | ✓ | Observe/Describe/Act-aware/Accept |
| 9 | **Conspiracy** (GCBS) | factors | **5** | Brotherton 2013 EFA/CFA; 5 factors | 2 | 0.922 | ✗ (we<research) | BGM collapsed to 2 (low/high believer). Silhouette inflated by degenerate split — **needs refit to k=5** |
| 10 | **Aesthetics** (art-pref) | style factors | **5** (Rentfrow); 6 viewer-clusters | Rentfrow EFA 5 artistic-style factors | **5** | 0.116 | ✓ | k matches but separation weak — **candidate for UMAP-2D retrain** |
| 11 | **Interests** (RIASEC) | types (circumplex) | **6** | Holland; circular/hexagonal structure | **6** | 0.359 | ✓ | Retrained UMAP-2D. True natural split is k=2 by elevation (sil 0.42); kept k=6 for research fidelity |
| 12 | **Attachment** (ECR-style) | 4 types / 2 dims | **4** types (**2** dims) | Bartholomew 1991; self×other 2×2 | **4** | 0.243 | ✓ | Below floor — **candidate for UMAP-2D retrain** |
| 13 | **Mood & Stress** (DASS-21) | severity profiles | **3** (low/mod/high) | LPA; 3 severity classes typical | 4 | 0.456 | ≈ (we=4 vs 3) | 3 subscales × severity; our 4th cluster is a mixed-severity group |

## TIER B — LLM-only (no clustering; STATIC_NORMS Gaussian percentiles + LLM archetype)

| # | Test (instrument) | Type | Research k (dims) | Research basis | Our handling | Notes |
|---|---|---|---|---|---|---|
| 14 | **Values** (PVQ) | values (circumplex) | **10** basic / **4** higher-order / **2** dims | Schwartz; MDS circumplex | 10-dim STATIC_NORMS | No dataset → no clustering; percentiles from published μ/σ |
| 15 | **Core Needs** (BPNSS) | needs | **3** | Deci & Ryan SDT; autonomy/competence/relatedness | 3-dim STATIC_NORMS | LLM archetype over 3 needs |
| 16 | **Wellbeing** (WHO-5) | unidimensional | **1** | WHO-5 single wellbeing factor | 1-dim STATIC_NORMS | Single score → severity bands |
| 17 | **Personality Pathology** (PID-5-BF) | domains | **5** | Krueger 2012; 5 maladaptive domains | 5-dim STATIC_NORMS | No dataset → LLM clustering over 5 domains |

---

## Compliance scorecard

| Verdict | Count | Tests |
|---|---|---|
| ✓ k matches research | 9 | 16PF, Dark Traits, FTI, NPI, HSQ, KIMS, Aesthetics, RIASEC, Attachment |
| ≈ close (±1) | 1 | DASS (4 vs 3) |
| ✗ our k below research | 3 | HEXACO (2 vs 5), GCBS (2 vs 5), Ambiversion (2 vs ~5) |
| Tier B (dimensional, no clustering) | 4 | PVQ, BPNSS, WHO-5, PID-5-BF |

## Proven silhouette lift from research-k compliance (the two we just fixed)

| Test | Off-research-k (before) | Research-k (after) | Lift | Research k |
|---|---|---|---|---|
| **16PF** | 0.079 (free BGM ~k6, raw traits) | **0.403** (k=4) | **+0.324** | 4 |
| **RIASEC** | 0.037 (free BGM k6, raw traits) | **0.356** (k=6) | **+0.319** | 6 |

Sweep confirms 16PF research-k=4 is the **global** silhouette maximum across k=2..8.

## Outstanding action items (mismatches worth fixing)
- **GCBS**: force k=5 (Brotherton) — BGM collapsed to 2; current 0.922 is a degenerate two-blob split, not 5 real factors.
- **HEXACO**: force k=5 (LPA standard) — currently k=2. Note literature genuinely disputes whether HEXACO types exist (Ashton & Lee found none).
- **Ambiversion (AMBI)**: no research typology exists → either keep dimensional or drop; cannot "comply" with a non-existent paper k.
- **Aesthetics / Attachment**: k already matches research but silhouette below floor → UMAP-2D retrain (same fix that rescued 16PF/RIASEC).
