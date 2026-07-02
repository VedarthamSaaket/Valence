import { useEffect, useRef } from 'react'

export default function PersonalityMap({ coords = [], userX, userY, color = '#7B61FF' }) {
  const canvasRef = useRef()

  useEffect(() => {
    const canvas = canvasRef.current
    if (!canvas || !coords.length) return
    const ctx = canvas.getContext('2d')
    const W = canvas.width = canvas.offsetWidth * window.devicePixelRatio
    const H = canvas.height = canvas.offsetHeight * window.devicePixelRatio
    ctx.scale(window.devicePixelRatio, window.devicePixelRatio)
    const w = canvas.offsetWidth, h = canvas.offsetHeight

    const xs = coords.map(c => c[0])
    const ys = coords.map(c => c[1])
    const xMin = Math.min(...xs) - 1, xMax = Math.max(...xs) + 1
    const yMin = Math.min(...ys) - 1, yMax = Math.max(...ys) + 1

    const toX = v => ((v - xMin) / (xMax - xMin)) * (w - 60) + 30
    const toY = v => h - (((v - yMin) / (yMax - yMin)) * (h - 60) + 30)

    ctx.clearRect(0, 0, w, h)

    ctx.strokeStyle = 'rgba(255,255,255,0.04)'
    ctx.lineWidth = 1
    for (let i = 0; i <= 4; i++) {
      const x = 30 + (i / 4) * (w - 60)
      const y = 30 + (i / 4) * (h - 60)
      ctx.beginPath(); ctx.moveTo(x, 30); ctx.lineTo(x, h - 30); ctx.stroke()
      ctx.beginPath(); ctx.moveTo(30, y); ctx.lineTo(w - 30, y); ctx.stroke()
    }

    coords.forEach(([x, y]) => {
      ctx.beginPath()
      ctx.arc(toX(x), toY(y), 2, 0, Math.PI * 2)
      ctx.fillStyle = 'rgba(255,255,255,0.12)'
      ctx.fill()
    })

    if (userX !== undefined && userY !== undefined) {
      const ux = toX(userX), uy = toY(userY)

      ctx.beginPath()
      ctx.arc(ux, uy, 18, 0, Math.PI * 2)
      ctx.strokeStyle = `${color}40`
      ctx.lineWidth = 1.5
      ctx.stroke()

      ctx.beginPath()
      ctx.arc(ux, uy, 10, 0, Math.PI * 2)
      ctx.strokeStyle = `${color}80`
      ctx.lineWidth = 2
      ctx.stroke()

      ctx.beginPath()
      ctx.arc(ux, uy, 5, 0, Math.PI * 2)
      ctx.fillStyle = color
      ctx.shadowColor = color
      ctx.shadowBlur = 12
      ctx.fill()
      ctx.shadowBlur = 0

      ctx.fillStyle = 'rgba(240,240,248,0.8)'
      ctx.font = '11px "JetBrains Mono", monospace'
      ctx.textAlign = 'center'
      ctx.fillText('You', ux, uy - 22)
    }
  }, [coords, userX, userY, color])

  return (
    <div style={{ position: 'relative', width: '100%', aspectRatio: '4/3', borderRadius: 16, overflow: 'hidden', background: 'var(--bg-deep)', border: '1px solid var(--border)' }}>
      <canvas ref={canvasRef} style={{ width: '100%', height: '100%', display: 'block' }} />
      <div style={{ position: 'absolute', bottom: 12, left: 16, fontSize: 11, color: 'var(--text-muted)', fontFamily: 'var(--font-mono)' }}>
        {coords.length.toLocaleString()} data points · UMAP projection
      </div>
    </div>
  )
}