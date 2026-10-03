import { useEffect, useRef, useState } from 'react'
import { useParams, Link, useNavigate } from 'react-router-dom'
import api from '../utils/api'
import bgImage from '../assets/Image60.jpeg'

const S = {
  fontDisplay: "'Libre Baskerville', Baskerville, Georgia, serif",
  fontSC: "'Cinzel', serif",
  fontBody: "'Libre Baskerville', Baskerville, Georgia, serif",
  fontMono: "'JetBrains Mono', monospace",
  textPrim: '#F4F7FA',
  textSec: 'rgba(244,247,250,0.60)',
  textMuted: 'rgba(244,247,250,0.32)',
  irisDim: '#8A9EAE',
  frost: 'rgba(200,214,230,0.06)',
  frostBorder: 'rgba(215,228,242,0.18)',
}

const ACCENTS = {
  hexaco: '#C8D8E8', darktriad: '#B0BCC8', fti: '#CFC0DA', npi: '#DCB8C8',
  ambi: '#A8B0C8', hsq: '#DCC8A0', kims: '#B8D8B8', gcbs: '#D8B898',
  riasec: '#C0CCD6', attachment: '#BCC0D4', dass: '#C0C0D0',
}

const EXPECTED_S = 90
const POLL_MS = 2500
const MAX_POLLS = 200

function parseInsights(result) {
  try {
    const r = result?.insights
    if (!r) return {}
    return typeof r === 'object' ? r : JSON.parse(r)
  } catch { return {} }
}

function Backdrop() {
  return (
    <div style={{ position: 'fixed', inset: 0, zIndex: 0, pointerEvents: 'none', overflow: 'hidden' }}>
      <img src={bgImage} alt="" style={{ position: 'absolute', top: '50%', left: '50%', transform: 'translate(-50%, -50%) rotate(-90deg) scale(1.5)', width: '100vh', height: '100vw', objectFit: 'cover', filter: 'grayscale(100%) brightness(0.8) contrast(1.05)' }} />
      <div style={{ position: 'absolute', inset: 0, background: 'radial-gradient(ellipse 80% 70% at 50% 40%, rgba(4,4,6,0.60) 0%, rgba(4,4,6,0.85) 70%, rgba(4,4,6,0.97) 100%)' }} />
    </div>
  )
}

function ConfidenceChip({ confidence }) {
  const tone = { High: '#B8D8B8', Moderate: '#DCC8A0' }[confidence.level] || '#C8D8E8'
  return (
    <span style={{ flexShrink: 0, fontFamily: S.fontSC, fontSize: 8, letterSpacing: '0.12em', textTransform: 'uppercase', color: tone, border: `1px solid ${tone}66`, padding: '4px 9px', whiteSpace: 'nowrap' }}>
      {confidence.level} confidence · {confidence.score}%
    </span>
  )
}

