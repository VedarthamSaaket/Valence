from __future__ import annotations

import atexit
import json
import os
import re
import shutil
import subprocess
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from typing import Dict, List, Optional

import httpx

from ml import meaning_check
from ml.psych_bibliography import applicable_points, general_points, references
from ml.psych_lexicon import INSTRUMENTS, LITERATURE, PATTERNS, SUPPORT_NOTE, TRAITS

MODEL_KEY = "mentallama"
MODEL_LABEL = "MentaLLaMA-chat-7B, interpretable mental-health analysis model (hosted locally)"

ENABLE_DEEP_DIVE = os.getenv("ENABLE_DEEP_DIVE", "true").lower() in ("1", "true", "yes")
MENTALLAMA_URL = os.getenv("MENTALLAMA_URL", "http://127.0.0.1:8081").rstrip("/")
MENTALLAMA_MODEL_PATH = os.getenv(
    "MENTALLAMA_MODEL_PATH",
    os.path.join(os.path.dirname(__file__), "..", "models", "llm", "MentaLLaMA-chat-7B.Q4_K_M.gguf"),
)
MENTALLAMA_AUTOSTART = os.getenv("MENTALLAMA_AUTOSTART", "true").lower() in ("1", "true", "yes")
INFER_TIMEOUT = float(os.getenv("MENTALLAMA_TIMEOUT", "120"))
MAX_BULLETS = 5
PARALLEL_SLOTS = int(os.getenv("MENTALLAMA_SLOTS", "4"))
LOG_DIR = os.path.join(os.path.dirname(__file__), "finetune_data")

SYSTEM_PROMPT = (
    "You are MentaLLaMA, a mental-health and personality analysis model. You write precise, "
    "non-diagnostic psychological interpretations of self-report questionnaire profiles using "
    "correct psychological terminology. You never state or imply a clinical diagnosis."
)

_server_lock = threading.Lock()
_server_proc: Optional[subprocess.Popen] = None


def enabled() -> bool:
    return ENABLE_DEEP_DIVE


def health_ok(timeout: float = 2.0) -> bool:
    try:
        r = httpx.get(f"{MENTALLAMA_URL}/health", timeout=timeout)
        return r.status_code == 200
    except Exception:
        return False


def _find_server_binary() -> Optional[str]:
    explicit = os.getenv("LLAMA_SERVER_BIN")
    if explicit and os.path.exists(explicit):
        return explicit
    found = shutil.which("llama-server")
    if found:
        return found
    for candidate in ("/opt/homebrew/bin/llama-server", "/usr/local/bin/llama-server"):
        if os.path.exists(candidate):
            return candidate
    return None


def _stop_server() -> None:
    global _server_proc
    if _server_proc and _server_proc.poll() is None:
        _server_proc.terminate()
    _server_proc = None


def ensure_server(wait: float = 90.0) -> bool:
    global _server_proc
    if not enabled():
        return False
    if health_ok():
        return True
    if not MENTALLAMA_AUTOSTART:
        return False
    with _server_lock:
        if health_ok():
            return True
        if _server_proc is None or _server_proc.poll() is not None:
            binary = _find_server_binary()
            model = os.path.abspath(MENTALLAMA_MODEL_PATH)
            if not binary or not os.path.exists(model):
                print(f"[psych] cannot start MentaLLaMA (binary={binary}, model exists={os.path.exists(model)})")
                return False
            port = MENTALLAMA_URL.rsplit(":", 1)[-1]
            _server_proc = subprocess.Popen(
                [binary, "-m", model, "--host", "127.0.0.1", "--port", port, "-ngl", "99",
                 "-c", str(2048 * PARALLEL_SLOTS), "-np", str(PARALLEL_SLOTS)],
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
            )
            atexit.register(_stop_server)
            print(f"[psych] starting MentaLLaMA server on port {port}")
        deadline = time.time() + wait
        while time.time() < deadline:
            if health_ok():
                print("[psych] MentaLLaMA ready")
                return True
            if _server_proc.poll() is not None:
                return False
            time.sleep(1.0)
    return False


def status() -> dict:
    return {"enabled": enabled(), "alive": health_ok()}


def _complete(user_prompt: str, max_tokens: int = 220, temperature: float = 0.45) -> Optional[str]:
    prompt = f"[INST] <<SYS>>\n{SYSTEM_PROMPT}\n<</SYS>>\n\n{user_prompt} [/INST] "
    try:
        r = httpx.post(
            f"{MENTALLAMA_URL}/completion",
            json={"prompt": prompt, "n_predict": max_tokens, "temperature": temperature,
                  "top_p": 0.9, "repeat_penalty": 1.12, "stop": ["[INST]", "\n\n"]},
            timeout=INFER_TIMEOUT,
        )
        r.raise_for_status()
        return (r.json().get("content") or "").strip()
    except Exception as e:
        print(f"[psych] MentaLLaMA call failed: {type(e).__name__}: {e}")
        return None


