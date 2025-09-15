import React, { useEffect, useMemo, useRef, useState } from "react";
import { motion } from "framer-motion";

/** ---------- Timings (ms) ---------- */
const FIRST_DWELL_NOTEBOOK = 3400; // longer first time
const DWELL_NOTEBOOK = 2200; // later cycles
const FADE_PAPER_MS = 800;  // fade notebook sheet only
const HOLD_EQ_MS = 250;  // hold equation after paper fades, before moving
const MOVE_EQ_MS = 900;  // move+shrink equation to graph label
const GRAPH_FADE_MS = 900;  // graph fade-in (during move)
const TYPE_SPEED_MS = 32;   // typing speed
const POST_TYPE_DWELL = 1400; // pause after typing
const FADE_BACK_MS = 600;  // crossfade back to notebook

const EXPLANATION =
  "f(x) = sin(x) + x/4 — the sine term oscillates; the linear term lifts the curve as x increases.";

function Caret({ show }) {
  return (
    <span
      className={`inline-block w-[8px] h-[1.1em] align-[-0.2em] ml-1 ${show ? "animate-pulse" : ""}`}
      style={{ background: "rgba(248,250,252,0.75)" }}
    />
  );
}

export default function Notebook3D() {
  const [phase, setPhase] = useState("NOTEBOOK");
  const [firstPass, setFirstPass] = useState(true);
  const [typed, setTyped] = useState("");
  const [eqProgress, setEqProgress] = useState(0); // 0..1
  const [paperOpacity, setPaperOpacity] = useState(1);
  const [graphOpacity, setGraphOpacity] = useState(0);
  const [eqColor, setEqColor] = useState("#0f172a");  

  const timers = useRef([]);
  const clearAll = () => { timers.current.forEach((id) => clearTimeout(id)); timers.current = []; };

  useEffect(() => {
    startNotebook(firstPass ? FIRST_DWELL_NOTEBOOK : DWELL_NOTEBOOK);
    return clearAll;
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const startNotebook = (dwell) => {
    clearAll();
    setPhase("NOTEBOOK");
    setTyped("");
    setEqProgress(0);
    setPaperOpacity(1);
    setGraphOpacity(0);
    setEqColor("black");  // Start with black color for equation

    timers.current.push(
      setTimeout(() => {
        setPhase("FADE_PAPER");
        animatePaperFadeOut();
      }, dwell)
    );
  };

  const animatePaperFadeOut = () => {
    const t0 = performance.now();
    const tick = (now) => {
      const t = Math.min(1, (now - t0) / FADE_PAPER_MS);
      setPaperOpacity(1 - t);
      if (t < 1) requestAnimationFrame(tick);
      else {
        setEqColor("#ffffff"); 
        setPhase("HOLD_EQ");
        timers.current.push(setTimeout(() => startMoveToGraph(), HOLD_EQ_MS));
      }
    };
    requestAnimationFrame(tick);
  };

  const startMoveToGraph = () => {
    setPhase("MOVE_TO_GRAPH");
    const t0 = performance.now();
    const tick = (now) => {
      const raw = Math.min(1, (now - t0) / MOVE_EQ_MS);
      const ease = raw < 0.5 ? 4 * raw * raw * raw : 1 - Math.pow(-2 * raw + 2, 3) / 2; // easeInOutCubic
      setEqProgress(ease);
      setGraphOpacity(raw); // graph fades in while equation moves
      if (raw < 1) requestAnimationFrame(tick);
      else startTyping();
    };
    requestAnimationFrame(tick);
  };

  const startTyping = () => {
    setPhase("TYPE_ON_GRAPH");
    setTyped("");
    let i = 0;
    const id = setInterval(() => {
      i++;
      setTyped(EXPLANATION.slice(0, i));
      if (i >= EXPLANATION.length) {
        clearInterval(id);
        timers.current.push(
          setTimeout(() => {
            setPhase("GRAPH_DWELL");
            timers.current.push(
              setTimeout(() => {
                setPhase("FADE_BACK");
                animateBack();  // Add the fade-back phase here
              }, POST_TYPE_DWELL)
            );
          }, 10)
        );
      }
    }, TYPE_SPEED_MS);
    timers.current.push(id);
  };

  const animateBack = () => {
    const t0 = performance.now();
    const tick = (now) => {
      const t = Math.min(1, (now - t0) / FADE_BACK_MS);
      setGraphOpacity(1 - t);
      setEqProgress(1 - t);  // Shrink equation back to its starting size
      setPaperOpacity(t);  // Fade the paper back in
      if (t < 1) requestAnimationFrame(tick);
      else {
        setFirstPass(false);
        startNotebook(DWELL_NOTEBOOK);  // Restart animation after fade-back completes
      }
    };
    requestAnimationFrame(tick);
  };

  // layout constants
  const NOTEBOOK_VB = { w: 1200, h: 760 };
  // Notebook equation position (same as what’s on paper):
  const eqStart = { x: 200, y: 330, font: 64 };  // Moved x position to the left (200)
  // Graph label landing spot (upper-left inside the plot area):
  const eqEnd = { x: 400, y: 500, font: 30 };

  const eqX = eqStart.x + (eqEnd.x - eqStart.x) * eqProgress;
  const eqY = eqStart.y + (eqEnd.y - eqStart.y) * eqProgress;
  const eqScale = 1 + (eqEnd.font / eqStart.font - 1) * eqProgress;

  return (
    <div className="relative h-80 w-full rounded-xl overflow-hidden bg-slate-900/60 border border-slate-700">
      <div className="absolute inset-0 grid place-items-center">
        <motion.div
          initial={{ opacity: 1 }}
          animate={{ opacity: paperOpacity }}
          transition={{ duration: 0.001 }}
          className="w-full h-full flex items-center justify-center"
        >
          <NotebookPaperOnly />
        </motion.div>
      </div>

      {/* Graph layer (fades in while equation moves) */}
      <div className="absolute inset-0">
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: graphOpacity }}
          transition={{ duration: 0.001 }}
          className="absolute inset-0 p-4 md:p-5"
        >
          <GraphSVG typed={typed} />
        </motion.div>
      </div>

      {/* Floating equation moving from notebook to graph label (the only equation label) */}
      <motion.svg
        className="absolute inset-0 pointer-events-none"
        viewBox={`0 0 ${NOTEBOOK_VB.w} ${NOTEBOOK_VB.h}`}
        preserveAspectRatio="xMidYMid slice"
      >
        <motion.text
          x={eqX+110}
          y={eqY}
          style={{ originX: 0, originY: 0 }}
          transform={`scale(${eqScale})`}
          fill={eqColor} 
          fontWeight="800"
          fontFamily="Inter, system-ui, sans-serif"
          fontSize="60"
        >
          f(x) = sin(x) + x/4
        </motion.text>
      </motion.svg>
    </div>
  );
}

