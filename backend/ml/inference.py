import numpy as np
import json
import os
import csv
import math
import pickle
from datetime import datetime
from typing import Dict, List, Any, Optional

MODELS_DIR   = os.path.join(os.path.dirname(__file__), "../models")
DATASETS_DIR = os.path.join(os.path.dirname(__file__), "../datasets")

DATASET_FOLDER_MAP = {
    # Tier A: ML pipeline (have raw dataset for training)
    "hexaco":     "HEXACO",
    "sixteenpf":  "16PF/16PF",
    "darktriad":  "SD3",
    "attachment": "ECR-data-1March2018",
    "riasec":     "RIASEC_data12Dec2018",
    "aesthetic":  "APS_data",
    "hsq":        "HSQ",
    "kims":       "KIMS",
    "fti":        "FTI",
    "dass":       "DASS_data_21.02.19",
    "npi":        "NPI",
    "ambi":       "AMBI_data_Nov2019",
    "gcbs":       "GCBS",
    # Tier B: LLM clustering (no dataset, archetypes generated at inference time)
    "pvq":   None,
    "bpnss": None,
    "who5":  None,
    "pid5":  None,
}

def score_hexaco(responses: Dict[str, int]) -> Dict[str, float]:
    """HEXACO-PI-R 240-item scoring. 6 broad factors aggregated from 4 facets x 10 items each."""
    def safe(key): return responses.get(key, 4)
    facet_prefixes = {
        "Honesty-Humility":  ["HSinc", "HFair", "HGree", "HMode"],
        "Emotionality":      ["EFear", "EAnxi", "EDepe", "ESent"],
        "Extraversion":      ["XExpr", "XSoci", "XSocB", "XLive"],
        "Agreeableness":     ["AForg", "AGent", "AFlex", "APati"],
        "Conscientiousness": ["COrga", "CDili", "CPerf", "CPrud"],
        "Openness":          ["OAesA", "OInqu", "OCrea", "OUnco"],
    }
    result = {}
    for trait, prefixes in facet_prefixes.items():
        items = [safe(f"{p}{i}") for p in prefixes for i in range(1, 11)]
        result[trait] = round((float(np.mean(items)) - 1) / 6, 4)
    return result


def score_sixteenpf(responses: Dict[str, int]) -> Dict[str, float]:
    def safe(key): return responses.get(key, 3)

    factor_map = {
        "Warmth":             [f"A{i}" for i in range(1, 11)],
        "Reasoning":          [f"B{i}" for i in range(1, 14)],
        "Stability":          [f"C{i}" for i in range(1, 11)],
        "Dominance":          [f"D{i}" for i in range(1, 11)],
        "Liveliness":         [f"E{i}" for i in range(1, 11)],
        "Rule-Consciousness": [f"F{i}" for i in range(1, 11)],
        "Social-Boldness":    [f"G{i}" for i in range(1, 11)],
        "Sensitivity":        [f"H{i}" for i in range(1, 11)],
        "Vigilance":          [f"I{i}" for i in range(1, 11)],
        "Abstractedness":     [f"J{i}" for i in range(1, 11)],
        "Privateness":        [f"K{i}" for i in range(1, 11)],
        "Apprehension":       [f"L{i}" for i in range(1, 11)],
        "Openness-to-Change": [f"M{i}" for i in range(1, 11)],
        "Self-Reliance":      [f"N{i}" for i in range(1, 11)],
        "Perfectionism":      [f"O{i}" for i in range(1, 11)],
        "Tension":            [f"P{i}" for i in range(1, 11)],
    }

    result = {}
    for trait, keys in factor_map.items():
        vals = [safe(k) for k in keys]
        result[trait] = round((np.mean(vals) - 1) / 4, 4)
    return result


def score_darktriad(responses: Dict[str, int]) -> Dict[str, float]:
    def safe(key): return responses.get(key, 3)
    def r(x): return 6 - x

    mach = np.mean([safe(f"M{i}") for i in range(1, 10)])
    narc = np.mean([safe("N1"), r(safe("N2")), safe("N3"), safe("N4"),
                    safe("N5"), r(safe("N6")), safe("N7"), r(safe("N8")), safe("N9")])
    psyc = np.mean([safe("P1"), r(safe("P2")), safe("P3"), safe("P4"),
                    safe("P5"), safe("P6"), r(safe("P7")), safe("P8"), safe("P9")])

    def norm(x): return round((x - 1) / 4, 4)
    return {
        "Machiavellianism": norm(mach),
        "Narcissism":       norm(narc),
        "Psychopathy":      norm(psyc),
    }


def score_dass(responses: Dict[str, int]) -> Dict[str, float]:
    def safe(key): return responses.get(key, 1)

    depression_keys = [f"D{i}" for i in range(1, 15)]
    anxiety_keys    = [f"A{i}" for i in range(1, 15)]
    stress_keys     = [f"S{i}" for i in range(1, 15)]

    dep_raw = sum(safe(k) - 1 for k in depression_keys)
    anx_raw = sum(safe(k) - 1 for k in anxiety_keys)
    str_raw = sum(safe(k) - 1 for k in stress_keys)

    return {
        "Depression": round(min(dep_raw / 42, 1.0), 4),
        "Anxiety":    round(min(anx_raw / 42, 1.0), 4),
        "Stress":     round(min(str_raw / 42, 1.0), 4),
    }


def score_hsq(responses: Dict[str, int]) -> Dict[str, float]:
    """Humor Styles Questionnaire (Martin et al. 2003), 4 styles, 32 items, 5-point Likert."""
    def safe(key): return responses.get(key, 3)
    def r(x): return 6 - x
    affiliative = float(np.mean([
        r(safe("Q1")), safe("Q5"), r(safe("Q9")), safe("Q13"),
        r(safe("Q17")), safe("Q21"), r(safe("Q25")), r(safe("Q29")),
    ]))
    self_enhancing = float(np.mean([safe(f"Q{i}") for i in [2, 6, 10, 14, 18, 22, 26, 30]]))
    aggressive     = float(np.mean([safe(f"Q{i}") for i in [3, 7, 11, 15, 19, 23, 27, 31]]))
    self_defeating = float(np.mean([safe(f"Q{i}") for i in [4, 8, 12, 16, 20, 24, 28, 32]]))
    norm = lambda x: round((x - 1) / 4, 4)
    return {
        "Affiliative":    norm(affiliative),
        "Self-Enhancing": norm(self_enhancing),
        "Aggressive":     norm(aggressive),
        "Self-Defeating": norm(self_defeating),
    }


def score_kims(responses: Dict[str, int]) -> Dict[str, float]:
    """Kentucky Inventory of Mindfulness Skills (Baer et al. 2004), 4 facets."""
    def safe(key): return responses.get(key, 3)
    def r(x): return 6 - x
    observing  = float(np.mean([safe(f"Q{i}") for i in [1, 5, 9, 13, 17, 21, 25, 29, 33, 37, 39]]))
    describing = float(np.mean([
        safe("Q2"), safe("Q6"), safe("Q10"),
        r(safe("Q14")), r(safe("Q18")), r(safe("Q22")),
        safe("Q26"), safe("Q30"), safe("Q34"),
    ]))
    acting = float(np.mean([
        r(safe("Q3")), safe("Q7"), r(safe("Q11")), safe("Q15"), safe("Q19"),
        r(safe("Q23")), r(safe("Q27")), r(safe("Q31")), r(safe("Q35")), safe("Q38"),
    ]))
    accepting = float(np.mean([
        r(safe("Q4")), r(safe("Q8")), r(safe("Q12")), r(safe("Q16")),
        r(safe("Q20")), r(safe("Q24")), r(safe("Q28")), r(safe("Q32")), r(safe("Q36")),
    ]))
    norm = lambda x: round((x - 1) / 4, 4)
    return {
        "Observing":                  norm(observing),
        "Describing":                 norm(describing),
        "Acting with Awareness":      norm(acting),
        "Accepting without Judgment": norm(accepting),
    }


