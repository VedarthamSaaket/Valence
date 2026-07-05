import { useEffect, useRef, useState } from 'react'
import { useParams, Link, useNavigate } from 'react-router-dom'
import api from '../utils/api'
import TombMemoryGame from '../components/TombMemoryGame'
import bgImage from '../assets/Image60.jpeg'

// ─── Deep Dive page ──────────────────────────────────────────────────────────
// /deep-dive/:resultId
// While the psych-model enrichment generates in the background (~1-3 min on
// free-tier CPU), this page is a Tomb-of-the-Mask arcade cabinet. When the
// enrichment lands, a SEE RESULTS button drops in; clicking it reveals the
// psych layer in the app's own aesthetic. Revisits with the enrichment
// already done skip the arcade entirely.

const S = {
  fontDisplay: "'Cormorant Garamond', Georgia, serif",
  fontSC: "'Cinzel', serif",
  fontBody: "'Playfair Display', Georgia, serif",
  textPrim: '#F4F7FA',
  textSec: 'rgba(244,247,250,0.60)',
  textMuted: 'rgba(244,247,250,0.32)',
  irisDim: '#8A9EAE',
  frost: 'rgba(200,214,230,0.06)',
  frostBorder: 'rgba(215,228,242,0.18)',
}
const PX = "'Press Start 2P', monospace"
const TOTM_YELLOW = '#FFE93B'

const ACCENTS = {
  hexaco: '#C8D8E8', sixteenpf: '#C0B8D0', darktriad: '#B0BCC8', fti: '#CFC0DA',
  npi: '#DCB8C8', ambi: '#A8B0C8', pid5: '#B8C0D8', hsq: '#DCC8A0', kims: '#B8D8B8',
  gcbs: '#D8B898', aesthetic: '#C8C4D4', riasec: '#C0CCD6', attachment: '#BCC0D4',
  pvq: '#C8D8B0', bpnss: '#A8D8C8', dass: '#C0C0D0', who5: '#B8E0C8',
}

// Median observed enrichment ≈ 190 s; the tide creeps toward 92% on the
// estimate and only fills completely when the backend actually reports done.
const EXPECTED_S = 200

function parseInsights(result) {
  try {
    const r = result?.insights
    if (!r) return {}
    return typeof r === 'object' ? r : JSON.parse(r)
  } catch { return {} }
}

