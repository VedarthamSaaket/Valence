import { useEffect, useRef, useState, useCallback } from 'react'

// ─── TOMB OF THE MASK aesthetic ───────────────────────────────────────────────
// Pure black. One screaming neon accent per level. Chunky 8×8 pixel glyphs.
// Snap flips (no smooth tweens , this is a 90s cabinet, not a css demo).
// Screen shake, pixel particle bursts, CRT scanlines, rising tide.

const PX = "'Press Start 2P', monospace"
const LEVELS = [
  { accent: '#FFE93B', dim: '#8a7c10', name: 'GOLD' },   // mask yellow
  { accent: '#FF2E97', dim: '#8a1050', name: 'MAGENTA' },
  { accent: '#00E5FF', dim: '#00707e', name: 'CYAN' },
  { accent: '#39FF14', dim: '#1a7e08', name: 'VENOM' },
  { accent: '#FF9F1C', dim: '#8a5208', name: 'EMBER' },
]
const RED = '#FF3131'

// 8×8 bitmaps. X = accent, D = dark accent (eye sockets, facets),
// W = white highlight, . = empty. Every glyph is symmetric where the
// real-world referent is symmetric (mask, skull, gem, star, coin, key) so
// they read cleanly at 5-6 px per cell. Redesigned to occupy the full 8×8
// grid and read at a glance from across the cabinet.
const GLYPHS = {
  alien: [                      // Space-Invaders style squid , iconic arcade
    '...XX...',
    '..XXXX..',
    '.XXXXXX.',
    'XX.XX.XX',                 // eye slits
    'XXXXXXXX',
    '..X..X..',
    '.X.XX.X.',
    'X.X..X.X',
  ],
  coin: [                       // stamped ring with a highlight bevel
    '.XXXXXX.',
    'XXWWWWXX',
    'XWXDDXWX',
    'XWXDDXWX',
    'XWXDDXWX',
    'XWXDDXWX',
    'XXWWWWXX',
    '.XXXXXX.',
  ],
  spike: [                      // upward triangle with base teeth
    '...XX...',
    '...XX...',
    '..XXXX..',
    '..XXXX..',
    '.XXXXXX.',
    '.XXXXXX.',
    'XXXXXXXX',
    'XX.XX.XX',
  ],
  key: [                        // original bow-tie / clover key silhouette
    '..XXXX..',
    '.XX..XX.',
    '.XX..XX.',
    '..XXXX..',
    '...XX...',
    '...XX.X.',
    '...XXXX.',
    '...XX.X.',
  ],
  star: [                       // classic 5-point star
    '...XX...',
    '...XX...',
    'XXXXXXXX',
    '.XXXXXX.',
    '..XXXX..',
    '.XXXXXX.',
    'XX....XX',
    'X......X',
  ],
  gem: [                        // faceted diamond with twin highlight pixels
    '..XXXX..',
    '.XWXXWX.',
    'XXXXXXXX',
    'XXXXXXXX',
    '.XXXXXX.',
    '..XXXX..',
    '...XX...',
    '........',
  ],
  skull: [                      // eye sockets + nasal + tooth row
    '.XXXXXX.',
    'XXXXXXXX',
    'XDDXXDDX',                 // eye sockets
    'XDDXXDDX',
    'XXX..XXX',                 // nasal cavity
    'XXXXXXXX',
    '.XXXXXX.',
    '.X.XX.X.',                 // teeth
  ],
  bolt: [                       // zig-zag lightning bolt
    '....XXX.',
    '...XXX..',
    '..XXX...',
    '.XXXXXX.',
    '..XXXX..',
    '...XXX..',
    '..XXX...',
    '.XXX....',
  ],
}
const GLYPH_KEYS = Object.keys(GLYPHS)

function PixelGlyph({ glyph, accent, dim, size = 44 }) {
  const ref = useRef()
  useEffect(() => {
    const c = ref.current
    if (!c) return
    const ctx = c.getContext('2d')
    ctx.clearRect(0, 0, 8, 8)
    const rows = GLYPHS[glyph]
    for (let y = 0; y < 8; y++) {
      for (let x = 0; x < 8; x++) {
        const ch = rows[y][x]
        if (ch === '.') continue
        ctx.fillStyle = ch === 'W' ? '#FFFFFF' : ch === 'D' ? '#050505' : accent
        ctx.fillRect(x, y, 1, 1)
      }
    }
  }, [glyph, accent, dim])
  return (
    <canvas ref={ref} width={8} height={8}
      style={{ width: size, height: size, imageRendering: 'pixelated', display: 'block' }} />
  )
}

