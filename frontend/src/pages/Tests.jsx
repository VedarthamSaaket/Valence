import { useNavigate } from 'react-router-dom'
import bgImage from '../assets/Image60.jpeg'

const FONT_SC = "'Cinzel', serif"
const FONT_DISPLAY = "'Cormorant Garamond', Georgia, serif"
const METAL = 'linear-gradient(135deg,#7a8a9a 0%,#c4d4e2 10%,#eaf4fa 22%,#ffffff 32%,#deeaf4 42%,#aabece 52%,#e6f0f8 64%,#fafcfe 74%,#c4d4e2 84%,#dceaf4 100%)'
const METAL2 = 'linear-gradient(135deg,#9eb0c2 0%,#d8eaf6 18%,#f6fafe 36%,#deeef8 54%,#fafcfe 72%,#c4d8ea 100%)'

const SILVER_ICON_COLORS = [
  '#C8D8E8', '#A8BED2', '#D8E8F4', '#B0C8DC',
  '#E0EAF4', '#98B0C8', '#C4D4E4', '#D0DCE8',
  '#B8CCDC', '#A0B8CC', '#CCE0F0', '#B4CAD8',
]

export const CATEGORIES = [
  {
    id: 'personality', label: 'Who You Are',
    sublabel: 'Identity, character and the shadow self', roman: 'I',
    tests: [
      { id: 'hexaco',    name: 'Six-Trait Personality',     subtitle: 'HEXACO Six-Factor Personality',     tag: 'Foundation',     icon: '◈', questions: 240, duration: '30 to 40 min', description: 'Six broad personality factors plus Honesty-Humility, the dimension the classic Big Five misses.',           traits: ['Honesty-Humility', 'Emotionality', 'Extraversion', 'Agreeableness', 'Conscientiousness', 'Openness'] },
      { id: 'darktriad', name: 'Dark Traits',       subtitle: 'Short Dark Triad',                   tag: 'Shadow Self',    icon: '⬡', questions: 27,  duration: '5 to 8 min',   description: 'Three darker traits most people prefer not to measure.',                                                  traits: ['Machiavellianism', 'Narcissism', 'Psychopathy'] },
      { id: 'fti',       name: 'Temperament Type',     subtitle: 'Fisher Temperament Inventory',       tag: 'Temperament',    icon: '◉', questions: 56,  duration: '8 to 12 min',  description: 'Four neurotransmitter-linked temperaments by Helen Fisher.',                                              traits: ['Explorer', 'Builder', 'Director', 'Negotiator'] },
      { id: 'npi',       name: 'How You See Yourself',      subtitle: 'Narcissistic Personality Inventory', tag: 'Self-View',      icon: '◈', questions: 40,  duration: '6 to 10 min',  description: 'Seven facets of how you see yourself in relation to others.',                                             traits: ['Authority', 'Self-Sufficiency', 'Superiority', 'Exhibitionism', 'Exploitativeness', 'Vanity', 'Entitlement'] },
      { id: 'ambi',      name: 'Broad Personality Scan', subtitle: 'Broad Personality Inventory',        tag: 'Broad Scan',     icon: '⬟', questions: 181, duration: '35 to 50 min', description: 'The widest personality scan in this collection, covering nearly two hundred personality scales.',         traits: ['Affect Regulation', 'Social Drive', 'Conscientiousness', 'Openness', 'Agreeableness', 'Energy Drive', 'Identity Coherence'] },
    ],
  },
  {
    id: 'mind', label: 'How You Think',
    sublabel: 'Cognition, perception and inner processing', roman: 'II',
    tests: [
      { id: 'hsq',       name: 'Humor Style',           subtitle: 'Humor Styles Questionnaire',         tag: 'Humor',          icon: '◇', questions: 32,  duration: '5 to 8 min',   description: 'Four flavors of humor, two warm and two corrosive.',                                                      traits: ['Affiliative', 'Self-Enhancing', 'Aggressive', 'Self-Defeating'] },
      { id: 'kims',      name: 'Mindfulness Skills',     subtitle: 'Mindfulness Skills Inventory',       tag: 'Mindfulness',    icon: '◈', questions: 39,  duration: '8 to 12 min',  description: 'Four skills that make up day-to-day mindfulness.',                                                        traits: ['Observing', 'Describing', 'Acting with Awareness', 'Accepting without Judgment'] },
      { id: 'gcbs',      name: 'Conspiracy Beliefs',   subtitle: 'Generic Conspiracist Beliefs',       tag: 'Worldview',      icon: '⬟', questions: 15,  duration: '4 to 6 min',   description: 'How skeptical you are about official accounts and powerful actors behind big events.',                    traits: ['Government Malfeasance', 'Malevolent Global', 'Extraterrestrial Coverup', 'Personal Wellbeing Threats', 'Control of Information'] },
    ],
  },
  {
    id: 'life', label: 'How You Live',
    sublabel: 'Work, relationships, values and needs', roman: 'III',
    tests: [
      { id: 'riasec',     name: 'Career Type',         subtitle: 'Holland Code RIASEC',                tag: 'Career',         icon: '⬡', questions: 48,  duration: '10 to 15 min', description: 'Six career personality types that explain what environments bring out your best work.',                  traits: ['Realistic', 'Investigative', 'Artistic', 'Social', 'Enterprising', 'Conventional'] },
      { id: 'attachment', name: 'Attachment Style',    subtitle: 'Attachment Patterns',                tag: 'Relationships',  icon: '◉', questions: 36,  duration: '8 to 12 min',  description: 'Your earliest bonds shaped how you attach to others today.',                                              traits: ['Secure', 'Anxious', 'Avoidant'] },
    ],
  },
  {
    id: 'wellbeing', label: 'How You Feel',
    sublabel: 'Current emotional state and wellbeing', roman: 'IV',
    tests: [
      { id: 'dass', name: 'Mood and Stress', subtitle: 'Mood and Stress Levels',     tag: 'Mood and Stress', icon: '◎', questions: 42, duration: '8 to 12 min', description: 'A snapshot of where you are right now across three currents of emotional experience. Not a diagnosis.', traits: ['Depression', 'Anxiety', 'Stress'] },
    ],
  },
]