DIRECTION = {
    "high": "Score direction: HIGH on {trait}. The person shows a lot of {trait}.",
    "low": "Score direction: LOW on {trait}. The person shows little {trait}; do not describe them as having it.",
    "mid": "Score direction: MID-RANGE on {trait}. Neither clearly high nor clearly low; describe it as moderate.",
}


LEVELS = ["Low", "Moderate", "High"]
GRADE_CAP = {"strong": "High", "moderate": "Moderate", "limited": "Low"}
_DECIMAL = re.compile(r"(?<![\w.])([01]\.\d{1,2})(?![\d])")
_PERCENTILE = re.compile(r"(\d{1,3})(?:st|nd|rd|th)?\s*(?:percentile|%)", re.IGNORECASE)


def _literature(test_id: str, item: dict) -> dict:
    base = LITERATURE.get(test_id, {"grade": "limited", "sources": "", "note": ""})
    if item.get("kind") == "integration":
        grade = "moderate" if base["grade"] == "strong" else base["grade"]
        return {"grade": grade, "sources": base["sources"],
                "note": "A synthesis across constructs; no single paper establishes it."}
    if item.get("kind") == "pattern":
        return {"grade": base.get("pattern_grade", base["grade"]), "sources": item["framework"],
                "note": base["note"]}
    override = (base.get("traits") or {}).get(item["traits"][0], {})
    return {"grade": override.get("grade", base["grade"]), "sources": base["sources"],
            "note": override.get("note", base["note"])}


def _figures_ok(text: str, scores: Dict[str, float], pcts: Dict[str, int]) -> bool:
    allowed_scores = set()
    for v in scores.values():
        allowed_scores.update({f"{v:.2f}", f"{v:.1f}", f"{v:.2f}".rstrip("0")})
    allowed_pcts = {int(v) for v in pcts.values()}
    for found in _DECIMAL.findall(text):
        if found not in allowed_scores:
            return False
    for found in _PERCENTILE.findall(text):
        if int(found) not in allowed_pcts:
            return False
    return True


def _stated_direction(text: str, trait: str) -> str:
    answer = _complete(
        f"Paragraph: {text}\n\n"
        f"Question: According to this paragraph only, is the person's level of {trait} described as "
        "HIGH, LOW or MID-RANGE? If the paragraph does not say, answer UNSTATED. "
        "Answer with exactly one word.",
        max_tokens=6, temperature=0.0,
    ) or ""
    word = answer.upper()
    if "UNSTATED" in word:
        return "unstated"
    if "MID" in word or "MODERATE" in word:
        return "mid"
    if "LOW" in word:
        return "low"
    if "HIGH" in word or "ELEVATED" in word:
        return "high"
    return "unstated"


def _verify(text: str, traits: List[str], scores: Dict[str, float], pcts: Dict[str, int]) -> dict:
    figures = _figures_ok(text, scores, pcts)
    directions = {}
    for trait in traits:
        stated = _stated_direction(text, trait)
        actual = _band(pcts.get(trait, 50))
        if stated == "unstated":
            directions[trait] = "unstated"
        elif stated == actual:
            directions[trait] = "match"
        elif "mid" in (stated, actual):
            directions[trait] = "shifted"
        else:
            directions[trait] = "contradicted"
    values = list(directions.values())
    if not figures or "contradicted" in values:
        status = "failed"
    elif values and all(v == "match" for v in values):
        status = "verified"
    elif "match" in values or "shifted" in values:
        status = "partly verified"
    else:
        status = "unverified"
    return {"status": status, "figures_match": figures, "directions": directions}


BASE_CONFIDENCE = 50
_CITATION = re.compile(r"([A-Z][A-Za-z\-]+)(?:\s+et al\.?|\s+(?:&|and)\s+[A-Z][A-Za-z\-]+)*,?\s*\(?((?:19|20)\d{2})\)?")


def _citations_ok(text: str, test_id: str, item: dict) -> bool:
    from ml.psych_bibliography import BIBLIOGRAPHY
    papers = BIBLIOGRAPHY.get(test_id, [])
    extra = item.get("framework", "") + " " + INSTRUMENTS.get(test_id, {}).get("citation", "")
    for surname, year in _CITATION.findall(text):
        known = any(surname in p["names"] and str(p["year"]) == year for p in papers)
        if not known and not (surname in extra and year in extra):
            return False
    return True


