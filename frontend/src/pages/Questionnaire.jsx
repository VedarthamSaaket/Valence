import { useState, useEffect, useLayoutEffect, useRef, useCallback } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import api from '../utils/api'
import bgImage from '../assets/Image60.jpeg'

// ─── Language Config ────────────────────────────────────────────────────────
const LANGS = [
  { code: 'EN', label: 'EN', mmCode: 'en' },
  { code: 'HI', label: 'HI', mmCode: 'hi' },
  { code: 'TE', label: 'TE', mmCode: 'te' },
  { code: 'KN', label: 'KN', mmCode: 'kn' },
  { code: 'DE', label: 'DE', mmCode: 'de' },
]

// MyMemory free API, no key required, 5000 chars/day anon
// Use email param if you have one to get 50k/day
async function translateText(text, targetLang) {
  if (targetLang === 'en') return text
  try {
    const url = `https://api.mymemory.translated.net/get?q=${encodeURIComponent(text)}&langpair=en|${targetLang}`
    const res = await fetch(url)
    const data = await res.json()
    if (data.responseStatus === 200 && data.responseData?.translatedText) {
      return data.responseData.translatedText
    }
    return text
  } catch {
    return text
  }
}

// Batch translate array of strings, chunking to avoid hitting char limits
async function translateBatch(texts, targetLangCode) {
  const CHUNK = 10
  const results = []
  for (let i = 0; i < texts.length; i += CHUNK) {
    const chunk = texts.slice(i, i + CHUNK)
    const translated = await Promise.all(chunk.map(t => translateText(t, targetLangCode)))
    results.push(...translated)
    // Small delay to respect rate limits
    if (i + CHUNK < texts.length) await new Promise(r => setTimeout(r, 150))
  }
  return results
}

// ─── Scale Configs ───────────────────────────────────────────────────────────
const SCALE = [
  { value: 1, label: 'Strongly Disagree', short: 'SD' },
  { value: 2, label: 'Disagree', short: 'D' },
  { value: 3, label: 'Neutral', short: 'N' },
  { value: 4, label: 'Agree', short: 'A' },
  { value: 5, label: 'Strongly Agree', short: 'SA' },
]

export const TEST_CONFIG = {
  hexaco:     { label: 'SIX-TRAIT PERSONALITY',        subtitle: 'The six broad traits that shape who you are',                                 roman: 'I',    progress: 'linear-gradient(90deg,#8090a2,#c8d8e8,#eef6fc,#d8e8f4,#f4f8fc)', accent: '#C8D8E8', glow: 'rgba(215,232,248,0.35)' },
  sixteenpf:  { label: 'SIXTEEN PERSONALITY TRAITS',   subtitle: 'Sixteen layers deep into your personality structure',                         roman: 'II',   progress: 'linear-gradient(90deg,#9080b8,#c0b0d8,#dcd0f0,#ccc0e8,#ece8f8)', accent: '#C0B0D8', glow: 'rgba(210,200,240,0.32)' },
  darktriad:  { label: 'DARK TRAITS',                  subtitle: 'Your shadow side, the traits most people will not measure',                   roman: 'III',  progress: 'linear-gradient(90deg,#6a7a88,#b0bcc8,#d8e0e8,#c4ccd6,#eaecf0)', accent: '#B0BCC8', glow: 'rgba(200,212,224,0.30)' },
  fti:        { label: 'TEMPERAMENT TYPE',             subtitle: 'Four temperament rhythms that run your style',                                roman: 'IV',   progress: 'linear-gradient(90deg,#7a6090,#cfc0da,#e8dcf0,#d8c8e8,#f0e8f8)', accent: '#CFC0DA', glow: 'rgba(220,200,232,0.30)' },
  npi:        { label: 'HOW YOU SEE YOURSELF',         subtitle: 'How you see yourself in relation to others',                                  roman: 'V',    progress: 'linear-gradient(90deg,#a06080,#dcb8c8,#f0d8e0,#e0c8d4,#f8e8ec)', accent: '#DCB8C8', glow: 'rgba(232,200,216,0.30)' },
  ambi:       { label: 'BROAD PERSONALITY SCAN',       subtitle: 'The widest personality scan in this collection',                              roman: 'VI',   progress: 'linear-gradient(90deg,#707890,#a8b0c8,#d8dcec,#c4ccd8,#e8eef4)', accent: '#A8B0C8', glow: 'rgba(200,208,228,0.30)' },
  pid5:       { label: 'FIVE TRAIT STYLES',            subtitle: 'Five trait styles, presented as styles not diagnoses',                        roman: 'VII',  progress: 'linear-gradient(90deg,#7888a0,#b8c0d8,#dce4f0,#c8d0e4,#ecf0f8)', accent: '#B8C0D8', glow: 'rgba(206,216,232,0.30)' },
  hsq:        { label: 'HUMOR STYLE',                  subtitle: 'Four flavors of humor, two warm and two corrosive',                           roman: 'VIII', progress: 'linear-gradient(90deg,#b08840,#dcc8a0,#f4e8c8,#e8d8b0,#f8efce)', accent: '#DCC8A0', glow: 'rgba(232,216,176,0.30)' },
  kims:       { label: 'MINDFULNESS SKILLS',           subtitle: 'Four skills that make up day-to-day mindfulness',                              roman: 'IX',   progress: 'linear-gradient(90deg,#609060,#b8d8b8,#dcecdc,#c8e0c8,#ecf6ec)', accent: '#B8D8B8', glow: 'rgba(200,224,200,0.30)' },
  gcbs:       { label: 'CONSPIRACY BELIEFS',           subtitle: 'How skeptical you are about official accounts',                                roman: 'X',    progress: 'linear-gradient(90deg,#a07840,#d8b898,#ecd8b8,#e0c8a8,#f4e8cc)', accent: '#D8B898', glow: 'rgba(228,208,176,0.30)' },
  aesthetic:  { label: 'AESTHETIC TASTE',              subtitle: 'What actually moves you, your aesthetic fingerprint',                          roman: 'XI',   progress: 'linear-gradient(90deg,#9490a0,#c8c4d4,#e8e4f4,#d4d0e4,#f4f0fc)', accent: '#C8C4D4', glow: 'rgba(212,208,228,0.30)' },
  riasec:     { label: 'CAREER TYPE',                  subtitle: 'The kind of work that actually fits how you are wired',                       roman: 'XII',  progress: 'linear-gradient(90deg,#8898a4,#c0ccd6,#dce8f0,#ccdae6,#e8f2f8)', accent: '#C0CCD6', glow: 'rgba(204,220,232,0.30)' },
  attachment: { label: 'ATTACHMENT STYLE',             subtitle: 'Your relationship wiring, the patterns you do not even see',                  roman: 'XIII', progress: 'linear-gradient(90deg,#9090a8,#bcc0d4,#dcdee8,#cccee0,#e8eaf4)', accent: '#BCC0D4', glow: 'rgba(206,208,228,0.30)' },
  pvq:        { label: 'CORE VALUES',                  subtitle: 'Ten guiding values that sort your decisions',                                  roman: 'XIV',  progress: 'linear-gradient(90deg,#809060,#c8d8b0,#e8f0d8,#d8e0c0,#f0f4e0)', accent: '#C8D8B0', glow: 'rgba(216,224,192,0.30)' },
  bpnss:      { label: 'INNER NEEDS',                  subtitle: 'Autonomy, competence, relatedness, the three needs you run on',                roman: 'XV',   progress: 'linear-gradient(90deg,#609088,#a8d8c8,#d0ecdc,#bce0d0,#e4f4e8)', accent: '#A8D8C8', glow: 'rgba(196,224,208,0.30)' },
  dass:       { label: 'MOOD AND STRESS',              subtitle: 'Where your head is at right now, stress, anxiety, mood',                       roman: 'XVI',  progress: 'linear-gradient(90deg,#9090a2,#c0c0d0,#e0e0ec,#cccce0,#f0f0f8)', accent: '#C0C0D0', glow: 'rgba(206,206,226,0.30)' },
  who5:       { label: 'WELLBEING CHECK',              subtitle: 'A quick check on how the last two weeks have felt',                            roman: 'XVII', progress: 'linear-gradient(90deg,#609880,#b8e0c8,#d8eed8,#c4e4cc,#e8f6e8)', accent: '#B8E0C8', glow: 'rgba(208,232,216,0.30)' },
}

