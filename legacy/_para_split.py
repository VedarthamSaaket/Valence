#!/usr/bin/env python3
"""Split all 17 question files into paraphrasing chunks for parallel agents.
Writes one input chunk per file to /tmp/para_in/, preserves originals for merge."""
import json, os, shutil

BASE = os.path.expanduser("~/Valence_backup/shared/questions")
ROOT = os.path.expanduser("~/Valence_backup/_para")
IN   = os.path.join(ROOT, "in")
OUT  = os.path.join(ROOT, "out")
for d in (IN, OUT):
    shutil.rmtree(d, ignore_errors=True)
    os.makedirs(d, exist_ok=True)

CHUNK = 28

# Per-test guidance: construct + voice/person + scale meaning. Keeps meaning + direction intact.
META = {
  "hexaco": {
    "construct": "HEXACO six-factor personality. Each item is a first-person 'I ...' self-statement.",
    "voice": "Keep FIRST PERSON ('I ...'). One sentence each.",
    "scale": "Agreement scale, 1 strongly disagree to 7 strongly agree.",
  },
  "ambi": {
    "construct": "Broad IPIP personality inventory. First-person 'I ...' self-statements covering many traits.",
    "voice": "Keep FIRST PERSON ('I ...'). One sentence each.",
    "scale": "Agreement scale, 1 strongly disagree to 7 strongly agree.",
  },
  "sixteenpf": {
    "construct": "Cattell 16 Personality Factors. Items are second-person everyday scenarios ('You ...').",
    "voice": "Keep SECOND PERSON scenario style ('You ...').",
    "scale": "1 not at all like me to 5 very much like me.",
  },
  "darktriad": {
    "construct": "Short Dark Triad (Machiavellianism, Narcissism, Psychopathy). Second-person 'You ...' style.",
    "voice": "Keep SECOND PERSON ('You ...'). Stay neutral and non-judgemental.",
    "scale": "1 not at all like me to 5 very much like me.",
  },
  "npi": {
    "construct": "Narcissistic Personality Inventory. FORCED CHOICE: each item is two opposing statements. The value number on each option is a scoring key and must stay attached to the SAME meaning.",
    "voice": "First person. Paraphrase BOTH options. NEVER swap which value maps to which meaning.",
    "scale": "Pick the statement that fits you better.",
  },
  "gcbs": {
    "construct": "Generic Conspiracist Beliefs Scale. Each item is a belief claim about hidden actors/cover-ups.",
    "voice": "Keep the claim's meaning and strength exactly. Only simplify vocabulary. Do NOT soften or strengthen the belief. Stay neutral, third person about 'the government / groups / organisations'.",
    "scale": "1 definitely not true to 5 definitely true.",
  },
  "fti": {
    "construct": "Fisher Temperament Inventory (Explorer, Builder, Director, Negotiator). First-person 'I ...'.",
    "voice": "Keep FIRST PERSON ('I ...').",
    "scale": "1 strongly disagree to 4 strongly agree.",
  },
  "kims": {
    "construct": "Kentucky Inventory of Mindfulness Skills. First-person 'I ...' about noticing, describing, awareness, acceptance.",
    "voice": "Keep FIRST PERSON ('I ...').",
    "scale": "1 never or rarely true to 5 very often or always true.",
  },
  "hsq": {
    "construct": "Humor Styles Questionnaire. First-person 'I ...' about how you use humour.",
    "voice": "Keep FIRST PERSON ('I ...').",
    "scale": "1 never or rarely true to 5 very often or always true.",
  },
  "pid5": {
    "construct": "Personality Inventory for DSM-5 Brief Form, used here as a personality-STYLE descriptor, not a diagnosis. First-person 'I ...'.",
    "voice": "Keep FIRST PERSON ('I ...'). Stay non-clinical and non-alarming.",
    "scale": "0 very/often false to 3 very/often true.",
  },
  "bpnss": {
    "construct": "Basic Psychological Needs Satisfaction (autonomy, competence, relatedness). First-person 'I ...'.",
    "voice": "Keep FIRST PERSON ('I ...').",
    "scale": "1 not at all true to 7 very true.",
  },
  "who5": {
    "construct": "WHO-5 Wellbeing Index over the last two weeks. First-person 'I have felt ...'.",
    "voice": "Keep FIRST PERSON ('I have ...').",
    "scale": "0 at no time to 5 all of the time.",
  },
  "pvq": {
    "construct": "Schwartz Portrait Values Questionnaire. Each item describes a PERSON in third person ('They ...') and you rate how much that person sounds like you. This third-person portrait format is essential to the test.",
    "voice": "Keep THIRD PERSON portrait style ('They ...' / 'It is important to them ...').",
    "scale": "1 very much like me to 6 not like me at all.",
  },
  "riasec": {
    "construct": "Holland Code RIASEC career interests. Each item is an activity you might enjoy.",
    "voice": "Keep the activity-phrase style (an activity you might like doing).",
    "scale": "1 strongly dislike to 5 strongly like.",
  },
  "attachment": {
    "construct": "Experiences in Close Relationships (attachment). Second-person 'You ...' about closeness and trust.",
    "voice": "Keep SECOND PERSON ('You ...').",
    "scale": "Agreement scale, 1 strongly disagree to 7 strongly agree.",
  },
  "dass": {
    "construct": "Depression Anxiety Stress Scales, about the PAST WEEK. Second-person 'You ...'.",
    "voice": "Keep SECOND PERSON ('You ...') and the past-week framing.",
    "scale": "1 rarely/never to 4 almost always.",
  },
  "aesthetic": {
    "construct": "Artistic Preferences (reactions to art and music). Second-person 'You ...'.",
    "voice": "Keep SECOND PERSON ('You ...').",
    "scale": "1 strongly disagree to 5 strongly agree.",
  },
}

manifest = []
for fname in sorted(os.listdir(BASE)):
    if not fname.endswith(".json"):
        continue
    test = fname[:-5]
    with open(os.path.join(BASE, fname), encoding="utf-8") as fh:
        data = json.load(fh)
    qs = data.get("questions", [])
    fmt = data.get("format", "likert")
    m = META.get(test, {"construct": test, "voice": "Keep the original voice.", "scale": ""})

    # Build flat list of paraphrasable units
    units = []
    for q in qs:
        if fmt == "forced_choice" or "options" in q:
            units.append({"id": q["id"], "kind": "fc",
                          "options": [{"value": o["value"], "text": o["text"]} for o in q["options"]]})
        else:
            units.append({"id": q["id"], "kind": "likert", "text": q["text"]})

    nchunks = (len(units) + CHUNK - 1) // CHUNK
    for ci in range(nchunks):
        chunk_units = units[ci*CHUNK:(ci+1)*CHUNK]
        chunk_id = f"{test}__{ci:02d}"
        payload = {
            "chunk_id": chunk_id,
            "test": test,
            "fmt": fmt,
            "construct": m["construct"],
            "voice": m["voice"],
            "scale": m["scale"],
            "items": chunk_units,
        }
        with open(os.path.join(IN, chunk_id + ".json"), "w", encoding="utf-8") as fh:
            json.dump(payload, fh, ensure_ascii=False, indent=2)
        manifest.append(chunk_id)

with open("/tmp/para_manifest.json", "w", encoding="utf-8") as fh:
    json.dump(manifest, fh)

print(f"Wrote {len(manifest)} chunks across {len(set(c.split('__')[0] for c in manifest))} tests")
print(json.dumps(manifest))
