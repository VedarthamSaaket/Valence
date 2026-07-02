import { useState } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import api from '../utils/api'
import Galaxy from '../components/Galaxy'

const METAL = 'linear-gradient(135deg,#7a8a9a 0%,#c4d4e2 10%,#eaf4fa 22%,#ffffff 32%,#deeaf4 42%,#aabece 52%,#e6f0f8 64%,#fafcfe 74%,#c4d4e2 84%,#dceaf4 100%)'

const S = {
  fontDisplay: "'Cormorant Garamond', Georgia, serif",
  fontSC: "'Cinzel', serif",
  fontBody: "'Playfair Display', Georgia, serif",
  textPrim: '#F4F7FA',
  textSec: 'rgba(244,247,250,0.56)',
  textMuted: 'rgba(244,247,250,0.30)',
  iris: '#D8E8F4',
  irisDim: '#8A9EAE',
  border: 'rgba(200,214,230,0.15)',
  frost: 'rgba(200,214,230,0.07)',
  frostBorder: 'rgba(215,228,242,0.20)',
}

export default function Auth() {
  const [params] = useSearchParams()
  const [mode, setMode] = useState(params.get('mode') === 'register' ? 'register' : 'login')
  const [form, setForm] = useState({ username: '', email: '', password: '' })
  const [showPassword, setShowPassword] = useState(false)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const { login } = useAuth()
  const navigate = useNavigate()

  const set = (k, v) => setForm(f => ({ ...f, [k]: v }))

  const submit = async () => {
    setError('')
    if (mode === 'register') {
      if (!form.username || !form.email || !form.password) return setError('All fields required')
      if (form.password.length < 8) return setError('Password must be at least 8 characters')
    } else {
      if (!form.email || !form.password) return setError('Email or username and password required')
    }
    setLoading(true)
    try {
      const endpoint = mode === 'register' ? '/auth/register' : '/auth/login'
      const payload = mode === 'register'
        ? { username: form.username, email: form.email, password: form.password }
        : { identifier: form.email, password: form.password }
      const res = await api.post(endpoint, payload)
      login(res.data.user, res.data.token)
      navigate('/dashboard')
    } catch (e) {
      setError(e.response?.data?.detail || 'Something went wrong')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div style={{
      minHeight: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center',
      padding: '100px 24px 40px', position: 'relative',
    }}>
      {/* Galaxy background, identical to the landing page */}
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

      <div className="animate-scale-in" style={{ width: '100%', maxWidth: 460, position: 'relative', zIndex: 1 }}>
        <div style={{
          padding: '52px 48px',
          background: S.frost,
          backdropFilter: 'blur(36px) saturate(1.6)',
          WebkitBackdropFilter: 'blur(36px) saturate(1.6)',
          border: `1px solid ${S.frostBorder}`,
          boxShadow: 'inset 0 1px 0 rgba(255,255,255,0.07), 0 32px 80px rgba(0,0,0,0.42)',
        }}>
          <div style={{ textAlign: 'center', marginBottom: 44 }}>
            <div style={{
              width: 48, height: 48, border: '1px solid rgba(215,232,244,0.38)', borderRadius: '50%',
              margin: '0 auto 22px',
              display: 'flex', alignItems: 'center', justifyContent: 'center',
            }}>
              <svg viewBox="0 0 14 14" fill="none" style={{ width: 14, height: 14 }}>
                <circle cx="7" cy="7" r="3" stroke="#D8E8F4" strokeWidth="1" />
                <circle cx="7" cy="7" r="6" stroke="#D8E8F4" strokeWidth="0.5" opacity="0.5" />
              </svg>
            </div>
            <h1 style={{
              fontFamily: S.fontDisplay, fontSize: 34, fontWeight: 300, marginBottom: 10,
              letterSpacing: '-0.01em',
              background: METAL, WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent',
              backgroundClip: 'text', backgroundSize: '200% 200%',
              animation: 'metal-sweep 8s ease-in-out infinite',
            }}>
              {mode === 'login' ? 'Welcome back' : 'Begin your journey'}
            </h1>
            <p style={{ fontFamily: S.fontSC, fontSize: 10, letterSpacing: '0.18em', color: S.textSec, textTransform: 'uppercase' }}>
              {mode === 'login' ? 'Sign in to continue to Valence' : 'Create your account to start'}
            </p>
          </div>

          <div style={{
            display: 'flex',
            background: 'rgba(215,228,242,0.04)',
            padding: 3, marginBottom: 36,
            border: '1px solid rgba(215,228,242,0.10)',
          }}>
            {['login', 'register'].map(m => (
              <button key={m} onClick={() => { setMode(m); setError('') }} style={{
                flex: 1, padding: '10px 0', border: 'none', cursor: 'pointer',
                fontFamily: S.fontSC, fontWeight: 600, fontSize: 9, letterSpacing: '0.20em',
                textTransform: 'uppercase', transition: 'all 220ms',
                backgroundColor: 'transparent',
                backgroundImage: mode === m
                  ? 'linear-gradient(135deg,#8090a2 0%,#c8d8e6 20%,#eef4fa 40%,#deeaf4 60%,#f4f8fc 80%,#baccda 100%)'
                  : 'none',
                backgroundSize: '200% 200%',
                animation: mode === m ? 'metal-sweep 5s ease-in-out infinite' : 'none',
                color: mode === m ? '#06060a' : S.textMuted,
              }}>
                {m === 'login' ? 'Sign In' : 'Sign Up'}
              </button>
            ))}
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: 18 }}>
            {mode === 'register' && (
              <div>
                <label style={{ display: 'block', fontFamily: S.fontSC, fontSize: 8, letterSpacing: '0.20em', color: S.irisDim, marginBottom: 9, textTransform: 'uppercase' }}>Username</label>
                <input className="input" style={{ fontFamily: S.fontSC, fontSize: 12, letterSpacing: '0.08em' }} placeholder="your_username" value={form.username}
                  onChange={e => set('username', e.target.value)}
                  onKeyDown={e => e.key === 'Enter' && submit()} />
              </div>
            )}
            <div>
              <label style={{ display: 'block', fontFamily: S.fontSC, fontSize: 8, letterSpacing: '0.20em', color: S.irisDim, marginBottom: 9, textTransform: 'uppercase' }}>
                {mode === 'login' ? 'Email or Username' : 'Email'}
              </label>
              <input className="input" style={{ fontFamily: S.fontSC, fontSize: 12, letterSpacing: '0.08em' }} type={mode === 'register' ? 'email' : 'text'}
                placeholder={mode === 'login' ? 'email or username' : 'you@example.com'}
                value={form.email} onChange={e => set('email', e.target.value)}
                onKeyDown={e => e.key === 'Enter' && submit()} />
            </div>
            <div>
              <label style={{ display: 'block', fontFamily: S.fontSC, fontSize: 8, letterSpacing: '0.20em', color: S.irisDim, marginBottom: 9, textTransform: 'uppercase' }}>Password</label>
              <div style={{ position: 'relative' }}>
                <input className="input" style={{ fontFamily: S.fontSC, fontSize: 12, letterSpacing: '0.08em' }} type={showPassword ? 'text' : 'password'}
                  placeholder={mode === 'register' ? 'min. 8 characters' : '••••••••'}
                  value={form.password} onChange={e => set('password', e.target.value)}
                  style={{ paddingRight: 44 }}
                  onKeyDown={e => e.key === 'Enter' && submit()} />
                <button onClick={() => setShowPassword(s => !s)} style={{
                  position: 'absolute', right: 14, top: '50%', transform: 'translateY(-50%)',
                  background: 'none', border: 'none', cursor: 'pointer', color: S.textMuted,
                  fontSize: 14, padding: 4, lineHeight: 1,
                }}>
                  {showPassword ? '○' : '◎'}
                </button>
              </div>
            </div>
          </div>

          {error && (
            <div style={{
              marginTop: 20, padding: '12px 16px',
              background: 'rgba(200,180,180,0.08)', border: '1px solid rgba(200,150,150,0.18)',
              color: 'rgba(220,180,180,0.88)',
              fontFamily: S.fontBody, fontStyle: 'italic', fontSize: 15,
            }}>{error}</div>
          )}

          <button onClick={submit} disabled={loading} className="btn btn-primary" style={{
            width: '100%', justifyContent: 'center', marginTop: 30, height: 52, fontSize: 10,
          }}>
            {loading
              ? <div className="spinner" style={{ width: 18, height: 18 }} />
              : (mode === 'login' ? 'Sign In' : 'Create Account')}
          </button>

          <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginTop: 30 }}>
            <div style={{ flex: 1, height: 1, background: S.border }} />
            <span style={{ fontFamily: S.fontSC, fontSize: 8, letterSpacing: '0.18em', color: S.textMuted }}>
              {mode === 'login' ? 'No account?' : 'Have an account?'}
            </span>
            <div style={{ flex: 1, height: 1, background: S.border }} />
          </div>
          <button onClick={() => { setMode(mode === 'login' ? 'register' : 'login'); setError('') }}
            className="btn btn-secondary" style={{ width: '100%', justifyContent: 'center', marginTop: 12 }}>
            {mode === 'login' ? 'Create Account' : 'Sign In'}
          </button>
        </div>
      </div>

      <style>{`
        @keyframes metal-sweep {
          0%,100% { background-position: 0% 50%; }
          50% { background-position: 100% 50%; }
        }
      `}</style>
    </div>
  )
}