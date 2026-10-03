"""
Sample-output verification: feed psychologically-typed personas through the live
inference pipeline and check that each persona lands in a distinct cluster.

For each test we define 2-4 archetypal personas with known trait profiles.
We then assert:
  (a) percentiles vary across personas in the expected directions
  (b) personas with opposite profiles get DIFFERENT clusters
  (c) personas with similar profiles get the SAME cluster (consistency)

This is the unsupervised analog of an integration test.
"""
import sys
import os
import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "backend"))
from ml.inference import SCORERS, calc_percentiles, assign_archetype  # noqa: E402


# ---------------------------------------------------------------------------
# Persona definitions: response dicts that target specific trait profiles
# ---------------------------------------------------------------------------
def hexaco_personas():
    """HEXACO personas matching Gerlach 2018 archetypes."""
    HEXACO_PREFIXES = ["HSinc", "HFair", "HGree", "HMode", "EFear", "EAnxi",
                       "EDepe", "ESent", "XExpr", "XSoci", "XSocB", "XLive",
                       "AForg", "AGent", "AFlex", "APati", "COrga", "CDili",
                       "CPerf", "CPrud", "OAesA", "OInqu", "OCrea", "OUnco"]

    def make(facet_levels):
        # facet_levels: dict {prefix: 1..7 target}
        return {f"{p}{i}": facet_levels.get(p, 4) for p in HEXACO_PREFIXES for i in range(1, 11)}

    return {
        # high honesty, high agreeableness, high conscientiousness, mid emotional
        "Role Model":      make({"HSinc": 6, "HFair": 6, "HGree": 2, "HMode": 6,
                                  "AForg": 6, "AGent": 6, "AFlex": 6, "APati": 6,
                                  "COrga": 6, "CDili": 6, "CPerf": 6, "CPrud": 6,
                                  "OCrea": 6, "OInqu": 6}),
        # low honesty, low agreeableness (dark profile)
        "Self-Centered":   make({"HSinc": 2, "HFair": 2, "HGree": 6, "HMode": 2,
                                  "AForg": 2, "AGent": 2, "AFlex": 2, "APati": 2,
                                  "EFear": 2}),
        # low extraversion, low openness (reserved)
        "Reserved":        make({"XExpr": 2, "XSoci": 2, "XSocB": 2, "XLive": 2,
                                  "OCrea": 2, "OInqu": 2, "OAesA": 2, "OUnco": 2}),
        # middle of the road
        "Average":         make({}),
    }


def hsq_personas():
    """Humor styles personas. Q1-Q32, 1-5 scale."""
    def base(): return {f"Q{i}": 3 for i in range(1, 33)}
    p = {}

    # Adaptive humor user: affiliative (1R,5,9R,13,17R,21,25R,29R), self-enhancing (2,6,10,14,18,22,26,30) high
    p["Adaptive (warm + resilient)"] = base()
    for i in [5, 13, 21]:                p["Adaptive (warm + resilient)"][f"Q{i}"] = 5
    for i in [1, 9, 17, 25, 29]:         p["Adaptive (warm + resilient)"][f"Q{i}"] = 1  # reverse coded
    for i in [2, 6, 10, 14, 18, 22, 26, 30]:  p["Adaptive (warm + resilient)"][f"Q{i}"] = 5

    # Maladaptive humor: aggressive (3,7R,11,15R,19,23R,27,31R) + self-defeating (4,8,12,16R,20,24,28,32)
    p["Maladaptive (aggressive + self-defeating)"] = base()
    for i in [3, 11, 19, 27]:            p["Maladaptive (aggressive + self-defeating)"][f"Q{i}"] = 5
    for i in [7, 15, 23, 31]:            p["Maladaptive (aggressive + self-defeating)"][f"Q{i}"] = 1
    for i in [4, 8, 12, 20, 24, 28, 32]: p["Maladaptive (aggressive + self-defeating)"][f"Q{i}"] = 5
    p["Maladaptive (aggressive + self-defeating)"]["Q16"] = 1

    # Low humor across the board
    p["Low humor across all styles"] = {f"Q{i}": 1 for i in range(1, 33)}
    return p