def score_fti(responses: Dict[str, int]) -> Dict[str, float]:
    """Fisher Temperament Inventory (Brown, Acevedo & Fisher 2013), 4 temperaments x 14 items."""
    def safe(key): return responses.get(key, 2.5)
    explorer   = float(np.mean([safe(f"Q{i}") for i in range(1, 15)]))
    builder    = float(np.mean([safe(f"Q{i}") for i in range(15, 29)]))
    director   = float(np.mean([safe(f"Q{i}") for i in range(29, 43)]))
    negotiator = float(np.mean([safe(f"Q{i}") for i in range(43, 57)]))
    norm = lambda x: round((x - 1) / 3, 4)
    return {
        "Explorer":   norm(explorer),
        "Builder":    norm(builder),
        "Director":   norm(director),
        "Negotiator": norm(negotiator),
    }


# NPI scoring keys (Raskin & Terry 1988). Value-per-Q that scores as narcissistic.
_NPI_NARC_KEY = {
    1: 1, 2: 1, 3: 1, 4: 2, 5: 2, 6: 1, 7: 2, 8: 1, 9: 2, 10: 2,
    11: 1, 12: 1, 13: 1, 14: 1, 15: 2, 16: 1, 17: 2, 18: 2, 19: 2, 20: 2,
    21: 1, 22: 2, 23: 2, 24: 1, 25: 1, 26: 2, 27: 1, 28: 2, 29: 1, 30: 1,
    31: 1, 32: 2, 33: 1, 34: 1, 35: 2, 36: 1, 37: 1, 38: 1, 39: 1, 40: 2,
}
_NPI_FACETS = {
    "Authority":        [1, 8, 10, 11, 12, 32, 33, 36],
    "Self-Sufficiency": [17, 21, 22, 31, 34, 39],
    "Superiority":      [4, 9, 26, 37, 40],
    "Exhibitionism":    [2, 3, 7, 20, 28, 30, 38],
    "Exploitativeness": [6, 13, 16, 23, 35],
    "Vanity":           [15, 19, 29],
    "Entitlement":      [5, 14, 18, 24, 25, 27],
}


def score_npi(responses: Dict[str, int]) -> Dict[str, float]:
    """Narcissistic Personality Inventory (Raskin & Terry 1988), 7 facets, forced-choice."""
    def safe(key): return responses.get(key, 0)
    result = {}
    for facet, qnums in _NPI_FACETS.items():
        score = sum(1 for q in qnums if safe(f"Q{q}") == _NPI_NARC_KEY[q])
        result[facet] = round(score / len(qnums), 4)
    return result


def score_ambi(responses: Dict[str, int]) -> Dict[str, float]:
    """
    Analog to Multiple Broadband Inventories (Yarkoni 2010), 181 items mapping to 200 IPIP scales.
    Phase B placeholder: 7 broad domains via item-range aggregation.
    Phase F replaces with full 200-scale scoring keys from ipip.ori.org/AMBIScoringKeys.htm.
    """
    def safe(key): return responses.get(key, 4)
    items = [safe(f"Q{i}") for i in range(1, 182)]
    chunks = {
        "Affect Regulation":  items[0:26],
        "Social Drive":       items[26:52],
        "Conscientiousness":  items[52:78],
        "Openness":           items[78:104],
        "Agreeableness":      items[104:130],
        "Energy Drive":       items[130:156],
        "Identity Coherence": items[156:181],
    }
    norm = lambda x: round((x - 1) / 6, 4)
    return {k: norm(float(np.mean(v))) for k, v in chunks.items()}


def score_gcbs(responses: Dict[str, int]) -> Dict[str, float]:
    """Generic Conspiracist Beliefs Scale (Brotherton, French & Pickering 2013), 5 factors x 3 items."""
    def safe(key): return responses.get(key, 3)
    factors = {
        "Government Malfeasance":     [1, 6, 11],
        "Malevolent Global":          [2, 7, 12],
        "Extraterrestrial Coverup":   [3, 8, 13],
        "Personal Wellbeing Threats": [4, 9, 14],
        "Control of Information":     [5, 10, 15],
    }
    norm = lambda x: round((x - 1) / 4, 4)
    return {f: norm(float(np.mean([safe(f"Q{i}") for i in qs]))) for f, qs in factors.items()}


# Schwartz PVQ-21 value mapping (ESS Round 1)
_PVQ_VALUES = {
    "Self-Direction": [1, 11],
    "Power":          [2, 17],
    "Universalism":   [3, 8, 19],
    "Achievement":    [4, 13],
    "Security":       [5, 14],
    "Stimulation":    [6, 15],
    "Conformity":     [7, 16],
    "Tradition":      [9, 20],
    "Hedonism":       [10, 21],
    "Benevolence":    [12, 18],
}


def score_pvq(responses: Dict[str, int]) -> Dict[str, float]:
    """Schwartz Portrait Values Questionnaire 21-item (ESS Round 1).
    Scale: 1=very much like me, 6=not like me at all. Reversed so higher = more like value."""
    def safe(key): return responses.get(key, 4)
    norm = lambda x: round((6 - x) / 5, 4)
    return {v: norm(float(np.mean([safe(f"Q{i}") for i in qs]))) for v, qs in _PVQ_VALUES.items()}


# BPNSS (Gagne 2003) subscales: (item_num, direction) where -1 means reverse
_BPNSS_AUTONOMY    = [(1, 1), (4, -1), (8, 1), (11, -1), (14, 1), (17, 1), (20, -1)]
_BPNSS_COMPETENCE  = [(3, -1), (5, 1), (10, 1), (13, 1), (15, -1), (19, -1)]
_BPNSS_RELATEDNESS = [(2, 1), (6, 1), (7, -1), (9, 1), (12, 1), (16, -1), (18, -1), (21, 1)]


def score_bpnss(responses: Dict[str, int]) -> Dict[str, float]:
    """Basic Psychological Needs Satisfaction (Gagne 2003 adaptation of Deci & Ryan SDT), 7-point Likert."""
    def safe(key): return responses.get(key, 4)
    def sub(spec):
        vals = []
        for q, direction in spec:
            v = safe(f"Q{q}")
            vals.append(v if direction == 1 else (8 - v))
        return float(np.mean(vals))
    norm = lambda x: round((x - 1) / 6, 4)
    return {
        "Autonomy":    norm(sub(_BPNSS_AUTONOMY)),
        "Competence":  norm(sub(_BPNSS_COMPETENCE)),
        "Relatedness": norm(sub(_BPNSS_RELATEDNESS)),
    }


def score_who5(responses: Dict[str, int]) -> Dict[str, float]:
    """WHO-5 Wellbeing Index. 5 items rated 0 to 5, raw sum x 4 yields 0 to 100. Returns 0 to 1."""
    def safe(key): return responses.get(key, 3)
    raw = sum(safe(f"Q{i}") for i in range(1, 6))
    return {"Wellbeing": round(raw * 4 / 100, 4)}


# PID-5-BF (Krueger et al. 2012) 5 personality trait domains, 5 items each
_PID5_DOMAINS = {
    "Disinhibition":        [1, 2, 3, 5, 6],
    "Detachment":           [4, 13, 14, 16, 18],
    "Psychoticism":         [7, 12, 21, 23, 24],
    "Negative Affectivity": [8, 9, 10, 11, 15],
    "Antagonism":           [17, 19, 20, 22, 25],
}


