import { useRef, useEffect, useState, useMemo, useId } from 'react';


const CurvedLoop = ({
    marqueeText = '',
    speed = 2,
    className,
    curveAmount = 400,
    direction = 'left',
    interactive = true,
    style = {},
}) => {
    const text = useMemo(() => {
        return marqueeText.replace(/\s+$/, '') + '\u00A0';
    }, [marqueeText]);

    const measureRef = useRef(null);
    const textPathRef = useRef(null);
    const [spacing, setSpacing] = useState(0);
    const [offset, setOffset] = useState(0);
    const [dragging, setDragging] = useState(false);

    const uid = useId();
    const pathId = `cl-${uid.replace(/:/g, '')}`;
    const gradId = `cl-grad-${uid.replace(/:/g, '')}`;

    
    const baseY = 160;
    const pathD = `M -200,${baseY} Q 720,${baseY + curveAmount} 1640,${baseY}`;
    const ready = spacing > 0;

    const totalText = spacing
        ? Array(Math.ceil(2200 / spacing) + 3).fill(text).join('')
        : text;

    const dragRef = useRef(false);
    const lastXRef = useRef(0);
    const dirRef = useRef(direction);
    const velRef = useRef(0);

    useEffect(() => { dirRef.current = direction; }, [direction]);

    useEffect(() => {
        if (measureRef.current) setSpacing(measureRef.current.getComputedTextLength());
    }, [text, className]);

    useEffect(() => {
        if (!spacing || !textPathRef.current) return;
        const initial = -spacing;
        textPathRef.current.setAttribute('startOffset', String(initial));
        setOffset(initial);
    }, [spacing]);

    useEffect(() => {
        if (!spacing || !ready) return;
        let raf;
        const step = () => {
            if (!dragRef.current && textPathRef.current) {
                const delta = dirRef.current === 'right' ? speed : -speed;
                let cur = parseFloat(textPathRef.current.getAttribute('startOffset') || '0');
                cur += delta;
                if (cur <= -spacing) cur += spacing;
                if (cur > 0) cur -= spacing;
                textPathRef.current.setAttribute('startOffset', String(cur));
                setOffset(cur);
            }
            raf = requestAnimationFrame(step);
        };
        raf = requestAnimationFrame(step);
        return () => cancelAnimationFrame(raf);
    }, [spacing, speed, ready]);

    const onPointerDown = e => {
        if (!interactive) return;
        dragRef.current = true;
        setDragging(true);
        lastXRef.current = e.clientX;
        velRef.current = 0;
        e.currentTarget.setPointerCapture(e.pointerId);
    };

    const onPointerMove = e => {
        if (!interactive || !dragRef.current || !textPathRef.current) return;
        const dx = e.clientX - lastXRef.current;
        lastXRef.current = e.clientX;
        velRef.current = dx;
        let cur = parseFloat(textPathRef.current.getAttribute('startOffset') || '0');
        cur += dx;
        if (cur <= -spacing) cur += spacing;
        if (cur > 0) cur -= spacing;
        textPathRef.current.setAttribute('startOffset', String(cur));
        setOffset(cur);
    };

    const endDrag = () => {
        if (!interactive) return;
        dragRef.current = false;
        setDragging(false);
        dirRef.current = velRef.current >= 0 ? 'right' : 'left';
    };

    return (
        <div
            style={{
                width: '100%',
                
                overflow: 'visible',
                visibility: ready ? 'visible' : 'hidden',
                cursor: interactive ? (dragging ? 'grabbing' : 'grab') : 'default',
                userSelect: 'none',
                WebkitUserSelect: 'none',
                
                height: 80,
                display: 'flex',
                alignItems: 'center',
                ...style,
            }}
            onPointerDown={onPointerDown}
            onPointerMove={onPointerMove}
            onPointerUp={endDrag}
            onPointerLeave={endDrag}
        >
            <svg
                
                viewBox="0 0 1440 320"
                preserveAspectRatio="xMidYMid meet"
                style={{
                    display: 'block',
                    width: '100%',
                    
                    overflow: 'visible',
                    fontSize: '3.2rem',
                    fontWeight: 300,
                    letterSpacing: '0.14em',
                    textTransform: 'uppercase',
                }}
            >
                <defs>
                    {}
                    <linearGradient id={gradId} x1="0%" y1="0%" x2="100%" y2="0%">
                        <stop offset="0%" stopColor="#6a7a8a" />
                        <stop offset="12%" stopColor="#b0bec8" />
                        <stop offset="25%" stopColor="#dce8f0" />
                        <stop offset="35%" stopColor="#f0f5f8" />
                        <stop offset="48%" stopColor="#c8d8e4" />
                        <stop offset="58%" stopColor="#8aa0b0" />
                        <stop offset="70%" stopColor="#dce8f2" />
                        <stop offset="80%" stopColor="#f2f6f8" />
                        <stop offset="92%" stopColor="#a8bcc8" />
                        <stop offset="100%" stopColor="#c0d0dc" />
                    </linearGradient>

                    <path id={pathId} d={pathD} fill="none" />
                </defs>

                {}
                <text
                    ref={measureRef}
                    xmlSpace="preserve"
                    fontSize="3.2rem"
                    fontWeight="300"
                    letterSpacing="0.14em"
                    style={{ visibility: 'hidden', opacity: 0, pointerEvents: 'none' }}
                >
                    {text}
                </text>

                {ready && (
                    <text
                        xmlSpace="preserve"
                        
                        fill={`url(#${gradId})`}
                        fontSize="3.2rem"
                        fontWeight="300"
                        letterSpacing="0.14em"
                        fontFamily="'Cormorant SC', serif"
                        className={className}
                    >
                        <textPath
                            ref={textPathRef}
                            href={`#${pathId}`}
                            startOffset={String(offset)}
                            xmlSpace="preserve"
                        >
                            {totalText}
                        </textPath>
                    </text>
                )}
            </svg>
        </div>
    );
};

export default CurvedLoop;