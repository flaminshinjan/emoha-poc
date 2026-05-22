/* Shared building blocks across both directions.
   These pieces handle the bits that don't differ visually much: avatar SVG portrait,
   emergency button, transcript playback simulation, etc.
*/

// ---------------- Avatar portrait (placeholder for the Tavus video) ----------------
// Male silhouette — short hair, no earrings, slight stubble shading.
function AvatarPortrait({ speaking = false, name = "Soumyajit", tint = "warm" }) {
  const skin = tint === "warm" ? "#c79474" : "#b88a6c";
  return (
    <div className="avatar-still">
      <div className="speak-ring" style={{ borderRadius: 0 }}></div>
      <div className="avatar-portrait">
        <svg viewBox="0 0 200 260" preserveAspectRatio="xMidYMax slice">
          <defs>
            <linearGradient id={`hair-${name}`} x1="0" y1="0" x2="0" y2="1">
              <stop offset="0" stopColor="#2a1d18" />
              <stop offset="1" stopColor="#160e0a" />
            </linearGradient>
            <linearGradient id={`shoulder-${name}`} x1="0" y1="0" x2="0" y2="1">
              <stop offset="0" stopColor="#4a5550" />
              <stop offset="1" stopColor="#2d3631" />
            </linearGradient>
          </defs>
          {/* shoulders — broader, squarer for a male frame */}
          <path d="M -10 270 Q 28 195 100 192 Q 172 195 210 270 Z" fill={`url(#shoulder-${name})`} opacity="0.95" />
          {/* shirt collar hint */}
          <path d="M 78 198 Q 100 210 122 198 L 118 210 Q 100 218 82 210 Z" fill="rgba(0,0,0,0.25)" />
          {/* neck */}
          <rect x="84" y="164" width="32" height="36" rx="6" fill={skin} opacity="0.95" />
          {/* face — slightly squarer than the original */}
          <ellipse cx="100" cy="118" rx="40" ry="50" fill={skin} />
          {/* short male hair — cropped, not falling past the ears */}
          <path d="M 60 96
                   Q 58 64 100 58
                   Q 142 64 140 96
                   Q 130 84 100 80
                   Q 70 84 60 96 Z" fill={`url(#hair-${name})`} />
          {/* brow accents */}
          <path d="M 80 110 Q 86 106 92 110" stroke="#2a1d18" strokeWidth="1.6" fill="none" strokeLinecap="round" opacity="0.85" />
          <path d="M 108 110 Q 114 106 120 110" stroke="#2a1d18" strokeWidth="1.6" fill="none" strokeLinecap="round" opacity="0.85" />
          {/* eyes (closed-ish, gentle) */}
          <path d="M 82 122 Q 86 126 90 122" stroke="#3a2820" strokeWidth="1.4" fill="none" strokeLinecap="round" />
          <path d="M 110 122 Q 114 126 118 122" stroke="#3a2820" strokeWidth="1.4" fill="none" strokeLinecap="round" />
          {/* nose hint */}
          <path d="M 100 130 Q 102 140 100 145" stroke="rgba(60,40,30,0.25)" strokeWidth="1.2" fill="none" strokeLinecap="round" />
          {/* mouth — animated when speaking */}
          <g className={speaking ? "mouth speaking" : "mouth"}>
            <path d="M 92 152 Q 100 158 108 152" stroke="#6a3325" strokeWidth="1.8" fill="none" strokeLinecap="round" />
          </g>
          {/* subtle jaw/stubble shading */}
          <path d="M 75 145 Q 100 168 125 145 Q 100 178 75 145 Z" fill="rgba(40,28,22,0.07)" />
        </svg>
      </div>
    </div>
  );
}

// ---------------- Emergency button (always visible) ----------------
function EmergencyButton({ label = "Talk to a human now", onClick, variant = "a" }) {
  if (variant === "a") {
    return (
      <button className="emergency btn-hover" onClick={onClick}
        style={{
          padding: "10px 16px 10px 14px",
          borderRadius: 999,
          background: "rgba(255,255,255,0.7)",
          border: "1px solid rgba(0,0,0,0.08)",
          fontSize: 13,
          color: "var(--ink)",
        }}>
        <span className="emergency-dot"></span>
        {label}
      </button>
    );
  }
  return (
    <button className="emergency btn-hover" onClick={onClick}
      style={{
        padding: "9px 14px",
        borderRadius: 4,
        background: "var(--card)",
        border: "1px solid var(--line-strong)",
        fontSize: 13,
        color: "var(--ink)",
        fontWeight: 500,
      }}>
      <span className="emergency-dot"></span>
      {label}
    </button>
  );
}