def score_pid5(responses: Dict[str, int]) -> Dict[str, float]:
    """Personality Inventory for DSM-5 Brief Form (Krueger et al. 2012). 25 items, 0 to 3 Likert."""
    def safe(key): return responses.get(key, 1)
    norm = lambda x: round(x / 3, 4)
    return {d: norm(float(np.mean([safe(f"Q{i}") for i in qs]))) for d, qs in _PID5_DOMAINS.items()}


def score_aesthetic(responses: Dict[str, int]) -> Dict[str, float]:
    def safe(key): return responses.get(key, 3)

    groups = {
        "Intense":     [f"RA{i}" for i in range(1, 9)],
        "Mainstream":  [f"LP{i}" for i in range(1, 9)],
        "Traditional": [f"MF{i}" for i in range(1, 9)],
        "Visual":      [f"V{i}"  for i in range(1, 7)],
    }
    return {
        t: round((np.mean([safe(k) for k in keys]) - 1) / 4, 4)
        for t, keys in groups.items()
    }


def score_riasec(responses: Dict[str, int]) -> Dict[str, float]:
    def safe(key): return responses.get(key, 3)

    groups = {
        "Realistic":     [f"R{i}" for i in range(1, 9)],
        "Investigative": [f"I{i}" for i in range(1, 9)],
        "Artistic":      [f"A{i}" for i in range(1, 9)],
        "Social":        [f"S{i}" for i in range(1, 9)],
        "Enterprising":  [f"E{i}" for i in range(1, 9)],
        "Conventional":  [f"C{i}" for i in range(1, 9)],
    }
    return {
        t: round((np.mean([safe(k) for k in keys]) - 1) / 4, 4)
        for t, keys in groups.items()
    }


def score_attachment(responses: Dict[str, int]) -> Dict[str, float]:
    def safe(key): return responses.get(key, 4)

    anx_keys = [f"ECR{i}" for i in range(1,  19)]
    avo_keys = [f"ECR{i}" for i in range(19, 37)]

    anxiety_score   = np.mean([safe(k) for k in anx_keys])
    avoidance_score = np.mean([safe(k) for k in avo_keys])
    secure_score    = round(1.0 - ((anxiety_score - 1) / 6 + (avoidance_score - 1) / 6) / 2, 4)

    return {
        "Anxious":  round((anxiety_score  - 1) / 6, 4),
        "Avoidant": round((avoidance_score - 1) / 6, 4),
        "Secure":   max(0.0, secure_score),
    }


SCORERS = {
    # Tier A (ML pipeline)
    "hexaco":     score_hexaco,
    "sixteenpf":  score_sixteenpf,
    "darktriad":  score_darktriad,
    "dass":       score_dass,
    "aesthetic":  score_aesthetic,
    "riasec":     score_riasec,
    "attachment": score_attachment,
    "hsq":        score_hsq,
    "kims":       score_kims,
    "fti":        score_fti,
    "npi":        score_npi,
    "ambi":       score_ambi,
    "gcbs":       score_gcbs,
    # Tier B (LLM clustering, scoring only for now)
    "pvq":   score_pvq,
    "bpnss": score_bpnss,
    "who5":  score_who5,
    "pid5":  score_pid5,
}

def save_response_to_dataset(test_id: str, raw_responses: Dict[str, int]) -> None:
    folder_name = DATASET_FOLDER_MAP.get(test_id)
    if not folder_name:
        return

    csv_path = os.path.join(DATASETS_DIR, folder_name, "data.csv")

    try:
        sorted_keys = sorted(raw_responses.keys())
        fieldnames  = ["timestamp"] + sorted_keys
        row         = {"timestamp": datetime.utcnow().isoformat(timespec="seconds")}
        row.update({k: raw_responses[k] for k in sorted_keys})

        file_exists = os.path.isfile(csv_path)
        with open(csv_path, "a", newline="", encoding="utf-8") as fh:
            writer = csv.DictWriter(fh, fieldnames=fieldnames, extrasaction="ignore")
            if not file_exists or os.path.getsize(csv_path) == 0:
                writer.writeheader()
            else:
                with open(csv_path, "r", newline="", encoding="utf-8") as rfh:
                    existing_header = next(csv.reader(rfh), None)
                if existing_header:
                    merged = existing_header + [k for k in fieldnames if k not in existing_header]
                    fh.seek(0, 2)
                    writer = csv.DictWriter(fh, fieldnames=merged, extrasaction="ignore")
            writer.writerow(row)
    except Exception:
        pass


# ---------------------------------------------------------------------------
# Model helpers
# ---------------------------------------------------------------------------

def load_model(test_id: str, model_type: str):
    path = os.path.join(MODELS_DIR, f"{test_id}_{model_type}.pkl")
    if not os.path.exists(path):
        return None
    with open(path, "rb") as f:
        return pickle.load(f)


def load_json(test_id: str, name: str):
    path = os.path.join(MODELS_DIR, f"{test_id}_{name}.json")
    if not os.path.exists(path):
        return None
    with open(path, encoding="utf-8") as f:
        return json.load(f)

# ---------------------------------------------------------------------------
# Published normative statistics for tests without raw datasets.
# (mu, sigma) on the 0 to 1 normalized scale used by our scorers.
# Used as second-tier fallback before the constant 50 fallback.
# ---------------------------------------------------------------------------
STATIC_NORMS: Dict[str, Dict[str, tuple]] = {
    # Schwartz Portrait Values 21 (PVQ-21).
    # Source: Schwartz 2012, "An Overview of the Schwartz Theory of Basic Values";
    #         Davidov, Schmidt & Schwartz 2008, Public Opinion Quarterly 72(3) (ESS pooled, n > 100,000).
    # Raw 1 to 6 (1 = very much like me), our scorer reverses so higher = more like value,
    # then normalizes (6 - raw) / 5 to 0 to 1. mu_norm = (6 - mu_raw) / 5; sigma_norm = sigma_raw / 5.
    "pvq": {
        "Self-Direction": (0.70, 0.18),
        "Power":          (0.34, 0.22),
        "Universalism":   (0.66, 0.18),
        "Achievement":    (0.54, 0.22),
        "Security":       (0.64, 0.18),
        "Stimulation":    (0.44, 0.22),
        "Conformity":     (0.54, 0.20),
        "Tradition":      (0.48, 0.20),
        "Hedonism":       (0.54, 0.22),
        "Benevolence":    (0.70, 0.18),
    },
    # Basic Psychological Needs Satisfaction Scale (BPNSS).
    # Source: Gagne 2003, Motivation and Emotion 27(3), n = 487;
    #         Johnston & Finney 2010, Contemporary Educational Psychology 35(4), n = 478.
    # Raw 1 to 7 Likert, our scorer normalizes (mu_raw - 1) / 6 to 0 to 1; sigma_norm = sigma_raw / 6.
    "bpnss": {
        "Autonomy":    (0.67, 0.15),
        "Competence":  (0.73, 0.15),
        "Relatedness": (0.75, 0.15),
    },
    # WHO-5 Wellbeing Index.
    # Source: Topp et al. 2015 systematic review, Psychotherapy and Psychosomatics 84(3), pooled n > 10,000;
    #         WHO-5 scoring manual (mean = 52/100, SD = 22/100 in general population).
    # Our scorer returns raw sum * 4 / 100, already on 0 to 1.
    "who5": {
        "Wellbeing": (0.52, 0.22),
    },
    # Personality Inventory for DSM-5 Brief Form (PID-5-BF).
    # Source: Anderson, Sellbom & Salekin 2018, Assessment 25(5), community n = 2461;
    #         Krueger et al. 2012, Psychological Medicine 42(9), n = 264.
    # Raw 0 to 3 Likert, our scorer normalizes raw / 3 to 0 to 1; sigma_norm = sigma_raw / 3.
    "pid5": {
        "Negative Affectivity": (0.32, 0.22),
        "Detachment":           (0.22, 0.18),
        "Antagonism":           (0.18, 0.17),
        "Disinhibition":        (0.23, 0.18),
        "Psychoticism":         (0.20, 0.20),
    },
}


