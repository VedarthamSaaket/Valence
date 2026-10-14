from typing import Dict, List, Optional

from ml.inference import ANSWER_RANGE, SCORERS, answers_in_range, calc_percentiles, load_json

MAX_TRAITS = 3
MAX_ITEMS = 3


def _questions(test_id: str) -> Dict[str, dict]:
    from routers.tests import load_questions

    data = load_questions(test_id)
    return {q.get("id"): q for q in (data.get("questions", []) if isinstance(data, dict) else data)}


def _neutral(test_id: str, value):
    lo, hi = ANSWER_RANGE[test_id]
    if hi - lo == 1:
        return lo + hi - value
    return (lo + hi) / 2


def _chosen(question: dict, value) -> Optional[str]:
    for option in question.get("options") or []:
        if option.get("value") == value:
            return option.get("text")
    return None


def drivers(test_id: str, raw: Dict[str, int], pcts: Dict[str, int]) -> List[dict]:
    scorer = SCORERS.get(test_id)
    if not scorer or test_id not in ANSWER_RANGE or not raw:
        return []
    base = scorer(raw)
    questions = _questions(test_id)
    effects: Dict[str, List[tuple]] = {trait: [] for trait in base}
    for qid, value in raw.items():
        if qid not in questions:
            continue
        altered = dict(raw)
        altered[qid] = _neutral(test_id, value)
        shifted = scorer(altered)
        for trait in base:
            delta = base[trait] - shifted[trait]
            if abs(delta) > 1e-9:
                effects[trait].append((delta, qid, value))

    out = []
    ranked = sorted(base, key=lambda t: -abs(pcts.get(t, 50) - 50))
    lo, hi = ANSWER_RANGE[test_id]
    shown = []
    for trait in ranked:
        if len(out) >= MAX_TRAITS:
            break
        raised = pcts.get(trait, 50) >= 50
        pushing = sorted([e for e in effects[trait] if (e[0] > 0) == raised], key=lambda e: -abs(e[0]))
        top = {qid for _, qid, _ in pushing[:MAX_ITEMS]}
        if not pushing or top in shown:
            continue
        shown.append(top)
        out.append({
            "trait": trait,
            "percentile": int(pcts.get(trait, 50)),
            "direction": "raised" if raised else "lowered",
            "answers_in_direction": len(pushing),
            "answers_counted": len(effects[trait]),
            "items": [{"text": questions[qid].get("text") or _chosen(questions[qid], value) or qid,
                       "answer": value, "choice": _chosen(questions[qid], value)}
                      for _, qid, value in pushing[:MAX_ITEMS]],
        })
    for entry in out:
        entry["scale"] = [lo, hi]
    return out


def type_basis(test_id: str, archetype_id: Optional[str], pcts: Dict[str, int]) -> Optional[dict]:
    catalogue = load_json(test_id, "archetypes") or {}
    meta = load_json(test_id, "meta") or {}
    names = meta.get("trait_names") or []
    info = next((v for k, v in catalogue.items() if v.get("id") == archetype_id or k == archetype_id), None)
    if not info or not info.get("centroid") or len(info["centroid"]) != len(names):
        return None
    typical = calc_percentiles(test_id, {n: float(c) for n, c in zip(names, info["centroid"])})
    defining = meta.get("cluster_traits") or names
    rows = sorted(
        [{"trait": t, "typical": int(typical[t]), "yours": int(pcts.get(t, 50))} for t in defining if t in typical],
        key=lambda r: -abs(r["typical"] - 50),
    )
    marked = [r for r in rows if r["typical"] >= 65 or r["typical"] <= 35]
    shared = [r for r in marked if (r["yours"] >= 65) == (r["typical"] >= 65) and (r["yours"] <= 35) == (r["typical"] <= 35)]
    loose = bool(marked) and len(shared) * 2 < len(marked)
    return {
        "fit": "loose" if loose else "close",
        "name": info.get("name"),
        "meaning": info.get("tagline"),
        "definition": info.get("description"),
        "share_pct": round(float(info["weight"]) * 100, 1) if info.get("weight") is not None else None,
        "types": len(catalogue),
        "basis": info.get("basis"),
        "traits": rows[:4],
    }


def explain(test_id: str, raw: Dict[str, int], pcts: Dict[str, int], archetype_id: Optional[str]) -> dict:
    valid = answers_in_range(test_id, raw)
    return {
        "scale_invalid": not valid,
        "type": type_basis(test_id, archetype_id, pcts),
        "drivers": drivers(test_id, raw, pcts) if valid else [],
    }
