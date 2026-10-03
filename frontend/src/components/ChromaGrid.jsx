import { useRef, useEffect } from 'react'
import { gsap } from 'gsap'
import './ChromaGrid.css'


export default function ChromaGrid({
  items = [],
  className = '',
  radius = 320,
  damping = 0.45,
  fadeOut = 0.6,
  ease = 'power3.out',
  columns = 2,
  onSelect,
}) {
  const rootRef = useRef(null)
  const fadeRef = useRef(null)
  const setX = useRef(null)
  const setY = useRef(null)
  const pos = useRef({ x: 0, y: 0 })

  useEffect(() => {
    const el = rootRef.current
    if (!el) return
    setX.current = gsap.quickSetter(el, '--x', 'px')
    setY.current = gsap.quickSetter(el, '--y', 'px')
    const { width, height } = el.getBoundingClientRect()
    pos.current = { x: width / 2, y: height / 2 }
    setX.current(pos.current.x)
    setY.current(pos.current.y)
  }, [])

  const moveTo = (x, y) => {
    gsap.to(pos.current, {
      x, y,
      duration: damping,
      ease,
      onUpdate: () => {
        setX.current?.(pos.current.x)
        setY.current?.(pos.current.y)
      },
      overwrite: true,
    })
  }

  const handleMove = e => {
    const r = rootRef.current.getBoundingClientRect()
    moveTo(e.clientX - r.left, e.clientY - r.top)
    gsap.to(fadeRef.current, { opacity: 0, duration: 0.25, overwrite: true })
  }

  const handleLeave = () => {
    gsap.to(fadeRef.current, { opacity: 1, duration: fadeOut, overwrite: true })
  }

  const handleCardMove = e => {
    const card = e.currentTarget
    const rect = card.getBoundingClientRect()
    card.style.setProperty('--mouse-x', `${e.clientX - rect.left}px`)
    card.style.setProperty('--mouse-y', `${e.clientY - rect.top}px`)
  }

  return (
    <div
      ref={rootRef}
      className={`vl-chroma-grid ${className}`}
      style={{ '--r': `${radius}px`, '--cols': columns }}
      onPointerMove={handleMove}
      onPointerLeave={handleLeave}
    >
      {items.map((t, i) => (
        <article
          key={t.id}
          className="vl-chroma-card"
          onMouseMove={handleCardMove}
          onClick={() => onSelect?.(t.id)}
          style={{ '--card-gradient': t.metalGrad, animationDelay: `${i * 80}ms` }}
        >
          {}
          <div className="vl-card-shine" />

          {}
          <div className="vl-card-topbar" style={{ background: t.metalGrad }} />

          {}
          <div className="vl-card-num">{t.num}</div>

          {}
          <div className="vl-card-icon">{t.icon}</div>

          {}
          <div className="vl-card-tag">{t.tag}</div>

          {}
          <h3 className="vl-card-name">{t.name}</h3>

          {}
          <p className="vl-card-desc">{t.description}</p>

          {}
          <div className="vl-card-traits">
            {t.traits.slice(0, 4).map(tr => (
              <span key={tr} className="vl-trait-pill">{tr}</span>
            ))}
            {t.traits.length > 4 && (
              <span className="vl-trait-pill">+{t.traits.length - 4}</span>
            )}
          </div>

          {}
          <div className="vl-card-footer">
            <span className="vl-card-meta">{t.questions} questions · {t.duration}</span>
            <span className="vl-card-arrow">↗</span>
          </div>
        </article>
      ))}

      {}
      <div className="vl-chroma-overlay" />
      <div ref={fadeRef} className="vl-chroma-fade" />
    </div>
  )
}