def _norm_cdf(z: float) -> float:
    """Standard normal CDF via math.erf (no scipy dependency)."""
    return 0.5 * (1.0 + math.erf(z / math.sqrt(2.0)))


def calc_percentiles(test_id: str, trait_scores: Dict[str, float]) -> Dict[str, int]:
    """
    Percentile scoring with a three-tier fallback chain:
      1. Empirical: rank against the trained-model distribution (from raw dataset). Used by 13 tests.
      2. Static Gaussian: convert score to z and look up normal CDF against published mu, sigma.
         Used by pvq, bpnss, who5, pid5 (no raw dataset, validation-paper norms instead).
      3. Constant 50: only if neither source covers the trait. True last resort.
    """
    distributions = load_json(test_id, "distributions")
    static = STATIC_NORMS.get(test_id, {})

    percentiles: Dict[str, int] = {}
    for trait, score in trait_scores.items():
        if distributions and trait in distributions:
            arr = np.sort(np.array(distributions[trait]))
            pct = int(np.searchsorted(arr, score) / len(arr) * 100)
            percentiles[trait] = max(1, min(99, pct))
        elif trait in static:
            mu, sigma = static[trait]
            if sigma <= 0:
                percentiles[trait] = 50
            else:
                z = (float(score) - mu) / sigma
                pct = int(round(_norm_cdf(z) * 100))
                percentiles[trait] = max(1, min(99, pct))
        else:
            percentiles[trait] = 50
    return percentiles


def assign_archetype(test_id: str, trait_vector: List[float]) -> Optional[Dict]:
    kmeans     = load_model(test_id, "kmeans")
    archetypes = load_json(test_id, "archetypes")

    if kmeans and archetypes:
        try:
            model_dtype  = kmeans.cluster_centers_.dtype if hasattr(kmeans, "cluster_centers_") else np.float64
            # Pad or trim input to match the number of features the model was trained on
            n_features   = kmeans.cluster_centers_.shape[1]
            padded       = np.zeros(n_features, dtype=model_dtype)
            src          = np.array(trait_vector, dtype=model_dtype)
            padded[:min(len(src), n_features)] = src[:min(len(src), n_features)]
            cluster_id   = str(kmeans.predict(padded.reshape(1, -1))[0])
            result       = archetypes.get(cluster_id)
            if result:
                return result
        except Exception as e:
            print(f"[archetype] kmeans prediction failed ({e}), using fallback")

    return get_fallback_archetype(test_id, trait_vector)


def get_fallback_archetype(test_id: str, trait_vector: List[float]) -> Dict:
    fallbacks = {
        "hexaco": [
            {"id": "principled_steward",   "name": "The Principled Steward",     "tagline": "Honesty as the through-line",          "color": "#6B8CAE"},
            {"id": "warm_connector",       "name": "The Warm Connector",         "tagline": "Energy that lifts a room",             "color": "#AE8A6B"},
            {"id": "thoughtful_observer",  "name": "The Thoughtful Observer",    "tagline": "Inner depth, careful presence",        "color": "#6AAE8A"},
            {"id": "open_explorer",        "name": "The Open Explorer",          "tagline": "Curiosity as a way of life",           "color": "#8A6BAE"},
        ],
        "sixteenpf": [
            {"id": "warm_strategist",      "name": "The Warm Strategist",        "tagline": "People-focused, quietly precise",      "color": "#7A9AAE"},
            {"id": "bold_pioneer",         "name": "The Bold Pioneer",           "tagline": "Confident, driven, self-directed",     "color": "#AE7A6B"},
            {"id": "grounded_analyst",     "name": "The Grounded Analyst",       "tagline": "Systematic, steady, thorough",         "color": "#7AAE7A"},
            {"id": "expressive_idealist",  "name": "The Expressive Idealist",    "tagline": "Vivid, open, moved by possibility",    "color": "#AE7A9A"},
        ],
        "darktriad": [
            {"id": "strategic_pragmatist", "name": "The Strategic Pragmatist",   "tagline": "Calculated, clear-eyed, effective",   "color": "#8A7A9A"},
            {"id": "grounded_empath",      "name": "The Grounded Empath",        "tagline": "Warmth over strategy",                "color": "#7A9A8A"},
        ],
        "fti": [
            {"id": "the_explorer",         "name": "The Explorer",                "tagline": "Novelty, energy, curiosity",          "color": "#9A7AAE"},
            {"id": "the_builder",          "name": "The Builder",                 "tagline": "Order, loyalty, steady hands",        "color": "#6AAE8A"},
            {"id": "the_director",         "name": "The Director",                "tagline": "Decisive, analytical, ambitious",     "color": "#AE7A6B"},
            {"id": "the_negotiator",       "name": "The Negotiator",              "tagline": "Empathy, imagination, big picture",   "color": "#7A9AAE"},
        ],
        "npi": [
            {"id": "self_assured_lead",    "name": "The Self-Assured Lead",      "tagline": "Confident, visible, takes charge",    "color": "#AE7A8A"},
            {"id": "modest_collaborator",  "name": "The Modest Collaborator",    "tagline": "Quiet, deferential, team-first",      "color": "#7AAE8A"},
            {"id": "balanced_self_view",   "name": "The Balanced Self-View",     "tagline": "Confident without inflation",         "color": "#8A8AAE"},
        ],
        "ambi": [
            {"id": "energized_organizer",  "name": "The Energized Organizer",    "tagline": "Drive meets discipline",              "color": "#6B6B8A"},
            {"id": "reflective_artisan",   "name": "The Reflective Artisan",     "tagline": "Inner world, careful craft",          "color": "#8A6BAE"},
            {"id": "warm_companion",       "name": "The Warm Companion",         "tagline": "Connection as a default state",       "color": "#AE8A6B"},
            {"id": "freewheeling_seeker",  "name": "The Freewheeling Seeker",    "tagline": "Open, mobile, low-attachment",        "color": "#6BAE9A"},
        ],
        "pid5": [
            {"id": "steady_baseline",      "name": "The Steady Baseline",        "tagline": "Low intensity across the board",      "color": "#7A8AAE"},
            {"id": "intense_responder",    "name": "The Intense Responder",      "tagline": "Strong feelings, vivid reactions",    "color": "#AE7A7A"},
            {"id": "guarded_independent",  "name": "The Guarded Independent",    "tagline": "Distance as protection",              "color": "#6B8AAE"},
        ],
        "hsq": [
            {"id": "warm_humorist",        "name": "The Warm Humorist",          "tagline": "Humor that brings people in",         "color": "#AE9A6B"},
            {"id": "inner_resilient",      "name": "The Inner Resilient",        "tagline": "Self-amusement as a coping tool",     "color": "#6BAE9A"},
            {"id": "edgy_jester",          "name": "The Edgy Jester",            "tagline": "Sharp, sometimes cutting",            "color": "#8A6BAE"},
            {"id": "self_deprecator",      "name": "The Self-Deprecator",        "tagline": "Laughs at self to keep others close", "color": "#AE6B8A"},
        ],
        "kims": [
            {"id": "embodied_noticer",     "name": "The Embodied Noticer",       "tagline": "Aware of the body and senses",        "color": "#8AAE8A"},
            {"id": "articulate_observer",  "name": "The Articulate Observer",    "tagline": "Words come easily for inner states",  "color": "#7AAE9A"},
            {"id": "present_actor",        "name": "The Present Actor",          "tagline": "Fully in what you are doing",         "color": "#6BAE7A"},
            {"id": "accepting_witness",    "name": "The Accepting Witness",      "tagline": "Lets experience be what it is",       "color": "#9AAE6B"},
        ],
        "gcbs": [
            {"id": "low_skeptic",          "name": "The Trusting View",          "tagline": "Mostly takes official accounts at face value", "color": "#AE8A6B"},
            {"id": "selective_skeptic",    "name": "The Selective Skeptic",      "tagline": "Questions some, accepts others",      "color": "#9AAE6B"},
            {"id": "deep_skeptic",         "name": "The Deep Skeptic",           "tagline": "Sees hidden hands behind big events", "color": "#8A6B6B"},
        ],
        "aesthetic": [
            {"id": "raw_intensity",        "name": "The Raw Intensity",          "tagline": "Power and edge over polish",          "color": "#AE6B6B"},
            {"id": "warm_traditionalist",  "name": "The Warm Traditionalist",    "tagline": "Roots, texture, authenticity",        "color": "#AE9A6B"},
            {"id": "visual_sensualist",    "name": "The Visual Sensualist",      "tagline": "Beauty as a way of seeing",           "color": "#8A6BAE"},
            {"id": "broad_appreciator",    "name": "The Broad Appreciator",      "tagline": "Something in everything",             "color": "#6BAE9A"},
        ],
        "riasec": [
            {"id": "creative_investigator","name": "The Creative Investigator",  "tagline": "Curiosity meets craft",               "color": "#8A6BAE"},
            {"id": "social_builder",       "name": "The Social Builder",         "tagline": "People and purpose together",         "color": "#6BAE8A"},
            {"id": "enterprising_mind",    "name": "The Enterprising Mind",      "tagline": "Leading, persuading, creating",       "color": "#AE8A6B"},
        ],
        "attachment": [
            {"id": "secure_connector",     "name": "The Secure Connector",       "tagline": "Trust as a foundation",              "color": "#6BAE8A"},
            {"id": "anxious_heart",        "name": "The Anxious Heart",          "tagline": "Love felt deeply, held tightly",     "color": "#AE8A6B"},
            {"id": "independent_spirit",   "name": "The Independent Spirit",     "tagline": "Space as a love language",           "color": "#6B8AAE"},
        ],
        "pvq": [
            {"id": "open_to_change",       "name": "The Open to Change",         "tagline": "Self-direction and stimulation lead", "color": "#9AAE6B"},
            {"id": "self_transcendent",    "name": "The Self-Transcendent",      "tagline": "Universalism, benevolence anchor",    "color": "#6BAE9A"},
            {"id": "self_enhancing",       "name": "The Self-Enhancing",         "tagline": "Achievement and power forward",       "color": "#AE8A6B"},
            {"id": "conservation_minded",  "name": "The Conservation-Minded",    "tagline": "Tradition, security, conformity",     "color": "#7A8AAE"},
        ],
        "bpnss": [
            {"id": "deeply_resourced",     "name": "The Deeply Resourced",       "tagline": "All three needs well-fed",            "color": "#6BAE9A"},
            {"id": "competence_first",     "name": "The Competence-First",       "tagline": "Strong on capability, light on closeness", "color": "#6B9AAE"},
            {"id": "connection_seeker",    "name": "The Connection-Seeker",      "tagline": "Closeness leads, autonomy lags",      "color": "#AE9A6B"},
        ],
        "dass": [
            {"id": "resilient_navigator",  "name": "The Resilient Navigator",    "tagline": "Steady through the storm",            "color": "#6A8A7A"},
            {"id": "sensitive_processor",  "name": "The Sensitive Processor",    "tagline": "Depth through feeling",               "color": "#8A7A6A"},
            {"id": "calm_center",          "name": "The Calm Center",            "tagline": "Equanimity as a practice",            "color": "#7A8A9A"},
        ],
        "who5": [
            {"id": "low_wellbeing",        "name": "Running Low",                "tagline": "These two weeks have been heavy",     "color": "#8A6B7A"},
            {"id": "mid_wellbeing",        "name": "Steady",                     "tagline": "Some good, some hard",                "color": "#9AAE6B"},
            {"id": "high_wellbeing",       "name": "Thriving",                   "tagline": "The last two weeks have felt full",   "color": "#6BAE8A"},
        ],
    }
    options = fallbacks.get(test_id, [{"id": "explorer", "name": "The Explorer", "tagline": "Charting unknown territory", "color": "#8A9AAE"}])
    idx = int(sum(trait_vector) * len(options)) % len(options)
    return options[idx]

