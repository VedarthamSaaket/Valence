import { useState, useEffect } from 'react'
import { Link, useLocation, useNavigate } from 'react-router-dom'
import { useAuth } from '../../context/AuthContext'

const METAL = 'linear-gradient(135deg,#7a8a9a 0%,#c4d4e2 10%,#eaf4fa 22%,#ffffff 32%,#deeaf4 42%,#aabece 52%,#e6f0f8 64%,#fafcfe 74%,#c4d4e2 84%,#dceaf4 100%)'

export default function Navbar() {
  const { user, logout } = useAuth()
  const location = useLocation()
  const navigate = useNavigate()
  const [scrolled, setScrolled] = useState(false)

  useEffect(() => {
    const onScroll = () => setScrolled(window.scrollY > 20)
    window.addEventListener('scroll', onScroll)
    return () => window.removeEventListener('scroll', onScroll)
  }, [])

  const handleLogout = async () => {
    await logout()
    navigate('/')
  }

  const iris = '#D8E8F4'
  const textSec = 'rgba(244,247,250,0.54)'
  const textMuted = 'rgba(244,247,250,0.30)'
  const textPrim = '#F4F7FA'
  const border = 'rgba(200,214,230,0.15)'
  const fontSC = "'Cormorant SC', serif"

  return (
    <nav style={{
      position: 'fixed', top: 0, left: 0, right: 0, zIndex: 100,
      height: 64,
      display: 'grid',
      gridTemplateColumns: '1fr auto 1fr',
      alignItems: 'center',
      padding: '0 40px',
      borderBottom: `1px solid ${border}`,
      background: scrolled ? 'rgba(4,4,6,0.92)' : 'rgba(4,4,6,0.76)',
      backdropFilter: 'blur(28px)',
      WebkitBackdropFilter: 'blur(28px)',
      transition: 'background 400ms cubic-bezier(0.4,0,0.2,1)',
    }}>

      {/* Left slot, empty or future use */}
      <div />

      {/* Center, Logo */}
      <Link to="/" style={{ textDecoration: 'none', display: 'flex', alignItems: 'center', gap: 12, justifyContent: 'center' }}>
        <div style={{
          width: 28, height: 28, border: `1px solid ${iris}`, borderRadius: '50%',
          display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0,
        }}>
          <svg viewBox="0 0 14 14" fill="none" style={{ width: 14, height: 14 }}>
            <circle cx="7" cy="7" r="3" stroke="#D8E8F4" strokeWidth="1" />
            <circle cx="7" cy="7" r="6" stroke="#D8E8F4" strokeWidth="0.5" opacity="0.5" />
          </svg>
        </div>
        <span style={{
          fontFamily: fontSC,
          fontSize: 18, fontWeight: 700, letterSpacing: '0.14em',
          background: METAL,
          WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent',
          backgroundClip: 'text', backgroundSize: '200% 200%',
          animation: 'metal-sweep 7s ease-in-out infinite',
        }}>Valence</span>
      </Link>

      {/* Right slot, auth actions */}
      <div style={{ display: 'flex', alignItems: 'center', gap: 12, justifyContent: 'flex-end' }}>
        {user ? (
          <>
            <Link to="/dashboard"
              style={{
                fontFamily: fontSC,
                fontSize: 11, letterSpacing: '0.16em',
                color: location.pathname === '/dashboard' ? textPrim : textMuted,
                textDecoration: 'none', padding: '10px 16px',
                transition: 'color 200ms',
              }}
              onMouseEnter={e => e.target.style.color = textPrim}
              onMouseLeave={e => { if (location.pathname !== '/dashboard') e.target.style.color = textMuted }}
            >Dashboard</Link>
            <div
              onClick={handleLogout}
              title="Click to sign out"
              style={{
                width: 34, height: 34, borderRadius: '50%',
                background: 'rgba(215,232,244,0.10)',
                border: '1px solid rgba(215,232,244,0.28)',
                display: 'flex', alignItems: 'center', justifyContent: 'center',
                fontFamily: fontSC,
                fontSize: 12, fontWeight: 600, color: iris,
                cursor: 'pointer',
              }}
            >
              {user.username?.[0]?.toUpperCase()}
            </div>
          </>
        ) : (
          <>
            <Link to="/auth"
              style={{
                fontFamily: fontSC,
                fontSize: 11, letterSpacing: '0.16em',
                color: textMuted, textDecoration: 'none',
                padding: '10px 16px', transition: 'color 200ms',
              }}
              onMouseEnter={e => e.target.style.color = textPrim}
              onMouseLeave={e => e.target.style.color = textMuted}
            >Sign In</Link>
            <Link to="/auth?mode=register" className="btn btn-primary btn-sm">Begin</Link>
          </>
        )}
      </div>

      <style>{`
        @keyframes metal-sweep {
          0%,100% { background-position: 0% 50%; }
          50% { background-position: 100% 50%; }
        }
      `}</style>
    </nav>
  )
}