export const SCALE_OVERRIDES = {
  dass: [
    { value: 1, label: 'Did not apply at all', short: '1' },
    { value: 2, label: 'Applied sometimes', short: '2' },
    { value: 3, label: 'Applied considerably', short: '3' },
    { value: 4, label: 'Applied very much', short: '4' },
  ],
  hexaco: [
    { value: 1, label: 'Strongly Disagree', short: '1' },
    { value: 2, label: 'Disagree', short: '2' },
    { value: 3, label: 'Slightly Disagree', short: '3' },
    { value: 4, label: 'Neutral', short: '4' },
    { value: 5, label: 'Slightly Agree', short: '5' },
    { value: 6, label: 'Agree', short: '6' },
    { value: 7, label: 'Strongly Agree', short: '7' },
  ],
  ambi: [
    { value: 1, label: 'Strongly Disagree', short: '1' },
    { value: 2, label: 'Disagree', short: '2' },
    { value: 3, label: 'Slightly Disagree', short: '3' },
    { value: 4, label: 'Neutral', short: '4' },
    { value: 5, label: 'Slightly Agree', short: '5' },
    { value: 6, label: 'Agree', short: '6' },
    { value: 7, label: 'Strongly Agree', short: '7' },
  ],
  bpnss: [
    { value: 1, label: 'Not at all true', short: '1' },
    { value: 2, label: '', short: '2' },
    { value: 3, label: 'Somewhat true', short: '3' },
    { value: 4, label: '', short: '4' },
    { value: 5, label: 'Mostly true', short: '5' },
    { value: 6, label: '', short: '6' },
    { value: 7, label: 'Very true', short: '7' },
  ],
  fti: [
    { value: 1, label: 'Strongly Disagree', short: 'SD' },
    { value: 2, label: 'Disagree', short: 'D' },
    { value: 3, label: 'Agree', short: 'A' },
    { value: 4, label: 'Strongly Agree', short: 'SA' },
  ],
  pvq: [
    { value: 1, label: 'Very much like me', short: '1' },
    { value: 2, label: 'Like me', short: '2' },
    { value: 3, label: 'Somewhat like me', short: '3' },
    { value: 4, label: 'A little like me', short: '4' },
    { value: 5, label: 'Not like me', short: '5' },
    { value: 6, label: 'Not like me at all', short: '6' },
  ],
  who5: [
    { value: 0, label: 'At no time', short: '0' },
    { value: 1, label: 'Some of the time', short: '1' },
    { value: 2, label: 'Less than half', short: '2' },
    { value: 3, label: 'More than half', short: '3' },
    { value: 4, label: 'Most of the time', short: '4' },
    { value: 5, label: 'All of the time', short: '5' },
  ],
  pid5: [
    { value: 0, label: 'Very or often false', short: '0' },
    { value: 1, label: 'Sometimes false', short: '1' },
    { value: 2, label: 'Sometimes true', short: '2' },
    { value: 3, label: 'Very or often true', short: '3' },
  ],
  gcbs: [
    { value: 1, label: 'Definitely not true', short: '1' },
    { value: 2, label: 'Probably not true', short: '2' },
    { value: 3, label: 'Cannot decide', short: '3' },
    { value: 4, label: 'Probably true', short: '4' },
    { value: 5, label: 'Definitely true', short: '5' },
  ],
  attachment: [
    { value: 1, label: 'Strongly Disagree', short: '1' },
    { value: 2, label: 'Disagree', short: '2' },
    { value: 3, label: 'Slightly Disagree', short: '3' },
    { value: 4, label: 'Neutral', short: '4' },
    { value: 5, label: 'Slightly Agree', short: '5' },
    { value: 6, label: 'Agree', short: '6' },
    { value: 7, label: 'Strongly Agree', short: '7' },
  ],
}