def project_umap(test_id: str, trait_vector: List[float]):
    coords_path = os.path.join(MODELS_DIR, f"{test_id}_map_coords.json")
    matrix_path = os.path.join(MODELS_DIR, f"{test_id}_trait_matrix.npy")

    if not os.path.exists(coords_path) or not os.path.exists(matrix_path):
        x = float(np.mean(trait_vector[:2]) * 10 - 5)
        y = float(np.mean(trait_vector[2:]) * 10 - 5) if len(trait_vector) > 2 else 0.0
        return round(x, 3), round(y, 3)

    try:
        matrix = np.load(matrix_path)
        with open(coords_path, encoding="utf-8") as f:
            coords = np.array(json.load(f))

        n = min(len(matrix), len(coords))
        matrix = matrix[:n]
        coords = coords[:n]

        vec = np.array(trait_vector, dtype=np.float32)
        dim = matrix.shape[1]
        if vec.shape[0] >= dim:
            vec_aligned = vec[:dim]
        else:
            vec_aligned = np.pad(vec, (0, dim - vec.shape[0]))

        dists = np.linalg.norm(matrix - vec_aligned, axis=1)
        k = min(5, n)
        top_k = np.argsort(dists)[:k]
        weights = 1.0 / (dists[top_k] + 1e-8)
        weights /= weights.sum()

        x = float(np.dot(weights, coords[top_k, 0]))
        y = float(np.dot(weights, coords[top_k, 1]))
        return round(x, 3), round(y, 3)

    except Exception as e:
        print(f"[umap] neighbor interpolation failed ({e}), using fallback")
        x = float(np.mean(trait_vector[:2]) * 10 - 5)
        y = float(np.mean(trait_vector[2:]) * 10 - 5) if len(trait_vector) > 2 else 0.0
        return round(x, 3), round(y, 3)


def _embed_to_10d(test_id: str, trait_vector: List[float]) -> Optional[np.ndarray]:
    """
    Map a user trait vector into the 10D UMAP embedding space used at training time
    by weighted k-NN against the cached population matrices. Returns None if the
    required matrices are missing.
    """
    # Exact path: if a UMAP reducer + scaler were saved (v10 umap2d tests),
    # transform the vector directly instead of approximating via k-NN.
    reducer_path = os.path.join(MODELS_DIR, f"{test_id}_umap2d.pkl")
    scaler_path  = os.path.join(MODELS_DIR, f"{test_id}_trait_scaler.pkl")
    trait_path   = os.path.join(MODELS_DIR, f"{test_id}_trait_matrix.npy")
    if os.path.exists(reducer_path) and os.path.exists(scaler_path) and os.path.exists(trait_path):
        try:
            import pickle
            with open(reducer_path, "rb") as fh: reducer = pickle.load(fh)
            with open(scaler_path, "rb") as fh: scaler = pickle.load(fh)
            dim = int(scaler.mean_.shape[0])
            vec = np.array(trait_vector, dtype=np.float64)
            vec = vec[:dim] if vec.shape[0] >= dim else np.pad(vec, (0, dim - vec.shape[0]))
            scaled = scaler.transform(vec.reshape(1, -1))
            return np.asarray(reducer.transform(scaled)[0], dtype=np.float64)
        except Exception:
            pass  # fall back to k-NN below

    umap10d_path = os.path.join(MODELS_DIR, f"{test_id}_umap10d_matrix.npy")
    if not (os.path.exists(umap10d_path) and os.path.exists(trait_path)):
        return None

    trait_matrix   = np.load(trait_path)
    umap10d_matrix = np.load(umap10d_path)
    n = min(len(trait_matrix), len(umap10d_matrix))
    trait_matrix   = trait_matrix[:n]
    umap10d_matrix = umap10d_matrix[:n]

    vec = np.array(trait_vector, dtype=np.float64)
    dim = trait_matrix.shape[1]
    if vec.shape[0] >= dim:
        vec_aligned = vec[:dim]
    else:
        vec_aligned = np.pad(vec, (0, dim - vec.shape[0]))

    dists   = np.linalg.norm(trait_matrix - vec_aligned, axis=1)
    top_k   = np.argsort(dists)[:10]
    weights = 1.0 / (dists[top_k] + 1e-8)
    weights /= weights.sum()
    return (umap10d_matrix[top_k] * weights[:, None]).sum(axis=0)


