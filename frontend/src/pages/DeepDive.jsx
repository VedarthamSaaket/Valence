import { useEffect, useRef, useState } from 'react'
import { useParams, Link, useNavigate } from 'react-router-dom'
import api from '../utils/api'
import bgImage from '../assets/Image60.jpeg'
import { generateHTMLReport } from './Results'

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

const BACKING = {
  strong: { color: '#8FCB9B', label: 'Research-backed' },
  partial: { color: '#E2C36B', label: 'Partly backed' },
  none: { color: '#8A9EAE', label: 'Interpretive' },
  withheld: { color: '#C99A8A', label: 'Explanation withheld' },
}
const BACKING_ORDER = ['strong', 'partial', 'none']

const cites = b => !!b.confidence?.reasons?.some(r => r.startsWith('Grounding: the paragraph cites'))

function backing(b) {
  if (!b.confidence?.research_points?.length) return 'none'
  return cites(b) ? 'strong' : 'partial'
}

function Dot({ level }) {
  return <span aria-hidden="true" style={{ display: 'inline-block', width: 8, height: 8, borderRadius: '50%', background: BACKING[level].color, flexShrink: 0 }} />
}

function BackingMark({ level }) {
  return (
    <span style={{ flexShrink: 0, display: 'inline-flex', alignItems: 'center', gap: 7, fontFamily: S.fontSC, fontSize: 8, letterSpacing: '0.12em', textTransform: 'uppercase', color: BACKING[level].color, whiteSpace: 'nowrap' }}>
      <Dot level={level} />{BACKING[level].label}
    </span>
  )
}

const noteBox = { padding: '18px 22px', background: 'rgba(215,228,242,0.04)', border: '1px solid rgba(215,228,242,0.08)' }
const noteText = { fontFamily: S.fontBody, fontStyle: 'italic', fontSize: 13.5, color: 'rgba(244,247,250,0.80)', lineHeight: 1.9, margin: 0, paddingLeft: 23 }
const noteSource = { fontFamily: S.fontMono, fontSize: 10.5, color: S.textMuted, lineHeight: 1.7, marginTop: 10, paddingLeft: 23 }

