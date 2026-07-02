import { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import api from '../utils/api'
import bgImage from '../assets/Image60.jpeg'

const S = {
  fontDisplay: "'Cormorant Garamond', Georgia, serif",
  fontSC: "'Cinzel', serif",
  fontBody: "'Libre Baskerville', Georgia, serif",
  fontMono: "'JetBrains Mono', monospace",
  textPrim: '#F4F7FA',
  textSec: 'rgba(244,247,250,0.60)',
  textMuted: 'rgba(244,247,250,0.32)',
  frost: 'rgba(200,214,230,0.05)',
  frostBorder: 'rgba(215,228,242,0.14)',
}

const METAL = 'linear-gradient(135deg,#8090a2 0%,#c8d8e8 18%,#eef6fc 36%,#d8e8f4 54%,#f4f8fc 72%,#b8ccda 100%)'

const TEST_META = {
  hexaco:     { name: 'Six-Trait Personality',    short: 'Six Traits',           accent: '#C8D8E8', roman: 'I' },
  sixteenpf:  { name: 'Sixteen Personality Traits',         short: '16 Traits',       accent: '#C0B8D0', roman: 'II' },
  darktriad:  { name: 'Dark Traits',      short: 'Dark Traits',       accent: '#B0BCC8', roman: 'III' },
  fti:        { name: 'Temperament Type',    short: 'Temperament',      accent: '#CFC0DA', roman: 'IV' },
  npi:        { name: 'How You See Yourself',     short: 'Self-View',        accent: '#DCB8C8', roman: 'V' },
  ambi:       { name: 'Broad Personality Scan',short: 'Broad Scan',       accent: '#A8B0C8', roman: 'VI' },
  pid5:       { name: 'Five Trait Styles',short: 'Five Styles',     accent: '#B8C0D8', roman: 'VII' },
  hsq:        { name: 'Humor Style',          short: 'Humor',            accent: '#DCC8A0', roman: 'VIII' },
  kims:       { name: 'Mindfulness Skills',    short: 'Mindfulness',      accent: '#B8D8B8', roman: 'IX' },
  gcbs:       { name: 'Conspiracy Beliefs',  short: 'Conspiracy',        accent: '#D8B898', roman: 'X' },
  aesthetic:  { name: 'Aesthetic Taste',     short: 'Aesthetic',        accent: '#C8C4D4', roman: 'XI' },
  riasec:     { name: 'Career Type',         short: 'Career',           accent: '#C0CCD6', roman: 'XII' },
  attachment: { name: 'Attachment Style',    short: 'Attachment',       accent: '#BCC0D4', roman: 'XIII' },
  pvq:        { name: 'Core Values',         short: 'Values',           accent: '#C8D8B0', roman: 'XIV' },
  bpnss:      { name: 'Inner Needs',       short: 'Inner Needs',            accent: '#A8D8C8', roman: 'XV' },
  dass:       { name: 'Mood and Stress',  short: 'Stress and Mood',  accent: '#C0C0D0', roman: 'XVI' },
  who5:       { name: 'Wellbeing Check',     short: 'Wellbeing',        accent: '#B8E0C8', roman: 'XVII' },
}

const ALL_TESTS = Object.entries(TEST_META).map(([id, m]) => ({ id, ...m }))

function MiniRadar({ traits, accent, size = 80 }) {
  const entries = Object.entries(traits).slice(0, 6)
  if (entries.length < 3) return null
  const n = entries.length
  const cx = size / 2, cy = size / 2, r = size / 2 - 8
  const angleStep = (2 * Math.PI) / n
  const pts = entries.map(([, v], i) => {
    const a = i * angleStep - Math.PI / 2
    const val = Math.max(0.05, Math.min(1, v))
    return [cx + Math.cos(a) * r * val, cy + Math.sin(a) * r * val]
  })
  const rings = [0.33, 0.66, 1.0].map(s =>
    entries.map((_, i) => {
      const a = i * angleStep - Math.PI / 2
      return [cx + Math.cos(a) * r * s, cy + Math.sin(a) * r * s]
    })
  )
  const polyStr = arr => arr.map(p => p.join(',')).join(' ')
  return (
    <svg viewBox={`0 0 ${size} ${size}`} style={{ width: size, height: size, flexShrink: 0 }}>
      {rings.map((ring, ri) => (
        <polygon key={ri} points={polyStr(ring)} fill="none" stroke="rgba(215,228,242,0.08)" strokeWidth="0.5" />
      ))}
      <polygon points={polyStr(pts)} fill={`${accent}22`} stroke={accent} strokeWidth="1" strokeOpacity="0.55" />
      {pts.map(([x, y], i) => <circle key={i} cx={x} cy={y} r="2" fill={accent} fillOpacity="0.70" />)}
    </svg>
  )
}

function TraitMiniBar({ trait, pct, accent }) {
  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 5 }}>
      <span style={{ fontFamily: S.fontBody, fontStyle: 'italic', fontSize: 11, color: S.textMuted, minWidth: 90, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{trait}</span>
      <div style={{ flex: 1, height: 2, background: 'rgba(215,228,242,0.07)' }}>
        <div style={{ height: '100%', width: `${pct}%`, background: accent, opacity: 0.55 }} />
      </div>
      <span style={{ fontFamily: S.fontMono, fontSize: 9, color: S.textMuted, minWidth: 28, textAlign: 'right' }}>{pct}th</span>
    </div>
  )
}

