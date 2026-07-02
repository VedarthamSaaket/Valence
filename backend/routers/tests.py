from fastapi import APIRouter, HTTPException
import json
import os

router = APIRouter()

QUESTIONS_DIR = os.path.join(os.path.dirname(__file__), "../../shared/questions")

TEST_META = {
    # ------------------ PERSONALITY (broad-trait) ------------------
    "hexaco": {
        "name":           "Six-Trait Personality",
        "subtitle":       "HEXACO Six-Factor Personality",
        "color":          "#6B8CAE",
        "duration":       "30 to 40 min",
        "question_count": 240,
        "category":       "personality",
        "description":    "Six broad personality factors with the addition of Honesty-Humility, a dimension the classic Big Five misses. The most complete trait picture in modern personality science.",
        "traits":         ["Honesty-Humility", "Emotionality", "Extraversion", "Agreeableness", "Conscientiousness", "Openness"],
    },
    "sixteenpf": {
        "name":           "Sixteen Personality Traits",
        "subtitle":       "Sixteen Personality Factors",
        "color":          "#7A9AAE",
        "duration":       "25 to 35 min",
        "question_count": 163,
        "category":       "personality",
        "description":    "Cattell's sixteen factors go deeper than any other personality framework. The highest dimensional resolution of how your mind is structured.",
        "traits":         ["Warmth", "Reasoning", "Stability", "Dominance", "Liveliness", "Rule-Consciousness",
                           "Social-Boldness", "Sensitivity", "Vigilance", "Abstractedness", "Privateness",
                           "Apprehension", "Openness-to-Change", "Self-Reliance", "Perfectionism", "Tension"],
    },
    "darktriad": {
        "name":           "Dark Traits",
        "subtitle":       "Short Dark Triad",
        "color":          "#8A7A9A",
        "duration":       "5 to 8 min",
        "question_count": 27,
        "category":       "personality",
        "description":    "Three darker traits most people prefer not to measure. Honest self-knowledge requires looking at all of yourself.",
        "traits":         ["Machiavellianism", "Narcissism", "Psychopathy"],
    },
    "fti": {
        "name":           "Temperament Type",
        "subtitle":       "Fisher Temperament Inventory",
        "color":          "#9A7AAE",
        "duration":       "8 to 12 min",
        "question_count": 56,
        "category":       "personality",
        "description":    "Four neurotransmitter-linked temperaments first proposed by Helen Fisher. Each one shapes how you think, decide, and connect.",
        "traits":         ["Explorer", "Builder", "Director", "Negotiator"],
    },
    "npi": {
        "name":           "How You See Yourself",
        "subtitle":       "Narcissistic Personality Inventory",
        "color":          "#AE7A8A",
        "duration":       "6 to 10 min",
        "question_count": 40,
        "category":       "personality",
        "description":    "Seven facets of how you see yourself in relation to others, from authority and self-sufficiency to vanity and entitlement.",
        "traits":         ["Authority", "Self-Sufficiency", "Superiority", "Exhibitionism", "Exploitativeness", "Vanity", "Entitlement"],
    },
    "ambi": {
        "name":           "Broad Personality Scan",
        "subtitle":       "Broad Personality Inventory",
        "color":          "#6B6B8A",
        "duration":       "35 to 50 min",
        "question_count": 181,
        "category":       "personality",
        "description":    "The widest personality scan in this collection, covering nearly two hundred personality scales in a single sitting.",
        "traits":         ["Affect Regulation", "Social Drive", "Conscientiousness", "Openness", "Agreeableness", "Energy Drive", "Identity Coherence"],
    },
    "pid5": {
        "name":           "Five Trait Styles",
        "subtitle":       "Five-Domain Personality Style",
        "color":          "#7A8AAE",
        "duration":       "5 to 8 min",
        "question_count": 25,
        "category":       "personality",
        "description":    "Five trait styles that show up across personality patterns. This describes personality styles, not clinical disorders. Not a diagnosis.",
        "traits":         ["Negative Affectivity", "Detachment", "Antagonism", "Disinhibition", "Psychoticism"],
        "disclaimer":     "This describes personality styles, not clinical disorders. Not a diagnosis.",
    },
    # ------------------ MIND (cognitive style) ------------------
    "hsq": {
        "name":           "Humor Style",
        "subtitle":       "Humor Styles Questionnaire",
        "color":          "#AE9A6B",
        "duration":       "5 to 8 min",
        "question_count": 32,
        "category":       "mind",
        "description":    "Four styles of humor, two that help relationships flourish and two that quietly erode them. Which ones do you use most?",
        "traits":         ["Affiliative", "Self-Enhancing", "Aggressive", "Self-Defeating"],
    },
    "kims": {
        "name":           "Mindfulness Skills",
        "subtitle":       "Mindfulness Skills Inventory",
        "color":          "#8AAE8A",
        "duration":       "8 to 12 min",
        "question_count": 39,
        "category":       "mind",
        "description":    "Four skills that make up day-to-day mindfulness, from noticing what is happening in your body to letting experience be what it is.",
        "traits":         ["Observing", "Describing", "Acting with Awareness", "Accepting without Judgment"],
    },
    "gcbs": {
        "name":           "Conspiracy Beliefs",
        "subtitle":       "Generic Conspiracist Beliefs Scale",
        "color":          "#AE8A6B",
        "duration":       "4 to 6 min",
        "question_count": 15,
        "category":       "mind",
        "description":    "Five flavors of how skeptical you are about official accounts and powerful actors behind big events.",
        "traits":         ["Government Malfeasance", "Malevolent Global", "Extraterrestrial Coverup", "Personal Wellbeing Threats", "Control of Information"],
    },
    "aesthetic": {
        "name":           "Aesthetic Taste",
        "subtitle":       "Artistic Preferences",
        "color":          "#AE6B8A",
        "duration":       "8 to 10 min",
        "question_count": 30,
        "category":       "mind",
        "description":    "How you respond to intense, mainstream, traditional, and visual aesthetics. Your honest aesthetic fingerprint.",
        "traits":         ["Intense", "Mainstream", "Traditional", "Visual"],
    },
    # ------------------ LIFE (values, needs, work, relationships) ------------------
    "riasec": {
        "name":           "Career Type",
        "subtitle":       "Career and Interest Type",
        "color":          "#AE9A6B",
        "duration":       "10 to 15 min",
        "question_count": 48,
        "category":       "life",
        "description":    "Six career personality types that explain what kind of work environment brings out your best.",
        "traits":         ["Realistic", "Investigative", "Artistic", "Social", "Enterprising", "Conventional"],
    },
    "attachment": {
        "name":           "Attachment Style",
        "subtitle":       "Attachment Patterns",
        "color":          "#6B8AAE",
        "duration":       "8 to 12 min",
        "question_count": 36,
        "category":       "life",
        "description":    "Your earliest bonds shaped how you attach to others today. See where you sit on the secure to anxious to avoidant map.",
        "traits":         ["Secure", "Anxious", "Avoidant"],
    },
    "pvq": {
        "name":           "Core Values",
        "subtitle":       "Schwartz Portrait Values",
        "color":          "#9AAE6B",
        "duration":       "4 to 6 min",
        "question_count": 21,
        "category":       "life",
        "description":    "Ten guiding values that shape what you treat as worth pursuing, from self-direction to security, achievement to benevolence.",
        "traits":         ["Self-Direction", "Power", "Universalism", "Achievement", "Security", "Stimulation",
                           "Conformity", "Tradition", "Hedonism", "Benevolence"],
    },
    "bpnss": {
        "name":           "Inner Needs",
        "subtitle":       "Basic Psychological Needs",
        "color":          "#6BAE9A",
        "duration":       "4 to 6 min",
        "question_count": 21,
        "category":       "life",
        "description":    "Three fundamental needs that humans run on, autonomy, competence, and relatedness. How well is each one being fed in your life right now?",
        "traits":         ["Autonomy", "Competence", "Relatedness"],
    },
    # ------------------ WELLBEING ------------------
    "dass": {
        "name":           "Mood and Stress",
        "subtitle":       "Stress, Anxiety and Mood Levels",
        "color":          "#6A8A7A",
        "duration":       "8 to 12 min",
        "question_count": 42,
        "category":       "wellbeing",
        "description":    "A snapshot of where you are right now across three currents of emotional experience. This is a self-reflection tool, not a diagnosis.",
        "traits":         ["Depression", "Anxiety", "Stress"],
        "disclaimer":     "This is a self-reflection tool, not a clinical diagnosis. If you are in distress, please reach out to a qualified mental health professional.",
    },
    "who5": {
        "name":           "Wellbeing Check",
        "subtitle":       "WHO-5 Wellbeing Check",
        "color":          "#7AAE8A",
        "duration":       "1 to 2 min",
        "question_count": 5,
        "category":       "wellbeing",
        "description":    "A quick check on how the last two weeks have felt. Five questions, one wellbeing number.",
        "traits":         ["Wellbeing"],
        "disclaimer":     "This is a wellbeing check, not a diagnosis.",
    },
}


def load_questions(test_id: str):
    path = os.path.join(QUESTIONS_DIR, f"{test_id}.json")
    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail=f"Test '{test_id}' not found")
    with open(path, encoding="utf-8") as f:
        return json.load(f)


@router.get("/")
def list_tests():
    return [{"id": k, **v} for k, v in TEST_META.items()]


@router.get("/list")
def get_test_list():
    return [{"id": k, **v} for k, v in TEST_META.items()]


@router.get("/{test_id}")
def get_test(test_id: str):
    if test_id not in TEST_META:
        raise HTTPException(status_code=404, detail="Test not found")
    return load_questions(test_id)