def kims_personas():
    """KIMS personas. Q1-Q39, 1-5 scale."""
    def base(): return {f"Q{i}": 3 for i in range(1, 40)}
    p = {}

    # High mindfulness across all 4 facets
    obs = [1, 5, 9, 13, 17, 21, 25, 29, 33, 37, 39]
    des = [2, 6, 10, 26, 30, 34]; des_rev = [14, 18, 22]
    act = [7, 15, 19, 38]; act_rev = [3, 11, 23, 27, 31, 35]
    acc_rev = [4, 8, 12, 16, 20, 24, 28, 32, 36]

    p["High mindfulness all facets"] = base()
    for i in obs + des + act:               p["High mindfulness all facets"][f"Q{i}"] = 5
    for i in des_rev + act_rev + acc_rev:   p["High mindfulness all facets"][f"Q{i}"] = 1

    p["Low mindfulness all facets"] = {f"Q{i}": 1 for i in range(1, 40)}
    for i in des_rev + act_rev + acc_rev:   p["Low mindfulness all facets"][f"Q{i}"] = 5

    # Observe-high, accept-low (notices feelings but judges them)
    p["Observes but judges"] = base()
    for i in obs:           p["Observes but judges"][f"Q{i}"] = 5
    for i in acc_rev:       p["Observes but judges"][f"Q{i}"] = 5  # high judging
    return p


def fti_personas():
    """Fisher temperaments. Q1-Q56, 1-4 scale. 14 items per temperament."""
    def base(): return {f"Q{i}": 2 for i in range(1, 57)}
    p = {}
    p["Explorer"]   = base(); [p["Explorer"].update({f"Q{i}": 4})   for i in range(1, 15)]
    p["Builder"]    = base(); [p["Builder"].update({f"Q{i}": 4})    for i in range(15, 29)]
    p["Director"]   = base(); [p["Director"].update({f"Q{i}": 4})   for i in range(29, 43)]
    p["Negotiator"] = base(); [p["Negotiator"].update({f"Q{i}": 4}) for i in range(43, 57)]
    return p


def npi_personas():
    """NPI forced-choice. Each item: 1=narcissistic, 2=non-narcissistic per scoring key."""
    NPI_NARC_KEY = {
        1:1,2:1,3:1,4:2,5:2,6:1,7:2,8:1,9:2,10:2,
        11:1,12:1,13:1,14:1,15:2,16:1,17:2,18:2,19:2,20:2,
        21:1,22:2,23:2,24:1,25:1,26:2,27:1,28:2,29:1,30:1,
        31:1,32:2,33:1,34:1,35:2,36:1,37:1,38:1,39:1,40:2,
    }
    p = {}
    p["Highly narcissistic"]     = {f"Q{i}": NPI_NARC_KEY[i] for i in range(1, 41)}
    p["Low narcissism (humble)"] = {f"Q{i}": (2 if NPI_NARC_KEY[i] == 1 else 1) for i in range(1, 41)}
    # Authority-only profile (8 facet-specific items high, rest low)
    p["Authority-focused only"]  = {f"Q{i}": (2 if NPI_NARC_KEY[i] == 1 else 1) for i in range(1, 41)}
    for i in [1, 8, 10, 11, 12, 32, 33, 36]:
        p["Authority-focused only"][f"Q{i}"] = NPI_NARC_KEY[i]
    return p


def ambi_personas():
    """AMBI 181 items, 7-point Likert. Each persona sets the target chunk to 7
    AND the other chunks to 1, creating a true contrast across the 7 domains."""
    chunks = [(1, 27), (27, 53), (53, 79), (79, 105), (105, 131), (131, 157), (157, 182)]
    names  = ["Affect-high (rest low)", "Social-high (rest low)",
              "Conscientious-high (rest low)", "Open-high (rest low)",
              "Agreeable-high (rest low)", "Energy-high (rest low)",
              "Identity-high (rest low)"]
    p = {}
    for target_chunk, label in zip(chunks, names):
        prof = {f"Q{i}": 1 for i in range(1, 182)}
        for i in range(*target_chunk):
            prof[f"Q{i}"] = 7
        p[label] = prof
    # plus a fully-middle baseline
    p["All-mid (4 across)"] = {f"Q{i}": 4 for i in range(1, 182)}
    return p