def _gmm_dim(gmm) -> int:
    """Number of features the fitted GMM (or BGM) expects."""
    means = getattr(gmm, "means_", None)
    if means is None:
        return 0
    return int(means.shape[1])


def assign_archetype(test_id: str, trait_vector: List[float],
                     trait_scores: Optional[Dict[str, float]] = None,
                     percentiles: Optional[Dict[str, int]] = None,
                     context_notes: Optional[List[Dict]] = None,
                     raw_responses: Optional[Dict[str, int]] = None) -> Optional[Dict]:
    """
    Cluster prediction priority:
      1. Bayesian Gaussian Mixture (saved as {test_id}_gmm.pkl by train_offline.py)
      2. Legacy KMeans (saved as {test_id}_kmeans.pkl by older runs)
      3. Rule-based fallback (get_fallback_archetype)
    """
    archetypes = load_json(test_id, "archetypes")
    gmm     = load_model(test_id, "gmm")
    kmeans  = load_model(test_id, "kmeans")
    cluster_id: Optional[str] = None

    if archetypes:
        try:
            vec_10d = _embed_to_10d(test_id, trait_vector)

            # Tier 1: Bayesian GMM (or vanilla GMM)
            if gmm is not None and vec_10d is not None:
                n_features = _gmm_dim(gmm)
                v = vec_10d
                if v.shape[0] >= n_features:
                    v = v[:n_features]
                else:
                    v = np.pad(v, (0, n_features - v.shape[0]))
                cluster_id = str(int(gmm.predict(v.reshape(1, -1))[0]))

            # Tier 2: legacy KMeans
            elif kmeans is not None:
                vec = np.array(trait_vector, dtype=np.float64)
                if vec_10d is not None and hasattr(kmeans, "cluster_centers_"):
                    n_features = kmeans.cluster_centers_.shape[1]
                    v = vec_10d
                    if v.shape[0] >= n_features:
                        v = v[:n_features]
                    else:
                        v = np.pad(v, (0, n_features - v.shape[0]))
                    cluster_id = str(int(kmeans.predict(v.reshape(1, -1))[0]))
                else:
                    n_features = kmeans.cluster_centers_.shape[1]
                    if vec.shape[0] >= n_features:
                        vec_aligned = vec[:n_features]
                    else:
                        vec_aligned = np.pad(vec, (0, n_features - vec.shape[0]))
                    cluster_id = str(int(kmeans.predict(vec_aligned.reshape(1, -1))[0]))

            refinement = None
            if trait_scores and percentiles and cluster_id is not None:
                try:
                    from ml.archetype_refiner import ArchetypeRefiner
                    refinement = ArchetypeRefiner.instance().refine(
                        test_id, trait_scores, cluster_id, percentiles,
                        context_notes=context_notes,
                        raw_responses=raw_responses,
                    )
                    if refinement and refinement.get("group") in archetypes:
                        cluster_id = refinement["group"]
                except Exception:
                    pass

            if cluster_id is not None:
                base = archetypes.get(cluster_id)
                if base:
                    # Copy so LLM personalisation never mutates the cached
                    # archetype catalogue on disk / in memory.
                    result = dict(base)
                    if refinement:
                        if refinement.get("name"):
                            result["name"] = refinement["name"]
                        if refinement.get("tagline"):
                            result["tagline"] = refinement["tagline"]
                        if refinement.get("adjustments"):
                            result["percentile_adjustments"] = refinement["adjustments"]
                    return result

        except Exception as e:
            print(f"[archetype] failed ({e}), using fallback")

    return get_fallback_archetype(test_id, trait_vector)

def calc_similarity(test_id: str, trait_vector: List[float]) -> float:
    dataset_path = os.path.join(MODELS_DIR, f"{test_id}_trait_matrix.npy")
    if not os.path.exists(dataset_path):
        return round(np.random.uniform(2.0, 8.0), 1)

    matrix = np.load(dataset_path)
    vec = np.array(trait_vector, dtype=np.float32)

    dim = matrix.shape[1]
    if vec.shape[0] >= dim:
        vec_aligned = vec[:dim]
    else:
        vec_aligned = np.pad(vec, (0, dim - vec.shape[0]))

    dists = np.linalg.norm(matrix - vec_aligned, axis=1)

    n_dims = matrix.shape[1]
    threshold = 0.12 * np.sqrt(n_dims)

    similar_count = np.sum(dists < threshold)
    pct = round((similar_count / len(matrix)) * 100, 1)
    return max(0.1, min(99.9, pct))

def get_neighborhood_traits(test_id: str, trait_vector: List[float], trait_names: List[str]) -> Dict:
    dataset_path = os.path.join(MODELS_DIR, f"{test_id}_trait_matrix.npy")
    if not os.path.exists(dataset_path):
        return {"description": "People with similar profiles share your depth of curiosity and reflective thinking."}
    matrix      = np.load(dataset_path)
    dists       = np.linalg.norm(matrix - np.array(trait_vector), axis=1)
    top_k       = min(100, len(matrix))
    nearest_idx = np.argsort(dists)[:top_k]
    neighbors   = matrix[nearest_idx]
    top_traits  = sorted(zip(trait_names, np.mean(neighbors, axis=0)), key=lambda x: -x[1])[:3]
    return {"top_traits": [{"trait": t, "score": round(float(s), 3)} for t, s in top_traits]}


# ---------------------------------------------------------------------------
# Main inference entry point
# ---------------------------------------------------------------------------

def run_inference(test_id: str, raw_responses: Dict[str, int],
                  context_notes: Optional[List[Dict]] = None) -> Dict[str, Any]:
    scorer = SCORERS.get(test_id)
    if not scorer:
        raise ValueError(f"No scorer for test_id: {test_id}")

    save_response_to_dataset(test_id, raw_responses)

    trait_scores    = scorer(raw_responses)
    trait_names     = list(trait_scores.keys())
    trait_vector    = list(trait_scores.values())

    percentiles     = calc_percentiles(test_id, trait_scores)
    archetype       = assign_archetype(test_id, trait_vector,
                                       trait_scores=trait_scores,
                                       percentiles=percentiles,
                                       context_notes=context_notes,
                                       raw_responses=raw_responses)

    # LLM-suggested percentile fine-tuning: applied only when volunteered
    # context justified it, capped at +/-5 points, clamped to [1, 99].
    if isinstance(archetype, dict) and archetype.get("percentile_adjustments"):
        adjustments = archetype.pop("percentile_adjustments")
        for trait, delta in adjustments.items():
            if trait in percentiles:
                try:
                    d = max(-5, min(5, int(delta)))
                    percentiles[trait] = int(max(1, min(99, round(percentiles[trait] + d))))
                except (TypeError, ValueError):
                    continue
    umap_x, umap_y = project_umap(test_id, trait_vector)
    similarity_pct  = calc_similarity(test_id, trait_vector)
    neighborhood    = get_neighborhood_traits(test_id, trait_vector, trait_names)
    rarity_pct      = round(100 - similarity_pct, 1)

    # Specialty psychology-model enrichment happens AFTER submit, in a
    # background thread (routers/results.py), and is persisted to the row —
    # the submit response never waits on a remote model.
    insights = generate_insights(test_id, trait_scores, percentiles, archetype,
                                 context_notes=context_notes)

    return {
        "trait_scores":   trait_scores,
        "percentiles":    percentiles,
        "archetype":      archetype,
        "umap_x":         umap_x,
        "umap_y":         umap_y,
        "similarity_pct": similarity_pct,
        "rarity_pct":     rarity_pct,
        "neighborhood":   neighborhood,
        "insights":       insights,
    }


