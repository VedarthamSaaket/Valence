import json
import os
from typing import Dict, List

import numpy as np
from scipy.optimize import linear_sum_assignment

MODELS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "backend", "models")

COLORS = ["#6B8CAE", "#AE6B8A", "#6BAE8A", "#AE9A6B", "#8A6BAE", "#6BAE9A"]

PROTOTYPES: Dict[str, List[dict]] = {
    "hexaco": [
        {"name": "Socially Considerate", "target": [0.9, 0.1, -0.4, 0.6, 0.2, -0.2],
         "tagline": "Fair-minded, patient and modest, with a quieter social presence",
         "description": "High Honesty-Humility and Agreeableness with slightly lower Extraversion."},
        {"name": "Adaptable Middle", "target": [-0.4, 0.2, 0.4, -0.2, -0.2, 0.1],
         "tagline": "Near the centre on every factor, leaning outgoing and pragmatic",
         "description": "No extreme factor; mildly higher Extraversion and mildly lower Honesty-Humility."},
        {"name": "Withdrawn", "target": [0.0, 0.6, -0.9, -0.7, -0.5, -0.7],
         "tagline": "Reserved and emotionally sensitive, cautious with people and new ideas",
         "description": "Low Extraversion, Agreeableness and Openness with higher Emotionality."},
        {"name": "Self-Focused", "target": [-1.4, -0.7, 0.2, -1.1, 0.2, 0.3],
         "tagline": "Competitive and unsentimental, driven by personal advantage",
         "description": "Very low Honesty-Humility and Agreeableness with low Emotionality."},
        {"name": "Role Model", "target": [0.3, -0.6, 1.2, 1.1, 0.4, 0.7],
         "tagline": "Outgoing, tolerant, curious and emotionally steady",
         "description": "High Extraversion, Agreeableness and Openness with low Emotionality."},
    ],
    "ambi": [
        {"name": "Role Model", "target": [-0.9, 0.7, 0.6, 0.7, 0.8],
         "tagline": "Emotionally steady, outgoing, open, considerate and dependable",
         "description": "Low Neuroticism with high scores on the other four domains."},
        {"name": "Self-Centred", "target": [0.1, 0.7, -0.4, -0.8, -0.7],
         "tagline": "Outgoing and assertive, with less concern for others and for order",
         "description": "High Extraversion with below-average Openness, Agreeableness and Conscientiousness."},
        {"name": "Reserved", "target": [-0.4, -0.7, -0.6, 0.2, 0.2],
         "tagline": "Calm and private, steady and considerate, with settled interests",
         "description": "Low Neuroticism, Extraversion and Openness with average Agreeableness and Conscientiousness."},
        {"name": "Tense and Withdrawn", "target": [1.1, -0.8, -0.3, -0.6, -1.0],
         "tagline": "Emotionally reactive and reserved, with less trust and less structure",
         "description": "High Neuroticism with low Extraversion, Agreeableness and Conscientiousness. This profile does not correspond to one of the four published types."},
        {"name": "Average", "target": [0.5, 0.2, -0.2, 0.0, -0.1],
         "tagline": "Close to the middle on most domains, a little more emotionally reactive",
         "description": "Near-average domain scores with somewhat higher Neuroticism."},
    ],
    "darktriad": [
        {"name": "Benevolent", "target": [-1.5, -1.0, -1.4],
         "tagline": "Very low on all three dark traits",
         "description": "Low Machiavellianism, narcissism and psychopathy."},
        {"name": "Low Dark Triad", "target": [-0.3, -0.4, -0.5],
         "tagline": "Below the sample average on all three dark traits",
         "description": "Mildly low Machiavellianism, narcissism and psychopathy."},
        {"name": "Moderate Dark Triad", "target": [0.5, 0.3, 0.5],
         "tagline": "Above the sample average on all three dark traits",
         "description": "Mildly elevated Machiavellianism, narcissism and psychopathy."},
        {"name": "High Dark Triad", "target": [1.2, 1.4, 1.4],
         "tagline": "Elevated on all three dark traits",
         "description": "High Machiavellianism, narcissism and psychopathy."},
    ],
    "npi": [
        {"name": "Low Narcissism", "target": [-0.8, -0.7, -0.8, -0.9, -0.8, -0.4, -0.8],
         "tagline": "Modest self-view across every facet",
         "description": "Low on all seven NPI facets."},
        {"name": "Moderate, Image-Invested", "target": [-0.1, -0.1, 0.1, 0.2, -0.1, 0.8, -0.1],
         "tagline": "Average self-regard with a clear investment in appearance",
         "description": "Mid-range facets with elevated Vanity."},
        {"name": "Moderate, Image-Indifferent", "target": [0.0, -0.1, -0.2, -0.2, -0.1, -0.9, -0.1],
         "tagline": "Average self-regard with little investment in appearance",
         "description": "Mid-range facets with low Vanity."},
        {"name": "High Narcissism", "target": [1.3, 1.2, 1.3, 1.4, 1.4, 0.8, 1.4],
         "tagline": "Elevated agentic and antagonistic self-view",
         "description": "High on all seven NPI facets, including Entitlement and Exploitativeness."},
    ],
    "dass": [
        {"name": "Low Distress", "target": [-1.3, -1.2, -1.4],
         "tagline": "Few symptoms of low mood, anxiety or tension this week",
         "description": "Low Depression, Anxiety and Stress scores."},
        {"name": "Mild Distress", "target": [-0.4, -0.5, -0.5],
         "tagline": "Some symptoms, below the reference sample average",
         "description": "Mildly low Depression, Anxiety and Stress scores."},
        {"name": "Elevated Distress", "target": [0.5, 0.5, 0.6],
         "tagline": "Symptoms above the reference sample average",
         "description": "Mildly elevated Depression, Anxiety and Stress scores."},
        {"name": "High Distress", "target": [1.4, 1.6, 1.5],
         "tagline": "Marked symptoms across mood, anxiety and tension",
         "description": "High Depression, Anxiety and Stress scores."},
    ],
    "kims": [
        {"name": "Low Mindfulness", "target": [-1.3, -1.1, -1.0, -0.7],
         "tagline": "Lower on all four mindfulness skills",
         "description": "Low Observing, Describing, Acting with Awareness and Accepting without Judgment."},
        {"name": "High Mindfulness", "target": [1.0, 1.1, 0.8, 0.5],
         "tagline": "Higher on all four mindfulness skills",
         "description": "High Observing, Describing, Acting with Awareness and Accepting without Judgment."},
        {"name": "Judgmentally Observing", "target": [0.4, -0.2, -0.5, -1.0],
         "tagline": "Notices inner experience closely but evaluates it harshly",
         "description": "Higher Observing with low Accepting without Judgment."},
        {"name": "Non-Judgmentally Aware", "target": [-0.3, -0.1, 0.3, 0.6],
         "tagline": "Present and accepting without closely monitoring sensations",
         "description": "Higher Acting with Awareness and Accepting without Judgment with lower Observing."},
    ],
    "hsq": [
        {"name": "Humor Denier", "target": [-1.1, -1.1, -0.4, -0.9],
         "tagline": "Uses little humor of any kind",
         "description": "Low on all four humor styles."},
        {"name": "Humor Endorser", "target": [0.9, 0.7, 0.9, 0.5],
         "tagline": "Uses every style of humor freely",
         "description": "High on all four humor styles."},
        {"name": "Self-Defeating Humorist", "target": [-0.4, -0.2, 0.0, 0.7],
         "tagline": "Leans on self-deprecation more than shared or coping humor",
         "description": "Elevated Self-Defeating humor with lower Affiliative humor."},
        {"name": "Positive Humor Endorser", "target": [0.4, 0.4, -0.7, -0.5],
         "tagline": "Uses warm and coping humor, avoids put-downs",
         "description": "Higher Affiliative and Self-Enhancing humor with low Aggressive and Self-Defeating humor."},
    ],
    "gcbs": [
        {"name": "Non-Believer", "target": [-1.3, -1.2, -0.9, -1.2, -1.3],
         "tagline": "Rejects conspiracy explanations across the board",
         "description": "Low on all five conspiracist belief factors."},
        {"name": "Grounded Skeptic", "target": [0.0, -0.2, -0.9, -0.4, -0.1],
         "tagline": "Some institutional doubt, but rejects extraterrestrial cover-up claims",
         "description": "Mid-range on institutional factors with low Extraterrestrial Coverup."},
        {"name": "Cautious Doubter", "target": [-0.4, -0.4, 0.1, -0.4, -0.2],
         "tagline": "Mostly trusting, with an open mind about the unexplained",
         "description": "Mildly low on institutional factors with average Extraterrestrial Coverup."},
        {"name": "Believer", "target": [0.7, 0.7, 0.7, 0.8, 0.7],
         "tagline": "Endorses conspiracy explanations more than most",
         "description": "Elevated on all five conspiracist belief factors."},
        {"name": "Strong Believer", "target": [1.4, 1.6, 1.2, 1.7, 1.2],
         "tagline": "Endorses conspiracy explanations across every theme",
         "description": "High on all five conspiracist belief factors."},
    ],
    "attachment": [
        {"name": "Secure", "target": [-0.8, -0.7, 1.1],
         "tagline": "Comfortable with closeness and unworried about abandonment",
         "description": "Low attachment anxiety and low attachment avoidance."},
        {"name": "Preoccupied", "target": [0.8, -0.7, -0.1],
         "tagline": "Seeks closeness and worries about losing it",
         "description": "High attachment anxiety with low attachment avoidance."},
        {"name": "Dismissing", "target": [-1.1, 1.4, -0.2],
         "tagline": "Self-reliant and uncomfortable with dependence",
         "description": "Low attachment anxiety with high attachment avoidance."},
        {"name": "Fearful-Avoidant", "target": [0.5, 0.8, -1.0],
         "tagline": "Wants closeness but keeps distance for fear of being hurt",
         "description": "High attachment anxiety and high attachment avoidance."},
    ],
}