/* ----------------- SVGs ----------------- */

/** Paper with lines & a second equation lower down
 *  (The top equation is NOT drawn here so there’s no duplicate during transition.)
 */
function NotebookPaperOnly() {
  return (
    <svg
      viewBox="0 0 1200 760"
      className="w-[95%] h-[85%] drop-shadow-lg"
      xmlns="http://www.w3.org/2000/svg"
    >
      {/* paper */}
      <rect x="0" y="0" width="1200" height="760" rx="24" fill="#f8fafc" />
      {/* margin */}
      <line x1="200" y1="0" x2="200" y2="760" stroke="rgba(239,68,68,0.35)" strokeWidth="6" />
      {/* ruling */}
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
      
      {/* "Math Notes" title */}
      <motion.text
        x="250"
        y="100"
        fill="#0f172a"
        fontWeight="700"
        fontFamily="Inter, system-ui, sans-serif"
        fontSize="70"
        style={{
          opacity: 1, // Title opacity is controlled by animation during fade-out
          transition: "opacity 0.8s ease"
        }}
      >
        Math Notes!
      </motion.text>
      <text x="250" y="500" fill="#0f172a" fontWeight="700" fontFamily="Inter, system-ui" fontSize="40">
        ∫ cos(x) dx = sin(x) + C
      </text>
    </svg>
  );
}

function GraphSVG({ typed }) {
  const pathD = useMemo(() => {
    const pts = [];
    const W = 640, H = 420;
    const toX = (x) => ((x + 6) / 12) * W;
    const toY = (y) => H / 2 - y * 28;
    for (let x = -6; x <= 6; x += 0.05) {
      const y = Math.sin(x) + x / 4;
      pts.push([toX(x), toY(y)]);
    }
    return "M" + pts.map(([x, y]) => `${x},${y}`).join(" L ");
  }, []);

  return (
    <div className="relative h-full w-full">
      {/* Slight offset so the plot isn’t perfectly centered */}
      <svg viewBox="0 0 640 420" className="absolute inset-0 m-auto w-[88%] h-[92%] ml-[4%]">
        {/* grid */}
        <defs>
          <pattern id="grid" width="40" height="40" patternUnits="userSpaceOnUse">
            <path d="M 40 0 L 0 0 0 40" fill="none" stroke="rgba(148,163,184,0.18)" strokeWidth="1" />
          </pattern>
        </defs>
        <rect x="0" y="0" width="640" height="420" fill="url(#grid)" />

        {/* axes */}
        <line x1="320" y1="0" x2="320" y2="420" stroke="rgba(56,189,248,0.65)" strokeWidth="2" />
        <line x1="0"  y1="210" x2="640" y2="210" stroke="rgba(56,189,248,0.65)" strokeWidth="2" />

        {/* curve */}
        <path
          d={pathD}
          fill="none"
          stroke="#38bdf8"
          strokeWidth="3"
          strokeLinejoin="round"
          strokeLinecap="round"
        />

        {/* typed explanation on the graph (top-right), away from curve */}
        <foreignObject x="360" y="24" width="260" height="140">
          <div
            xmlns="http://www.w3.org/1999/xhtml"
            className="text-[16px] leading-snug text-slate-100"
            style={{ fontFamily: "Inter, system-ui, sans-serif", fontWeight: "700" }}
          >
            {typed}
            <Caret show />
          </div>
        </foreignObject>
      </svg>
    </div>
  );
}





