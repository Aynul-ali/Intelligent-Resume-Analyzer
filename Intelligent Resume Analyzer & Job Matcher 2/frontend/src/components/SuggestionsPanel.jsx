const PRIORITY_META = {
  high: { color: "#ef4444", bg: "rgba(239,68,68,0.12)", border: "rgba(239,68,68,0.3)", label: "High Priority" },
  medium: { color: "#f59e0b", bg: "rgba(245,158,11,0.12)", border: "rgba(245,158,11,0.3)", label: "Medium Priority" },
  low: { color: "#6366f1", bg: "rgba(99,102,241,0.12)", border: "rgba(99,102,241,0.3)", label: "Low Priority" },
};

const CATEGORY_ICONS = {
  Skills: "🎯",
  "Language Alignment": "📝",
  "Resume Completeness": "📋",
  Impact: "📈",
  Structure: "🏗️",
  General: "💡",
};

function SuggestionCard({ suggestion, index }) {
  const p = PRIORITY_META[suggestion.priority] || PRIORITY_META.low;
  const icon = CATEGORY_ICONS[suggestion.category] || "💡";

  // Parse backtick-wrapped skill names in description
  const formattedDesc = suggestion.description.replace(
    /`([^`]+)`/g,
    '<code class="inline-code">$1</code>'
  );

  return (
    <div
      className="suggestion-card"
      style={{ "--card-color": p.color, "--card-border": p.border }}
    >
      <div className="suggestion-number">{index + 1}</div>
      <div className="suggestion-body">
        <div className="suggestion-meta">
          <span className="suggestion-icon">{icon}</span>
          <span className="suggestion-category">{suggestion.category}</span>
          <span
            className="priority-badge"
            style={{ background: p.bg, color: p.color, border: `1px solid ${p.border}` }}
          >
            {p.label}
          </span>
        </div>
        <h3 className="suggestion-title">{suggestion.title}</h3>
        <p
          className="suggestion-desc"
          dangerouslySetInnerHTML={{ __html: formattedDesc }}
        />
      </div>
    </div>
  );
}

export default function SuggestionsPanel({ suggestions }) {
  if (!suggestions || suggestions.length === 0) {
    return (
      <div className="suggestions-panel empty">
        <p>🎉 No major improvements needed! Your resume is well-matched.</p>
      </div>
    );
  }

  return (
    <div className="suggestions-panel">
      <div className="suggestions-header">
        <span className="suggestions-count">{suggestions.length} recommendations</span>
      </div>
      <div className="suggestions-list">
        {suggestions.map((s, i) => (
          <SuggestionCard key={i} suggestion={s} index={i} />
        ))}
      </div>
    </div>
  );
}
