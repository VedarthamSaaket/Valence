import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import api from '../utils/api'
import bgImage from '../assets/Image60.jpeg'

const S = {
  fontSerif: "'Libre Baskerville', Baskerville, Georgia, serif",
  fontSC: "'Cinzel', serif",
  textPrim: '#F4F7FA',
  textSec: 'rgba(244,247,250,0.60)',
  textMuted: 'rgba(244,247,250,0.40)',
  irisDim: '#8A9EAE',
  frost: 'rgba(200,214,230,0.06)',
  frostBorder: 'rgba(215,228,242,0.18)',
}

export default function Acknowledgements() {
  const [groups, setGroups] = useState(null)

  useEffect(() => {
    api.get('/research/acknowledgements').then(res => setGroups(res.data)).catch(() => setGroups([]))
  }, [])

  return (
    <div className="page" style={{ minHeight: '100vh', position: 'relative', paddingBottom: 80 }}>
      <div style={{ position: 'fixed', inset: 0, zIndex: 0, pointerEvents: 'none', overflow: 'hidden' }}>
        <img src={bgImage} alt="" style={{ position: 'absolute', top: '50%', left: '50%', transform: 'translate(-50%, -50%) rotate(-90deg) scale(1.5)', width: '100vh', height: '100vw', objectFit: 'cover', filter: 'grayscale(100%) brightness(0.8) contrast(1.05)' }} />
        <div style={{ position: 'absolute', inset: 0, background: 'radial-gradient(ellipse 80% 70% at 50% 40%, rgba(4,4,6,0.60) 0%, rgba(4,4,6,0.85) 70%, rgba(4,4,6,0.97) 100%)' }} />
      </div>

      <div style={{ maxWidth: 820, margin: '0 auto', padding: '52px 32px 0', position: 'relative', zIndex: 1 }}>
        <div style={{ fontFamily: S.fontSC, fontSize: 8, letterSpacing: '0.26em', color: S.textMuted, marginBottom: 10 }}>ACKNOWLEDGEMENTS</div>
        <h1 style={{ fontFamily: S.fontSerif, fontStyle: 'italic', fontSize: 'clamp(28px,4vw,40px)', fontWeight: 400, color: S.textPrim, lineHeight: 1.15, marginBottom: 16 }}>
          With thanks to the researchers
        </h1>
        <p style={{ fontFamily: S.fontSerif, fontStyle: 'italic', fontSize: 14, color: S.textSec, lineHeight: 1.9, marginBottom: 12 }}>
          Valence exists because of the researchers named below. They designed these instruments, tested them with care, and published what they learned so that others could build on it. We thank each of them for their work.
        </p>
        <p style={{ fontFamily: S.fontSerif, fontStyle: 'italic', fontSize: 13, color: S.textMuted, lineHeight: 1.9, marginBottom: 28 }}>
          Our thanks are offered independently. The researchers named here were not involved in making Valence.
        </p>

        {groups === null && <div className="spinner" style={{ width: 32, height: 32 }} />}

        {(groups || []).map(group => (
          <section key={group.test_id} style={{ marginBottom: 3, background: S.frost, border: `1px solid ${S.frostBorder}`, padding: '22px 28px' }}>
            <div style={{ fontFamily: S.fontSC, fontSize: 9, letterSpacing: '0.20em', color: S.irisDim, textTransform: 'uppercase', marginBottom: 4 }}>{group.code}</div>
            <div style={{ fontFamily: S.fontSerif, fontStyle: 'italic', fontSize: 15, color: S.textPrim, marginBottom: 12 }}>{group.domain}</div>
            <ul style={{ listStyle: 'none', margin: 0, padding: 0 }}>
              {group.authors.map((names, i) => (
                <li key={i} style={{ fontFamily: S.fontSerif, fontStyle: 'italic', fontSize: 13, color: S.textSec, lineHeight: 1.9 }}>{names}</li>
              ))}
            </ul>
          </section>
        ))}

        <div style={{ marginTop: 3, display: 'flex', gap: 3 }}>
          <Link to="/" className="btn btn-secondary" style={{ flex: 1, justifyContent: 'center' }}>Home</Link>
          <Link to="/tests" className="btn btn-primary" style={{ flex: 1, justifyContent: 'center' }}>Assessments</Link>
        </div>
      </div>
    </div>
  )
}