// Retro square-wave beeps via WebAudio. Created lazily on first user gesture.
function useBeeper() {
  const ctxRef = useRef(null)
  const mutedRef = useRef(false)
  const beep = useCallback((freq, dur = 0.07, vol = 0.04) => {
    if (mutedRef.current) return
    try {
      if (!ctxRef.current) ctxRef.current = new (window.AudioContext || window.webkitAudioContext)()
      const ctx = ctxRef.current
      if (ctx.state === 'suspended') ctx.resume()
      const osc = ctx.createOscillator()
      const gain = ctx.createGain()
      osc.type = 'square'
      osc.frequency.value = freq
      gain.gain.setValueAtTime(vol, ctx.currentTime)
      gain.gain.exponentialRampToValueAtTime(0.0001, ctx.currentTime + dur)
      osc.connect(gain).connect(ctx.destination)
      osc.start()
      osc.stop(ctx.currentTime + dur)
    } catch (_) { /* audio unavailable , silent cabinet */ }
  }, [])
  return { beep, mutedRef }
}

function shuffle(arr) {
  const a = [...arr]
  for (let i = a.length - 1; i > 0; i--) {
    const j = Math.floor(Math.random() * (i + 1))
    ;[a[i], a[j]] = [a[j], a[i]]
  }
  return a
}

function makeDeck() {
  return shuffle(GLYPH_KEYS.flatMap(g => [
    { id: `${g}-a`, glyph: g, up: false, matched: false },
    { id: `${g}-b`, glyph: g, up: false, matched: false },
  ]))
}

let PARTICLE_ID = 0

