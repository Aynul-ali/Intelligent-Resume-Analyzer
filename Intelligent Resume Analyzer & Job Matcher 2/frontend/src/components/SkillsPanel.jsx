const CATEGORY_META = {
  programming_languages: { label: "Languages", emoji: "💻", color: "#6366f1" },
  web_frameworks: { label: "Frameworks", emoji: "🌐", color: "#8b5cf6" },
  databases: { label: "Databases", emoji: "🗄️", color: "#06b6d4" },
  cloud_devops: { label: "Cloud & DevOps", emoji: "☁️", color: "#0ea5e9" },
  data_ml_ai: { label: "Data & AI", emoji: "🤖", color: "#10b981" },
  mobile: { label: "Mobile", emoji: "📱", color: "#f59e0b" },
  soft_skills: { label: "Soft Skills", emoji: "🌟", color: "#ec4899" },
  tools_practices: { label: "Tools", emoji: "🔧", color: "#f97316" },
};

function SkillPill({ skill, variant = "default" }) {
  const colors = {
    default: { bg: "rgba(255,255,255,0.07)", border: "rgba(255,255,255,0.12)", text: "#cbd5e1" },
    matched: { bg: "rgba(16,185,129,0.15)", border: "rgba(16,185,129,0.4)", text: "#10b981" },
    missing: { bg: "rgba(239,68,68,0.12)", border: "rgba(239,68,68,0.35)", text: "#f87171" },
    extra: { bg: "rgba(99,102,241,0.12)", border: "rgba(99,102,241,0.35)", text: "#818cf8" },
  };
  const c = colors[variant] || colors.default;

  return (
    <span
      className="skill-pill"
      style={{ background: c.bg, border: `1px solid ${c.border}`, color: c.text }}
    >
      {skill}
    </span>
  );
}

function SkillColumn({ title, icon, skills, variant, emptyMsg, count }) {
  return (
    <div className="skill-column">
      <div className="skill-col-header">
        <span className="skill-col-icon">{icon}</span>
        <span className="skill-col-title">{title}</span>
        <span className="skill-col-count">{count ?? skills.length}</span>
      </div>
      <div className="skill-pills">
        {skills.length === 0 ? (
          <p className="empty-skills">{emptyMsg}</p>
        ) : (
          skills.map((s) => <SkillPill key={s} skill={s} variant={variant} />)
        )}
      </div>
    </div>
  );
}

export default function SkillsPanel({ resumeSkills, jobSkills, skillGap }) {
  const { matched, missing, extra } = skillGap;

  return (
    <div className="skills-panel">
      <div className="skills-grid">
        <SkillColumn
          title="Your Skills"
          icon="📌"
          skills={resumeSkills.all}
          variant="default"
          emptyMsg="No skills detected in your resume."
          count={resumeSkills.count}
        />
        <SkillColumn
          title="Job Requires"
          icon="🎯"
          skills={jobSkills.all}
          variant="default"
          emptyMsg="No specific skills found in the job description."
          count={jobSkills.count}
        />
      </div>

      <div className="skills-gap-row">
        <SkillColumn
          title="Matched Skills"
          icon="✅"
          skills={matched}
          variant="matched"
          emptyMsg="No overlapping skills found — consider aligning your resume with the role."
        />
        <SkillColumn
          title="Missing Skills"
          icon="⚠️"
          skills={missing}
          variant="missing"
          emptyMsg="Great! No critical skills are missing."
        />
        <SkillColumn
          title="Unique to You"
          icon="✨"
          skills={extra.slice(0, 12)}
          variant="extra"
          emptyMsg="Your skills fully overlap with the job requirements."
        />
      </div>
    </div>
  );
}