def _cited_points(text: str, points: List[dict]) -> List[str]:
    return sorted({p["label"] for p in points if any(name in text for name in p["names"])})


def _plain(construct: str) -> str:
    core = construct.split(":", 1)[1].strip() if ":" in construct else construct
    return f"This person shows {core[0].lower() + core[1:]}."


def _premises(item: dict, items: List[dict], pcts: Dict[str, int]) -> List[str]:
    words = {"high": "high", "low": "low", "mid": "in the middle range"}
    out = [f"This person's {t} score is {words[_band(pcts.get(t, 50))]}." for t in item["traits"]]
    if item["kind"] == "integration":
        out += [_plain(i["construct"]) for i in items]
    else:
        out.append(_plain(item["construct"]))
    out += [p["text"] for p in item.get("points", [])]
    return out


def _confidence(item: dict, text: str, verification: dict, meaning: Optional[dict]) -> dict:
    points = item.get("points", [])
    directions = list(verification["directions"].values())
    matched = sum(1 for d in directions if d == "match")
    labels = sorted({p["label"] for p in points})
    cited = _cited_points(text, points)
    research = 20 if len(points) >= 2 else 12 if points else 0
    grounding = 5 if cited else 0
    check = int(round(5 * matched / len(directions))) if directions else 0
    sense = 5 + int(round(10 * meaning["supported"] / meaning["sentences"])) if meaning else 0
    score = BASE_CONFIDENCE + research + grounding + check + sense
    reasons = [
        (f"Research match: your scores meet the conditions of {len(points)} published finding(s): {'; '.join(labels)}."
         if points else "Research match: no finding in the bibliography applies directly to this score pattern."),
        (f"Grounding: the paragraph cites {'; '.join(cited)}." if cited
         else "Grounding: the paragraph does not cite a specific finding."),
        f"Score check: {matched} of {len(directions)} score directions confirmed; every quoted figure matches your results.",
        (f"Meaning check: none of the {meaning['sentences']} sentences contradicts the construct or the findings; "
         f"{meaning['supported']} are directly supported by them." if meaning
         else "Meaning check: not available for this paragraph."),
    ]
    return {"level": "High" if score >= 80 else "Moderate", "score": score,
            "research_points": labels, "verification": verification, "meaning": meaning, "reasons": reasons}


def _band(pct: int) -> str:
    if pct >= 65:
        return "high"
    if pct <= 35:
        return "low"
    return "mid"


def _evidence(traits: List[str], scores: Dict[str, float], pcts: Dict[str, int]) -> str:
    return "; ".join(
        f"{t} {scores.get(t, 0):.2f} ({_ordinal(pcts.get(t, 50))} percentile)" for t in traits if t in scores
    )


def _ordinal(n: int) -> str:
    n = int(n)
    suffix = "th" if 10 <= n % 100 <= 20 else {1: "st", 2: "nd", 3: "rd"}.get(n % 10, "th")
    return f"{n}{suffix}"


def select_constructs(test_id: str, scores: Dict[str, float], pcts: Dict[str, int]) -> List[dict]:
    chosen: List[dict] = []
    covered = set()
    bands = {t: _band(p) for t, p in pcts.items()}
    for cond, construct, framework, traits in PATTERNS.get(test_id, []):
        try:
            hit = cond(pcts)
        except Exception:
            hit = False
        if hit and len(chosen) < 2:
            levels = ", ".join(
                f"{ {'high': 'HIGH', 'low': 'LOW', 'mid': 'MID-RANGE'}[_band(pcts.get(t, 50))] } on {t}"
                for t in traits[:4]
            )
            chosen.append({"construct": construct, "framework": framework,
                           "traits": traits[:4], "kind": "pattern",
                           "points": applicable_points(test_id, traits[:4], bands)[:3],
                           "direction": f"Score directions: {levels}. State each exactly as given."})
            if len(traits) <= 2:
                covered.update(traits)
    lexicon = TRAITS.get(test_id, {})
    ranked = sorted(scores.keys(), key=lambda t: -abs(pcts.get(t, 50) - 50))
    for trait in [t for t in ranked if t not in covered] + [t for t in ranked if t in covered]:
        if len(chosen) >= MAX_BULLETS:
            break
        entry = lexicon.get(trait)
        if not entry or any(c["kind"] == "trait" and c["traits"] == [trait] for c in chosen):
            continue
        band = _band(pcts.get(trait, 50))
        chosen.append({"construct": entry[band], "framework": entry["framework"],
                       "traits": [trait], "kind": "trait",
                       "points": applicable_points(test_id, [trait], bands)[:3],
                       "direction": DIRECTION[band].format(trait=trait)})
    return chosen