CODE_TYPES: Dict[str, Dict[str, tuple]] = {
    "riasec": {
        "Realistic": ("Doer", "hands-on, practical work with tools and things"),
        "Investigative": ("Thinker", "analysis, research and abstract problems"),
        "Artistic": ("Creator", "self-expression and unstructured creative work"),
        "Social": ("Helper", "teaching, supporting and caring for people"),
        "Enterprising": ("Persuader", "leading, selling and taking initiative"),
        "Conventional": ("Organizer", "order, detail and structured procedures"),
    },
    "fti": {
        "Explorer": ("Explorer", "novelty, spontaneity and curiosity"),
        "Builder": ("Builder", "caution, loyalty and respect for norms"),
        "Director": ("Director", "analysis, directness and tough-mindedness"),
        "Negotiator": ("Negotiator", "empathy, intuition and seeing the whole picture"),
    },
}


def _stats(test_id: str):
    with open(os.path.join(MODELS_DIR, f"{test_id}_meta.json"), encoding="utf-8") as fh:
        meta = json.load(fh)
    with open(os.path.join(MODELS_DIR, f"{test_id}_archetypes.json"), encoding="utf-8") as fh:
        archetypes = json.load(fh)
    with open(os.path.join(MODELS_DIR, f"{test_id}_distributions.json"), encoding="utf-8") as fh:
        dists = json.load(fh)
    names = meta["trait_names"]
    mu = np.array([np.mean(dists[n]) for n in names])
    sd = np.array([np.std(dists[n]) + 1e-8 for n in names])
    return meta, archetypes, names, mu, sd