const QUESTIONS_PER_PAGE = 10

const CHROME = {
  gradient: 'linear-gradient(135deg, #5a6a7a 0%, #a0b4c4 12%, #ccdae6 24%, #e8f2f8 34%, #f6fafe 42%, #e4eef6 50%, #c4d6e4 60%, #98aec0 70%, #ddeaf4 80%, #f4f8fc 90%, #b4c8d8 100%)',
  border: 'rgba(228,240,252,0.72)',
  glow: '0 0 18px rgba(210,230,248,0.32), 0 0 48px rgba(190,215,238,0.14), 0 2px 8px rgba(0,0,0,0.28)',
  glowInner: 'inset 0 1px 0 rgba(255,255,255,0.42), inset 0 -1px 0 rgba(180,210,232,0.18)',
  textColor: '#04060a',
}

const S = {
  fontDisplay: "'Cormorant Garamond', Georgia, serif",
  fontSC: "'Cinzel', serif",
  fontBody: "'Playfair Display', Georgia, serif",
  fontMono: "'JetBrains Mono', monospace",
  textPrim: '#F4F7FA',
  textSec: 'rgba(244,247,250,0.56)',
  textMuted: 'rgba(244,247,250,0.30)',
  iris: '#D8E8F4',
  irisDim: '#8A9EAE',
  border: 'rgba(200,214,230,0.15)',
  frost: 'rgba(200,214,230,0.07)',
  frostBorder: 'rgba(215,228,242,0.20)',
}

const blockCopy = e => e.preventDefault()

// ─── Language Switcher Component ─────────────────────────────────────────────
function LangBar({ activeLang, onSelect, translating }) {
  return (
    <div style={{
      display: 'flex',
      alignItems: 'center',
      gap: 0,
      border: '1px solid rgba(215,228,242,0.16)',
      overflow: 'hidden',
      flexShrink: 0,
    }}>
      {LANGS.map((lang, i) => {
        const active = activeLang === lang.code
        return (
          <button
            key={lang.code}
            onClick={() => !translating && onSelect(lang)}
            disabled={translating}
            title={lang.code}
            style={{
              padding: '9px 14px',
              border: 'none',
              borderLeft: i > 0 ? '1px solid rgba(215,228,242,0.10)' : 'none',
              backgroundColor: active ? 'transparent' : 'rgba(215,228,242,0.025)',
              backgroundImage: active ? CHROME.gradient : 'none',
              backgroundSize: '300% 300%',
              animation: active ? 'chrome-sweep 5s ease-in-out infinite' : 'none',
              color: active ? CHROME.textColor : S.textMuted,
              fontFamily: S.fontSC,
              fontWeight: active ? 700 : 400,
              fontSize: 9,
              letterSpacing: '0.18em',
              cursor: translating ? 'wait' : 'pointer',
              transition: 'all 220ms cubic-bezier(0.4,0,0.2,1)',
              transform: active ? 'translateY(-1px)' : 'scale(1)',
              boxShadow: active ? CHROME.glow : 'none',
              outline: 'none',
              position: 'relative',
              overflow: 'hidden',
              minWidth: 38,
              textAlign: 'center',
            }}
          >
            {active && (
              <span style={{
                position: 'absolute', inset: 0,
                background: 'linear-gradient(105deg, transparent 30%, rgba(255,255,255,0.22) 48%, rgba(255,255,255,0.36) 52%, transparent 70%)',
                backgroundSize: '200% 100%',
                animation: 'sheen-slide 3s ease-in-out infinite',
                pointerEvents: 'none',
              }} />
            )}
            <span style={{ position: 'relative' }}>{lang.label}</span>
          </button>
        )
      })}
      {translating && (
        <div style={{
          padding: '0 10px',
          display: 'flex', alignItems: 'center', gap: 6,
          borderLeft: '1px solid rgba(215,228,242,0.10)',
        }}>
          <div className="spinner" style={{ width: 10, height: 10, borderWidth: 1 }} />
        </div>
      )}
    </div>
  )
}