export default function DeepDive() {
  const { resultId } = useParams()
  const navigate = useNavigate()
  const [result, setResult] = useState(null)
  const [failed, setFailed] = useState(false)
  const [revealed, setRevealed] = useState(false) // user pressed SEE RESULTS
  const [elapsed, setElapsed] = useState(0)
  const startRef = useRef(Date.now())

  // initial fetch
  useEffect(() => {
    api.get(`/results/${resultId}`)
      .then(res => {
        setResult(res.data)
        const dd = parseInsights(res.data).deep_dive
        // Revisit with enrichment already landed → straight to results.
        if (dd?.status === 'ok' && dd?.insights?.length) setRevealed(true)
      })
      .catch(() => navigate('/dashboard'))
  }, [resultId])

  // poll while pending
  useEffect(() => {
    if (!result || result.enrichment_status !== 'pending') return
    let tries = 0
    const iv = setInterval(() => {
      tries += 1
      if (tries > 60) { clearInterval(iv); setFailed(true); return }
      api.get(`/results/${resultId}`)
        .then(res => {
          if (res.data.enrichment_status !== 'pending') {
            clearInterval(iv)
            setResult(res.data)
          }
        })
        .catch(() => { clearInterval(iv); setFailed(true) })
    }, 5000)
    return () => clearInterval(iv)
  }, [resultId, result?.enrichment_status])

  // tide clock (1s tick while waiting)
  useEffect(() => {
    if (!result || result.enrichment_status !== 'pending') return
    const iv = setInterval(() => setElapsed((Date.now() - startRef.current) / 1000), 1000)
    return () => clearInterval(iv)
  }, [result?.enrichment_status])

  if (!result) return (
    <div style={{ minHeight: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center', background: '#000' }}>
      <span style={{ fontFamily: PX, fontSize: 12, color: TOTM_YELLOW, animation: 'dd-blink 0.5s steps(1) infinite' }}>LOADING...</span>
      <style>{`@keyframes dd-blink { 0%,49%{opacity:1} 50%,100%{opacity:0} }`}</style>
    </div>
  )

  const insights = parseInsights(result)
  const dd = insights.deep_dive
  const pending = result.enrichment_status === 'pending' && !failed
  const ready = dd?.status === 'ok' && (dd?.insights?.length > 0)
  const accent = ACCENTS[result.test_type] || ACCENTS.hexaco

  // ── RESULTS ────────────────────────────────────────────────────────────────
  if (revealed && ready) {
    const lines = dd.insights || []
    return (
      <div className="page" style={{ minHeight: '100vh', position: 'relative', paddingBottom: 80 }}>
        <div style={{ position: 'fixed', inset: 0, zIndex: 0, pointerEvents: 'none', overflow: 'hidden' }}>
          <img src={bgImage} alt="" style={{ position: 'absolute', top: '50%', left: '50%', transform: 'translate(-50%, -50%) rotate(-90deg) scale(1.5)', width: '100vh', height: '100vw', objectFit: 'cover', filter: 'grayscale(100%) brightness(0.8) contrast(1.05)' }} />
          <div style={{ position: 'absolute', inset: 0, background: 'radial-gradient(ellipse 80% 70% at 50% 40%, rgba(4,4,6,0.60) 0%, rgba(4,4,6,0.85) 70%, rgba(4,4,6,0.97) 100%)' }} />
        </div>

        <div style={{ maxWidth: 780, margin: '0 auto', padding: '52px 32px 0', position: 'relative', zIndex: 1 }}>
          <div className="animate-fade-up" style={{ marginBottom: 28 }}>
            <div style={{ fontFamily: S.fontSC, fontSize: 8, letterSpacing: '0.26em', color: S.textMuted, marginBottom: 10 }}>DEEP DIVE · PSYCHOLOGY MODEL</div>
            <h1 style={{ fontFamily: S.fontDisplay, fontStyle: 'italic', fontSize: 'clamp(30px,4.5vw,46px)', fontWeight: 300, letterSpacing: '-0.01em', color: S.textPrim, lineHeight: 1.05 }}>
              {result.archetype_name || 'Your Profile'}
            </h1>
          </div>

          <div className="animate-fade-up" style={{ background: S.frost, backdropFilter: 'blur(32px) saturate(1.4)', WebkitBackdropFilter: 'blur(32px) saturate(1.4)', border: `1px solid ${S.frostBorder}`, boxShadow: 'inset 0 1px 0 rgba(255,255,255,0.05)', padding: '28px 32px' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 10, padding: '12px 16px', background: 'rgba(215,228,242,0.04)', border: `1px solid ${accent}33`, borderLeft: `2px solid ${accent}88`, marginBottom: 22 }}>
              <span style={{ color: accent, fontSize: 12, opacity: 0.8 }}>✦</span>
              <span style={{ fontFamily: S.fontSC, fontSize: 8.5, letterSpacing: '0.10em', color: S.textSec, textTransform: 'uppercase' }}>Deep Dive · psychology-compliant analysis</span>
            </div>

            <div style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
              {lines.map((ins, i) => (
                <div key={i} style={{ display: 'flex', gap: 18, alignItems: 'flex-start', padding: '16px 20px', background: 'rgba(215,228,242,0.04)', border: '1px solid rgba(215,228,242,0.08)', borderLeft: `2px solid ${accent}66` }}>
                  <span style={{ fontFamily: S.fontDisplay, fontSize: 16, fontWeight: 300, color: accent, opacity: 0.6, flexShrink: 0, marginTop: 1 }}>{String(i + 1).padStart(2, '0')}</span>
                  <p style={{ fontFamily: S.fontBody, fontStyle: 'italic', fontSize: 14, color: 'rgba(244,247,250,0.58)', lineHeight: 1.80 }}>{ins}</p>
                </div>
              ))}
            </div>

            {dd.affect_context && (
              <div style={{ marginTop: 18, padding: '14px 18px', background: 'rgba(215,228,242,0.03)', border: '1px solid rgba(215,228,242,0.07)', borderLeft: `2px solid ${accent}44` }}>
                <div style={{ fontFamily: S.fontSC, fontSize: 7, letterSpacing: '0.18em', color: S.irisDim, textTransform: 'uppercase', marginBottom: 6 }}>
                  Emotional Signal In Your Notes
                </div>
                <p style={{ fontFamily: S.fontSC, fontSize: 12, color: 'rgba(244,247,250,0.55)', lineHeight: 1.75 }}>{dd.affect_context}</p>
              </div>
            )}

            <p style={{ fontFamily: S.fontSC, fontSize: 11, letterSpacing: '0.04em', color: S.textMuted, lineHeight: 1.75, marginTop: 18 }}>
              These observations are reflective, generated from your scored profile and any context you volunteered. Not a clinical diagnosis.
            </p>
          </div>

          <div style={{ marginTop: 3, display: 'flex', gap: 3 }}>
            <Link to={`/results/${resultId}`} className="btn btn-secondary" style={{ flex: 1, justifyContent: 'center' }}>Base Results</Link>
            <Link to="/dashboard" className="btn btn-primary" style={{ flex: 1, justifyContent: 'center' }}>Dashboard</Link>
          </div>
        </div>
      </div>
    )
  }

  // ── UNAVAILABLE (enrichment finished without a usable deep dive, or timed out)
  if (!pending && !ready) {
    return (
      <div style={{ minHeight: '100vh', display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', gap: 26, background: '#000', padding: 24 }}>
        <span style={{ fontFamily: PX, fontSize: 16, color: '#FF3131', textShadow: '0 0 10px #FF3131' }}>GAME OVER</span>
        <p style={{ fontFamily: PX, fontSize: 9, color: '#888', textAlign: 'center', lineHeight: 2.2, maxWidth: 420 }}>
          {failed
            ? 'THE PSYCH MODEL IS TAKING TOO LONG. CHECK BACK FROM YOUR DASHBOARD IN A FEW MINUTES.'
            : 'THE PSYCHOLOGY MODEL DID NOT RETURN A DEEP DIVE FOR THIS RESULT.'}
        </p>
        <div style={{ display: 'flex', gap: 14 }}>
          <Link to={`/results/${resultId}`} style={{ fontFamily: PX, fontSize: 9, color: TOTM_YELLOW, textDecoration: 'none', border: `3px solid ${TOTM_YELLOW}`, padding: '12px 18px' }}>BASE RESULTS</Link>
          <Link to="/dashboard" style={{ fontFamily: PX, fontSize: 9, color: '#888', textDecoration: 'none', border: '3px solid #444', padding: '12px 18px' }}>DASHBOARD</Link>
        </div>
      </div>
    )
  }

  // ── ARCADE (pending, or landed but not yet revealed) ──────────────────────
  const tide = ready ? 1 : Math.min(0.92, elapsed / EXPECTED_S)

  return (
    <div className="page" style={{ minHeight: '100vh', position: 'relative', padding: '72px 16px 40px', display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 18 }}>
      {/* Dashboard-style background */}
      <div style={{ position: 'fixed', inset: 0, zIndex: 0, pointerEvents: 'none', overflow: 'hidden' }}>
        <img
          src={bgImage} alt=""
          style={{
            position: 'absolute', top: '50%', left: '50%',
            transform: 'translate(-50%, -50%) rotate(-90deg) scale(1.5)',
            width: '100vh', height: '100vw', objectFit: 'cover',
            filter: 'grayscale(100%) brightness(0.55) contrast(1.1)',
          }}
        />
        <div style={{ position: 'absolute', inset: 0, background: 'radial-gradient(ellipse 80% 70% at 50% 40%, rgba(4,4,6,0.72) 0%, rgba(4,4,6,0.90) 70%, rgba(4,4,6,0.98) 100%)' }} />
        <div style={{ position: 'absolute', inset: 0, background: 'linear-gradient(to bottom, rgba(4,4,6,0.20) 0%, rgba(4,4,6,0.0) 40%, rgba(4,4,6,0.94) 100%)' }} />
      </div>

      <div style={{ position: 'relative', zIndex: 1, textAlign: 'center' }}>
        <div style={{ fontFamily: PX, fontSize: 'clamp(12px, 2.6vw, 15px)', color: TOTM_YELLOW, textShadow: `0 0 10px ${TOTM_YELLOW}`, marginBottom: 8, letterSpacing: 1 }}>
          DEEP DIVE
        </div>
        <div style={{ fontFamily: PX, fontSize: 7, color: '#888', lineHeight: 2 }}>
          {ready
            ? 'ANALYSIS COMPLETE'
            : <>PSYCH MODEL ANALYZING<span style={{ animation: 'dd-blink 0.6s steps(1) infinite' }}>_</span></>}
        </div>
      </div>

      <div style={{ position: 'relative', zIndex: 1 }}>
        <TombMemoryGame />
      </div>

      {/* External loading bar, sits below the cabinet not inside it */}
      <div style={{ position: 'relative', zIndex: 1, width: '100%', maxWidth: 380 }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', fontFamily: PX, fontSize: 6, color: '#666', letterSpacing: 1, marginBottom: 6 }}>
          <span>ANALYSIS</span>
          <span>{ready ? '100%' : `${Math.round(tide * 100)}%`}</span>
        </div>
        <div style={{ height: 6, background: '#0a0a0a', border: '1px solid #222', position: 'relative', overflow: 'hidden' }}>
          <div style={{
            position: 'absolute', left: 0, top: 0, bottom: 0,
            width: `${Math.max(1, Math.round(tide * 100))}%`,
            background: TOTM_YELLOW,
            boxShadow: `0 0 8px ${TOTM_YELLOW}`,
            transition: 'width 1s steps(6)',
          }} />
        </div>
      </div>

      <div style={{ position: 'relative', zIndex: 1, display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 10 }}>
        <button
          onClick={() => { if (ready) setRevealed(true) }}
          disabled={!ready}
          style={{
            fontFamily: PX, fontSize: 11,
            color: ready ? '#000' : '#3a3a3a',
            background: ready ? TOTM_YELLOW : '#0a0a0a',
            border: ready ? '4px solid #fff' : '3px solid #2a2a2a',
            boxShadow: ready ? `0 0 20px ${TOTM_YELLOW}, 0 0 52px ${TOTM_YELLOW}55` : 'none',
            padding: '13px 24px',
            cursor: ready ? 'pointer' : 'not-allowed',
            animation: ready ? 'dd-pulse 0.5s steps(2) infinite' : 'none',
            letterSpacing: 1,
          }}
        >
          {ready ? '▶ SEE RESULTS' : 'RESULTS LOCKED'}
        </button>
      </div>

      <style>{`
        @keyframes dd-blink { 0%,49%{opacity:1} 50%,100%{opacity:0} }
        @keyframes dd-pulse {
          0%,49% { box-shadow: 0 0 20px ${TOTM_YELLOW}, 0 0 52px ${TOTM_YELLOW}55; }
          50%,100% { box-shadow: 0 0 6px ${TOTM_YELLOW}66; }
        }
      `}</style>
    </div>
  )
}