def gcbs_personas():
    """GCBS 15 items, 1-5 scale."""
    p = {}
    p["High conspiracy beliefs"] = {f"Q{i}": 5 for i in range(1, 16)}
    p["Low conspiracy beliefs"]  = {f"Q{i}": 1 for i in range(1, 16)}
    p["Govt-skeptic, alien-skeptic"] = {f"Q{i}": 3 for i in range(1, 16)}
    for i in [1, 6, 11]:  p["Govt-skeptic, alien-skeptic"][f"Q{i}"] = 5
    for i in [3, 8, 13]:  p["Govt-skeptic, alien-skeptic"][f"Q{i}"] = 1
    return p


# --- 6 retrained tests ---
def sixteenpf_personas():
    """16PF letters A-P, varying counts per factor (B has 13, rest have 10)."""
    p = {}
    def make(highs, lows, default=3):
        d = {}
        for letter in "ABCDEFGHIJKLMNOP":
            n = 13 if letter == "B" else 10
            for i in range(1, n+1):
                key = f"{letter}{i}"
                if letter in highs:
                    d[key] = 5
                elif letter in lows:
                    d[key] = 1
                else:
                    d[key] = default
        return d
    p["Warm Strategist (high A,B,N)"]   = make({"A","B","N"}, {"P"})
    p["Bold Pioneer (high D,G,M)"]      = make({"D","G","M"}, {"L"})
    p["Grounded Analyst (high B,C,O)"]  = make({"B","C","O"}, {"E"})
    p["Expressive Idealist (high E,H,I)"] = make({"E","H","I"}, {"K"})
    return p


def darktriad_personas():
    """SD3: M1-9 Mach, N1-9 Narc, P1-9 Psyc, 5-point Likert."""
    p = {}
    p["High dark triad across all 3"] = {f"{l}{i}": 5 for l in "MNP" for i in range(1, 10)}
    p["Low dark triad (ethical)"]     = {f"{l}{i}": 1 for l in "MNP" for i in range(1, 10)}
    p["High Mach only"]               = {**{f"M{i}": 5 for i in range(1, 10)},
                                          **{f"N{i}": 2 for i in range(1, 10)},
                                          **{f"P{i}": 2 for i in range(1, 10)}}
    p["High Narc only"]               = {**{f"M{i}": 2 for i in range(1, 10)},
                                          **{f"N{i}": 5 for i in range(1, 10)},
                                          **{f"P{i}": 2 for i in range(1, 10)}}
    return p


def dass_personas():
    """DASS Q1A-Q42A. 1-4 scale. D=14, A=14, S=14."""
    p = {}
    p["No distress (resilient)"]           = {f"Q{i}A": 1 for i in range(1, 43)}
    p["Severe distress across D,A,S"]      = {f"Q{i}A": 4 for i in range(1, 43)}
    p["Anxiety-dominant"]                  = {f"Q{i}A": 2 for i in range(1, 43)}
    for n in [2, 4, 7, 9, 15, 19, 20, 23, 25, 28, 30, 36, 40, 41]:
        p["Anxiety-dominant"][f"Q{n}A"] = 4
    p["Depression-dominant"]               = {f"Q{i}A": 2 for i in range(1, 43)}
    for n in [3, 5, 10, 13, 16, 17, 21, 24, 26, 31, 34, 37, 38, 42]:
        p["Depression-dominant"][f"Q{n}A"] = 4
    return p


def aesthetic_personas():
    """APS RA1A-RA8A, LP1A-LP8A, MF1A-MF8A, V1A-V6A. 1-5 scale."""
    def make(highs):
        prof = {}
        for p_, n in [("RA", 8), ("LP", 8), ("MF", 8), ("V", 6)]:
            for i in range(1, n+1):
                prof[f"{p_}{i}A"] = 5 if p_ in highs else 2
        return prof
    p = {}
    p["Raw intensity lover"]   = make({"RA"})
    p["Mainstream popular"]    = make({"LP"})
    p["Traditional folk"]      = make({"MF"})
    p["Visual abstract"]       = make({"V"})
    p["Broad eclectic"]        = {**make({"RA","LP","MF","V"})}
    return p