def _profile_block(scores: Dict[str, float], pcts: Dict[str, int]) -> str:
    return "\n".join(
        f"  {name}: {score:.2f} ({_ordinal(pcts.get(name, 50))} percentile)" for name, score in scores.items()
    )


def _notes_block(context_notes: Optional[List[Dict]]) -> str:
    if not context_notes:
        return ""
    lines = []
    for n in context_notes[:6]:
        note = (n.get("note") or "").strip()
        if note:
            q = (n.get("question") or "").strip()
            lines.append(f'  On "{q}": {note[:240]}' if q else f"  {note[:240]}")
    if not lines:
        return ""
    return "Context the person volunteered:\n" + "\n".join(lines) + "\n\n"


def _header(test_id: str, scores: Dict[str, float], pcts: Dict[str, int], archetype: dict,
            context_notes: Optional[List[Dict]]) -> str:
    inst = INSTRUMENTS.get(test_id, {"label": test_id, "citation": ""})
    arch = (archetype or {}).get("name") or "unlabelled"
    return (
        f"A person completed the {inst['label']} ({inst['citation']}). "
        f"Their profile type is '{arch}'.\n\n"
        "Scored profile (0-1 scale, percentile within the self-selected reference sample):\n"
        f"{_profile_block(scores, pcts)}\n\n{_notes_block(context_notes)}"
    )


def _bullet_prompt(header: str, item: dict, scores: Dict[str, float], pcts: Dict[str, int]) -> str:
    return (
        header
        + "Write one analytic paragraph about the construct below. Requirements: 3 to 4 sentences; "
          "cite the score or percentile as evidence; explain the underlying psychological mechanism "
          "with precise terminology; finish with one concrete, observable day-to-day manifestation. "
          "The construct line states the finding: explain it, never contradict it, and do not "
          "attribute difficulties that the scores do not show. Do not diagnose. Do not use headings "
          "or lists.\n\n"
        f"Construct: {item['construct']}\n"
        f"Theoretical framework: {item['framework']}\n"
        f"Evidence: {_evidence(item['traits'], scores, pcts)}"
        + (f"\n{item['direction']}" if item.get("direction") else "")
        + _findings_block(item.get("points", []))
    )


def _findings_block(points: List[dict]) -> str:
    if not points:
        return ""
    lines = "\n".join(
        f"  - [{p['label']}] Study: {p.get('summary', '')} Finding that applies here: {p['text']}" for p in points
    )
    return ("\nPublished findings that apply to this person. Base the paragraph on them, cite the authors "
            f"and year in the text, and cite no other source:\n{lines}")


def _integration_prompt(header: str, items: List[dict], points: Optional[List[dict]] = None) -> str:
    listing = "\n".join(f"  - {i['construct']}" for i in items)
    return (
        header
        + "The following constructs characterise this profile:\n"
        f"{listing}\n\n"
        "Write one integrative paragraph of 3 to 4 sentences: explain how these constructs interact "
        "as a single functional pattern, name one adaptive strength, and name one self-regulation or "
        "interpersonal area where the pattern could create friction. Use precise psychological "
        "terminology. Do not diagnose. Do not use headings or lists."
        + _findings_block(points or [])
    )


_DIAGNOSTIC = re.compile(
    r"\b(you (have|suffer from)|is suffering from|diagnos(is|ed) (of|with)|meets? (the )?criteria for)\b",
    re.IGNORECASE,
)


def _clean(text: Optional[str]) -> str:
    if not text:
        return ""
    t = " ".join(text.split())
    t = re.sub(r"^(Sure[,!.]?|Certainly[,!.]?|Here is[^:]*:)\s*", "", t, flags=re.IGNORECASE)
    t = re.split(r"\b(?:References?|Bibliography|Sources?)\s*:", t, maxsplit=1)[0].strip()
    cut = max(t.rfind("."), t.rfind("!"), t.rfind("?"))
    if cut > 40:
        t = t[:cut + 1]
    if len(t) < 60 or _DIAGNOSTIC.search(t):
        return ""
    return t


def _log(test_id: str, record: dict) -> None:
    try:
        os.makedirs(LOG_DIR, exist_ok=True)
        with open(os.path.join(LOG_DIR, f"{test_id}.jsonl"), "a", encoding="utf-8") as f:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")
    except Exception as e:
        print(f"[psych log] {e}")