export const ALL_TESTS = CATEGORIES.flatMap(cat => cat.tests)

const ALL_TESTS_FLAT = CATEGORIES.flatMap(cat =>
  cat.tests.map((t, i) => ({ ...t, globalIdx: cat.tests.indexOf(t) + CATEGORIES.slice(0, CATEGORIES.indexOf(cat)).reduce((a, c) => a + c.tests.length, 0) }))
)

export default function Tests() {
  const navigate = useNavigate()

  return (
    <div style={{ minHeight: '100vh', paddingTop: 64, paddingBottom: 100, position: 'relative', isolation: 'isolate' }}>

      <div style={{
        position: 'fixed', inset: 0, zIndex: 0, pointerEvents: 'none',
      }}>
        <img
          src={bgImage}
          alt=""
          style={{
            position: 'absolute',
            top: '50%',
            left: '50%',
            transform: 'translate(-50%, -50%) rotate(-90deg) scale(1.5)',
            width: '100vh',
            height: '100vw',
            objectFit: 'cover',
            filter: 'brightness(0.85) contrast(1.05)',
          }}
        />
        <div style={{
          position: 'absolute', inset: 0,
          background: 'radial-gradient(ellipse 80% 70% at 50% 50%, rgba(4,4,6,0.55) 0%, rgba(4,4,6,0.82) 70%, rgba(4,4,6,0.96) 100%)',
        }} />
        <div style={{
          position: 'absolute', inset: 0,
          background: 'linear-gradient(to bottom, rgba(4,4,6,0.0) 0%, rgba(4,4,6,0.0) 60%, rgba(4,4,6,0.9) 100%)',
        }} />
      </div>

      <div style={{ position: 'relative', zIndex: 1, maxWidth: 1120, margin: '0 auto', padding: '60px 40px 0' }}>

        <div style={{ marginBottom: 80 }}>
          <div style={{
            display: 'inline-block',
            fontFamily: FONT_SC, fontSize: 9, letterSpacing: '0.24em',
            padding: '5px 14px',
            border: '1px solid rgba(215,232,248,0.18)',
            borderRadius: 2,
            color: 'rgba(215,232,248,0.44)',
            marginBottom: 32,
          }}>
            Assessments
          </div>
          <h1 style={{
            fontFamily: FONT_DISPLAY,
            fontSize: 'clamp(52px, 7vw, 96px)',
            fontWeight: 300,
            letterSpacing: '-0.02em',
            lineHeight: 0.95,
            margin: '0 0 28px',
            background: METAL,
            WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent',
            backgroundClip: 'text', backgroundSize: '200% 200%',
            animation: 'metal-sweep 8s ease-in-out infinite',
          }}>
            Eleven tests.<br />
            <em style={{
              fontStyle: 'italic', fontWeight: 300,
              background: METAL2,
              WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent',
              backgroundClip: 'text', backgroundSize: '200% 200%',
              animation: 'metal-sweep 5s ease-in-out infinite reverse',
            }}>One portrait.</em>
          </h1>
          <p style={{
            fontFamily: FONT_DISPLAY,
            fontStyle: 'italic',
            fontSize: 18,
            fontWeight: 300,
            color: 'rgba(232,240,250,0.80)',
            maxWidth: 480,
            lineHeight: 1.75,
            letterSpacing: '0.01em',
          }}>
            Each assessment reveals a different layer of who you are. Take them in any order. Complete all eleven for your master profile.
          </p>
        </div>

        {CATEGORIES.map((cat, ci) => {
          const prevCount = CATEGORIES.slice(0, ci).reduce((a, c) => a + c.tests.length, 0)
          return (
            <div key={cat.id} style={{ marginBottom: 88 }}>
              <div style={{
                display: 'flex', alignItems: 'flex-end', gap: 24,
                marginBottom: 36,
                paddingBottom: 22,
                borderBottom: '1px solid rgba(215,232,248,0.08)',
              }}>
                <span style={{
                  fontFamily: FONT_DISPLAY,
                  fontSize: 80,
                  fontWeight: 300,
                  lineHeight: 1,
                  color: 'rgba(215,232,248,0.04)',
                  flexShrink: 0,
                  letterSpacing: '-0.03em',
                  paddingBottom: 4,
                  userSelect: 'none',
                }}>{cat.roman}</span>
                <div style={{ paddingBottom: 4 }}>
                  <div style={{
                    fontFamily: FONT_DISPLAY,
                    fontSize: 'clamp(28px, 3.5vw, 40px)',
                    fontWeight: 400,
                    lineHeight: 1.1,
                    letterSpacing: '-0.015em',
                    background: METAL,
                    WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent',
                    backgroundClip: 'text', backgroundSize: '200% 200%',
                    animation: `metal-sweep ${7 + ci}s ease-in-out infinite`,
                    marginBottom: 5,
                  }}>
                    {cat.label}
                  </div>
                  <div style={{
                    fontFamily: FONT_DISPLAY,
                    fontStyle: 'italic',
                    fontSize: 14,
                    fontWeight: 300,
                    color: 'rgba(232,240,250,0.72)',
                    letterSpacing: '0.02em',
                  }}>
                    {cat.sublabel}
                  </div>
                </div>
              </div>

              <div style={{
                display: 'grid',
                gridTemplateColumns: 'repeat(2, 1fr)',
                gap: 1,
              }}>
                {cat.tests.map((test, ti) => (
                  <TestCard
                    key={test.id}
                    test={test}
                    globalNum={prevCount + ti + 1}
                    iconColor={SILVER_ICON_COLORS[prevCount + ti]}
                    delay={ti * 60}
                    onClick={() => navigate(`/tests/${test.id}`)}
                  />
                ))}
              </div>
            </div>
          )
        })}

        <div style={{
          padding: '22px 28px',
          border: '1px solid rgba(215,232,248,0.07)',
          background: 'rgba(4,4,6,0.38)',
          backdropFilter: 'blur(12px)',
          WebkitBackdropFilter: 'blur(12px)',
          marginTop: 8, marginBottom: 0,
        }}>
          <p style={{
            fontFamily: FONT_DISPLAY,
            fontStyle: 'italic',
            fontSize: 14,
            color: 'rgba(232,240,250,0.72)',
            lineHeight: 1.7,
          }}>
            Results are most meaningful with honest, reflective responses. All data is stored privately in your dashboard. Complete all eleven tests to unlock your unified master archetype.
          </p>
        </div>

      </div>

      <style>{`
        @keyframes metal-sweep {
          0%,100% { background-position: 0% 50%; }
          50%      { background-position: 100% 50%; }
        }
        .test-row-card:hover {
          background: rgba(215,232,248,0.04) !important;
          border-color: rgba(215,232,248,0.14) !important;
        }
        .test-row-card:hover .card-bar {
          height: 100% !important;
        }
        .test-row-card:hover .card-arrow {
          color: rgba(215,232,248,0.50) !important;
          transform: translate(2px, -2px) !important;
        }
        .test-row-card:hover .card-icon-box {
          border-color: rgba(215,232,248,0.22) !important;
          background: rgba(215,232,248,0.07) !important;
        }
      `}</style>
    </div>
  )
}

