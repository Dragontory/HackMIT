import React, { useRef } from 'react';

const clamp = (v, min, max) => Math.min(Math.max(v, min), max);

const TiltCard = ({ className = '', children }) => {
  const ref = useRef(null);
  const maxTilt = 6; // degrees

  const handleMove = (e) => {
    const el = ref.current;
    if (!el) return;
    const rect = el.getBoundingClientRect();
    const px = (e.clientX - rect.left) / rect.width;  // 0..1
    const py = (e.clientY - rect.top) / rect.height;  // 0..1

    // Map to -max..+max
    const tiltX = clamp((0.5 - py) * (maxTilt * 2), -maxTilt, maxTilt);
    const tiltY = clamp((px - 0.5) * (maxTilt * 2), -maxTilt, maxTilt);

    el.style.transform = `perspective(900px) rotateX(${tiltX}deg) rotateY(${tiltY}deg) translateZ(0)`;
  };

  const handleLeave = () => {
    const el = ref.current;
    if (!el) return;
    el.style.transform = 'perspective(900px) rotateX(0deg) rotateY(0deg) translateZ(0)';
  };

  return (
    <div
      ref={ref}
      onMouseMove={handleMove}
      onMouseLeave={handleLeave}
      className={`card-tilt transform-gpu ${className}`}
    >
      {children}
    </div>
  );
};

export default TiltCard;
