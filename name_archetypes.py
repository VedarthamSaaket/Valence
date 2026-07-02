"""
Derive semantically meaningful archetype names from BGM cluster centroids.

For each cluster, we identify the top-2 dominant traits (highest centroid values)
and the bottom-1 trait (lowest), then assemble a name template per test.

This is a deterministic seed for archetype copy. The LLM enricher
(archetype_refiner.py) then rewrites these into personalized output at inference
time. This script just makes sure the cluster -> archetype JSON has informative
labels instead of "Archetype 1, 2, 3...".
"""
import json
import os
import sys
from typing import Dict, List

MODELS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "backend", "models")
TESTS = ["hexaco", "hsq", "kims", "fti", "npi", "ambi", "gcbs", "sixteenpf", "riasec",
         "aesthetic", "attachment", "darktriad", "dass"]


# Trait name -> short descriptive when the trait is the dominant one
# Curated per test for psychological coherence
TRAIT_LABELS = {
    "hexaco": {
        "Honesty-Humility":  ("Principled", "Pragmatic"),
        "Emotionality":      ("Feeling-Deep", "Even-Keeled"),
        "Extraversion":      ("Outwardly Lit", "Inward-Drawn"),
        "Agreeableness":     ("Warm-Hearted", "Hard-Nosed"),
        "Conscientiousness": ("Disciplined",  "Free-Flowing"),
        "Openness":          ("Curious",      "Conventional"),
    },
    "hsq": {
        "Affiliative":    ("Warm Humorist",      "Reserved"),
        "Self-Enhancing": ("Inner Resilient",    "Earnest"),
        "Aggressive":     ("Edgy Jester",        "Soft-Toned"),
        "Self-Defeating": ("Self-Deprecating",   "Self-Composed"),
    },
    "kims": {
        "Observing":                  ("Embodied Noticer",    "Outwardly Tuned"),
        "Describing":                 ("Articulate Witness",  "Inarticulate"),
        "Acting with Awareness":      ("Present Actor",       "Autopilot"),
        "Accepting without Judgment": ("Accepting Witness",   "Judging Mind"),
    },
    "fti": {
        "Explorer":   ("Explorer",   "Cautious"),
        "Builder":    ("Builder",    "Spontaneous"),
        "Director":   ("Director",   "Receptive"),
        "Negotiator": ("Negotiator", "Pragmatic"),
    },
    "npi": {
        "Authority":        ("Authority Holder", "Quiet"),
        "Self-Sufficiency": ("Self-Reliant",     "Interdependent"),
        "Superiority":      ("Confident Lead",   "Humble"),
        "Exhibitionism":    ("Spotlight Lover",  "Background"),
        "Exploitativeness": ("Strategic",        "Trusting"),
        "Vanity":           ("Image-Aware",      "Image-Indifferent"),
        "Entitlement":      ("Expects-The-Best", "Receives-As-Given"),
    },
    "ambi": {
        "Affect Regulation":  ("Affect-Regulated",     "Affect-Reactive"),
        "Social Drive":       ("Socially Driven",      "Solitude-Drawn"),
        "Conscientiousness":  ("Disciplined",          "Free-Flowing"),
        "Openness":           ("Open Explorer",        "Conventional"),
        "Agreeableness":      ("Warm Connector",       "Hard-Nosed"),
        "Energy Drive":       ("High-Energy",          "Low-Key"),
        "Identity Coherence": ("Identity-Anchored",    "Identity-Fluid"),
    },
    "gcbs": {
        "Government Malfeasance":     ("Govt-Skeptic",        "Govt-Trusting"),
        "Malevolent Global":          ("Hidden-Power Skeptic", "Status-Quo Believer"),
        "Extraterrestrial Coverup":   ("ET-Cover-Up Believer", "ET-Skeptic"),
        "Personal Wellbeing Threats": ("Body-Threat Wary",    "Body-Threat Calm"),
        "Control of Information":     ("Info-Withheld",       "Info-Open"),
    },
    "sixteenpf": {
        "Warmth":             ("Warm",            "Reserved"),
        "Reasoning":          ("Sharp-Minded",    "Concrete"),
        "Stability":          ("Steady",          "Reactive"),
        "Dominance":          ("Assertive",       "Deferential"),
        "Liveliness":         ("Lively",          "Serious"),
        "Rule-Consciousness": ("Dutiful",         "Expedient"),
        "Social-Boldness":    ("Socially Bold",   "Shy"),
        "Sensitivity":        ("Sensitive",       "Utilitarian"),
        "Vigilance":          ("Vigilant",        "Trusting"),
        "Abstractedness":     ("Imaginative",     "Grounded"),
        "Privateness":        ("Private",         "Forthright"),
        "Apprehension":       ("Self-Doubting",   "Self-Assured"),
        "Openness-to-Change": ("Open-to-Change",  "Traditional"),
        "Self-Reliance":      ("Self-Reliant",    "Group-Oriented"),
        "Perfectionism":      ("Perfectionist",   "Flexible"),
        "Tension":            ("Driven",          "Relaxed"),
    },
    "riasec": {
        "Realistic":     ("Hands-On Doer",   "Abstract"),
        "Investigative": ("Analyst",         "Non-Analytical"),
        "Artistic":      ("Creator",         "Conventional-Minded"),
        "Social":        ("Helper",          "Detached"),
        "Enterprising":  ("Leader",          "Non-Assertive"),
        "Conventional":  ("Organizer",       "Unstructured"),
    },
    "aesthetic": {
        "Intense":     ("Raw-Intensity Seeker",  "Gentle-Palette"),
        "Mainstream":  ("Popular-Current",       "Off-The-Path"),
        "Traditional": ("Classic Devotee",       "Modernist"),
        "Visual":      ("Visual Sensualist",     "Idea-First"),
    },
    "attachment": {
        "Anxious":  ("Closeness-Seeking",  "Worry-Free"),
        "Avoidant": ("Independent Spirit", "Openly Close"),
        "Secure":   ("Secure Connector",   "Guarded"),
    },
    "darktriad": {
        "Machiavellianism": ("Strategist",       "Straight-Dealer"),
        "Narcissism":       ("Self-Assured",     "Modest"),
        "Psychopathy":      ("Cool-Detached",    "Warm-Feeling"),
    },
    "dass": {
        "Depression": ("Heavy-Hearted",  "Bright-Mooded"),
        "Anxiety":    ("Alert-Wired",    "Calm-Bodied"),
        "Stress":     ("Pressure-Loaded","Unburdened"),
    },
}