function TestCard({ test, globalNum, iconColor, delay, onClick }) {
  const numStr = String(globalNum).padStart(2, '0')
  return (
    <div
      className="test-row-card"
      onClick={onClick}
      style={{
        padding: '28px 32px',
        background: 'rgba(4,4,6,0.62)',
        backdropFilter: 'blur(14px)',
        WebkitBackdropFilter: 'blur(14px)',
        border: '1px solid rgba(215,232,248,0.16)',
        cursor: 'pointer',
        position: 'relative',
        overflow: 'hidden',
        transition: 'background 280ms ease, border-color 280ms ease',
        animationDelay: `${delay}ms`,
      }}
    >
      <div style={{
        position: 'absolute', top: 0, left: 0, width: 2,
        height: 0, background: METAL,
        transition: 'height 380ms cubic-bezier(.4,0,.2,1)',
      }} className="card-bar" />

      <div style={{ display: 'flex', gap: 20, alignItems: 'flex-start' }}>
        <div
          className="card-icon-box"
          style={{
            width: 44, height: 44, borderRadius: 2, flexShrink: 0,
            border: `1px solid rgba(215,232,248,0.12)`,
            background: `rgba(215,232,248,0.04)`,
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            fontSize: 18, color: iconColor,
            transition: 'border-color 280ms, background 280ms',
            position: 'relative',
          }}
        >
          {test.icon}
          <span style={{
            position: 'absolute',
            bottom: -16,
            left: '50%',
            transform: 'translateX(-50%)',
            fontFamily: "'Cinzel', serif",
            fontSize: 7,
            letterSpacing: '0.08em',
            color: 'rgba(215,232,248,0.18)',
            whiteSpace: 'nowrap',
          }}>{numStr}</span>
        </div>

        <div style={{ flex: 1, minWidth: 0 }}>
          <div style={{ display: 'flex', alignItems: 'baseline', gap: 10, marginBottom: 6, flexWrap: 'wrap' }}>
            <h3 style={{
              fontFamily: FONT_DISPLAY,
              fontSize: 22,
              fontWeight: 400,
              letterSpacing: '-0.01em',
              color: 'rgba(248,251,254,0.98)',
              lineHeight: 1.1,
            }}>
              {test.name}
            </h3>
            <span style={{
              fontFamily: FONT_SC,
              fontSize: 8,
              letterSpacing: '0.20em',
              color: 'rgba(215,232,248,0.62)',
            }}>{test.subtitle.toUpperCase()}</span>
          </div>
          <p style={{
            fontFamily: FONT_DISPLAY,
            fontStyle: 'italic',
            fontSize: 14,
            color: 'rgba(244,247,250,0.80)',
            lineHeight: 1.65,
            marginBottom: 12,
          }}>
            {test.description}
          </p>
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: 5, marginBottom: 10 }}>
            {test.traits.map(tr => (
              <span key={tr} style={{
                fontFamily: FONT_SC,
                fontSize: 7,
                letterSpacing: '0.16em',
                padding: '2px 8px',
                border: '1px solid rgba(215,232,248,0.22)',
                borderRadius: 2,
                color: 'rgba(215,232,248,0.72)',
                background: 'rgba(215,232,248,0.05)',
              }}>{tr}</span>
            ))}
          </div>
          <div style={{
            fontFamily: FONT_SC,
            fontSize: 8,
            letterSpacing: '0.18em',
            color: 'rgba(215,232,248,0.62)',
          }}>
            {test.questions} Questions, {test.duration}
          </div>
        </div>

        <div style={{
          color: 'rgba(215,232,248,0.18)',
          fontSize: 18,
          flexShrink: 0,
          transition: 'color 280ms, transform 280ms',
          paddingTop: 2,
        }} className="card-arrow">↗</div>
      </div>
    </div>
  )
}