# ---------------------------------------------------------------------------
# Insight generation
# ---------------------------------------------------------------------------

def generate_insights(test_id: str, scores: Dict, percentiles: Dict, archetype: Dict,
                      context_notes: Optional[List[Dict]] = None) -> Dict:
    insights  = []
    strengths = []

    if test_id == "hexaco":
        if percentiles.get("Honesty-Humility", 50) > 70:
            insights.append("Your high Honesty-Humility suggests sincerity, fairness, and an aversion to manipulation or exploitation, even when bending the rules would benefit you.")
            strengths.append("Honesty and humility")
        if percentiles.get("Openness", 50) > 70:
            insights.append("Your high openness suggests strong intellectual curiosity and a genuine appetite for new experiences and ideas.")
            strengths.append("Intellectual curiosity")
        if percentiles.get("Conscientiousness", 50) > 70:
            insights.append("Your conscientiousness indicates you are organized, dependable, and goal-oriented in how you approach your responsibilities.")
            strengths.append("Disciplined work ethic")
        if percentiles.get("Agreeableness", 50) > 70:
            insights.append("Your agreeableness reflects forgiveness, patience, and a cooperative style that others tend to notice and trust.")
            strengths.append("Empathy and warmth")
        if percentiles.get("Extraversion", 50) < 35:
            insights.append("Your lower extraversion suggests you prefer depth over breadth in social interaction, and that solitude tends to restore rather than drain you.")
        if percentiles.get("Emotionality", 50) > 70:
            insights.append("Your high emotionality means you feel things strongly, both your own emotions and the emotions of people close to you.")
        if not insights:
            insights.append("Your HEXACO profile shows a balanced distribution across all six dimensions, without strong peaks or troughs in any single area.")

    elif test_id == "sixteenpf":
        top = sorted(percentiles.items(), key=lambda x: -x[1])[:3]
        for t, p in top:
            if p > 65:
                strengths.append(t)
        if strengths:
            insights.append(f"Your most prominent factors are {', '.join(strengths[:2])}. These shape how you engage with challenges, people, and environments on a daily basis.")
        if percentiles.get("Tension", 50) > 70:
            insights.append("Elevated tension suggests you may carry more internal pressure than you let on to others, even when things appear fine on the surface.")
        if percentiles.get("Stability", 50) > 65:
            insights.append("Your emotional stability is a quiet asset, keeping you functional and grounded even during demanding stretches.")
            if "Emotional stability" not in strengths:
                strengths.append("Emotional stability")
        if not insights:
            insights.append("Your 16PF profile is broadly balanced across the sixteen personality dimensions, without strong dominance in any single factor.")

    elif test_id == "darktriad":
        if all(percentiles.get(t, 50) < 40 for t in ["Machiavellianism", "Narcissism", "Psychopathy"]):
            insights.append("Your profile shows low dark triad traits. You tend to be cooperative, empathic, and transparent in how you deal with others.")
            strengths.append("Ethical consistency")
        if percentiles.get("Machiavellianism", 50) > 60:
            insights.append("You tend toward strategic thinking and long-term planning, often calculating the likely consequences of a move before committing to it.")
        if percentiles.get("Narcissism", 50) > 60:
            insights.append("You have a strong sense of self-worth and carry a natural leadership confidence that others can find either compelling or demanding.")
        if percentiles.get("Psychopathy", 50) > 60:
            insights.append("Your psychopathy score is elevated, suggesting a tendency toward risk tolerance, emotional detachment under pressure, and directness that can unsettle others.")

    elif test_id == "dass":
        if percentiles.get("Stress", 50) < 35:
            insights.append("Your stress levels are low relative to others. You manage demands and uncertainty well without becoming easily overwhelmed.")
            strengths.append("Stress tolerance")
        if percentiles.get("Anxiety", 50) > 65:
            insights.append("Your anxiety score is elevated this week. If this pattern persists, it may be worth paying attention to the physical and cognitive signals your body is sending.")
        if percentiles.get("Depression", 50) > 65:
            insights.append("Your depression score is elevated. A persistent flatness, lack of anticipation, or difficulty seeing meaning are worth taking seriously rather than pushing through.")
        if percentiles.get("Depression", 50) < 30:
            insights.append("Your mood scores reflect a generally positive emotional baseline, things land, anticipation is present, and motivation feels accessible.")
            strengths.append("Positive affect")
        if not insights:
            insights.append("Your emotional scores fall within a moderate range across all three dimensions this week.")

    elif test_id == "aesthetic":
        top = sorted(percentiles.items(), key=lambda x: -x[1])[:2]
        for t, p in top:
            if p > 65:
                strengths.append(t)
        if strengths:
            insights.append(f"Your aesthetic sensibility is most pronounced in {' and '.join(strengths)}. These are the aesthetic registers that move you most readily and shape what you are drawn to.")
        else:
            insights.append("Your aesthetic responses are moderated across all four domains, you respond to a broad range rather than having strong peaks in any one area.")
        if scores.get("Intense", 0) > 0.65:
            insights.append("Your affinity for intense, raw, or unconventional aesthetics suggests you are drawn to work that has an edge or tension to it rather than something smooth or polished.")
        if scores.get("Traditional", 0) > 0.65:
            insights.append("Your pull toward traditional, rooted aesthetic forms suggests you find authenticity and heritage more compelling than novelty or innovation for its own sake.")

    elif test_id == "riasec":
        top  = sorted(percentiles.items(), key=lambda x: -x[1])[:2]
        code = "".join(t[0] for t, _ in top)
        insights.append(f"Your Holland code begins with {code}. Work environments that match this profile tend to bring out your strongest performance and sustain your motivation over time.")
        for t, p in top:
            if p > 65:
                strengths.append(t)
        bottom = sorted(percentiles.items(), key=lambda x: x[1])[:1]
        if bottom:
            t, p = bottom[0]
            if p < 30:
                insights.append(f"Your lowest area is {t}. Roles that demand this as a core function are likely to drain rather than energize you.")

    elif test_id == "attachment":
        if percentiles.get("Secure", 50) > 65:
            insights.append("Your attachment profile leans secure. You tend to feel comfortable with both intimacy and independence, without needing one to crowd out the other.")
            strengths.append("Secure base")
        if percentiles.get("Anxious", 50) > 65:
            insights.append("You show elevated attachment anxiety. You may find yourself wanting more closeness than you are currently getting, and reading small signals from a partner as evidence of withdrawal.")
        if percentiles.get("Avoidant", 50) > 65:
            insights.append("Your avoidant score is high. Emotional distance tends to feel safer or more comfortable than full vulnerability, which can create patterns of pulling back precisely when closeness becomes available.")
        if not insights:
            insights.append("Your attachment profile is moderate across all three dimensions, suggesting a flexible rather than strongly patterned relational style.")

    elif test_id == "fti":
        top = sorted(percentiles.items(), key=lambda x: -x[1])[:2]
        if top:
            primary, p = top[0]
            insights.append(f"Your strongest temperament is the {primary}. This is the cognitive and emotional rhythm that shows up most consistently in how you move through life.")
            strengths.append(primary)
            if len(top) > 1 and top[1][1] > 55:
                insights.append(f"Your secondary temperament is the {top[1][0]}. You blend both rhythms rather than running entirely on one.")
        if not insights:
            insights.append("Your temperament blend is balanced across all four styles, with no single rhythm dominating.")

    elif test_id == "hsq":
        if percentiles.get("Affiliative", 50) > 65:
            insights.append("You use humor as a way of bringing people together. Easy banter, shared laughter, and light moments with friends are part of how you build closeness.")
            strengths.append("Warm humor")
        if percentiles.get("Self-Enhancing", 50) > 65:
            insights.append("You use humor as a coping resource. When something hits hard, finding the absurd or funny angle is often what helps you metabolize it.")
            strengths.append("Humor as resilience")
        if percentiles.get("Aggressive", 50) > 65:
            insights.append("Your humor sometimes has a sharper edge, used to put others on the back foot or score points. It can land well or wound, depending on the room.")
        if percentiles.get("Self-Defeating", 50) > 65:
            insights.append("You often make yourself the punchline. It can earn affection in the short term but tends to wear on self-worth over time.")
        if not insights:
            insights.append("Your humor styles are balanced rather than dominated by any single mode.")

    elif test_id == "kims":
        if percentiles.get("Observing", 50) > 65:
            insights.append("You notice the texture of present-moment experience, sensations in the body, sounds, shifts in mood, more than most people do.")
            strengths.append("Inner noticing")
        if percentiles.get("Describing", 50) > 65:
            insights.append("You can put inner states into words easily. This makes you a useful thinking partner for people who struggle to name what they feel.")
            strengths.append("Articulating experience")
        if percentiles.get("Acting with Awareness", 50) > 65:
            insights.append("You stay present with what you are doing rather than going through it on autopilot. Distractions and rumination have less hold on you.")
            strengths.append("Present focus")
        if percentiles.get("Accepting without Judgment", 50) > 65:
            insights.append("You let experience be what it is rather than fighting or grading it. This is the mindfulness facet most associated with reduced anxiety over time.")
            strengths.append("Non-reactivity")
        if not insights:
            insights.append("Your mindfulness profile is moderate across all four skills, with room to grow in any of them.")

    elif test_id == "npi":
        top = sorted(percentiles.items(), key=lambda x: -x[1])[:2]
        if top and top[0][1] > 65:
            insights.append(f"Your most prominent self-view facet is {top[0][0]}. This is the lens through which you most readily understand your own worth and place.")
            strengths.append(top[0][0])
        if percentiles.get("Authority", 50) > 70:
            insights.append("You see yourself as a natural leader. Taking charge feels comfortable rather than effortful.")
        if percentiles.get("Entitlement", 50) > 70:
            insights.append("You hold a strong sense of what you deserve from others. This can fuel confidence in negotiations, but can also strain relationships when expectations go unmet.")
        if all(percentiles.get(t, 50) < 40 for t in ["Authority", "Superiority", "Entitlement", "Exploitativeness"]):
            insights.append("Your self-view is humble and other-focused. You don't lean on grandiosity as a default mode.")
            strengths.append("Humility")
        if not insights:
            insights.append("Your self-view profile is moderately balanced across all seven facets.")

    elif test_id == "ambi":
        top = sorted(percentiles.items(), key=lambda x: -x[1])[:3]
        if top:
            primaries = ", ".join(t for t, _ in top[:2])
            insights.append(f"Across the broad personality scan, your strongest signals show up in {primaries}. These shape the personality silhouette others most notice in you.")
            for t, p in top[:2]:
                if p > 60:
                    strengths.append(t)
        if not insights:
            insights.append("Your broad personality scan is unusually balanced, without a single dominant signal across the seven domains.")

    elif test_id == "gcbs":
        avg = sum(percentiles.values()) / max(len(percentiles), 1) if percentiles else 50
        if avg > 65:
            insights.append("You tend to hold a strongly skeptical view of official narratives and powerful institutions. You see hidden hands more readily than most.")
        elif avg < 35:
            insights.append("You tend to take official accounts at close to face value. Your default is trust unless there is clear reason otherwise.")
            strengths.append("Default trust")
        else:
            insights.append("Your skepticism is selective. Some claims you take at face value, others you examine more carefully.")
            strengths.append("Selective skepticism")

    elif test_id == "pvq":
        top = sorted(percentiles.items(), key=lambda x: -x[1])[:3]
        if top:
            ranked = ", ".join(t for t, _ in top[:3])
            insights.append(f"Your three strongest values are {ranked}. These are the priorities you most consistently sort decisions by, even when you are not explicitly thinking about them.")
            for t, p in top[:2]:
                if p > 60:
                    strengths.append(t)
        bottom = sorted(percentiles.items(), key=lambda x: x[1])[:1]
        if bottom and bottom[0][1] < 30:
            insights.append(f"Your lowest-ranked value is {bottom[0][0]}. People who lead with this value may feel out of step with you.")

    elif test_id == "bpnss":
        for trait in ["Autonomy", "Competence", "Relatedness"]:
            p = percentiles.get(trait, 50)
            if p > 65:
                insights.append(f"Your {trait.lower()} need is being well met in your current life. This is one of the foundations holding you up.")
                strengths.append(trait)
            elif p < 35:
                insights.append(f"Your {trait.lower()} need is currently under-fed. When this one runs low for a long time, it tends to drain motivation and mood.")
        if not insights:
            insights.append("All three of your basic psychological needs are being moderately met. None is particularly starved, none is particularly overflowing.")

    elif test_id == "who5":
        score = scores.get("Wellbeing", 0.5)
        if score >= 0.50:
            insights.append("Your wellbeing over the last two weeks reads as broadly healthy. Energy, mood, and interest in daily life are all in a good range.")
            strengths.append("Recent wellbeing")
        elif score >= 0.28:
            insights.append("Your wellbeing over the last two weeks is in a moderate range. Things are functional but you may not be feeling fully fueled.")
        else:
            insights.append("Your wellbeing score for the last two weeks is low. This is a self-reflection signal worth taking seriously, especially if it persists. If you are in distress, please reach out to a qualified mental health professional or support resource.")

    elif test_id == "pid5":
        top = sorted(percentiles.items(), key=lambda x: -x[1])[:2]
        if top and top[0][1] > 65:
            insights.append(f"Your most pronounced trait pattern is {top[0][0]}. This describes a style, not a clinical condition.")
        if all(p < 50 for p in percentiles.values()) if percentiles else False:
            insights.append("Your trait scores are uniformly low across all five domains. This is a stable, low-intensity profile.")
            strengths.append("Low trait intensity")
        if not insights:
            insights.append("Your trait pattern is mixed across the five domains. None of these are diagnoses, only personality style descriptions.")

    summary = f"As {archetype.get('name', 'a unique individual')}, {archetype.get('tagline', 'your personality is one of a kind')}."

    if context_notes:
        try:
            from ml.archetype_refiner import ArchetypeRefiner
            insights = ArchetypeRefiner.instance().enrich_insights(
                test_id, scores, percentiles, insights, context_notes
            )
        except Exception:
            pass

    return {
        "summary":   summary,
        "insights":  insights[:5],
        "strengths": strengths[:4],
    }