// ─── Main Component ──────────────────────────────────────────────────────────
export default function Questionnaire() {
  const { testId } = useParams()
  const navigate = useNavigate()
  const [test, setTest] = useState(null)
  const [responses, setResponses] = useState({})
  const [page, setPage] = useState(0)
  const [submitting, setSubmitting] = useState(false)
  const [consent, setConsent] = useState(false)
  const [error, setError] = useState('')
  const [questionContexts, setQuestionContexts] = useState({})
  const [expandedContext, setExpandedContext] = useState(new Set())
  const topRef = useRef()

  // Language state
  const [activeLang, setActiveLang] = useState('EN')
  const [translating, setTranslating] = useState(false)
  const [translatedQuestions, setTranslatedQuestions] = useState(null) // null = use original
  const [translatedInstructions, setTranslatedInstructions] = useState(null)
  // Cache: { [langCode]: { questions: [...], instructions: string } }
  const translationCache = useRef({})

  const cfg = TEST_CONFIG[testId] || TEST_CONFIG.hexaco
  const scale = SCALE_OVERRIDES[testId] || SCALE

  // Always return to the top of the question set when the page index changes.
  // useLayoutEffect fires synchronously before paint, and we force an INSTANT
  // scroll: smooth scrolls get silently cancelled when the new question set
  // re-renders and the page height changes mid-animation.
  useLayoutEffect(() => {
    const html = document.documentElement
    const prevBehavior = html.style.scrollBehavior
    html.style.scrollBehavior = 'auto'   // override global `scroll-behavior: smooth`
    window.scrollTo(0, 0)
    html.scrollTop = 0
    document.body.scrollTop = 0          // Safari fallback
    html.style.scrollBehavior = prevBehavior
  }, [page])

  useEffect(() => {
    window.scrollTo(0, 0)
    api.get(`/tests/${testId}`)
      .then(res => setTest(res.data))
      .catch(() => navigate('/tests'))
  }, [testId])

  // Keep EVERY analysis model warm for the whole time the test is open: the
  // first ping nudges the general-purpose archetype refiner AND the
  // psychology layer (HF classifiers + the specialty worker for this
  // instrument), and the interval re-pings so nothing idles out mid-test. By
  // submit time everything is resident — "Analyze results" pays no
  // cold-start latency. Fire-and-forget; failures are invisible.
  useEffect(() => {
    const ping = () => api.get(`/psych/warmup/${testId}`).catch(() => {})
    ping()
    const iv = setInterval(ping, 4 * 60 * 1000)
    return () => clearInterval(iv)
  }, [testId])

  const handleLangSelect = useCallback(async (lang) => {
    if (lang.code === activeLang) return
    setActiveLang(lang.code)

    if (lang.code === 'EN') {
      setTranslatedQuestions(null)
      setTranslatedInstructions(null)
      return
    }

    // Check cache first
    if (translationCache.current[lang.code]) {
      const cached = translationCache.current[lang.code]
      setTranslatedQuestions(cached.questions)
      setTranslatedInstructions(cached.instructions)
      return
    }

    if (!test) return
    setTranslating(true)
    try {
      const questions = test.questions || []
      const texts = questions.map(q => q.text)

      // Translate in batches
      const translatedTexts = await translateBatch(texts, lang.mmCode)
      const translatedQs = questions.map((q, i) => ({ ...q, text: translatedTexts[i] }))

      // Translate instructions
      let translatedInstr = test.instructions || ''
      if (translatedInstr) {
        translatedInstr = await translateText(translatedInstr, lang.mmCode)
      }

      // Cache it
      translationCache.current[lang.code] = {
        questions: translatedQs,
        instructions: translatedInstr,
      }

      setTranslatedQuestions(translatedQs)
      setTranslatedInstructions(translatedInstr)
    } catch (err) {
      console.error('Translation failed:', err)
    } finally {
      setTranslating(false)
    }
  }, [activeLang, test])

  if (!test) return (
    <div style={{ minHeight: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
      <div className="spinner" style={{ width: 44, height: 44 }} />
    </div>
  )

  const questions = translatedQuestions || test.questions || []
  const instructions = activeLang === 'EN' ? (test.instructions || '') : (translatedInstructions ?? test.instructions ?? '')
  const totalPages = Math.ceil(questions.length / QUESTIONS_PER_PAGE)
  const currentQuestions = questions.slice(page * QUESTIONS_PER_PAGE, (page + 1) * QUESTIONS_PER_PAGE)
  const answeredOnPage = currentQuestions.filter(q => responses[q.id] !== undefined).length
  const allOnPageAnswered = answeredOnPage === currentQuestions.length
  const totalAnswered = Object.keys(responses).length
  const progress = totalAnswered / questions.length
  const isLastPage = page === totalPages - 1

  const answer = (qId, val) => setResponses(r => ({ ...r, [qId]: val }))

  const toggleContext = (qId) => {
    setExpandedContext(prev => {
      const next = new Set(prev)
      next.has(qId) ? next.delete(qId) : next.add(qId)
      return next
    })
  }

  const setCtx = (qId, val) => {
    setQuestionContexts(prev => ({ ...prev, [qId]: val }))
  }

  // Scrolling is handled by the useLayoutEffect on [page] above, it fires
  // after the new page renders but before paint, so it cannot be cancelled.
  const nextPage = () => {
    if (!allOnPageAnswered) { setError('Please answer all questions on this page'); return }
    setError('')
    setPage(p => p + 1)
  }

  const prevPage = () => {
    setPage(p => p - 1)
  }

  const submit = async () => {
    if (!allOnPageAnswered) { setError('Please answer all questions'); return }
    setError('')
    setSubmitting(true)
    try {
      const ctxFiltered = Object.fromEntries(
        Object.entries(questionContexts).filter(([, v]) => v && v.trim())
      )
      const res = await api.post('/results/submit', {
        test_type: testId,
        responses,
        consent_to_dataset: consent,
        ...(Object.keys(ctxFiltered).length > 0 && { question_contexts: ctxFiltered }),
      })
      navigate(`/results/${res.data.result_id}`)
    } catch (e) {
      setError(e.response?.data?.detail || 'Submission failed. Please try again.')
      setSubmitting(false)
    }
  }

  return (
    <div
      className="page"
      style={{ paddingBottom: 100, position: 'relative', minHeight: '100vh' }}
      ref={topRef}
    >
      {/* Background */}
      <div style={{
        position: 'fixed', inset: 0, zIndex: 0, pointerEvents: 'none', overflow: 'hidden',
      }}>
        <img
          src={bgImage} alt=""
          style={{
            position: 'absolute', top: '50%', left: '50%',
            transform: 'translate(-50%, -50%) rotate(-90deg) scale(1.5)',
            width: '100vh', height: '100vw', objectFit: 'cover',
            filter: 'grayscale(100%) brightness(0.85) contrast(1.05)',
          }}
        />
        <div style={{ position: 'absolute', inset: 0, background: 'radial-gradient(ellipse 80% 70% at 50% 50%, rgba(4,4,6,0.55) 0%, rgba(4,4,6,0.82) 70%, rgba(4,4,6,0.96) 100%)' }} />
        <div style={{ position: 'absolute', inset: 0, background: 'linear-gradient(to bottom, rgba(4,4,6,0.0) 0%, rgba(4,4,6,0.0) 60%, rgba(4,4,6,0.9) 100%)' }} />
      </div>

      <div style={{ position: 'relative', zIndex: 1 }}>
        <div className="container-sm" style={{ paddingTop: 52 }}>

          {/* Header with language bar */}
          <div className="animate-fade-up" style={{ marginBottom: 48 }}>
            <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', gap: 20, marginBottom: 24 }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 20, flex: 1 }}>
                <span style={{
                  fontFamily: S.fontDisplay, fontSize: 56, fontWeight: 300, lineHeight: 1,
                  color: 'rgba(215,228,242,0.10)', letterSpacing: '-0.02em', userSelect: 'none',
                }}>{cfg.roman}</span>
                <div>
                  <div style={{ fontFamily: S.fontSC, fontSize: 10, letterSpacing: '0.28em', color: cfg.accent, marginBottom: 4 }}>{cfg.label}</div>
                  <div style={{ fontFamily: S.fontBody, fontStyle: 'italic', fontSize: 14, color: S.textMuted, letterSpacing: '0.02em' }}>{cfg.subtitle}</div>
                </div>
              </div>
              {/* Language Switcher */}
              <LangBar activeLang={activeLang} onSelect={handleLangSelect} translating={translating} />
            </div>

            <h1 style={{
              fontFamily: S.fontDisplay, fontSize: 'clamp(36px, 6vw, 64px)',
              fontWeight: 300, lineHeight: 1.0, letterSpacing: '-0.02em',
              background: cfg.progress,
              WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent',
              backgroundClip: 'text', backgroundSize: '300% 100%',
              animation: 'metal-sweep 6s ease-in-out infinite', marginBottom: 28,
            }}>{test.name}</h1>

            {/* Progress bar */}
            <div style={{ display: 'flex', alignItems: 'center', gap: 16, marginBottom: 12 }}>
              <div style={{ fontFamily: S.fontMono, fontSize: 10, color: S.textMuted, letterSpacing: '0.08em', flexShrink: 0 }}>
                {String(page + 1).padStart(2, '0')} / {String(totalPages).padStart(2, '0')}
              </div>
              <div style={{ flex: 1, height: 1, background: 'rgba(215,228,242,0.10)', position: 'relative', overflow: 'hidden' }}>
                <div style={{
                  position: 'absolute', left: 0, top: 0, bottom: 0,
                  width: `${progress * 100}%`, background: cfg.progress, backgroundSize: '200% 100%',
                  animation: 'metal-sweep 4s ease-in-out infinite', transition: 'width 400ms',
                  boxShadow: `0 0 8px ${cfg.glow}`,
                }} />
              </div>
              <div style={{ fontFamily: S.fontMono, fontSize: 10, color: S.textMuted, letterSpacing: '0.08em', flexShrink: 0 }}>
                {totalAnswered} / {questions.length}
              </div>
            </div>
            <div style={{ height: 1, background: `linear-gradient(90deg, transparent, ${cfg.accent}33, transparent)` }} />
          </div>

          {/* Instructions */}
          {page === 0 && instructions && (
            <div className="animate-fade-up" style={{
              marginBottom: 36, padding: '20px 28px',
              background: 'rgba(215,228,242,0.04)',
              backdropFilter: 'blur(32px) saturate(1.5)', WebkitBackdropFilter: 'blur(32px) saturate(1.5)',
              border: `1px solid rgba(215,228,242,0.12)`,
              borderLeft: `2px solid ${cfg.accent}66`,
            }}>
              <div style={{ fontFamily: S.fontSC, fontSize: 9, letterSpacing: '0.22em', color: cfg.accent, marginBottom: 10, textTransform: 'uppercase' }}>Instructions</div>
              <p style={{ fontFamily: S.fontBody, fontStyle: 'italic', fontSize: 15, color: S.textSec, lineHeight: 1.8, margin: 0 }}>
                {instructions}
              </p>
            </div>
          )}

          {/* Translation loading overlay */}
          {translating && (
            <div style={{
              marginBottom: 20, padding: '14px 20px',
              background: 'rgba(215,228,242,0.04)', border: `1px solid ${cfg.accent}33`,
              borderLeft: `2px solid ${cfg.accent}66`,
              display: 'flex', alignItems: 'center', gap: 12,
              fontFamily: S.fontBody, fontStyle: 'italic', fontSize: 13, color: S.textMuted,
            }}>
              <div className="spinner" style={{ width: 14, height: 14, borderWidth: 1 }} />
              Translating questions...
            </div>
          )}

          {/* Questions */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
            {currentQuestions.map((q, qi) => {
              const answered = responses[q.id] !== undefined
              const globalIdx = page * QUESTIONS_PER_PAGE + qi + 1
              return (
                <div key={q.id} className="animate-fade-up q-card" style={{ animationDelay: `${qi * 65}ms` }}>
                  <div style={{
                    position: 'relative', padding: '28px 32px 24px',
                    background: answered ? 'rgba(215,232,244,0.07)' : 'rgba(200,214,230,0.04)',
                    backdropFilter: 'blur(24px) saturate(1.4)', WebkitBackdropFilter: 'blur(24px) saturate(1.4)',
                    border: `1px solid ${answered ? 'rgba(215,232,244,0.20)' : 'rgba(215,228,242,0.10)'}`,
                    borderLeft: `2px solid ${answered ? cfg.accent + 'bb' : 'rgba(215,228,242,0.12)'}`,
                    boxShadow: answered
                      ? `inset 0 1px 0 rgba(255,255,255,0.07), 0 4px 32px ${cfg.glow}`
                      : 'inset 0 1px 0 rgba(255,255,255,0.04)',
                    transition: 'all 300ms cubic-bezier(0.4,0,0.2,1)',
                  }}>
                    <div style={{ display: 'flex', gap: 18, alignItems: 'flex-start' }}>
                      {/* Index number */}
                      <div style={{
                        flexShrink: 0, marginTop: 2, width: 32, height: 32,
                        border: `1px solid ${answered ? cfg.accent + '66' : 'rgba(215,228,242,0.12)'}`,
                        display: 'flex', alignItems: 'center', justifyContent: 'center',
                        background: answered ? cfg.accent + '14' : 'transparent', transition: 'all 300ms',
                      }}>
                        <span style={{ fontFamily: S.fontMono, fontSize: 10, color: answered ? cfg.accent : S.textMuted, letterSpacing: '0.06em' }}>
                          {String(globalIdx).padStart(2, '0')}
                        </span>
                      </div>

                      <div style={{ flex: 1 }}>
                        {/* Question text (likert) or forced-choice label */}
                        {q.type !== 'forced_choice' && (
                          <p
                            style={{
                              fontFamily: S.fontDisplay, fontSize: 20, fontWeight: 300, fontStyle: 'italic',
                              lineHeight: 1.80, letterSpacing: '0.008em', marginBottom: 24, color: S.textPrim,
                              userSelect: 'none', WebkitUserSelect: 'none', MozUserSelect: 'none', msUserSelect: 'none',
                            }}
                            onCopy={blockCopy} onCut={blockCopy}
                          >
                            {q.text}
                          </p>
                        )}

                        {/* Forced-choice (NPI), pick one of two statements */}
                        {q.type === 'forced_choice' && (
                          <div style={{ display: 'flex', flexDirection: 'column', gap: 10, marginBottom: 8 }}>
                            {(q.options || []).map(opt => {
                              const selected = responses[q.id] === opt.value
                              return (
                                <button
                                  key={opt.value}
                                  onClick={() => answer(q.id, opt.value)}
                                  style={{
                                    textAlign: 'left', padding: '18px 22px',
                                    border: selected ? `1.5px solid ${CHROME.border}` : '1px solid rgba(215,228,242,0.09)',
                                    backgroundColor: selected ? 'transparent' : 'rgba(215,228,242,0.025)',
                                    backgroundImage: selected ? CHROME.gradient : 'none',
                                    backgroundSize: '300% 300%',
                                    animation: selected ? 'chrome-sweep 5s ease-in-out infinite' : 'none',
                                    color: selected ? CHROME.textColor : S.textSec,
                                    fontFamily: S.fontDisplay, fontStyle: 'italic', fontWeight: 300,
                                    fontSize: 18, lineHeight: 1.70, cursor: 'pointer',
                                    transition: 'all 220ms cubic-bezier(0.4,0,0.2,1)',
                                    transform: selected ? 'translateY(-2px)' : 'scale(1)',
                                    boxShadow: selected ? `${CHROME.glow}, ${CHROME.glowInner}` : 'inset 0 1px 0 rgba(255,255,255,0.04)',
                                    outline: 'none', position: 'relative', overflow: 'hidden',
                                    userSelect: 'none', WebkitUserSelect: 'none',
                                  }}
                                  onCopy={blockCopy} onCut={blockCopy}
                                >
                                  {selected && (
                                    <span style={{
                                      position: 'absolute', inset: 0,
                                      background: 'linear-gradient(105deg, transparent 30%, rgba(255,255,255,0.22) 48%, rgba(255,255,255,0.36) 52%, transparent 70%)',
                                      backgroundSize: '200% 100%', animation: 'sheen-slide 3s ease-in-out infinite',
                                      pointerEvents: 'none',
                                    }} />
                                  )}
                                  <span style={{ position: 'relative' }}>{opt.text}</span>
                                </button>
                              )
                            })}
                          </div>
                        )}

                        {/* Likert scale buttons */}
                        {q.type !== 'forced_choice' && (
                          <>
                            <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap' }}>
                              {scale.map(opt => {
                                const selected = responses[q.id] === opt.value
                                return (
                                  <button
                                    key={opt.value}
                                    onClick={() => answer(q.id, opt.value)}
                                    title={opt.label}
                                    style={{
                                      flex: 1, minWidth: 54, padding: '14px 6px',
                                      border: selected ? `1.5px solid ${CHROME.border}` : '1px solid rgba(215,228,242,0.09)',
                                      backgroundColor: selected ? 'transparent' : 'rgba(215,228,242,0.025)',
                                      backgroundImage: selected ? CHROME.gradient : 'none',
                                      backgroundSize: '300% 300%',
                                      animation: selected ? 'chrome-sweep 5s ease-in-out infinite' : 'none',
                                      color: selected ? CHROME.textColor : S.textMuted,
                                      fontFamily: S.fontMono, fontWeight: selected ? 700 : 400,
                                      fontSize: 11, cursor: 'pointer',
                                      transition: 'all 220ms cubic-bezier(0.4,0,0.2,1)',
                                      transform: selected ? 'translateY(-3px) scale(1.05)' : 'scale(1)',
                                      boxShadow: selected ? `${CHROME.glow}, ${CHROME.glowInner}` : 'inset 0 1px 0 rgba(255,255,255,0.04)',
                                      outline: 'none', position: 'relative', overflow: 'hidden',
                                    }}
                                  >
                                    {selected && (
                                      <span style={{
                                        position: 'absolute', inset: 0,
                                        background: 'linear-gradient(105deg, transparent 30%, rgba(255,255,255,0.22) 48%, rgba(255,255,255,0.36) 52%, transparent 70%)',
                                        backgroundSize: '200% 100%', animation: 'sheen-slide 3s ease-in-out infinite',
                                        pointerEvents: 'none',
                                      }} />
                                    )}
                                    <span style={{ display: 'block', fontFamily: S.fontDisplay, fontSize: 18, fontWeight: 300, lineHeight: 1, marginBottom: opt.short !== String(opt.value) ? 4 : 0, position: 'relative' }}>{opt.value}</span>
                                    {opt.short !== String(opt.value) && <span style={{ fontSize: 8, fontFamily: S.fontSC, letterSpacing: '0.14em', opacity: selected ? 0.80 : 0.35, textTransform: 'uppercase', position: 'relative' }}>{opt.short}</span>}
                                  </button>
                                )
                              })}
                            </div>

                            {/* Scale labels */}
                            <div style={{ display: 'flex', justifyContent: 'space-between', marginTop: 10 }}>
                              <span style={{ fontFamily: S.fontBody, fontStyle: 'italic', fontSize: 12.5, color: S.textSec, letterSpacing: '0.02em' }}>{scale[0].label}</span>
                              <span style={{ fontFamily: S.fontBody, fontStyle: 'italic', fontSize: 12.5, color: S.textSec, letterSpacing: '0.02em' }}>{scale[scale.length - 1].label}</span>
                            </div>
                          </>
                        )}


                        {/* Optional context */}
                        <div style={{ marginTop: 14 }}>
                          <button
                            onClick={() => toggleContext(q.id)}
                            style={{
                              background: 'rgba(215,228,242,0.03)', cursor: 'pointer',
                              padding: '6px 12px',
                              border: `1px solid ${expandedContext.has(q.id) ? cfg.accent + '55' : 'rgba(215,228,242,0.18)'}`,
                              fontFamily: S.fontSC, fontSize: 10, letterSpacing: '0.16em',
                              color: expandedContext.has(q.id) ? cfg.accent : S.textSec,
                              textTransform: 'uppercase',
                              transition: 'all 200ms',
                            }}
                          >
                            {expandedContext.has(q.id) ? '− Hide context' : '+ Add context (optional)'}
                          </button>
                          {expandedContext.has(q.id) && (
                            <div style={{ marginTop: 10 }}>
                              <textarea
                                value={questionContexts[q.id] || ''}
                                onChange={e => setCtx(q.id, e.target.value)}
                                placeholder="Add any personal context that might help refine your results, e.g. recent experiences, specific situations you had in mind..."
                                style={{
                                  width: '100%', minHeight: 72, maxHeight: 160, resize: 'vertical',
                                  padding: '12px 16px',
                                  background: 'rgba(215,228,242,0.04)',
                                  backdropFilter: 'blur(20px)', WebkitBackdropFilter: 'blur(20px)',
                                  border: `1px solid rgba(215,228,242,0.12)`,
                                  color: S.textPrim, fontFamily: S.fontBody, fontStyle: 'italic',
                                  fontSize: 13, lineHeight: 1.7, letterSpacing: '0.01em',
                                  outline: 'none', boxSizing: 'border-box',
                                }}
                                onFocus={e => { e.target.style.borderColor = cfg.accent + '55' }}
                                onBlur={e => { e.target.style.borderColor = 'rgba(215,228,242,0.12)' }}
                              />
                              <div style={{ fontFamily: S.fontSC, fontSize: 9, letterSpacing: '0.14em', color: S.textSec, marginTop: 6, textTransform: 'uppercase' }}>
                                This context is evaluated alongside your responses for a more personalized result
                              </div>
                            </div>
                          )}
                        </div>
                      </div>
                    </div>

                    {answered && (
                      <div style={{
                        position: 'absolute', bottom: 0, left: 0, right: 0, height: 1,
                        background: `linear-gradient(90deg, transparent, ${cfg.accent}55, transparent)`,
                      }} />
                    )}
                  </div>
                </div>
              )
            })}
          </div>

          {/* Error */}
          {error && (
            <div style={{
              marginTop: 20, padding: '14px 20px',
              background: 'rgba(200,140,140,0.07)', border: '1px solid rgba(200,120,120,0.18)',
              borderLeft: '2px solid rgba(220,140,140,0.40)',
              color: 'rgba(230,185,185,0.90)',
              fontFamily: S.fontBody, fontStyle: 'italic', fontSize: 14,
            }}>{error}</div>
          )}

          {/* Consent */}
          {isLastPage && (
            <div className="animate-fade-up" style={{
              marginTop: 10, padding: '24px 28px',
              background: 'rgba(215,228,242,0.04)',
              backdropFilter: 'blur(24px)', WebkitBackdropFilter: 'blur(24px)',
              border: `1px solid rgba(215,228,242,0.12)`,
              borderLeft: `2px solid ${cfg.accent}44`,
            }}>
              <label style={{ display: 'flex', alignItems: 'flex-start', gap: 18, cursor: 'pointer' }}>
                <div style={{ flexShrink: 0, marginTop: 2 }}>
                  <input
                    type="checkbox" checked={consent} onChange={e => setConsent(e.target.checked)}
                    style={{ width: 16, height: 16, cursor: 'pointer', accentColor: S.iris }}
                  />
                </div>
                <div>
                  <span style={{ fontFamily: S.fontSC, fontSize: 9, letterSpacing: '0.20em', display: 'block', marginBottom: 8, color: cfg.accent, textTransform: 'uppercase' }}>
                    Contribute to the Research Dataset
                  </span>
                  <span style={{ fontFamily: S.fontBody, fontStyle: 'italic', fontSize: 13.5, color: S.textSec, lineHeight: 1.8 }}>
                    I consent to my anonymous responses being added to the dataset. This helps improve personality archetype accuracy for everyone. No personal information is stored, only your numeric responses.
                  </span>
                </div>
              </label>
            </div>
          )}

          {/* Navigation */}
          <div style={{ display: 'flex', justifyContent: 'space-between', marginTop: 28, gap: 12 }}>
            <button onClick={prevPage} disabled={page === 0} className="btn btn-secondary" style={{ opacity: page === 0 ? 0.25 : 1 }}>
              Back
            </button>
            {isLastPage ? (
              <button
                onClick={submit} disabled={submitting || !allOnPageAnswered}
                className="btn btn-primary btn-lg"
                style={{ flex: 1, justifyContent: 'center', maxWidth: 320, marginLeft: 'auto' }}
              >
                {submitting
                  ? <><div className="spinner" style={{ width: 16, height: 16 }} /> Analyzing</>
                  : 'Submit and See Results'}
              </button>
            ) : (
              <button onClick={nextPage} disabled={!allOnPageAnswered} className="btn btn-primary">
                Next
              </button>
            )}
          </div>

          {/* Page dots */}
          <div style={{ display: 'flex', justifyContent: 'center', gap: 8, marginTop: 32 }}>
            {Array.from({ length: totalPages }).map((_, i) => (
              <div key={i} style={{
                width: i === page ? 20 : 5, height: 5,
                background: i === page ? cfg.accent : 'rgba(215,228,242,0.15)',
                transition: 'all 300ms cubic-bezier(0.4,0,0.2,1)',
                boxShadow: i === page ? `0 0 8px ${cfg.glow}` : 'none',
              }} />
            ))}
          </div>

        </div>
      </div>

      <style>{`
        @keyframes metal-sweep {
          0%,100% { background-position: 0% 50%; }
          50%      { background-position: 100% 50%; }
        }
        @keyframes chrome-sweep {
          0%   { background-position: 0%   50%; }
          50%  { background-position: 100% 50%; }
          100% { background-position: 0%   50%; }
        }
        @keyframes sheen-slide {
          0%   { background-position: 200% 0; }
          60%  { background-position: -50%  0; }
          100% { background-position: -50%  0; }
        }
        .q-card:hover > div {
          border-color: rgba(215,228,242,0.18) !important;
        }
      `}</style>
    </div>
  )
}