def _entry(info: dict, idx: int, name: str, tagline: str, description: str, basis: str) -> dict:
    return {
        "id": info.get("id"),
        "name": name,
        "tagline": tagline,
        "color": COLORS[idx % len(COLORS)],
        "description": description,
        "basis": basis,
        "centroid": info.get("centroid"),
        "size": info.get("size", 0),
        "weight": info.get("weight"),
    }


def name_by_prototype(test_id: str) -> Dict:
    meta, archetypes, names, mu, sd = _stats(test_id)
    protos = PROTOTYPES[test_id]
    cids = list(archetypes.keys())
    z = np.array([(np.array(archetypes[c]["centroid"]) - mu) / sd for c in cids])
    targets = np.array([p["target"] for p in protos])
    cost = np.linalg.norm(z[:, None, :] - targets[None, :, :], axis=2)
    rows, cols = linear_sum_assignment(cost)
    out = {}
    for r, c in zip(rows, cols):
        p = protos[c]
        out[cids[r]] = _entry(archetypes[cids[r]], int(cids[r]), p["name"], p["tagline"],
                              p["description"], meta.get("k_basis", ""))
        out[cids[r]]["match_distance"] = round(float(cost[r, c]), 3)
    return {c: out[c] for c in cids if c in out}


def name_by_code(test_id: str) -> Dict:
    meta, archetypes, names, mu, sd = _stats(test_id)
    types = CODE_TYPES[test_id]
    out = {}
    for cid, info in archetypes.items():
        primary = names[int(cid)]
        noun, pull = types[primary]
        name = primary if noun == primary else f"{primary} ({noun})"
        out[cid] = _entry(info, int(cid), name, f"Drawn to {pull}",
                          f"{primary} is the highest of this person's scores relative to the reference sample.",
                          meta.get("k_basis", ""))
    return out


def name_one(test_id: str) -> Dict:
    named = name_by_code(test_id) if test_id in CODE_TYPES else name_by_prototype(test_id)
    with open(os.path.join(MODELS_DIR, f"{test_id}_archetypes.json"), "w", encoding="utf-8") as fh:
        json.dump(named, fh, indent=2)
    return named


if __name__ == "__main__":
    for tid in list(PROTOTYPES.keys()) + list(CODE_TYPES.keys()):
        named = name_one(tid)
        print(f"{tid:<11}", [(v["name"], v.get("match_distance")) for v in named.values()])
