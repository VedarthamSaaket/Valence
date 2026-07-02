import { Link, useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import Galaxy from '../components/Galaxy'
import CurvedLoop from '../components/CurvedLoop'

const CATEGORIES = [
  {
    id: 'personality',
    label: 'Who You Are',
    roman: 'I',
    tests: [
      {
        id: 'hexaco',
        num: '01',
        tag: 'Foundation, 240 Questions',
        name: ['Six-Trait', 'Personality'],
        desc: 'Six broad personality factors including Honesty-Humility, the dimension the classic Big Five misses. The most complete trait picture in modern personality science.',
        traits: ['Honesty-Humility', 'Emotionality', 'Extraversion', 'Agreeableness', 'Conscientiousness', 'Openness'],
      },
      {
        id: 'sixteenpf',
        num: '02',
        tag: 'Deep Structure, 163 Questions',
        name: ['Sixteen', 'Traits'],
        desc: "Cattell's sixteen factors go deeper than any other personality framework. The highest dimensional resolution of how your mind is structured.",
        traits: ['Warmth', 'Reasoning', 'Stability', 'Dominance', 'Liveliness', 'Tension'],
      },
      {
        id: 'darktriad',
        num: '03',
        tag: 'Shadow Self, 27 Questions',
        name: ['Dark', 'Traits'],
        desc: 'Three darker traits most people prefer not to measure. Honest self-knowledge requires looking at all of yourself.',
        traits: ['Machiavellianism', 'Narcissism', 'Psychopathy'],
      },
      {
        id: 'fti',
        num: '04',
        tag: 'Temperament, 56 Questions',
        name: ['Temperament', 'Type'],
        desc: 'Four neurotransmitter-linked temperaments first proposed by Helen Fisher. Each one shapes how you think, decide, and connect.',
        traits: ['Explorer', 'Builder', 'Director', 'Negotiator'],
      },
      {
        id: 'npi',
        num: '05',
        tag: 'Self-View, 40 Questions',
        name: ['How You See', 'Yourself'],
        desc: 'Seven facets of how you see yourself in relation to others, from authority and self-sufficiency to vanity and entitlement.',
        traits: ['Authority', 'Self-Sufficiency', 'Superiority', 'Exhibitionism', 'Exploitativeness', 'Vanity', 'Entitlement'],
      },
      {
        id: 'ambi',
        num: '06',
        tag: 'Broad Scan, 181 Questions',
        name: ['Broad', 'Personality'],
        desc: 'The widest personality scan in this collection, covering nearly two hundred personality scales in a single sitting.',
        traits: ['Affect Regulation', 'Social Drive', 'Conscientiousness', 'Openness', 'Agreeableness', 'Energy Drive', 'Identity Coherence'],
      },
      {
        id: 'pid5',
        num: '07',
        tag: 'Trait Styles, 25 Questions',
        name: ['Five Trait', 'Styles'],
        desc: 'Five trait styles that show up across personality patterns. This describes personality styles, not clinical disorders. Not a diagnosis.',
        traits: ['Negative Affectivity', 'Detachment', 'Antagonism', 'Disinhibition', 'Psychoticism'],
      },
    ],
  },
  {
    id: 'mind',
    label: 'How You Think',
    roman: 'II',
    tests: [
      {
        id: 'hsq',
        num: '08',
        tag: 'Humor Style, 32 Questions',
        name: ['Humor', 'Style'],
        desc: 'Four styles of humor, two that help relationships flourish and two that quietly erode them. Which ones do you use most?',
        traits: ['Affiliative', 'Self-Enhancing', 'Aggressive', 'Self-Defeating'],
      },
      {
        id: 'kims',
        num: '09',
        tag: 'Mindfulness, 39 Questions',
        name: ['Mindfulness', 'Skills'],
        desc: 'Four skills that make up day-to-day mindfulness, from noticing what is happening in your body to letting experience be what it is.',
        traits: ['Observing', 'Describing', 'Acting with Awareness', 'Accepting without Judgment'],
      },
      {
        id: 'gcbs',
        num: '10',
        tag: 'Worldview, 15 Questions',
        name: ['Conspiracy', 'Beliefs'],
        desc: 'Five flavors of how skeptical you are about official accounts and powerful actors behind big events.',
        traits: ['Government Malfeasance', 'Malevolent Global', 'Extraterrestrial Coverup', 'Personal Wellbeing Threats', 'Control of Information'],
      },
      {
        id: 'aesthetic',
        num: '11',
        tag: 'Perception, 30 Questions',
        name: ['Aesthetic', 'Taste'],
        desc: 'How you respond to intense, mainstream, traditional, and visual aesthetics. Your honest aesthetic fingerprint.',
        traits: ['Intense', 'Mainstream', 'Traditional', 'Visual'],
      },
    ],
  },
  {
    id: 'life',
    label: 'How You Live',
    roman: 'III',
    tests: [
      {
        id: 'riasec',
        num: '12',
        tag: 'Career, 48 Questions',
        name: ['Career', 'Type'],
        desc: 'Six career personality types that explain what environments bring out your best work.',
        traits: ['Realistic', 'Investigative', 'Artistic', 'Social', 'Enterprising', 'Conventional'],
      },
      {
        id: 'attachment',
        num: '13',
        tag: 'Relationships, 36 Questions',
        name: ['Attachment', 'Style'],
        desc: 'Your earliest bonds shaped how you attach to others today. See where you sit on the secure to anxious to avoidant map.',
        traits: ['Secure', 'Anxious', 'Avoidant'],
      },
      {
        id: 'pvq',
        num: '14',
        tag: 'Values, 21 Questions',
        name: ['Core', 'Values'],
        desc: 'Ten guiding values that shape what you treat as worth pursuing, from self-direction to security, achievement to benevolence.',
        traits: ['Self-Direction', 'Universalism', 'Achievement', 'Security', 'Hedonism', 'Benevolence'],
      },
      {
        id: 'bpnss',
        num: '15',
        tag: 'Inner Needs, 21 Questions',
        name: ['Inner', 'Needs'],
        desc: 'Three fundamental needs that humans run on, autonomy, competence, and relatedness. How well is each one being fed in your life right now?',
        traits: ['Autonomy', 'Competence', 'Relatedness'],
      },
    ],
  },
  {
    id: 'wellbeing',
    label: 'How You Feel',
    roman: 'IV',
    tests: [
      {
        id: 'dass',
        num: '16',
        tag: 'Mood and Stress, 42 Questions',
        name: ['Mood', 'and Stress'],
        desc: 'A snapshot of where you are right now across three currents of emotional experience. This is a self-reflection tool, not a diagnosis.',
        traits: ['Depression', 'Anxiety', 'Stress'],
      },
      {
        id: 'who5',
        num: '17',
        tag: 'Quick Check, 5 Questions',
        name: ['Wellbeing', 'Check'],
        desc: 'A quick check on how the last two weeks have felt. Five questions, one wellbeing number.',
        traits: ['Wellbeing'],
      },
    ],
  },
]

const FEATURES = [
  { idx: 'I', icon: '◈', title: 'Personality Archetype', body: 'ML clustering assigns you to an archetype derived from real population data. Not a predefined label, an empirical discovery.' },
  { idx: 'II', icon: '⬡', title: 'Personality Map', body: 'UMAP dimensionality reduction places you in a 2D landscape of personality space. See exactly where you sit among thousands.' },
  { idx: 'III', icon: '◎', title: 'Population Percentiles', body: 'Every trait scored against the real dataset distribution. Know precisely how rare your personality configuration is.' },
  { idx: 'IV', icon: '◇', title: 'Trait Radar', body: 'Visual breakdown of all trait dimensions simultaneously. The shape of your personality, rendered precisely.' },
  { idx: 'V', icon: '◉', title: 'Behavioral Insights', body: 'Pattern analysis of your highest and lowest traits translated into concrete language about how you move through the world.' },
  { idx: 'VI', icon: '⬟', title: 'Unified Profile', body: 'Complete all seventeen assessments and receive a master archetype drawn from your full dimensional personality vector.' },
]

const S = {
  fontDisplay: "'Cormorant Garamond', Georgia, serif",
  fontSC: "'Cormorant SC', serif",
  fontBody: "'Cormorant Garamond', Georgia, serif",
  fontSub: "'Libre Baskerville', Georgia, serif",
  border: 'rgba(190,200,215,0.10)',
  borderMd: 'rgba(200,210,225,0.24)',
  textPrim: '#EFF2F5',
  textSec: 'rgba(239,242,245,0.50)',
  textMuted: 'rgba(239,242,245,0.26)',
  bgCard: 'rgba(8,9,14,0.28)',
  bgCardHover: 'rgba(14,16,24,0.48)',
  iris: '#C8D4E0',
  irisDim: '#7A8A9A',
}

const METAL = 'linear-gradient(135deg,#6a7a8a 0%,#b0bec8 12%,#dce8f0 25%,#f0f5f8 35%,#c8d8e4 48%,#8aa0b0 58%,#dce8f2 70%,#f2f6f8 80%,#a8bcc8 92%,#c0d0dc 100%)'
const METAL2 = 'linear-gradient(135deg,#8a9eae 0%,#c8d8e4 20%,#f0f5f8 40%,#d0dce8 60%,#f4f8fa 80%,#b0c4d0 100%)'

function MetalText({ children, style: extra }) {
  return (
    <span style={{
      background: METAL, WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent',
      backgroundClip: 'text', backgroundSize: '200% 200%',
      animation: 'metal-sweep 8s ease-in-out infinite', ...extra,
    }}>{children}</span>
  )
}

function MetalEm({ children }) {
  return (
    <em style={{
      fontStyle: 'italic',
      background: METAL2, WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent',
      backgroundClip: 'text', backgroundSize: '200% 200%',
      animation: 'metal-sweep 5s ease-in-out infinite reverse',
    }}>{children}</em>
  )
}

function LabelGold({ children, style: extra }) {
  return (
    <span style={{
      fontFamily: S.fontSC, fontSize: 11, fontWeight: 500,
      letterSpacing: '0.18em', textTransform: 'uppercase',
      background: METAL2, WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent',
      backgroundClip: 'text', backgroundSize: '200% 200%',
      animation: 'metal-sweep 5s ease-in-out infinite', ...extra,
    }}>{children}</span>
  )
}

function TestCard({ t, onCardClick }) {
  return (
    <div
      className="test-card"
      onClick={() => onCardClick(t.id)}
      style={{
        padding: '36px 32px',
        height: '100%',
        boxSizing: 'border-box',
        background: S.bgCard,
        backdropFilter: 'blur(10px) saturate(1.2)',
        WebkitBackdropFilter: 'blur(10px) saturate(1.2)',
        border: '1px solid rgba(200,212,224,0.10)',
        boxShadow: 'inset 0 1px 0 rgba(255,255,255,0.06), 0 4px 24px rgba(0,0,0,0.18)',
        cursor: 'pointer', textAlign: 'left',
        transition: 'background 320ms ease, border-color 320ms ease, box-shadow 320ms ease',
      }}
    >
      <div style={{
        position: 'absolute', top: 0, left: 0, right: 0, height: '35%',
        background: 'linear-gradient(180deg, rgba(255,255,255,0.04) 0%, transparent 100%)',
        pointerEvents: 'none',
      }} />

      <div className="card-accent-bar" style={{
        position: 'absolute', top: 0, left: 0, width: 2,
        background: METAL, transition: 'height 400ms cubic-bezier(.4,0,.2,1)',
      }} />

      <div style={{
        fontFamily: S.fontDisplay, fontSize: 48, fontWeight: 300,
        lineHeight: 1, color: S.borderMd, marginBottom: 16,
      }}>{t.num}</div>

      <div style={{
        fontFamily: S.fontSC, fontSize: 10, letterSpacing: '0.2em',
        background: METAL2, WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent',
        backgroundClip: 'text', backgroundSize: '200% 200%',
        animation: 'metal-sweep 6s ease-in-out infinite', marginBottom: 12,
      }}>{t.tag}</div>

      <h3 style={{
        fontFamily: S.fontDisplay, fontSize: 26, fontWeight: 400,
        lineHeight: 1.1, marginBottom: 10, letterSpacing: '-0.01em', color: S.textPrim,
      }}>
        {t.name[0]}<br />{t.name[1]}
      </h3>

      <p style={{
        fontFamily: S.fontDisplay, fontStyle: 'italic', fontSize: 13.5,
        color: S.textSec, lineHeight: 1.65, maxWidth: 280, marginBottom: 20,
      }}>{t.desc}</p>

      <div style={{ display: 'flex', flexWrap: 'wrap', gap: 5 }}>
        {t.traits.map(tr => (
          <span key={tr} style={{
            fontFamily: S.fontSC, fontSize: 9, letterSpacing: '0.12em',
            padding: '3px 9px', border: '1px solid rgba(200,210,225,0.10)',
            borderRadius: 2, color: S.textMuted, background: 'rgba(255,255,255,0.02)',
          }}>{tr}</span>
        ))}
      </div>

      <div style={{ position: 'absolute', bottom: 28, right: 28, fontSize: 18, color: S.borderMd }}>↗</div>
    </div>
  )
}

export default function Landing() {
  const { user } = useAuth()
  const navigate = useNavigate()

  const handleTestClick = (testId) => {
    if (user) {
      navigate(`/tests/${testId}`)
    } else {
      navigate('/auth?mode=register')
    }
  }

  const handleBeginClick = () => {
    if (user) {
      navigate('/tests')
    } else {
      navigate('/auth?mode=register')
    }
  }

  return (
    <div style={{ position: 'relative', minHeight: '100vh', fontFamily: S.fontBody }}>

      {/* Galaxy background */}
      <div style={{
        position: 'fixed', inset: 0, zIndex: 0, pointerEvents: 'none',
        willChange: 'transform', transform: 'translateZ(0)', backfaceVisibility: 'hidden',
      }}>
        <Galaxy
          mouseRepulsion={true} mouseInteraction={true}
          density={1.2} glowIntensity={0.55} saturation={0.1} hueShift={140}
          twinkleIntensity={0.45} rotationSpeed={0.04} repulsionStrength={2.2}
          autoCenterRepulsion={0} starSpeed={0.5} speed={1} transparent={true}
        />
      </div>

      <div style={{ position: 'relative', zIndex: 1 }}>

        {/* ── Hero ── */}
        <section style={{
          minHeight: '100vh',
          display: 'flex', flexDirection: 'column', justifyContent: 'center', alignItems: 'flex-start',
          padding: '120px 40px 80px',
          position: 'relative', overflow: 'hidden', background: 'transparent',
        }}>
          <div style={{ position: 'absolute', inset: 0, pointerEvents: 'none', zIndex: 0 }}>
            {[
              { w: 700, h: 700, left: '-150px', top: '-80px', bg: 'rgba(180,195,215,0.04)', delay: '0.3s' },
              { w: 600, h: 600, right: '-100px', bottom: '60px', bg: 'rgba(155,180,200,0.035)', delay: '0.6s' },
              { w: 500, h: 500, left: '38%', top: '25%', bg: 'rgba(200,210,225,0.045)', delay: '0.9s' },
            ].map((b, i) => (
              <div key={i} style={{
                position: 'absolute', borderRadius: '50%', filter: 'blur(130px)',
                opacity: 0, width: b.w, height: b.h,
                left: b.left, right: b.right, top: b.top, bottom: b.bottom,
                background: `radial-gradient(circle, ${b.bg}, transparent 70%)`,
                animation: 'blob-in 2s ease forwards', animationDelay: b.delay,
              }} />
            ))}
          </div>

          <div style={{
            position: 'absolute', right: 80, top: 80, bottom: 80, width: 1,
            background: 'linear-gradient(to bottom, transparent, rgba(200,210,225,0.12) 20%, rgba(190,200,215,0.08) 80%, transparent)',
          }} />

          <div style={{ position: 'relative', zIndex: 1, width: '100%' }}>
            <div style={{ marginBottom: 40, display: 'flex', alignItems: 'center', gap: 20 }}>
              <div style={{ width: 40, height: 1, background: S.borderMd, flexShrink: 0 }} />
              <LabelGold>Personality Analytics Platform</LabelGold>
              <div style={{ width: 40, height: 1, background: S.borderMd, flexShrink: 0 }} />
            </div>

            <div style={{ position: 'relative', paddingBottom: '0.18em' }}>
              <div style={{
                fontFamily: S.fontDisplay, fontSize: 'clamp(160px,28vw,360px)',
                fontWeight: 700, lineHeight: 0.8, letterSpacing: '-0.04em',
                position: 'absolute', top: '-0.12em', left: '-0.03em',
                color: 'transparent', WebkitTextStroke: '1px rgba(200,210,225,0.045)',
                pointerEvents: 'none', userSelect: 'none', whiteSpace: 'nowrap', zIndex: 0,
              }}>Know</div>

              <h1 style={{
                fontFamily: S.fontDisplay, fontSize: 'clamp(72px,13vw,180px)',
                fontWeight: 300, lineHeight: 1.0, letterSpacing: '-0.02em',
                background: 'linear-gradient(135deg,#8090a0 0%,#c0d0dc 10%,#e8f0f8 22%,#f8fafc 32%,#d0dce8 44%,#98aab8 54%,#e0eaf2 66%,#f4f8fa 76%,#b8c8d4 88%,#ccdae4 100%)',
                WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent',
                backgroundClip: 'text', backgroundSize: '300% 300%',
                animation: 'metal-sweep 8s ease-in-out infinite',
                position: 'relative', zIndex: 1, margin: 0,
                overflow: 'visible', paddingBottom: '0.1em',
              }}>
                Know<br />
                <em style={{
                  fontStyle: 'italic', fontWeight: 300,
                  background: 'linear-gradient(135deg,#a8c0d0 0%,#dceaf4 20%,#f0f6fa 38%,#c0d4e0 55%,#f4f8fc 72%,#b0c8d8 88%,#d8e8f2 100%)',
                  WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent',
                  backgroundClip: 'text', backgroundSize: '200% 200%',
                  animation: 'metal-sweep 5s ease-in-out infinite reverse',
                }}>yourself</em><br />
                completely.
              </h1>
            </div>

            <div style={{ marginTop: 48, display: 'grid', gridTemplateColumns: '1fr auto', alignItems: 'flex-end', gap: 48 }}>
              <p style={{
                fontFamily: S.fontSub, fontSize: 'clamp(14px,1.5vw,17px)',
                fontWeight: 400, fontStyle: 'italic',
                color: 'rgba(220,228,238,0.52)', maxWidth: 440,
                lineHeight: 1.75, margin: 0, letterSpacing: '0.01em',
              }}>
                Twelve scientifically validated personality tests.<br />
                Machine learning analysis. Your position in the<br />
                global personality landscape, visualized.
              </p>
              <div style={{ display: 'flex', flexDirection: 'column', gap: 12, alignItems: 'flex-end' }}>
                <button
                  onClick={handleBeginClick}
                  className="btn btn-primary"
                  style={{ padding: '13px 32px' }}
                >
                  Begin Your Assessment
                </button>
                {!user && (
                  <Link to="/auth" className="btn btn-secondary" style={{ padding: '12px 28px' }}>
                    Sign In
                  </Link>
                )}
                {user && (
                  <Link to="/dashboard" className="btn btn-secondary" style={{ padding: '12px 28px' }}>
                    My Dashboard
                  </Link>
                )}
              </div>
            </div>
          </div>

          <div style={{
            position: 'absolute', bottom: 32, left: '50%', transform: 'translateX(-50%)',
            display: 'flex', flexDirection: 'column', alignItems: 'center',
            animation: 'float 3s ease-in-out infinite',
          }}>
            <div style={{ width: 1, height: 48, background: `linear-gradient(to bottom, ${S.iris}, transparent)` }} />
          </div>
        </section>

        <div style={{ height: 1, background: 'linear-gradient(90deg, transparent, rgba(200,210,225,0.14) 30%, rgba(200,210,225,0.14) 70%, transparent)' }} />

        {/* ── Tests grid ── */}
        <section style={{ padding: '120px 40px', background: 'transparent' }}>
          <div className="container">

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 48, marginBottom: 72, alignItems: 'end' }}>
              <div>
                <div style={{
                  fontFamily: S.fontDisplay, fontSize: 11, fontWeight: 300,
                  letterSpacing: '0.2em', color: S.irisDim, marginBottom: 16,
                }}>01, Assessments</div>
                <h2 style={{
                  fontFamily: S.fontDisplay, fontSize: 'clamp(42px,6vw,80px)',
                  fontWeight: 400, lineHeight: 1.0, letterSpacing: '-0.015em', margin: 0,
                }}>
                  <MetalText>Twelve lenses.</MetalText><br />
                  <MetalText>One </MetalText><MetalEm>portrait.</MetalEm>
                </h2>
              </div>
              <p style={{
                fontFamily: S.fontDisplay, fontStyle: 'italic', fontSize: 18,
                fontWeight: 300, color: S.textSec, lineHeight: 1.75, maxWidth: 360, margin: 0,
              }}>
                Three categories. Each test reveals a different layer of your psychology.
                Together, they form something you have never seen before.
              </p>
            </div>

            {!user && (
              <div style={{
                marginBottom: 40, padding: '14px 24px',
                background: 'rgba(200,212,224,0.04)',
                border: '1px solid rgba(200,212,224,0.12)',
                borderLeft: '2px solid rgba(200,212,224,0.30)',
                display: 'flex', alignItems: 'center', justifyContent: 'space-between',
                flexWrap: 'wrap', gap: 12,
              }}>
                <span style={{ fontFamily: S.fontDisplay, fontStyle: 'italic', fontSize: 15, color: S.textSec }}>
                  Create a free account to take any test and save your results.
                </span>
                <div style={{ display: 'flex', gap: 10 }}>
                  <Link to="/auth?mode=register" className="btn btn-primary" style={{ padding: '9px 22px', fontSize: 11 }}>
                    Create Account
                  </Link>
                  <Link to="/auth" className="btn btn-secondary" style={{ padding: '8px 18px', fontSize: 11 }}>
                    Sign In
                  </Link>
                </div>
              </div>
            )}

            {CATEGORIES.map((cat, ci) => (
              <div key={cat.id} style={{ marginBottom: 56 }}>
                <div style={{
                  display: 'flex', alignItems: 'baseline', gap: 16,
                  marginBottom: 20, paddingBottom: 14,
                  borderBottom: '1px solid rgba(200,210,225,0.08)',
                }}>
                  <span style={{
                    fontFamily: S.fontDisplay, fontSize: 40, fontWeight: 300,
                    lineHeight: 1, color: 'rgba(200,210,225,0.06)', letterSpacing: '-0.02em',
                  }}>{cat.roman}</span>
                  <span style={{
                    fontFamily: S.fontDisplay, fontSize: 'clamp(20px, 2.5vw, 28px)', fontWeight: 400,
                    background: METAL, WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent',
                    backgroundClip: 'text', backgroundSize: '200% 200%',
                    animation: `metal-sweep ${7 + ci}s ease-in-out infinite`,
                    letterSpacing: '-0.01em',
                  }}>{cat.label}</span>
                </div>

                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 1 }}>
                  {cat.tests.map(t => (
                    <TestCard key={t.id} t={t} onCardClick={handleTestClick} />
                  ))}
                </div>
              </div>
            ))}
          </div>
        </section>

        {/* ── Features ── */}
        <section style={{
          padding: '120px 40px',
          background: 'rgba(6,6,10,0.30)',
          backdropFilter: 'blur(6px)', WebkitBackdropFilter: 'blur(6px)',
        }}>
          <div className="container">
            <div style={{ display: 'flex', alignItems: 'center', gap: 16, marginBottom: 20 }}>
              <div style={{ width: 32, height: 1, background: S.iris }} />
              <LabelGold>02, What You Receive</LabelGold>
            </div>
            <h2 style={{
              fontFamily: S.fontDisplay, fontSize: 'clamp(42px,6vw,80px)',
              fontWeight: 400, lineHeight: 1.0, letterSpacing: '-0.015em', marginBottom: 0,
            }}>
              <MetalText>Not a quiz.</MetalText><br />
              <MetalEm>A platform.</MetalEm>
            </h2>
            <div style={{
              display: 'grid', gridTemplateColumns: 'repeat(3,1fr)',
              marginTop: 80, borderTop: `1px solid ${S.border}`, borderLeft: `1px solid ${S.border}`,
            }}>
              {FEATURES.map(f => (
                <div key={f.idx} className="feature-cell" style={{
                  padding: '44px 36px',
                  borderRight: `1px solid ${S.border}`, borderBottom: `1px solid ${S.border}`,
                  position: 'relative',
                  background: 'rgba(10,10,16,0.22)',
                  backdropFilter: 'blur(14px) saturate(1.15)', WebkitBackdropFilter: 'blur(14px) saturate(1.15)',
                  boxShadow: 'inset 0 1px 0 rgba(255,255,255,0.045)',
                  transition: 'background 300ms',
                }}>
                  <div style={{ position: 'absolute', top: 0, left: 0, right: 0, height: 1, background: 'rgba(255,255,255,0.06)', pointerEvents: 'none' }} />
                  <div style={{
                    fontFamily: S.fontDisplay, fontSize: 44, fontWeight: 300,
                    color: S.border, lineHeight: 1, marginBottom: 18,
                  }}>{f.idx}</div>
                  <span style={{ position: 'absolute', top: 36, right: 36, fontSize: 18, color: S.iris, opacity: 0.32 }}>{f.icon}</span>
                  <h3 style={{
                    fontFamily: S.fontDisplay, fontSize: 21, fontWeight: 400, marginBottom: 10,
                    background: METAL, WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent',
                    backgroundClip: 'text', backgroundSize: '200% 200%',
                    animation: 'metal-sweep 7s ease-in-out infinite',
                  }}>{f.title}</h3>
                  <p style={{ fontFamily: S.fontBody, fontStyle: 'italic', fontSize: 13.5, color: S.textSec, lineHeight: 1.7 }}>{f.body}</p>
                </div>
              ))}
            </div>
          </div>
        </section>

        {/* ── CTA with NARROW marquee belts ── */}
        <section style={{
          padding: '0',
          textAlign: 'center',
          position: 'relative',
          background: 'transparent',
        }}>
          {/* Ghost wordmark behind content */}
          <div style={{
            fontFamily: S.fontDisplay, fontSize: 'clamp(100px,20vw,260px)',
            fontWeight: 700, lineHeight: 0.85,
            position: 'absolute', inset: 0,
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            color: 'transparent', WebkitTextStroke: '1px rgba(200,210,225,0.045)',
            pointerEvents: 'none', userSelect: 'none', letterSpacing: '-0.04em', zIndex: 0,
          }}>Valence</div>

          {/* TOP belt */}
          <div style={{ position: 'relative', zIndex: 2 }}>
            <CurvedLoop
              marqueeText="Valence, Know Yourself, Personality Analytics, "
              speed={1.0}
              curveAmount={-120}
              direction="left"
              interactive={true}
            />
          </div>

          {/* CTA copy */}
          <div style={{ position: 'relative', zIndex: 3, padding: '24px 40px 20px' }}>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 16, marginBottom: 40 }}>
              <div style={{ maxWidth: 80, flex: 1, height: 1, background: S.border }} />
              <div style={{ width: 6, height: 6, background: S.iris, transform: 'rotate(45deg)', flexShrink: 0 }} />
              <div style={{ maxWidth: 80, flex: 1, height: 1, background: S.border }} />
            </div>
            <h2 style={{
              fontFamily: S.fontDisplay, fontSize: 'clamp(42px,6vw,80px)',
              fontWeight: 400, lineHeight: 1.0, letterSpacing: '-0.015em', marginBottom: 24,
            }}>
              <MetalText>Begin your</MetalText><br />
              <MetalEm>self-discovery.</MetalEm>
            </h2>
            <p style={{
              fontFamily: S.fontDisplay, fontStyle: 'italic', fontSize: 19,
              color: S.textSec, marginBottom: 48, fontWeight: 300,
            }}>
              The architecture of your mind, finally visible.
            </p>
            <button
              onClick={handleBeginClick}
              className="btn btn-primary"
              style={{ fontSize: 12, padding: '15px 48px' }}
            >
              {user ? 'Go to Tests' : 'Create Free Account'}
            </button>
          </div>

          {/* BOTTOM belt */}
          <div style={{ position: 'relative', zIndex: 2 }}>
            <CurvedLoop
              marqueeText="Valence, Know Yourself, Personality Analytics, "
              speed={1.0}
              curveAmount={120}
              direction="right"
              interactive={true}
            />
          </div>
        </section>

        {/* ── Footer ── */}
        <footer style={{
          marginTop: 40, padding: '48px 40px',
          borderTop: `1px solid ${S.border}`,
          background: 'rgba(6,6,10,0.18)',
          backdropFilter: 'blur(8px)', WebkitBackdropFilter: 'blur(8px)',
        }}>
          <div className="container" style={{
            display: 'flex', justifyContent: 'space-between',
            alignItems: 'center', flexWrap: 'wrap', gap: 20,
          }}>
            <span style={{
              fontFamily: S.fontSC, fontSize: 18, fontWeight: 600, letterSpacing: '0.22em',
              background: METAL, WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent',
              backgroundClip: 'text', backgroundSize: '200% 200%',
              animation: 'metal-sweep 8s ease-in-out infinite',
            }}>Valence</span>
            <span style={{
              fontFamily: S.fontSC, fontSize: 11, letterSpacing: '0.18em',
              color: S.textMuted, maxWidth: 600, textAlign: 'center', lineHeight: 2,
            }}>
              IPIP-NEO (Goldberg), 16PF (Cattell), SD3 (Jones &amp; Paulhus), DASS-21, OHBDS, ZTPI (Zimbardo), EQ-SQ (Baron-Cohen), APS, IPIP-AS (Goldberg), RIASEC (Holland), NIS, ECR (Brennan)
            </span>
            <span style={{
              fontFamily: S.fontSC, fontSize: 11, letterSpacing: '0.18em', color: S.textMuted,
            }}>Psychology, Machine Learning</span>
          </div>
        </footer>

      </div>

      <style>{`
        @keyframes metal-sweep {
          0%,100% { background-position: 0% 50%; }
          50%      { background-position: 100% 50%; }
        }
        @keyframes blob-in {
          to { opacity: 1; }
        }
        @keyframes float {
          0%,100% { transform: translateX(-50%) translateY(0); }
          50%      { transform: translateX(-50%) translateY(8px); }
        }
        .test-card:hover {
          background: rgba(14,16,24,0.48) !important;
          border-color: rgba(200,212,224,0.22) !important;
          box-shadow: inset 0 1px 0 rgba(255,255,255,0.09), 0 8px 40px rgba(0,0,0,0.28) !important;
        }
        .card-accent-bar { height: 0 !important; }
        .test-card:hover .card-accent-bar { height: 100% !important; }
        .feature-cell:hover {
          background: rgba(14,14,22,0.36) !important;
        }
      `}</style>
    </div>
  )
}