def enrich_result(test_id: str, trait_scores: Dict[str, float], percentiles: Dict[str, int],
                  archetype: dict, insights: Dict, context_notes: Optional[List[Dict]] = None) -> Dict:
    if not enabled():
        insights["deep_dive"] = {"bullets": [], "insights": [], "status": "unavailable"}
        return insights

    t0 = time.time()
    bullets: List[dict] = []
    withheld = 0
    if ensure_server():
        header = _header(test_id, trait_scores, percentiles, archetype or {}, context_notes)
        items = select_constructs(test_id, trait_scores, percentiles)

        bands = {t: _band(p) for t, p in percentiles.items()}
        multi = [p for p in applicable_points(test_id, list(trait_scores.keys()), bands)
                 if sum(1 for it in items if p in it.get("points", [])) != 1]
        integration_item = {"construct": "Integrative formulation",
                            "framework": "Functional interaction of the constructs above",
                            "traits": list(trait_scores.keys()), "kind": "integration",
                            "points": (general_points(test_id) + multi)[:3]}

        def write(item: dict):
            if item["kind"] == "integration":
                prompt, budget = _integration_prompt(header, items, item["points"]), 260
            else:
                prompt, budget = _bullet_prompt(header, item, trait_scores, percentiles), 220
            premises = _premises(item, items, percentiles)
            for temperature in (0.45, 0.3):
                text = _clean(_complete(prompt, max_tokens=budget, temperature=temperature))
                if not text:
                    continue
                if not _citations_ok(text, test_id, item):
                    continue
                verification = _verify(text, item["traits"], trait_scores, percentiles)
                rejected = ("failed", "unverified") if item["kind"] == "trait" else ("failed",)
                if verification["status"] in rejected:
                    continue
                meaning = meaning_check.check(text, premises)
                if meaning and meaning["contradicted"]:
                    continue
                return text, verification, meaning
            return "", None, None

        jobs = items + ([integration_item] if len(items) >= 2 else [])
        with ThreadPoolExecutor(max_workers=PARALLEL_SLOTS) as pool:
            written = list(pool.map(write, jobs))

        for item, (text, verification, meaning) in zip(jobs, written):
            if not text:
                withheld += 1
                continue
            bullets.append({
                "construct": item["construct"],
                "framework": item["framework"],
                "evidence": _evidence(item["traits"], trait_scores, percentiles),
                "text": text,
                "confidence": _confidence(item, text, verification, meaning),
            })
        if len([b for b in bullets if b["construct"] != "Integrative formulation"]) < 2:
            bullets = [b for b in bullets if b["construct"] != "Integrative formulation"]

    latency = round(time.time() - t0, 2)
    inst = INSTRUMENTS.get(test_id, {})
    counts = {lvl: sum(1 for b in bullets if b["confidence"]["level"] == lvl) for lvl in ("High", "Moderate")}
    insights["deep_dive"] = {
        "instrument": inst.get("label"),
        "citation": inst.get("citation"),
        "bullets": bullets,
        "insights": [f"{b['construct']}. {b['text']}" for b in bullets],
        "support_note": SUPPORT_NOTE.get(test_id),
        "profile_fit": (archetype or {}).get("membership_probability"),
        "confidence_summary": {"counts": counts, "withheld": withheld} if bullets else None,
        "references": references(test_id),
        "source_note": (
            "This deep dive is generated as psychologically compliant text, based on published research "
            "for this instrument."
        ),
        "confidence_method": (
            "Every paragraph starts from the same base confidence. Confidence rises when your scores meet "
            "the conditions of findings in the published research listed below, when the paragraph is "
            "grounded in those findings, when it states your score directions and figures correctly, and "
            "when its sentences are supported by the construct and the findings. Paragraphs that contradict "
            "your scores, contradict the research, or cite work outside the bibliography are withheld."
        ),
        "latency_s": latency,
        "status": "ok" if bullets else "unavailable",
    }
    _log(test_id, {
        "ts": time.time(), "test_id": test_id, "model_key": MODEL_KEY,
        "trait_scores": trait_scores, "percentiles": percentiles,
        "archetype": {k: (archetype or {}).get(k) for k in ("id", "name", "tagline")},
        "bullets": bullets, "latency_s": latency,
        "status": "ok" if bullets else "unavailable",
    })
    if bullets:
        print(f"[psych] MentaLLaMA deep dive for {test_id}: {len(bullets)} bullets in {latency}s")
    return insights