function ResultCard({ result, meta }) {
  const { accent, short, roman } = meta
  const topTraits = Object.entries(result.percentiles || {}).sort((a, b) => b[1] - a[1]).slice(0, 3)
  const medianPct = (() => {
    const vals = Object.values(result.percentiles || {})
    if (!vals.length) return 50
    return Math.round([...vals].sort((a, b) => a - b)[Math.floor(vals.length / 2)])
  })()
  const date = new Date(result.taken_at).toLocaleDateString('en-GB', { day: 'numeric', month: 'short', year: 'numeric' })

  return (
    <div style={{ background: S.frost, backdropFilter: 'blur(24px)', WebkitBackdropFilter: 'blur(24px)', border: `1px solid ${S.frostBorder}`, boxShadow: `inset 0 1px 0 rgba(255,255,255,0.04)`, position: 'relative', overflow: 'hidden' }}>
      <div style={{ position: 'absolute', top: 0, left: 0, width: 2, height: '100%', background: `linear-gradient(180deg, ${accent}99, transparent)` }} />
      <div style={{ position: 'absolute', top: 0, left: 0, right: 0, height: 1, background: `linear-gradient(90deg, transparent, ${accent}44, transparent)` }} />

      <div style={{ padding: '20px 24px' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 16 }}>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 6 }}>
              <span style={{ fontFamily: S.fontDisplay, fontSize: 13, color: 'rgba(215,228,242,0.18)', letterSpacing: '0.04em' }}>{roman}</span>
              <span style={{ fontFamily: S.fontSC, fontSize: 7.5, letterSpacing: '0.22em', color: accent, textTransform: 'uppercase' }}>{short}</span>
            </div>
            <h3 style={{ fontFamily: S.fontDisplay, fontSize: 20, fontWeight: 300, letterSpacing: '-0.01em', color: S.textPrim, lineHeight: 1.1, fontStyle: 'italic' }}>
              {result.archetype_name || meta.name}
            </h3>
          </div>
          <MiniRadar traits={result.trait_scores || {}} accent={accent} size={72} />
        </div>

        <div style={{ display: 'flex', gap: 20, marginBottom: 16 }}>
          <div style={{ textAlign: 'center' }}>
            <div style={{ fontFamily: S.fontDisplay, fontSize: 26, fontWeight: 300, lineHeight: 1, background: METAL, WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent', backgroundClip: 'text', backgroundSize: '200% 200%', animation: 'metal-sweep 7s ease-in-out infinite' }}>{medianPct}th</div>
            <div style={{ fontFamily: S.fontSC, fontSize: 7, letterSpacing: '0.14em', color: S.textMuted, marginTop: 3 }}>Median pct</div>
          </div>
          <div style={{ width: 1, background: 'rgba(215,228,242,0.08)' }} />
          <div style={{ flex: 1 }}>
            {topTraits.map(([trait, pct]) => (
              <TraitMiniBar key={trait} trait={trait} pct={Math.round(pct)} accent={accent} />
            ))}
          </div>
        </div>

        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <span style={{ fontFamily: S.fontSC, fontSize: 7, letterSpacing: '0.14em', color: S.textMuted }}>{date}</span>
          <Link to={`/tests/${result.test_type}`} style={{ fontFamily: S.fontSC, fontSize: 7, letterSpacing: '0.18em', color: accent, textDecoration: 'none', padding: '5px 12px', border: `1px solid ${accent}33`, transition: 'all 200ms' }}
            onMouseEnter={e => { e.currentTarget.style.background = `${accent}18`; e.currentTarget.style.borderColor = `${accent}77` }}
            onMouseLeave={e => { e.currentTarget.style.background = 'transparent'; e.currentTarget.style.borderColor = `${accent}33` }}>
            Retake
          </Link>
        </div>
      </div>
    </div>
  )
}

