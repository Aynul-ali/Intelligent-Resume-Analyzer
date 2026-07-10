import { useState } from "react";

const SAMPLE_JD = `We are looking for a Senior Machine Learning Engineer with 3+ years of experience.

Requirements:
- Strong Python programming skills
- Experience with TensorFlow or PyTorch
- Knowledge of NLP and transformer models
- Familiarity with AWS or GCP cloud platforms
- Experience with Docker and Kubernetes
- Proficient in SQL and NoSQL databases (PostgreSQL, MongoDB)
- Understanding of MLOps practices (CI/CD, model versioning)
- Experience with FastAPI or Flask for model serving
- Strong communication and teamwork skills
- Experience with Git and agile methodologies`;

export default function JobDescriptionInput({ value, onChange, isLoading }) {
  const [showSample, setShowSample] = useState(false);

  const handleUseSample = () => {
    onChange(SAMPLE_JD);
    setShowSample(false);
  };

  const wordCount = value.trim()
    ? value.trim().split(/\s+/).filter(Boolean).length
    : 0;

  return (
    <div className="jd-input">
      <div className="jd-header">
        <p className="jd-hint">
          {wordCount} words{" "}
          {wordCount < 50 && wordCount > 0 && (
            <span className="warn-text">(at least 50 words recommended)</span>
          )}
        </p>
        <button
          className="link-btn"
          onClick={() => setShowSample(!showSample)}
          disabled={isLoading}
        >
          {showSample ? "Hide sample" : "Try a sample JD"}
        </button>
      </div>

      {showSample && (
        <div className="sample-preview">
          <pre className="sample-text">{SAMPLE_JD}</pre>
          <button className="btn-secondary" onClick={handleUseSample}>
            Use This Sample →
          </button>
        </div>
      )}

      <textarea
        className="jd-textarea"
        placeholder="Paste the job description here...&#10;&#10;Include requirements, responsibilities, and any skills mentioned."
        value={value}
        onChange={(e) => onChange(e.target.value)}
        rows={12}
        disabled={isLoading}
        id="job-description"
      />

      <div className="paste-hint">
        <kbd>Ctrl+V</kbd> / <kbd>⌘V</kbd> to paste &nbsp;·&nbsp; Tip: Include
        the full JD for best results
      </div>
    </div>
  );
}
