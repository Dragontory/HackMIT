import React, { useEffect, useMemo, useRef, useState } from "react";
import { motion, AnimatePresence } from "framer-motion";

/** Tweak timings (ms) */
const DWELL_NOTEBOOK = 2200;   // how long notebook stays before fading out
const FADE_MS        = 600;    // crossfade duration
const TYPE_SPEED_MS  = 35;     // per-character speed
const POST_TYPE_DWELL= 1200;   // pause after typing on graph before fading back

const EXPLANATION =
  "This graph shows f(x) = sin(x) + x/4. The sine term oscillates, " +
  "while the linear term gradually shifts the curve upward as x increases.";

export default function Notebook3D() {
  const [phase, setPhase] = useState("notebook"); // 'notebook' | 'graph'
  const [typed, setTyped] = useState("");

  // loop controller
  const cycleRef = useRef(null);
  const typingRef = useRef(null);

  useEffect(() => {
    // start on notebook, then move to graph after dwell + fade
    startNotebookPhase();
    return () => {
      clearTimers();
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  function clearTimers() {
    if (cycleRef.current) clearTimeout(cycleRef.current);
    if (typingRef.current) clearInterval(typingRef.current);
  }

  function startNotebookPhase() {
    clearTimers();
    setPhase("notebook");
    setTyped("");
    cycleRef.current = setTimeout(() => {
      // fade to graph
      setPhase("graph");
    }, DWELL_NOTEBOOK);
  }

  function startTyping() {
    // type explanation on graph
    setTyped("");
    let i = 0;
    clearInterval(typingRef.current);
    typingRef.current = setInterval(() => {
      i++;
      setTyped(EXPLANATION.slice(0, i));
      if (i >= EXPLANATION.length) {
        clearInterval(typingRef.current);
        // after finishing typing, dwell, then go back
        cycleRef.current = setTimeout(() => startNotebookPhase(), POST_TYPE_DWELL);
      }
    }, TYPE_SPEED_MS);
  }

  // whenever we enter graph phase, kick off typing (after fade settles slightly)
  useEffect(() => {
    if (phase === "graph") {
      const id = setTimeout(startTyping, FADE_MS * 0.6);
      return () => clearTimeout(id);
    } else {
      // ensure we stop typing if we leave
      clearInterval(typingRef.current);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [phase]);

  return (
    <div className="relative h-80 w-full rounded-xl overflow-hidden bg-slate-900/60 border border-slate-700">
      <AnimatePresence mode="wait">
        {phase === "notebook" ? (
          <motion.div
            key="notebook"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: FADE_MS / 1000 }}
            className="absolute inset-0 grid place-items-center"
          >
            <NotebookSVG />
          </motion.div>
        ) : (
          <motion.div
            key="graph"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: FADE_MS / 1000 }}
            className="absolute inset-0"
          >
            <GraphWithTyping typed={typed} />
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}

/* ---------- Visuals ---------- */

function NotebookSVG() {
  // simple, crisp notebook look in SVG
  return (
    <svg
      viewBox="0 0 1200 760"
      className="w-[95%] h-[85%] drop-shadow-lg"
      xmlns="http://www.w3.org/2000/svg"
    >
      {/* Paper */}
      <rect x="0" y="0" width="1200" height="760" rx="24" fill="#f8fafc" />
      {/* Margin line */}
      <line x1="200" y1="0" x2="200" y2="760" stroke="rgba(239,68,68,0.35)" strokeWidth="6" />
      {/* Ruling */}
      {Array.from({ length: 7 }).map((_, i) => {
        const y = 120 + i * 90;
        return (
          <line
            key={i}
            x1="220"
            y1={y}
            x2="1120"
            y2={y}
            stroke="rgba(100,116,139,0.25)"
            strokeWidth="4"
          />
        );
      })}
      {/* Equation text */}
      <text x="250" y="330" fill="#0f172a" fontWeight="700" fontFamily="Inter, system-ui" fontSize="64">
        f(x) = sin(x) + x/4
      </text>
      <text x="250" y="500" fill="#0f172a" fontWeight="700" fontFamily="Inter, system-ui" fontSize="54">
        ∫ cos(x) dx = sin(x) + C
      </text>
    </svg>
  );
}

function GraphWithTyping({ typed }) {
  return (
    <div className="absolute inset-0 flex items-stretch gap-4 p-4 md:p-6">
      {/* LEFT: Graph */}
      <div className="relative flex-1 rounded-lg overflow-hidden bg-[#0b1220] border border-slate-700">
        <GraphSVG />
      </div>

      {/* RIGHT: Typing panel */}
      <div className="hidden md:flex w-[40%] min-w-[260px] rounded-lg border border-slate-700 bg-slate-800 p-4 md:p-5">
        <div className="text-slate-200 text-sm leading-relaxed">
          <span className="text-sky-400 font-semibold">Explainer:</span>{" "}
          <span className="whitespace-pre-wrap">{typed}</span>
          <TypingCursor active />
        </div>
      </div>
    </div>
  );
}

function TypingCursor({ active }) {
  return (
    <span
      className={`inline-block w-[10px] h-[1.2em] align-[-0.2em] ml-1 ${
        active ? "animate-pulse" : ""
      }`}
      style={{ background: "rgba(248,250,252,0.7)" }}
    />
  );
}

function GraphSVG() {
  // Draw axes + grid + animated path (CSS-only animation shim)
  // (We fake animation by using a large dashed offset via CSS animation)
  const pathId = "graph-line";
  const d = useMemo(() => {
    // generate a smooth path for sin(x) + x/4 across [-6, 6]
    const pts = [];
    const W = 600;
    const H = 400;
    const toX = (x) => ((x + 6) / 12) * W;
    const toY = (y) => H / 2 - y * 28; // scale
    for (let x = -6; x <= 6; x += 0.05) {
      const y = Math.sin(x) + x / 4;
      pts.push([toX(x), toY(y)]);
    }
    return "M" + pts.map(([x, y]) => `${x},${y}`).join(" L ");
  }, []);

  return (
    <svg viewBox="0 0 640 420" className="absolute inset-0 m-auto w-[92%] h-[90%]">
      {/* Grid */}
      <defs>
        <pattern id="grid" width="40" height="40" patternUnits="userSpaceOnUse">
          <path d="M 40 0 L 0 0 0 40" fill="none" stroke="rgba(148,163,184,0.18)" strokeWidth="1" />
        </pattern>
      </defs>
      <rect x="0" y="0" width="640" height="420" fill="url(#grid)" />

      {/* Axes */}
      <line x1="320" y1="0" x2="320" y2="420" stroke="rgba(56,189,248,0.65)" strokeWidth="2" />
      <line x1="0" y1="210" x2="640" y2="210" stroke="rgba(56,189,248,0.65)" strokeWidth="2" />

      {/* Equation label */}
      <text x="20" y="36" fill="#93c5fd" fontFamily="Inter, system-ui" fontWeight="600" fontSize="16">
        f(x) = sin(x) + x/4
      </text>

      {/* Path */}
      <path
        id={pathId}
        d={d}
        fill="none"
        stroke="#38bdf8"
        strokeWidth="3"
        strokeLinejoin="round"
        strokeLinecap="round"
        style={{
          strokeDasharray: "6 10",
          animation: "dash-move 2.4s linear infinite",
        }}
      />

      {/* Little “playhead” dot moving along x */}
      <circle r="4" fill="#c084fc">
        <animateMotion
          dur="3.6s"
          repeatCount="indefinite"
          path={`M 0,0 L 640,0`}
        />
        <animate
          attributeName="cy"
          dur="3.6s"
          repeatCount="indefinite"
          values="210;120;210;300;210"
        />
      </circle>

      {/* Path animation CSS */}
      <style>{`
        @keyframes dash-move {
          to { stroke-dashoffset: -64; }
        }
      `}</style>
    </svg>
  );
}