function ProgressRing({ completed, total = 17 }) {
  const r = 44, circumference = 2 * Math.PI * r
  const progress = completed / total
  return (
    <svg width={110} height={110} style={{ flexShrink: 0 }}>
      <circle cx={55} cy={55} r={r} fill="none" stroke="rgba(215,228,242,0.07)" strokeWidth={2} />
      <circle cx={55} cy={55} r={r} fill="none" stroke="url(#ringGrad)" strokeWidth={1.5}
        strokeDasharray={circumference} strokeDashoffset={circumference * (1 - progress)}
        strokeLinecap="round" transform="rotate(-90 55 55)" style={{ transition: 'stroke-dashoffset 1.2s cubic-bezier(0.4,0,0.2,1)' }} />
      <defs>
        <linearGradient id="ringGrad" x1="0" y1="0" x2="1" y2="0">
          <stop offset="0%" stopColor="#8090a2" />
          <stop offset="50%" stopColor="#c8d8e8" />
          <stop offset="100%" stopColor="#eef6fc" />
        </linearGradient>
      </defs>
      <text x={55} y={51} textAnchor="middle" fontFamily="'Cormorant Garamond', serif" fontSize={26} fontWeight={300} fill="#F4F7FA">{completed}</text>
      <text x={55} y={64} textAnchor="middle" fontFamily="'Cinzel', serif" fontSize={7} letterSpacing={2} fill="rgba(244,247,250,0.32)">OF {total}</text>
    </svg>
  )
}

