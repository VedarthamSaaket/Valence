import { useEffect, useRef } from 'react'

const SILVER_PARTICLES = [
    '#c8d8e8', '#deeaf4', '#f0f6fa', '#b8ccd8', '#e4eef6',
    '#a8bece', '#d0e0ec', '#f4f8fc', '#c0d4e4', '#e0eaf2',
]

export default function ParticleCanvas({ count = 55 }) {
    const canvasRef = useRef(null)

    useEffect(() => {
        const canvas = canvasRef.current
        if (!canvas) return
        const ctx = canvas.getContext('2d')
        if (!ctx) return

        const resize = () => {
            canvas.width = window.innerWidth
            canvas.height = window.innerHeight
        }
        resize()
        window.addEventListener('resize', resize)

        const particles = Array.from({ length: count }, () => ({
            x: Math.random() * canvas.width,
            y: Math.random() * canvas.height,
            vx: (Math.random() - 0.5) * 0.22,
            vy: -Math.random() * 0.38 - 0.08,
            size: Math.random() * 1.8 + 0.4,
            opacity: Math.random() * 0.55 + 0.12,
            color: SILVER_PARTICLES[Math.floor(Math.random() * SILVER_PARTICLES.length)],
        }))

        let raf

        const draw = () => {
            ctx.clearRect(0, 0, canvas.width, canvas.height)

            particles.forEach(p => {
                p.x += p.vx
                p.y += p.vy

                if (p.y < -10) {
                    p.y = canvas.height + 10
                    p.x = Math.random() * canvas.width
                }
                if (p.x < -10) p.x = canvas.width + 10
                if (p.x > canvas.width + 10) p.x = -10

                const alpha = p.opacity
                const hex = Math.floor(alpha * 255).toString(16).padStart(2, '0')

                ctx.beginPath()
                ctx.arc(p.x, p.y, p.size, 0, Math.PI * 2)
                ctx.fillStyle = p.color + hex
                ctx.fill()

                const grd = ctx.createRadialGradient(p.x, p.y, 0, p.x, p.y, p.size * 5)
                grd.addColorStop(0, p.color + '18')
                grd.addColorStop(1, 'transparent')
                ctx.beginPath()
                ctx.arc(p.x, p.y, p.size * 5, 0, Math.PI * 2)
                ctx.fillStyle = grd
                ctx.fill()
            })

            raf = requestAnimationFrame(draw)
        }

        draw()

        return () => {
            cancelAnimationFrame(raf)
            window.removeEventListener('resize', resize)
        }
    }, [count])

    return (
        <canvas
            ref={canvasRef}
            className="particles-canvas"
            style={{ opacity: 0.55 }}
        />
    )
}