// ---------------- Level meter / speaking indicator ----------------
function LevelBars() {
  return (
    <div className="level-bars">
      <span></span><span></span><span></span><span></span><span></span>
    </div>
  );
}

// ---------------- Step indicator dots ----------------
function StepDots({ count, current }) {
  return (
    <div className="step-dots">
      {Array.from({ length: count }).map((_, i) => (
        <span key={i} className={`step-dot ${i === current ? "active" : i < current ? "done" : ""}`}></span>
      ))}
    </div>
  );
}

// ---------------- Score ring ----------------
function ScoreRing({ value = 6, max = 10, size = 96, stroke = 8, color = "var(--accent)" }) {
  const r = (size - stroke) / 2;
  const c = 2 * Math.PI * r;
  const offset = c - (value / max) * c;
  // viewBox is critical: lets the SVG (and its inner circles) scale uniformly
  // when CSS resizes the element on mobile. Without it, shrinking the <svg>
  // clips the arc since the circles' cx/cy/r are absolute.
  return (
    <svg className="score-ring" width={size} height={size}
         viewBox={`0 0 ${size} ${size}`}
         preserveAspectRatio="xMidYMid meet">
      <circle className="bg" cx={size/2} cy={size/2} r={r} stroke="rgba(0,0,0,0.08)" strokeWidth={stroke} fill="none" />
      <circle className="fg" cx={size/2} cy={size/2} r={r} stroke={color} strokeWidth={stroke}
              fill="none" strokeDasharray={c} strokeDashoffset={offset} strokeLinecap="round" />
    </svg>
  );
}

// ---------------- Insight ribbon (gentle human-language version of state) ----------------
// Cycles through gentle observations every few seconds while on the call.
function InsightRibbon({ active, variant = "a", phase = 0 }) {
  const messages = [
    { icon: "❡", text: "Listening for what feels heavy" },
    { icon: "❡", text: "I'm hearing some guilt around being far away" },
    { icon: "❡", text: "Noting: parent lives alone, recent fall" },
    { icon: "❡", text: "Thinking about isolation and emergency readiness" },
    { icon: "❡", text: "Beginning to picture a plan that fits" },
  ];
  const m = messages[Math.min(phase, messages.length - 1)];
  if (!active) return null;
  return (
    <div className="insight-row" key={phase} style={{
      transition: "opacity 0.4s ease",
      color: "var(--ink-soft)",
    }}>
      <span style={{
        display: "inline-block", width: 6, height: 6, borderRadius: 999,
        background: "var(--accent)", flexShrink: 0,
      }}></span>
      <span style={{ fontStyle: variant === "a" ? "italic" : "normal" }}>{m.text}</span>
    </div>
  );
}

// ---------------- Brief steps definition (shared) ----------------
const BRIEF_STEPS = [
  { id: "caller_name", q: "First — what should we call you?", placeholder: "Your name", kind: "text" },
  { id: "parent", q: "Who are we talking about?", kind: "parent" },
  { id: "where", q: "Where do they live?", kind: "where" },
  { id: "mobility", q: "How are they getting around these days?", kind: "options",
    options: [
      { id: "full", label: "Independently, no help needed" },
      { id: "partial", label: "Some help — a stick, a cane, occasional support" },
      { id: "limited", label: "Limited — needs help most days" },
    ]},
  { id: "conditions", q: "Anything ongoing health-wise?", kind: "chips",
    options: ["Diabetes", "Blood pressure", "Heart", "Joint pain", "Memory", "Recent surgery", "None right now"]},
  { id: "prompt", q: "What made you reach out today?", placeholder: "It's okay to be brief — Soumyajit will follow up gently.", kind: "textarea" },
];

const ADVISORS = [
  { slug: "soumyajit", name: "Soumyajit", role: "Calm, grounded", desc: "Best for when you need someone to listen first.", color: "#3b6a63" },
];

// ---------------- Demo transcript snippets (for live call illustration) ----------------
const TRANSCRIPT = [
  { who: "advisor", t: "Hi {name}. Take a breath. I'm here when you're ready." },
  { who: "caller", t: "Thanks. I just… don't know where to start." },
  { who: "advisor", t: "That's completely okay. Tell me — how's {parent} been the last few weeks?" },
  { who: "caller", t: "She had a small fall in the bathroom. She's okay, but I'm in Bangalore and she's alone in Lucknow." },
  { who: "advisor", t: "Mm. That sounds heavy. Being far when something like that happens." },
];

// Expose to global so direction files can use them.
Object.assign(window, {
  AvatarPortrait,
  EmergencyButton,
  LevelBars,
  StepDots,
  ScoreRing,
  InsightRibbon,
  BRIEF_STEPS,
  ADVISORS,
  TRANSCRIPT,
});