export default function Dashboard() {
  const { user } = useAuth()
  const [profile, setProfile] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    api.get('/user/profile')
      .then(res => setProfile(res.data))
      .finally(() => setLoading(false))
  }, [])

  if (loading) return (
    <div style={{ minHeight: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
      <div className="spinner" style={{ width: 44, height: 44 }} />
    </div>
  )

  const completedTests = profile?.completed_tests || []
  const recentResults = profile?.recent_results || []
  const latestByTest = {}
  recentResults.forEach(r => { if (!latestByTest[r.test_type]) latestByTest[r.test_type] = r })
  const completedWithResults = ALL_TESTS.filter(t => completedTests.includes(t.id) && latestByTest[t.id])
  const remaining = ALL_TESTS.filter(t => !completedTests.includes(t.id))

  return (
    <div className="page" style={{ paddingBottom: 80, position: 'relative', minHeight: '100vh' }}>
      {/* Atmospheric background, matches the treated imagery used across the app */}
      <div style={{ position: 'fixed', inset: 0, zIndex: 0, pointerEvents: 'none', overflow: 'hidden' }}>
        <img
          src={bgImage} alt=""
          style={{
            position: 'absolute', top: '50%', left: '50%',
            transform: 'translate(-50%, -50%) rotate(-90deg) scale(1.5)',
            width: '100vh', height: '100vw', objectFit: 'cover',
            filter: 'grayscale(100%) brightness(0.8) contrast(1.05)',
          }}
        />
        <div style={{ position: 'absolute', inset: 0, background: 'radial-gradient(ellipse 80% 70% at 50% 40%, rgba(4,4,6,0.60) 0%, rgba(4,4,6,0.85) 70%, rgba(4,4,6,0.97) 100%)' }} />
        <div style={{ position: 'absolute', inset: 0, background: 'linear-gradient(to bottom, rgba(4,4,6,0.15) 0%, rgba(4,4,6,0.0) 40%, rgba(4,4,6,0.92) 100%)' }} />
        <div style={{ position: 'absolute', left: '12%', top: '18%', width: 520, height: 520, borderRadius: '50%', background: 'radial-gradient(circle, rgba(190,210,228,0.05), transparent 70%)', filter: 'blur(120px)' }} />
        <div style={{ position: 'absolute', right: '10%', bottom: '16%', width: 440, height: 440, borderRadius: '50%', background: 'radial-gradient(circle, rgba(160,188,208,0.045), transparent 70%)', filter: 'blur(120px)' }} />
      </div>

      <div style={{ maxWidth: 1100, margin: '0 auto', padding: '52px 32px 0', position: 'relative', zIndex: 1 }}>

        <div className="animate-fade-up" style={{ display: 'flex', gap: 28, alignItems: 'flex-start', marginBottom: 48, flexWrap: 'wrap' }}>
          <div style={{ flex: 1, minWidth: 280 }}>
            <div style={{ fontFamily: S.fontSC, fontSize: 8, letterSpacing: '0.26em', color: S.textMuted, marginBottom: 10 }}>Dashboard</div>
            <h1 style={{ fontFamily: S.fontDisplay, fontSize: 'clamp(36px,5vw,60px)', fontWeight: 300, letterSpacing: '-0.02em', lineHeight: 1.0, background: METAL, WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent', backgroundClip: 'text', backgroundSize: '200% 200%', animation: 'metal-sweep 8s ease-in-out infinite', marginBottom: 10 }}>
              {user.username}
            </h1>
            <p style={{ fontFamily: S.fontBody, fontStyle: 'italic', fontSize: 14, color: S.textMuted }}>{user.email}</p>
          </div>
          <Link to="/tests" className="btn btn-primary" style={{ alignSelf: 'flex-start', marginTop: 8 }}>Explore Tests</Link>
        </div>

        <div className="animate-fade-up" style={{ background: S.frost, backdropFilter: 'blur(24px)', WebkitBackdropFilter: 'blur(24px)', border: `1px solid ${S.frostBorder}`, marginBottom: 3, padding: '28px 32px', position: 'relative', overflow: 'hidden' }}>
          <div style={{ position: 'absolute', top: 0, left: 0, right: 0, height: 1, background: 'linear-gradient(90deg, transparent, rgba(215,228,242,0.18), transparent)' }} />
          <div style={{ display: 'flex', gap: 32, alignItems: 'center', flexWrap: 'wrap' }}>
            <ProgressRing completed={completedTests.length} />
            <div style={{ flex: 1, minWidth: 200 }}>
              <div style={{ fontFamily: S.fontSC, fontSize: 8, letterSpacing: '0.24em', color: S.textMuted, marginBottom: 10 }}>Unified Personality Profile</div>
              <p style={{ fontFamily: S.fontBody, fontStyle: 'italic', fontSize: 14, color: S.textSec, lineHeight: 1.75, marginBottom: 18 }}>
                {completedTests.length === 0
                  ? 'Take your first test to start building your psychological profile.'
                  : completedTests.length < 4
                    ? `You have completed ${completedTests.length} of 17 assessments. Each one adds a new layer to your portrait.`
                    : `You have completed ${completedTests.length} assessments. Your profile is taking shape.`}
              </p>
              {profile?.master_archetype && (
                <div style={{ display: 'inline-flex', alignItems: 'center', gap: 10, padding: '8px 16px', background: 'rgba(215,228,242,0.06)', border: '1px solid rgba(215,228,242,0.14)' }}>
                  <span style={{ color: 'rgba(215,228,242,0.45)', fontSize: 12 }}>✦</span>
                  <span style={{ fontFamily: S.fontSC, fontSize: 8, letterSpacing: '0.18em', color: S.textSec }}>{profile.master_archetype}</span>
                </div>
              )}
            </div>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(110px, 1fr))', gap: 8, width: '100%' }}>
              {ALL_TESTS.map(t => {
                const done = completedTests.includes(t.id)
                return (
                  <Link key={t.id} to={`/tests/${t.id}`} style={{ textDecoration: 'none' }}>
                    <div style={{ padding: '10px 8px', textAlign: 'center', background: done ? `${t.accent}10` : 'rgba(215,228,242,0.02)', border: `1px solid ${done ? t.accent + '33' : 'rgba(215,228,242,0.07)'}`, transition: 'all 200ms' }}
                      onMouseEnter={e => { e.currentTarget.style.background = `${t.accent}1a` }}
                      onMouseLeave={e => { e.currentTarget.style.background = done ? `${t.accent}10` : 'rgba(215,228,242,0.02)' }}>
                      <div style={{ fontFamily: S.fontDisplay, fontSize: 11, color: done ? t.accent : 'rgba(215,228,242,0.20)', marginBottom: 3, lineHeight: 1 }}>{done ? '✓' : t.roman}</div>
                      <div style={{ fontFamily: S.fontSC, fontSize: 6, letterSpacing: '0.14em', color: done ? t.accent : S.textMuted, textTransform: 'uppercase', lineHeight: 1.4 }}>{t.short}</div>
                    </div>
                  </Link>
                )
              })}
            </div>
          </div>
        </div>

        {completedWithResults.length === 0 ? (
          <div className="animate-fade-up" style={{ background: S.frost, backdropFilter: 'blur(24px)', WebkitBackdropFilter: 'blur(24px)', border: `1px solid ${S.frostBorder}`, padding: '72px 32px', textAlign: 'center' }}>
            <div style={{ fontFamily: S.fontDisplay, fontSize: 56, fontWeight: 300, color: 'rgba(215,228,242,0.06)', letterSpacing: '-0.02em', marginBottom: 24, lineHeight: 1 }}>◈</div>
            <h2 style={{ fontFamily: S.fontDisplay, fontStyle: 'italic', fontSize: 32, fontWeight: 300, marginBottom: 14, letterSpacing: '-0.01em', background: METAL, WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent', backgroundClip: 'text', backgroundSize: '200% 200%', animation: 'metal-sweep 8s ease-in-out infinite' }}>
              Your journey begins here
            </h2>
            <p style={{ fontFamily: S.fontBody, fontStyle: 'italic', fontSize: 16, color: S.textSec, maxWidth: 400, margin: '0 auto 32px', lineHeight: 1.75 }}>
              Take your first assessment to start building your psychological portrait.
            </p>
            <Link to="/tests" className="btn btn-primary">Choose a Test</Link>
          </div>
        ) : (
          <div>
            <div className="animate-fade-up" style={{ display: 'flex', alignItems: 'baseline', gap: 16, marginBottom: 20, marginTop: 28 }}>
              <h2 style={{ fontFamily: S.fontDisplay, fontStyle: 'italic', fontSize: 26, fontWeight: 300, color: S.textPrim }}>Your Results</h2>
              <span style={{ fontFamily: S.fontSC, fontSize: 8, letterSpacing: '0.20em', color: S.textMuted }}>{completedWithResults.length} completed</span>
            </div>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(320px, 1fr))', gap: 3 }}>
              {completedWithResults.map(test => (
                <ResultCard key={test.id} result={latestByTest[test.id]} meta={test} />
              ))}
            </div>

            {remaining.length > 0 && (
              <div style={{ marginTop: 36 }}>
                <div className="animate-fade-up" style={{ display: 'flex', alignItems: 'baseline', gap: 16, marginBottom: 20 }}>
                  <h2 style={{ fontFamily: S.fontDisplay, fontStyle: 'italic', fontSize: 22, fontWeight: 300, color: S.textSec }}>Still to Explore</h2>
                  <span style={{ fontFamily: S.fontSC, fontSize: 8, letterSpacing: '0.20em', color: S.textMuted }}>{remaining.length} remaining</span>
                </div>
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(220px, 1fr))', gap: 3 }}>
                  {remaining.map(test => (
                    <Link key={test.id} to={`/tests/${test.id}`} style={{ textDecoration: 'none' }}>
                      <div style={{ padding: '18px 22px', background: 'rgba(215,228,242,0.02)', border: '1px solid rgba(215,228,242,0.07)', transition: 'all 220ms', position: 'relative', overflow: 'hidden' }}
                        onMouseEnter={e => { e.currentTarget.style.background = 'rgba(215,228,242,0.05)'; e.currentTarget.style.borderColor = `${test.accent}33` }}
                        onMouseLeave={e => { e.currentTarget.style.background = 'rgba(215,228,242,0.02)'; e.currentTarget.style.borderColor = 'rgba(215,228,242,0.07)' }}>
                        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                          <div>
                            <div style={{ fontFamily: S.fontDisplay, fontSize: 13, color: 'rgba(215,228,242,0.14)', letterSpacing: '0.04em', marginBottom: 6 }}>{test.roman}</div>
                            <div style={{ fontFamily: S.fontDisplay, fontStyle: 'italic', fontSize: 16, color: S.textSec, fontWeight: 300 }}>{test.name}</div>
                            <div style={{ fontFamily: S.fontSC, fontSize: 7, letterSpacing: '0.16em', color: S.textMuted, marginTop: 4 }}>{test.short}</div>
                          </div>
                          <span style={{ color: 'rgba(215,228,242,0.18)', fontSize: 16 }}>↗</span>
                        </div>
                      </div>
                    </Link>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}
      </div>

      <style>{`
        @keyframes metal-sweep { 0%,100%{background-position:0% 50%} 50%{background-position:100% 50%} }
      `}</style>
    </div>
  )
}