// The tide-inside-cabinet used to double as the enrichment progress bar. The
// bar now lives outside the cabinet (see DeepDive.jsx), so the board stays
// visually clean regardless of enrichment state.
export default function TombMemoryGame() {
  const [deck, setDeck] = useState(makeDeck)
  const [picks, setPicks] = useState([])       // indices currently face-up (unmatched)
  const [lock, setLock] = useState(false)
  const [score, setScore] = useState(0)
  const [combo, setCombo] = useState(0)
  const [level, setLevel] = useState(0)
  const [shakeKey, setShakeKey] = useState(0)
  const [flashRed, setFlashRed] = useState([])  // indices blinking red
  const [particles, setParticles] = useState([])
  const [muted, setMuted] = useState(false)
  const [levelFlash, setLevelFlash] = useState(false)
  // Attract-mode boot splash sits over the cabinet for a beat before the
  // real board interaction begins , standard 90s arcade cadence.
  const [booted, setBooted] = useState(false)
  const boardRef = useRef()
  const { beep, mutedRef } = useBeeper()
  mutedRef.current = muted

  useEffect(() => {
    const t = setTimeout(() => setBooted(true), 1600)
    return () => clearTimeout(t)
  }, [])

  const L = LEVELS[level % LEVELS.length]

  const burst = useCallback((idx, color) => {
    const board = boardRef.current
    if (!board) return
    const tile = board.children[idx]
    if (!tile) return
    const bR = board.getBoundingClientRect()
    const tR = tile.getBoundingClientRect()
    const cx = tR.left - bR.left + tR.width / 2
    const cy = tR.top - bR.top + tR.height / 2
    const burstParts = Array.from({ length: 10 }, () => ({
      id: ++PARTICLE_ID,
      x: cx, y: cy,
      dx: (Math.random() - 0.5) * 120,
      dy: (Math.random() - 0.5) * 120,
      color,
      size: Math.random() > 0.5 ? 6 : 4,
    }))
    setParticles(p => [...p, ...burstParts])
    setTimeout(() => {
      setParticles(p => p.filter(pp => !burstParts.some(b => b.id === pp.id)))
    }, 550)
  }, [])

  const flip = (idx) => {
    if (lock) return
    const card = deck[idx]
    if (card.up || card.matched) return
    beep(520 + Math.random() * 60, 0.05)

    const next = deck.map((c, i) => i === idx ? { ...c, up: true } : c)
    setDeck(next)
    const nowPicks = [...picks, idx]

    if (nowPicks.length < 2) { setPicks(nowPicks); return }

    const [a, b] = nowPicks
    setPicks([])
    if (next[a].glyph === next[b].glyph) {
      // MATCH , flash, burst, shake, combo score
      const newCombo = combo + 1
      setCombo(newCombo)
      setScore(s => s + 100 * newCombo)
      setShakeKey(k => k + 1)
      beep(880, 0.09); setTimeout(() => beep(1320, 0.11), 70)
      setDeck(d => d.map((c, i) => (i === a || i === b) ? { ...c, matched: true } : c))
      burst(a, L.accent); burst(b, L.accent)

      // board cleared → next level, new color, deck reshuffle
      const remaining = next.filter((c, i) => !(i === a || i === b) && !c.matched)
      if (remaining.length === 0) {
        setTimeout(() => {
          setLevel(l => l + 1)
          setDeck(makeDeck())
          setLevelFlash(true)
          beep(660, 0.08); setTimeout(() => beep(880, 0.08), 90); setTimeout(() => beep(1100, 0.14), 180)
          setTimeout(() => setLevelFlash(false), 900)
        }, 450)
      }
    } else {
      // MISMATCH , red blink, combo dies
      setLock(true)
      setCombo(0)
      setFlashRed([a, b])
      beep(180, 0.12, 0.05)
      setTimeout(() => {
        setFlashRed([])
        setDeck(d => d.map((c, i) => (i === a || i === b) ? { ...c, up: false } : c))
        setLock(false)
      }, 650)
    }
  }

  return (
    <div style={{ position: 'relative', width: '100%', maxWidth: 380, margin: '0 auto', userSelect: 'none' }}>
      {/* Cabinet frame */}
      <div key={shakeKey} style={{
        position: 'relative', background: '#000',
        border: `3px solid ${L.accent}`,
        boxShadow: `0 0 18px ${L.accent}55, inset 0 0 14px ${L.accent}22`,
        padding: '14px 12px 16px', overflow: 'hidden',
        animation: shakeKey ? 'totm-shake 0.28s steps(2)' : 'none',
        imageRendering: 'pixelated',
      }}>

        {/* HUD */}
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 12, position: 'relative', zIndex: 2, gap: 8, paddingRight: 44 }}>
          <div style={{ fontFamily: PX, fontSize: 8, color: L.accent, textShadow: `0 0 5px ${L.accent}`, lineHeight: 1.9 }}>
            SCORE<br /><span style={{ color: '#fff', fontSize: 11 }}>{String(score).padStart(6, '0')}</span>
          </div>
          <div style={{ fontFamily: PX, fontSize: 8, color: L.accent, textAlign: 'center', textShadow: `0 0 5px ${L.accent}`, lineHeight: 1.9 }}>
            LVL {level + 1}<br />
            <span style={{ color: '#fff', fontSize: 7 }}>{L.name}</span>
          </div>
          <div style={{ fontFamily: PX, fontSize: 8, color: combo > 1 ? '#fff' : L.dim, textAlign: 'right', textShadow: combo > 1 ? `0 0 7px ${L.accent}` : 'none', lineHeight: 1.9 }}>
            COMBO<br /><span style={{ fontSize: 11, color: combo > 1 ? L.accent : L.dim }}>x{Math.max(combo, 1)}</span>
          </div>
        </div>

        {/* Board */}
        <div ref={boardRef} style={{
          display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 6,
          position: 'relative', zIndex: 2,
        }}>
          {deck.map((card, i) => {
            const red = flashRed.includes(i)
            const faceUp = card.up || card.matched
            // Stagger the face-down bob so the board looks alive rather
            // than a wall of static "?" tiles , 4 phases across the grid.
            // Embed the delay INTO the animation shorthand rather than
            // setting animationDelay separately: mixing the two triggers
            // React's "shorthand + longhand for the same property" warning
            // whenever the shorthand flips to 'none' between renders.
            const bobDelay = (i % 4) * 0.15
            return (
              <button key={card.id} onClick={() => flip(i)}
                style={{
                  aspectRatio: '1', padding: 0, cursor: (card.matched || lock) ? 'default' : 'pointer',
                  background: card.matched ? '#000' : faceUp ? '#0a0a0a' : '#000',
                  border: `2px solid ${red ? RED : card.matched ? L.accent : faceUp ? L.accent : L.dim}`,
                  boxShadow: red ? `0 0 12px ${RED}` : card.matched ? `inset 0 0 8px ${L.accent}55` : faceUp ? `0 0 10px ${L.accent}88` : 'none',
                  display: 'flex', alignItems: 'center', justifyContent: 'center',
                  opacity: card.matched ? 0.75 : 1,
                  transition: 'none', // snap. no tween. 1996 feel.
                  outline: 'none',
                  position: 'relative',
                  animation: (!faceUp && booted)
                    ? `totm-bob 1.4s steps(2) ${bobDelay}s infinite`
                    : 'none',
                }}>
                {faceUp ? (
                  <PixelGlyph glyph={card.glyph} accent={red ? RED : L.accent} dim={L.dim} size={38} />
                ) : (
                  <span style={{
                    fontFamily: PX, fontSize: 13, color: L.dim,
                    animation: booted
                      ? `totm-blink 1.1s steps(1) ${bobDelay}s infinite`
                      : 'none',
                  }}>?</span>
                )}
              </button>
            )
          })}

          {/* pixel particles */}
          {particles.map(p => (
            <span key={p.id} style={{
              position: 'absolute', left: p.x, top: p.y, width: p.size, height: p.size,
              background: p.color, pointerEvents: 'none', zIndex: 5,
              '--dx': `${p.dx}px`, '--dy': `${p.dy}px`,
              animation: 'totm-part 0.5s steps(5) forwards',
            }} />
          ))}
        </div>

        {/* level-clear flash */}
        {levelFlash && (
          <div style={{
            position: 'absolute', inset: 0, zIndex: 6, display: 'flex', alignItems: 'center', justifyContent: 'center',
            background: 'rgba(0,0,0,0.82)',
          }}>
            <span style={{ fontFamily: PX, fontSize: 14, color: L.accent, textShadow: `0 0 10px ${L.accent}`, animation: 'totm-blink 0.25s steps(1) infinite' }}>
              LEVEL UP!
            </span>
          </div>
        )}

        {/* attract-mode boot splash , overlays the cabinet for ~1.6 s */}
        {!booted && (
          <div style={{
            position: 'absolute', inset: 0, zIndex: 8, display: 'flex',
            flexDirection: 'column', alignItems: 'center', justifyContent: 'center',
            gap: 12, background: '#000',
          }}>
            <span style={{
              fontFamily: PX, fontSize: 12, color: L.accent,
              textShadow: `0 0 8px ${L.accent}`, letterSpacing: 1,
            }}>
              READY
            </span>
            <span style={{
              fontFamily: PX, fontSize: 8, color: '#fff',
              animation: 'totm-blink 0.35s steps(1) infinite',
            }}>
              INSERT COIN
            </span>
          </div>
        )}



        {/* CRT scanlines + vignette */}
        <div style={{
          position: 'absolute', inset: 0, zIndex: 7, pointerEvents: 'none',
          background: 'repeating-linear-gradient(0deg, rgba(0,0,0,0.28) 0 1px, transparent 1px 3px)',
        }} />
        <div style={{
          position: 'absolute', inset: 0, zIndex: 7, pointerEvents: 'none',
          background: 'radial-gradient(ellipse at center, transparent 55%, rgba(0,0,0,0.55) 100%)',
        }} />
      </div>

      {/* sound toggle, sits inside the top-right of the cabinet without
          overlapping the HUD thanks to the paddingRight reserved above */}
      <button onClick={() => setMuted(m => !m)} style={{
        position: 'absolute', top: 8, right: 8, zIndex: 10,
        fontFamily: PX, fontSize: 6, color: muted ? '#555' : L.accent,
        background: '#000', border: `2px solid ${muted ? '#333' : L.dim}`,
        padding: '4px 6px', cursor: 'pointer',
      }}>
        SND {muted ? 'OFF' : 'ON'}
      </button>

      <style>{`
        @keyframes totm-shake {
          0% { transform: translate(0,0); }
          25% { transform: translate(-4px,2px); }
          50% { transform: translate(4px,-3px); }
          75% { transform: translate(-3px,-2px); }
          100% { transform: translate(0,0); }
        }
        @keyframes totm-part {
          to { transform: translate(var(--dx), var(--dy)); opacity: 0; }
        }
        @keyframes totm-blink {
          0%, 49% { opacity: 1; }
          50%, 100% { opacity: 0; }
        }
        @keyframes totm-wave {
          0%, 49% { transform: translateX(0); }
          50%, 100% { transform: translateX(8px); }
        }
        @keyframes totm-bob {
          0%, 49% { transform: translateY(0); }
          50%, 100% { transform: translateY(-2px); }
        }
      `}</style>
    </div>
  )
}