function NoteHead({ accent, label, level }) {
  return (
    <div style={{ display: 'flex', gap: 12, alignItems: 'baseline', marginBottom: 8 }}>
      <span style={{ color: accent, fontSize: 11, opacity: 0.8, flexShrink: 0 }}>◆</span>
      <span style={{ flex: 1, fontFamily: S.fontSC, fontSize: 8.5, letterSpacing: '0.16em', color: S.irisDim, textTransform: 'uppercase' }}>{label}</span>
      <BackingMark level={BACKING[level] ? level : 'strong'} />
    </div>
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
  const pageRef = useRef()
  const [downloading, setDownloading] = useState(false)

  const handleDownload = async () => {
    setDownloading(true)
    try {
      await generateHTMLReport(pageRef.current, { name: 'Deep Dive' }, `${result.test_type}-deep-dive`, result)
    } catch (e) {
      console.error('Report generation failed:', e)
    }
    setDownloading(false)
  }

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
  const withheldPoints = dd?.withheld_points || []
  const ready = dd?.status === 'ok' && bullets.length > 0
  const pending = result.enrichment_status === 'pending' && !timedOut
  const accent = ACCENTS[result.test_type] || ACCENTS.hexaco
  const notes = result.research_notes
  const looseFit = result.explain?.type?.fit === 'loose'
  const progress = Math.min(0.94, elapsed / EXPECTED_S)
  const supported = bullets.filter(b => b.confidence?.research_points?.length > 0).length
  const rest = bullets.length - supported
  const findings = [...new Set(bullets.flatMap(b => b.confidence?.research_points || []))]
  const tiers = BACKING_ORDER.map(level => ({ level, count: bullets.filter(b => backing(b) === level).length })).filter(t => t.count > 0)
  const collective = [
    supported === 0
      ? 'No published study applies directly to your scores, so the points above are interpretations based on what this test is known to measure.'
      : `${supported === bullets.length ? (supported === 1 ? 'The point above is' : `All ${supported} points above are`) : `${supported} of the ${bullets.length} points above ${supported === 1 ? 'is' : 'are'}`} supported directly by published studies that match your scores.${rest > 0 ? ` The other ${rest === 1 ? 'one is an interpretation' : `${rest} are interpretations`} based on what this test is known to measure.` : ''}`,
    findings.length > 0 && `Studies used: ${findings.join('; ')}.`,
    'Every number quoted above matches your actual results, and nothing written contradicts your scores or the research.',
  ].filter(Boolean)
  const bodyText = b =>(b.text.startsWith(b.construct) ? b.text.slice(b.construct.length).trim() : b.text)

  return (
    <div className="page" style={{ minHeight: '100vh', position: 'relative', paddingBottom: 80 }}>
      <Backdrop />
      <div ref={pageRef} style={{ maxWidth: 820, margin: '0 auto', padding: '52px 32px 0', position: 'relative', zIndex: 1 }}>
        <div className="animate-fade-up" style={{ marginBottom: 28 }}>
          <div style={{ fontFamily: S.fontSC, fontSize: 8, letterSpacing: '0.26em', color: S.textMuted, marginBottom: 10 }}>
            DEEP DIVE · PSYCHOLOGICAL FORMULATION
          </div>
          <h1 style={{ fontFamily: S.fontDisplay, fontStyle: 'italic', fontSize: 'clamp(30px,4.5vw,46px)', fontWeight: 300, letterSpacing: '-0.01em', color: S.textPrim, lineHeight: 1.05 }}>
            {looseFit ? 'Between Types' : (result.archetype_name || 'Your Profile')}
          </h1>
          {looseFit && (
            <div style={{ fontFamily: S.fontBody, fontStyle: 'italic', fontSize: 13, color: S.textSec, marginTop: 10 }}>
              Nearest type: {result.archetype_name}, a loose fit. Your scores differ from its typical member on the traits that define it.
            </div>
          )}
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

          {!pending && ready && (
            <ul style={{ listStyle: 'none', margin: 0, padding: 0, display: 'flex', flexDirection: 'column', gap: 14 }}>
              {bullets.map((b, i) => (
                <li key={i} style={{ padding: '18px 22px', background: 'rgba(215,228,242,0.04)', border: '1px solid rgba(215,228,242,0.08)', borderLeft: `2px solid ${accent}77` }}>
                  <div style={{ display: 'flex', gap: 12, alignItems: 'baseline', marginBottom: 6 }}>
                    <span style={{ color: accent, fontSize: 11, opacity: 0.8, flexShrink: 0 }}>◆</span>
                    <h3 style={{ fontFamily: S.fontDisplay, fontStyle: 'italic', fontSize: 16.5, fontWeight: 400, color: S.textPrim, lineHeight: 1.3, margin: 0, flex: 1 }}>{b.construct}</h3>
                    {b.confidence && <BackingMark level={backing(b)} />}
                  </div>
                  <div style={{ fontFamily: S.fontSC, fontSize: 8.5, letterSpacing: '0.08em', color: S.irisDim, lineHeight: 1.7, marginBottom: 4, paddingLeft: 23 }}>
                    {b.framework}
                  </div>
                  {b.evidence && (
                    <div style={{ fontFamily: S.fontMono, fontSize: 10.5, color: S.textMuted, lineHeight: 1.7, marginBottom: 10, paddingLeft: 23 }}>
                      {b.evidence}
                    </div>
                  )}
                  <p style={{ fontFamily: S.fontBody, fontStyle: 'italic', fontSize: 13.5, color: 'rgba(244,247,250,0.80)', lineHeight: 1.9, margin: 0, paddingLeft: 23 }}>{bodyText(b)}</p>
                </li>
              ))}
            </ul>
          )}

          {!pending && ready && withheldPoints.length > 0 && (
            <ul style={{ listStyle: 'none', margin: '14px 0 0', padding: 0, display: 'flex', flexDirection: 'column', gap: 14 }}>
              {withheldPoints.map((w, i) => (
                <li key={i} style={{ padding: '18px 22px', background: 'rgba(215,228,242,0.02)', border: '1px dashed rgba(215,228,242,0.14)' }}>
                  <div style={{ display: 'flex', gap: 12, alignItems: 'baseline', marginBottom: 6 }}>
                    <span style={{ color: S.irisDim, fontSize: 11, opacity: 0.8, flexShrink: 0 }}>◇</span>
                    <h3 style={{ fontFamily: S.fontDisplay, fontStyle: 'italic', fontSize: 16.5, fontWeight: 400, color: S.textSec, lineHeight: 1.3, margin: 0, flex: 1 }}>{w.construct}</h3>
                    <BackingMark level="withheld" />
                  </div>
                  <div style={{ fontFamily: S.fontSC, fontSize: 8.5, letterSpacing: '0.08em', color: S.irisDim, lineHeight: 1.7, marginBottom: 4, paddingLeft: 23 }}>{w.framework}</div>
                  <div style={{ fontFamily: S.fontMono, fontSize: 10.5, color: S.textMuted, lineHeight: 1.7, marginBottom: 10, paddingLeft: 23 }}>{w.evidence}</div>
                  <p style={{ fontFamily: S.fontBody, fontStyle: 'italic', fontSize: 13, color: S.textSec, lineHeight: 1.85, margin: 0, paddingLeft: 23 }}>
                    Your scores point to this finding, but the written explanation was withheld. {w.reason} The finding in the title comes from your scores alone and is shown so that nothing is hidden from you.
                  </p>
                </li>
              ))}
            </ul>
          )}

          {!pending && ready && (
            <div style={{ marginTop: 18, padding: '14px 18px', background: 'rgba(215,228,242,0.04)', border: '1px solid rgba(215,228,242,0.08)', borderLeft: `2px solid ${accent}88` }}>
              <div style={{ fontFamily: S.fontSC, fontSize: 7.5, letterSpacing: '0.16em', color: S.irisDim, textTransform: 'uppercase', marginBottom: 8 }}>How these points stand against the research</div>
              <div style={{ display: 'flex', flexWrap: 'wrap', alignItems: 'center', gap: '6px 18px', fontFamily: S.fontDisplay, fontStyle: 'italic', fontSize: 17, color: S.textPrim, marginBottom: 10 }}>
                {tiers.map(t => (
                  <span key={t.level} style={{ display: 'inline-flex', alignItems: 'center', gap: 8 }}>
                    <Dot level={t.level} />{t.count} {BACKING[t.level].label.toLowerCase()}
                  </span>
                ))}
                {dd.confidence_summary?.withheld > 0 && <span>{dd.confidence_summary.withheld} withheld after failing the checks</span>}
              </div>
              {collective.map((line, i) => (
                <p key={i} style={{ fontFamily: S.fontBody, fontStyle: 'italic', fontSize: 12.5, color: S.textSec, lineHeight: 1.75, margin: '0 0 6px' }}>{line}</p>
              ))}
            </div>
          )}

          {!pending && !ready && (
            <div style={{ padding: '20px 4px 6px' }}>
              <div style={{ fontFamily: S.fontDisplay, fontStyle: 'italic', fontSize: 22, fontWeight: 300, color: S.textPrim, marginBottom: 8 }}>
                The deep dive is not available yet
              </div>
              <p style={{ fontFamily: S.fontBody, fontStyle: 'italic', fontSize: 13.5, color: S.textSec, lineHeight: 1.8, marginBottom: 18 }}>
                The deep dive could not be prepared just now. Please try again in a moment.
              </p>
              <button data-report-exclude="true" onClick={() => requestGeneration(true)} className="btn btn-primary">Try Again</button>
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
              <Link data-report-exclude="true" to="/acknowledgements" style={{ display: 'inline-block', marginTop: 8, fontFamily: S.fontSC, fontSize: 8.5, letterSpacing: '0.16em', color: S.irisDim, textTransform: 'uppercase' }}>Acknowledgements</Link>
            </div>
          )}

          {!pending && ready && dd.support_note && (
            <div style={{ marginTop: 18, padding: '14px 18px', background: 'rgba(215,228,242,0.03)', border: '1px solid rgba(215,228,242,0.10)', borderLeft: `2px solid ${accent}55` }}>
              <p style={{ fontFamily: S.fontBody, fontStyle: 'italic', fontSize: 12.5, color: S.textSec, lineHeight: 1.75, margin: 0 }}>{dd.support_note}</p>
            </div>
          )}


          {!pending && ready && (
            <button data-report-exclude="true" onClick={() => requestGeneration(true)} style={{ marginTop: 10, background: 'none', border: 'none', padding: 0, cursor: 'pointer', fontFamily: S.fontSC, fontSize: 8.5, letterSpacing: '0.16em', color: S.irisDim, textTransform: 'uppercase' }}>
              Regenerate
            </button>
          )}
        </div>

        {notes && (notes.facts.length > 0 || notes.myths.length > 0) && (
          <div className="animate-fade-up" style={{ marginTop: 3, background: S.frost, backdropFilter: 'blur(32px) saturate(1.4)', WebkitBackdropFilter: 'blur(32px) saturate(1.4)', border: `1px solid ${S.frostBorder}`, boxShadow: 'inset 0 1px 0 rgba(255,255,255,0.05)', padding: '28px 32px' }}>
            {notes.facts.length > 0 && (
              <div>
                <div style={{ fontFamily: S.fontSC, fontSize: 8, letterSpacing: '0.26em', color: S.textMuted, marginBottom: 6 }}>FROM THE RESEARCH</div>
                <h2 style={{ fontFamily: S.fontDisplay, fontStyle: 'italic', fontSize: 24, fontWeight: 300, color: S.textPrim, margin: '0 0 16px' }}>What studies found about scores like yours</h2>
                <ul style={{ listStyle: 'none', margin: 0, padding: 0, display: 'flex', flexDirection: 'column', gap: 10 }}>
                  {notes.facts.map((f, i) => (
                    <li key={i} style={noteBox}>
                      <NoteHead accent={accent} label="Fact" level={f.backing} />
                      <p style={noteText}>{f.text}</p>
                      <div style={noteSource}>{f.source} · {f.basis}</div>
                    </li>
                  ))}
                </ul>
              </div>
            )}

            {notes.myths.length > 0 && (
              <div style={{ marginTop: 30 }}>
                <div style={{ fontFamily: S.fontSC, fontSize: 8, letterSpacing: '0.26em', color: S.textMuted, marginBottom: 6 }}>MYTHS, CHECKED</div>
                <h2 style={{ fontFamily: S.fontDisplay, fontStyle: 'italic', fontSize: 24, fontWeight: 300, color: S.textPrim, margin: '0 0 16px' }}>What your result does not mean</h2>
                <ul style={{ listStyle: 'none', margin: 0, padding: 0, display: 'flex', flexDirection: 'column', gap: 10 }}>
                  {notes.myths.map((m, i) => (
                    <li key={i} style={noteBox}>
                      <NoteHead accent={accent} label="Myth" level={m.backing} />
                      <p style={{ fontFamily: S.fontDisplay, fontStyle: 'italic', fontSize: 16, color: S.textSec, lineHeight: 1.5, margin: '0 0 12px', paddingLeft: 23, textDecoration: 'line-through', textDecorationColor: 'rgba(244,247,250,0.28)' }}>{m.myth}</p>
                      <div style={{ fontFamily: S.fontSC, fontSize: 7.5, letterSpacing: '0.16em', color: accent, textTransform: 'uppercase', marginBottom: 4, paddingLeft: 23 }}>What the research shows</div>
                      <p style={noteText}>{m.truth}</p>
                      <div style={noteSource}>{m.source} · {m.basis}</div>
                    </li>
                  ))}
                </ul>
              </div>
            )}

            {notes.links?.length > 0 && (
              <div style={{ marginTop: 30 }}>
                <div style={{ fontFamily: S.fontSC, fontSize: 8, letterSpacing: '0.26em', color: S.textMuted, marginBottom: 6 }}>OTHER INVENTORIES</div>
                <h2 style={{ fontFamily: S.fontDisplay, fontStyle: 'italic', fontSize: 24, fontWeight: 300, color: S.textPrim, margin: '0 0 16px' }}>How patterns like yours may show up elsewhere</h2>
                <ul style={{ listStyle: 'none', margin: 0, padding: 0, display: 'flex', flexDirection: 'column', gap: 10 }}>
                  {notes.links.map((l, i) => (
                    <li key={i} style={noteBox}>
                      <NoteHead accent={accent} label="Overlap" level={l.backing} />
                      <p style={noteText}>{l.text}</p>
                      <div style={noteSource}>{l.source} · {l.basis}</div>
                    </li>
                  ))}
                </ul>
              </div>
            )}

            <div style={{ marginTop: 18, padding: '14px 18px', background: 'rgba(215,228,242,0.03)', border: '1px solid rgba(215,228,242,0.08)' }}>
              <div style={{ fontFamily: S.fontSC, fontSize: 7.5, letterSpacing: '0.16em', color: S.irisDim, textTransform: 'uppercase', marginBottom: 8 }}>Studies behind this section</div>
              <ol style={{ margin: 0, paddingLeft: 18 }}>
                {notes.sources.map((ref, i) => (
                  <li key={i} style={{ fontFamily: S.fontBody, fontStyle: 'italic', fontSize: 11.5, color: S.textMuted, lineHeight: 1.7, marginBottom: 4 }}>{ref}</li>
                ))}
              </ol>
              <p style={{ fontFamily: S.fontBody, fontStyle: 'italic', fontSize: 11.5, color: S.textMuted, lineHeight: 1.7, margin: '8px 0 0' }}>
                These are findings about groups of people in published studies, chosen by your score levels. They describe tendencies, and no single finding has to hold for you.
              </p>
              <Link data-report-exclude="true" to="/acknowledgements" style={{ display: 'inline-block', marginTop: 8, fontFamily: S.fontSC, fontSize: 8.5, letterSpacing: '0.16em', color: S.irisDim, textTransform: 'uppercase' }}>Acknowledgements</Link>
            </div>
          </div>
        )}

        <div role="note" style={{ marginTop: 3, padding: '20px 26px', background: 'rgba(200,214,230,0.08)', border: `1px solid ${accent}66`, borderLeft: `3px solid ${accent}` }}>
          <div style={{ fontFamily: S.fontSC, fontSize: 11, letterSpacing: '0.20em', color: S.textPrim, textTransform: 'uppercase', marginBottom: 8 }}>
            This is not a diagnosis
          </div>
          <p style={{ fontFamily: S.fontBody, fontStyle: 'italic', fontSize: 13.5, color: S.textSec, lineHeight: 1.8, margin: 0 }}>
            This deep dive is generated automatically from your questionnaire scores. It is reflective material for self-understanding, not a clinical assessment, and it cannot identify or rule out any mental health condition. Percentiles rank you within a self-selected online sample, not the general population. If anything here worries you, or you are struggling, please speak with a qualified mental health professional.
          </p>
        </div>

        <div data-report-exclude="true" style={{ marginTop: 3 }}>
          <button onClick={handleDownload} disabled={downloading} className="btn btn-primary" style={{ width: '100%', justifyContent: 'center' }}>
            {downloading ? 'Preparing Report...' : 'Download Deep Dive'}
          </button>
        </div>

        <div data-report-exclude="true" style={{ marginTop: 3, display: 'flex', gap: 3 }}>
          <Link to={`/results/${resultId}`} className="btn btn-secondary" style={{ flex: 1, justifyContent: 'center' }}>Base Results</Link>
          <Link to="/dashboard" className="btn btn-secondary" style={{ flex: 1, justifyContent: 'center' }}>Dashboard</Link>
        </div>
      </div>
    </div>
  )
}