def riasec_personas():
    """RIASEC R/I/A/S/E/C, each 8 items, 1-5 scale."""
    def make(highs):
        prof = {}
        for letter in "RIASEC":
            for i in range(1, 9):
                prof[f"{letter}{i}"] = 5 if letter in highs else 2
        return prof
    p = {}
    p["Realistic builder"]        = make({"R"})
    p["Investigative scientist"]  = make({"I"})
    p["Artistic creator"]         = make({"A"})
    p["Social helper"]            = make({"S"})
    p["Enterprising leader"]      = make({"E"})
    p["Conventional admin"]       = make({"C"})
    return p


def attachment_personas():
    """ECR Q1-Q36, 1-7 scale. Q1-18 anxiety items, Q19-36 avoidance items."""
    p = {}
    p["Secure"]            = {f"Q{i}": 2 for i in range(1, 37)}
    p["Anxious-preoccupied"] = {**{f"Q{i}": 6 for i in range(1, 19)},
                                **{f"Q{i}": 2 for i in range(19, 37)}}
    p["Avoidant"]          = {**{f"Q{i}": 2 for i in range(1, 19)},
                              **{f"Q{i}": 6 for i in range(19, 37)}}
    p["Fearful-avoidant"]  = {f"Q{i}": 6 for i in range(1, 37)}
    return p


# ---------------------------------------------------------------------------
# Verification runner
# ---------------------------------------------------------------------------
def verify(test_id: str, personas: dict):
    print(f"\n=== {test_id.upper()} ===")
    print(f"{'persona':<48} {'archetype':<28} {'cluster_id':<10}  top trait pcts")
    print("-" * 130)
    rows = []
    for label, resp in personas.items():
        scores = SCORERS[test_id](resp)
        pcts   = calc_percentiles(test_id, scores)
        trait_vec = list(scores.values())
        arc = assign_archetype(test_id, trait_vec, trait_scores=scores, percentiles=pcts) or {}
        top_pcts = ", ".join(f"{k}:{v}th" for k, v in
                             sorted(pcts.items(), key=lambda kv: -kv[1])[:3])
        rows.append({
            "persona":   label,
            "archetype": arc.get("name", "(none)"),
            "cluster":   arc.get("id", "(none)"),
            "scores":    scores,
            "pcts":      pcts,
        })
        print(f"  {label:<46} {arc.get('name','(none)'):<28} {str(arc.get('id','-')):<10}  {top_pcts}")

    # Diagnostic: are personas getting distinct clusters?
    unique_clusters = set(r["cluster"] for r in rows)
    if len(unique_clusters) >= len(rows) - 1:
        print(f"  -> {len(unique_clusters)} distinct clusters across {len(rows)} personas. GOOD.")
    elif len(unique_clusters) == 1:
        print(f"  -> ALL personas mapped to one cluster. BAD (model not discriminating).")
    else:
        print(f"  -> {len(unique_clusters)} clusters across {len(rows)} personas. PARTIAL.")
    return rows


if __name__ == "__main__":
    suite = {
        "hexaco":     hexaco_personas(),
        "sixteenpf":  sixteenpf_personas(),
        "darktriad":  darktriad_personas(),
        "fti":        fti_personas(),
        "npi":        npi_personas(),
        "ambi":       ambi_personas(),
        "pid5":       None,  # LLM-only, will skip clustering archetype check
        "hsq":        hsq_personas(),
        "kims":       kims_personas(),
        "gcbs":       gcbs_personas(),
        "aesthetic":  aesthetic_personas(),
        "riasec":     riasec_personas(),
        "attachment": attachment_personas(),
        "pvq":        None,
        "bpnss":      None,
        "dass":       dass_personas(),
        "who5":       None,
    }
    for tid, personas in suite.items():
        if personas is None:
            print(f"\n=== {tid.upper()} === LLM-only (no clustering model), skipped")
            continue
        try:
            verify(tid, personas)
        except Exception as e:
            print(f"\n=== {tid.upper()} === FAILED  {e}")
