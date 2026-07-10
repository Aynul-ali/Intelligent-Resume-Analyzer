import { useEffect, useRef, useState } from "react";

function getScoreColor(score) {
  if (score >= 70) return { stroke: "#10b981", text: "#10b981", label: "Strong Match", bg: "rgba(16,185,129,0.1)" };
  if (score >= 40) return { stroke: "#f59e0b", text: "#f59e0b", label: "Moderate Match", bg: "rgba(245,158,11,0.1)" };
  return { stroke: "#ef4444", text: "#ef4444", label: "Weak Match", bg: "rgba(239,68,68,0.1)" };
}

export default function MatchScoreCard({ score, breakdown }) {
  const [displayScore, setDisplayScore] = useState(0);
  const [animated, setAnimated] = useState(false);
  const animRef = useRef(null);

  const { stroke, text, label, bg } = getScoreColor(score);

  // Animate count-up
  useEffect(() => {
    if (!score) return;
    let start = 0;
    const duration = 1200;
    const step = 16;
    const increment = score / (duration / step);

    const timer = setInterval(() => {
      start += increment;
      if (start >= score) {
        setDisplayScore(score);
        setAnimated(true);
        clearInterval(timer);
      } else {
        setDisplayScore(Math.round(start));
      }
    }, step);
    return () => clearInterval(timer);
  }, [score]);

  // SVG circle params
  const radius = 80;
  const circumference = 2 * Math.PI * radius;
  const strokeDashoffset = circumference - (displayScore / 100) * circumference;

  return (
    <div className="score-card" style={{ "--score-color": stroke, "--score-bg": bg }}>
      <div className="score-ring-container">
        <svg width="200" height="200" viewBox="0 0 200 200">
          {/* Background track */}
          <circle
            cx="100" cy="100" r={radius}
            fill="none"
            stroke="rgba(255,255,255,0.08)"
            strokeWidth="12"
          />
          {/* Progress arc */}
          <circle
            cx="100" cy="100" r={radius}
            fill="none"
            stroke={stroke}
            strokeWidth="12"
            strokeLinecap="round"
            strokeDasharray={circumference}
            strokeDashoffset={strokeDashoffset}
            transform="rotate(-90 100 100)"
            style={{ transition: "stroke-dashoffset 0.05s linear", filter: `drop-shadow(0 0 8px ${stroke}60)` }}
          />
          {/* Glow dot at tip */}
          <circle
            cx="100" cy="20" r="6"
            fill={stroke}
            style={{ filter: `drop-shadow(0 0 6px ${stroke})` }}
            transform={`rotate(${(displayScore / 100) * 360} 100 100)`}
          />
        </svg>
        <div className="score-inner">
          <span className="score-value" style={{ color: text }}>
            {Math.round(displayScore)}
          </span>
          <span className="score-percent" style={{ color: text }}>%</span>
        </div>
      </div>

      <div className="score-label" style={{ color: text, background: bg }}>
        {label}
      </div>

      {breakdown && (
        <div className="score-breakdown">
          <BreakdownBar label="Semantic Match" value={breakdown.semantic_similarity} color={stroke} />
          <BreakdownBar label="Skills Match" value={breakdown.skill_match_percentage} color={stroke} />
          <BreakdownBar label="Skills Section" value={breakdown.skills_section_score} color={stroke} />
          <BreakdownBar label="Experience" value={breakdown.experience_section_score} color={stroke} />
        </div>
      )}
    </div>
  );
}

function BreakdownBar({ label, value, color }) {
  const [width, setWidth] = useState(0);

  useEffect(() => {
    const t = setTimeout(() => setWidth(value), 300);
    return () => clearTimeout(t);
  }, [value]);

  return (
    <div className="breakdown-row">
      <div className="breakdown-label">{label}</div>
      <div className="breakdown-bar-track">
        <div
          className="breakdown-bar-fill"
          style={{
            width: `${width}%`,
            background: color,
            transition: "width 0.8s cubic-bezier(0.4,0,0.2,1)",
          }}
        />
      </div>
      <div className="breakdown-value" style={{ color }}>
        {Math.round(value)}%
      </div>
    </div>
  );
}