# Color palette per test, distinct hues per cluster index
COLORS = ["#6B8CAE", "#AE6B8A", "#6BAE8A", "#AE9A6B", "#8A6BAE", "#6BAE9A",
          "#AE8A6B", "#9A7AAE", "#7A8AAE", "#AE7A8A", "#7AAE9A", "#8AAE6B"]


def name_one(test_id: str) -> Dict:
    import numpy as np
    meta_path = os.path.join(MODELS_DIR, f"{test_id}_meta.json")
    arc_path  = os.path.join(MODELS_DIR, f"{test_id}_archetypes.json")
    dist_path = os.path.join(MODELS_DIR, f"{test_id}_distributions.json")
    if not all(os.path.exists(p) for p in (meta_path, arc_path, dist_path)):
        return {"test_id": test_id, "error": "missing artifacts"}

    with open(meta_path) as fh:
        meta = json.load(fh)
    with open(arc_path) as fh:
        archetypes = json.load(fh)
    with open(dist_path) as fh:
        dists = json.load(fh)

    trait_names = meta.get("trait_names") or list(dists.keys())
    if not trait_names:
        return {"test_id": test_id, "error": "no trait_names in meta"}

    # population statistics per trait (mean + std)
    pop_stats = {t: (float(np.mean(dists[t])), float(np.std(dists[t]) + 1e-8)) for t in trait_names}

    labels = TRAIT_LABELS.get(test_id, {})
    renamed: Dict[str, Dict] = {}

    for cid, info in archetypes.items():
        centroid = info.get("centroid") or []
        if len(centroid) != len(trait_names):
            renamed[cid] = info
            continue

        # z-score of each centroid against the population
        z = {}
        for trait, val in zip(trait_names, centroid):
            mu, sd = pop_stats[trait]
            z[trait] = (val - mu) / sd

        # Pick distinctive features: highest +z and lowest -z. Try a strict
        # threshold first, then relax, so near-mean clusters still get a
        # descriptive name instead of a generic "The Balanced".
        sorted_pos = sorted(z.items(), key=lambda kv: -kv[1])
        sorted_neg = sorted(z.items(), key=lambda kv: kv[1])

        top_high, top_low = [], []
        for threshold in (0.5, 0.25, 0.1):
            top_high = [t for t, v in sorted_pos if v >= threshold][:2]
            top_low  = [t for t, v in sorted_neg if v <= -threshold][:1]
            if top_high or top_low:
                break

        name_parts: List[str] = []
        for t in top_high:
            high_word = labels.get(t, (t, ""))[0]
            if high_word:
                name_parts.append(high_word)
        for t in top_low:
            low_word = labels.get(t, ("", t))[1]
            if low_word:
                name_parts.append(low_word)

        if name_parts:
            name = "The " + " ".join(name_parts[:2])
        else:
            # Truly flat profile: lean on whichever trait sits highest.
            lean = sorted_pos[0][0]
            name = f"The Balanced, {labels.get(lean, (lean, ''))[0]}-Leaning"

        tagline_parts = []
        for t in top_high[:2]:
            tagline_parts.append(f"high {t.lower()} ({z[t]:+.1f}sd)")
        for t in top_low[:1]:
            tagline_parts.append(f"low {t.lower()} ({z[t]:+.1f}sd)")
        if not tagline_parts:
            tagline_parts.append("centroid near population mean across all traits")
        tagline = ", ".join(tagline_parts)

        idx = int(cid) if cid.isdigit() else len(renamed)
        renamed[cid] = {
            "id":          info.get("id", f"cluster_{cid}"),
            "name":        name,
            "tagline":     tagline,
            "color":       COLORS[idx % len(COLORS)],
            "description": "Centroid (z vs population): " + ", ".join(
                f"{t} {z[t]:+.1f}sd" for t in trait_names),
            "centroid":    info.get("centroid"),
            "size":        info.get("size", 0),
            "weight":      info.get("weight"),
        }

    # Uniqueness pass: no two clusters in a test may share a name. When a
    # collision happens, append each cluster's next-most distinctive trait
    # word so both names stay descriptive.
    seen: Dict[str, List[str]] = {}
    for cid, info in renamed.items():
        seen.setdefault(info["name"], []).append(cid)
    for name, cids in seen.items():
        if len(cids) < 2:
            continue
        for cid in cids:
            info = renamed[cid]
            centroid = info.get("centroid") or []
            if len(centroid) == len(trait_names):
                zz = sorted(
                    ((t, (v - pop_stats[t][0]) / pop_stats[t][1])
                     for t, v in zip(trait_names, centroid)),
                    key=lambda kv: -abs(kv[1]),
                )
                for t, v in zz:
                    word = labels.get(t, (t, t))[0 if v >= 0 else 1] or t
                    candidate = f"{info['name']} ({word}-{'Forward' if v >= 0 else 'Light'})"
                    if candidate not in {x["name"] for x in renamed.values()}:
                        info["name"] = candidate
                        break
                else:
                    info["name"] = f"{info['name']} {cid}"
            else:
                info["name"] = f"{info['name']} {cid}"

    with open(arc_path, "w", encoding="utf-8") as fh:
        json.dump(renamed, fh, indent=2)
    return {
        "test_id":     test_id,
        "n_clusters":  len(renamed),
        "sample_names": [v["name"] for v in renamed.values()],
    }


if __name__ == "__main__":
    results = []
    for tid in TESTS:
        try:
            r = name_one(tid)
        except Exception as e:
            r = {"test_id": tid, "error": str(e)}
        results.append(r)
        if "error" in r:
            print(f"  {tid:<10} ERROR  {r['error']}")
        else:
            print(f"  {tid:<10} {r['n_clusters']:>2} clusters named   e.g. {r['sample_names']}")
    print("\nDone.")
