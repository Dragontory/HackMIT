import React, { useEffect } from 'react';
import { motion, useMotionValue, useTransform, useSpring } from 'framer-motion';

const INTENSITY = 1.8; // ↑ make bigger for more motion (e.g., 2.4)

export default function Background() {
  const mx = useMotionValue(0);
  const my = useMotionValue(0);

  // Smooth the motion a bit (feels nicer when stronger)
  const sx = useSpring(mx, { stiffness: 80, damping: 20, mass: 0.6 });
  const sy = useSpring(my, { stiffness: 80, damping: 20, mass: 0.6 });

  // Rotations (increase ranges)
  const rotateX = useTransform(sy, [-1, 1], [8 * INTENSITY, -8 * INTENSITY]);
  const rotateY = useTransform(sx, [-1, 1], [-12 * INTENSITY, 12 * INTENSITY]);

  // Parallax per-layer (increase ranges)
  const x1 = useTransform(sx, [-1, 1], [-36 * INTENSITY, 36 * INTENSITY]);
  const y1 = useTransform(sy, [-1, 1], [-22 * INTENSITY, 22 * INTENSITY]);

  const x2 = useTransform(sx, [-1, 1], [-64 * INTENSITY, 64 * INTENSITY]);
  const y2 = useTransform(sy, [-1, 1], [-36 * INTENSITY, 36 * INTENSITY]);

  const x3 = useTransform(sx, [-1, 1], [48 * INTENSITY, -48 * INTENSITY]);
  const y3 = useTransform(sy, [-1, 1], [-28 * INTENSITY, 28 * INTENSITY]);

  useEffect(() => {
    const handle = (e) => {
      const vw = window.innerWidth || 1;
      const vh = window.innerHeight || 1;
      mx.set((e.clientX / vw) * 2 - 1);
      my.set((e.clientY / vh) * 2 - 1);
    };
    window.addEventListener('mousemove', handle, { passive: true });
    return () => window.removeEventListener('mousemove', handle);
  }, [mx, my]);

  return (
    <div className="pointer-events-none absolute inset-0 -z-10 overflow-hidden" aria-hidden>
      <div className="absolute inset-0" style={{ perspective: '1000px' }}>
        <motion.div style={{ rotateX, rotateY }} className="absolute left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2 transform-gpu">
          <motion.div
            className="h-[46vmax] w-[46vmax] rounded-full blur-3xl opacity-30"
            style={{
              x: x1,
              y: y1,
              background: 'radial-gradient(closest-side, #38bdf8 0%, rgba(56,189,248,0.18) 35%, transparent 70%)',
            }}
          />
          <motion.div
            className="h-[46vmax] w-[46vmax] -mt-32 -ml-20 rounded-full blur-3xl opacity-28"
            style={{
              x: x2,
              y: y2,
              background: 'radial-gradient(closest-side, #818cf8 0%, rgba(129,140,248,0.18) 35%, transparent 70%)',
            }}
          />
          <motion.div
            className="h-[46vmax] w-[46vmax] -mt-32 ml-20 rounded-full blur-3xl opacity-28"
            style={{
              x: x3,
              y: y3,
              background: 'radial-gradient(closest-side, #c084fc 0%, rgba(192,132,252,0.18) 35%, transparent 70%)',
            }}
          />
        </motion.div>
      </div>
    </div>
  );
}