export default function DeepDive() {
  const { resultId } = useParams()
  const navigate = useNavigate()
  const [result, setResult] = useState(null)
  const [timedOut, setTimedOut] = useState(false)
  const [elapsed, setElapsed] = useState(0)
  const startRef = useRef(Date.now())
  const requestedRef = useRef(false)

  const requestGeneration = (force = false) => {
    startRef.current = Date.now()
    setElapsed(0)
    setTimedOut(false)
    api.post(`/results/${resultId}/deep-dive`, { force })
      .then(() => api.get(`/results/${resultId}`))
      .then(res => setResult(res.data))
      .catch(() => setTimedOut(true))
  }

  useEffect(() => {
    api.get(`/results/${resultId}`)
      .then(res => {
        setResult(res.data)
        const dd = parseInsights(res.data).deep_dive
        const ready = dd?.status === 'ok' && dd?.bullets?.length > 0
        if (!ready && res.data.enrichment_status !== 'pending' && !requestedRef.current) {
          requestedRef.current = true
          requestGeneration(false)
        }
      })
      .catch(() => navigate('/dashboard'))
  }, [resultId])

  useEffect(() => {
    if (!result || result.enrichment_status !== 'pending') return
    let polls = 0
    const iv = setInterval(() => {
      polls += 1
      if (polls > MAX_POLLS) { clearInterval(iv); setTimedOut(true); return }
      api.get(`/results/${resultId}`)
        .then(res => {
          if (res.data.enrichment_status !== 'pending') {
            clearInterval(iv)
            setResult(res.data)
          }
        })
        .catch(() => { clearInterval(iv); setTimedOut(true) })
    }, POLL_MS)
    const tick = setInterval(() => setElapsed((Date.now() - startRef.current) / 1000), 500)
    return () => { clearInterval(iv); clearInterval(tick) }
  }, [resultId, result?.enrichment_status])

  if (!result) return (
    <div style={{ minHeight: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
      <div className="spinner" style={{ width: 40, height: 40 }} />
    </div>
  )

  const dd = parseInsights(result).deep_dive
  const bullets = dd?.bullets || []
  const ready = dd?.status === 'ok' && bullets.length > 0
  const pending = result.enrichment_status === 'pending' && !timedOut
  const accent = ACCENTS[result.test_type] || ACCENTS.hexaco
  const progress = Math.min(0.94, elapsed / EXPECTED_S)

  return (
    <div className="page" style={{ minHeight: '100vh', position: 'relative', paddingBottom: 80 }}>
      <Backdrop />
      <div style={{ maxWidth: 820, margin: '0 auto', padding: '52px 32px 0', position: 'relative', zIndex: 1 }}>
        <div className="animate-fade-up" style={{ marginBottom: 28 }}>
          <div style={{ fontFamily: S.fontSC, fontSize: 8, letterSpacing: '0.26em', color: S.textMuted, marginBottom: 10 }}>
            DEEP DIVE · PSYCHOLOGICAL FORMULATION
          </div>
          <h1 style={{ fontFamily: S.fontDisplay, fontStyle: 'italic', fontSize: 'clamp(30px,4.5vw,46px)', fontWeight: 300, letterSpacing: '-0.01em', color: S.textPrim, lineHeight: 1.05 }}>
            {result.archetype_name || 'Your Profile'}
          </h1>
          {dd?.instrument && (
            <div style={{ fontFamily: S.fontBody, fontStyle: 'italic', fontSize: 13, color: S.textSec, marginTop: 10 }}>
              {dd.instrument}{dd.citation ? ` (${dd.citation})` : ''}
            </div>
          )}
        </div>

        <div className="animate-fade-up" style={{ background: S.frost, backdropFilter: 'blur(32px) saturate(1.4)', WebkitBackdropFilter: 'blur(32px) saturate(1.4)', border: `1px solid ${S.frostBorder}`, boxShadow: 'inset 0 1px 0 rgba(255,255,255,0.05)', padding: '28px 32px' }}>
          {dd?.source_note && (
            <p style={{ fontFamily: S.fontBody, fontStyle: 'italic', fontSize: 13, color: S.textSec, lineHeight: 1.8, margin: '0 0 16px', paddingLeft: 14, borderLeft: `2px solid ${accent}88` }}>{dd.source_note}</p>
          )}

          {pending && (
            <div style={{ padding: '26px 4px 10px' }}>
              <div style={{ fontFamily: S.fontDisplay, fontStyle: 'italic', fontSize: 22, fontWeight: 300, color: S.textPrim, marginBottom: 8 }}>
                Writing your formulation
              </div>
              <p style={{ fontFamily: S.fontBody, fontStyle: 'italic', fontSize: 13.5, color: S.textSec, lineHeight: 1.8, marginBottom: 20 }}>
                Each construct in your profile is being interpreted and checked against your scores. This usually takes one to two minutes.
              </p>
              <div style={{ height: 2, background: 'rgba(215,228,242,0.10)', position: 'relative', overflow: 'hidden' }}>
                <div style={{ position: 'absolute', left: 0, top: 0, bottom: 0, width: `${Math.max(2, Math.round(progress * 100))}%`, background: accent, transition: 'width 500ms linear' }} />
              </div>
              <div style={{ fontFamily: S.fontMono, fontSize: 10, color: S.textMuted, marginTop: 8 }}>{Math.round(elapsed)}s</div>
            </div>
          )}

          {!pending && ready && dd.confidence_summary && (
            <div style={{ marginBottom: 14, padding: '14px 18px', background: 'rgba(215,228,242,0.04)', border: '1px solid rgba(215,228,242,0.08)' }}>
              <div style={{ fontFamily: S.fontSC, fontSize: 7.5, letterSpacing: '0.16em', color: S.irisDim, textTransform: 'uppercase', marginBottom: 8 }}>How confident is this</div>
              <div style={{ fontFamily: S.fontDisplay, fontStyle: 'italic', fontSize: 18, color: S.textPrim, marginBottom: 8 }}>
                {['High', 'Moderate'].filter(l => dd.confidence_summary.counts[l] > 0).map(l => `${dd.confidence_summary.counts[l]} ${l.toLowerCase()}`).join(' · ')}
                {dd.confidence_summary.withheld > 0 ? ` · ${dd.confidence_summary.withheld} withheld after failing the check` : ''}
              </div>
              <p style={{ fontFamily: S.fontBody, fontStyle: 'italic', fontSize: 12.5, color: S.textSec, lineHeight: 1.75, margin: 0 }}>{dd.confidence_method}</p>
            </div>
          )}

          {!pending && ready && (
            <ul style={{ listStyle: 'none', margin: 0, padding: 0, display: 'flex', flexDirection: 'column', gap: 14 }}>
              {bullets.map((b, i) => (
                <li key={i} style={{ padding: '18px 22px', background: 'rgba(215,228,242,0.04)', border: '1px solid rgba(215,228,242,0.08)', borderLeft: `2px solid ${accent}77` }}>
                  <div style={{ display: 'flex', gap: 12, alignItems: 'baseline', marginBottom: 6 }}>
                    <span style={{ color: accent, fontSize: 11, opacity: 0.8, flexShrink: 0 }}>◆</span>
                    <h3 style={{ fontFamily: S.fontDisplay, fontStyle: 'italic', fontSize: 16.5, fontWeight: 400, color: S.textPrim, lineHeight: 1.3, margin: 0, flex: 1 }}>{b.construct}</h3>
                    {b.confidence && <ConfidenceChip confidence={b.confidence} />}
                  </div>
                  <div style={{ fontFamily: S.fontSC, fontSize: 8.5, letterSpacing: '0.08em', color: S.irisDim, lineHeight: 1.7, marginBottom: 4, paddingLeft: 23 }}>
                    {b.framework}
                  </div>
                  {b.evidence && (
                    <div style={{ fontFamily: S.fontMono, fontSize: 10.5, color: S.textMuted, lineHeight: 1.7, marginBottom: 10, paddingLeft: 23 }}>
                      {b.evidence}
                    </div>
                  )}
                  <p style={{ fontFamily: S.fontBody, fontStyle: 'italic', fontSize: 13.5, color: 'rgba(244,247,250,0.80)', lineHeight: 1.9, margin: 0, paddingLeft: 23 }}>{b.text}</p>
                  {b.confidence?.reasons && (
                    <ul style={{ listStyle: 'none', margin: '12px 0 0', padding: '10px 0 0 23px', borderTop: '1px solid rgba(215,228,242,0.07)' }}>
                      {b.confidence.reasons.map((reason, j) => (
                        <li key={j} style={{ fontFamily: S.fontBody, fontStyle: 'italic', fontSize: 11.5, color: S.textMuted, lineHeight: 1.7 }}>{reason}</li>
                      ))}
                    </ul>
                  )}
                </li>
              ))}
            </ul>
          )}

          {!pending && !ready && (
            <div style={{ padding: '20px 4px 6px' }}>
              <div style={{ fontFamily: S.fontDisplay, fontStyle: 'italic', fontSize: 22, fontWeight: 300, color: S.textPrim, marginBottom: 8 }}>
                The deep dive is not available yet
              </div>
              <p style={{ fontFamily: S.fontBody, fontStyle: 'italic', fontSize: 13.5, color: S.textSec, lineHeight: 1.8, marginBottom: 18 }}>
                The deep dive could not be prepared just now. Please try again in a moment.
              </p>
              <button onClick={() => requestGeneration(true)} className="btn btn-primary">Try Again</button>
            </div>
          )}

          {!pending && ready && dd.references?.length > 0 && (
            <div style={{ marginTop: 18, padding: '14px 18px', background: 'rgba(215,228,242,0.03)', border: '1px solid rgba(215,228,242,0.08)' }}>
              <div style={{ fontFamily: S.fontSC, fontSize: 7.5, letterSpacing: '0.16em', color: S.irisDim, textTransform: 'uppercase', marginBottom: 8 }}>Research this deep dive draws on</div>
              <ol style={{ margin: 0, paddingLeft: 18 }}>
                {dd.references.map((ref, i) => (
                  <li key={i} style={{ fontFamily: S.fontBody, fontStyle: 'italic', fontSize: 11.5, color: S.textMuted, lineHeight: 1.7, marginBottom: 4 }}>{ref}</li>
                ))}
              </ol>
              <Link to="/acknowledgements" style={{ display: 'inline-block', marginTop: 8, fontFamily: S.fontSC, fontSize: 8.5, letterSpacing: '0.16em', color: S.irisDim, textTransform: 'uppercase' }}>Acknowledgements</Link>
            </div>
          )}

          {!pending && ready && dd.support_note && (
            <div style={{ marginTop: 18, padding: '14px 18px', background: 'rgba(215,228,242,0.03)', border: '1px solid rgba(215,228,242,0.10)', borderLeft: `2px solid ${accent}55` }}>
              <p style={{ fontFamily: S.fontBody, fontStyle: 'italic', fontSize: 12.5, color: S.textSec, lineHeight: 1.75, margin: 0 }}>{dd.support_note}</p>
            </div>
          )}


          {!pending && ready && (
            <button onClick={() => requestGeneration(true)} style={{ marginTop: 10, background: 'none', border: 'none', padding: 0, cursor: 'pointer', fontFamily: S.fontSC, fontSize: 8.5, letterSpacing: '0.16em', color: S.irisDim, textTransform: 'uppercase' }}>
              Regenerate
            </button>
          )}
        </div>

        <div role="note" style={{ marginTop: 3, padding: '20px 26px', background: 'rgba(200,214,230,0.08)', border: `1px solid ${accent}66`, borderLeft: `3px solid ${accent}` }}>
          <div style={{ fontFamily: S.fontSC, fontSize: 11, letterSpacing: '0.20em', color: S.textPrim, textTransform: 'uppercase', marginBottom: 8 }}>
            This is not a diagnosis
          </div>
          <p style={{ fontFamily: S.fontBody, fontStyle: 'italic', fontSize: 13.5, color: S.textSec, lineHeight: 1.8, margin: 0 }}>
            This deep dive is generated automatically from your questionnaire scores. It is reflective material for self-understanding, not a clinical assessment, and it cannot identify or rule out any mental health condition. Percentiles rank you within a self-selected online sample, not the general population. If anything here worries you, or you are struggling, please speak with a qualified mental health professional.
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
