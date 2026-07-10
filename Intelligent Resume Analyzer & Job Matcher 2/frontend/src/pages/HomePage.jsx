import { useState, useRef } from "react";
import { api } from "../api/client";
import ResumeUploader from "../components/ResumeUploader";
import JobDescriptionInput from "../components/JobDescriptionInput";
import MatchScoreCard from "../components/MatchScoreCard";
import SkillsPanel from "../components/SkillsPanel";
import SuggestionsPanel from "../components/SuggestionsPanel";

const STEPS = { INPUT: "input", LOADING: "loading", RESULTS: "results" };

export default function HomePage() {
  const [step, setStep] = useState(STEPS.INPUT);
  const [resumeInput, setResumeInput] = useState(null); // { type: "file"|"text", file?, text? }
  const [jobDescription, setJobDescription] = useState("");
  const [results, setResults] = useState(null);
  const [error, setError] = useState(null);
  const [loadingMsg, setLoadingMsg] = useState("Initializing AI models...");
  const resultsRef = useRef(null);

  const canAnalyze = resumeInput && jobDescription.trim().length >= 50;

  const handleAnalyze = async () => {
    if (!canAnalyze) return;
    setError(null);
    setStep(STEPS.LOADING);

    try {
      let resumeText = "";

      // Step 1: Get resume text
      if (resumeInput.type === "file") {
        setLoadingMsg("Extracting text from your resume...");
        const uploadRes = await api.uploadResume(resumeInput.file);
        resumeText = uploadRes.extracted_text;
      } else {
        resumeText = resumeInput.text;
      }

      // Step 2: Run analysis
      setLoadingMsg("Running semantic analysis with Sentence-BERT...");
      const analysisRes = await api.analyze(resumeText, jobDescription);

      setResults(analysisRes);
      setStep(STEPS.RESULTS);

      // Scroll to results
      setTimeout(() => {
        resultsRef.current?.scrollIntoView({ behavior: "smooth" });
      }, 100);
    } catch (err) {
      setError(err.message || "Analysis failed. Please try again.");
      setStep(STEPS.INPUT);
    }
  };

  const handleReset = () => {
    setStep(STEPS.INPUT);
    setResults(null);
    setError(null);
    setResumeInput(null);
    setJobDescription("");
    window.scrollTo({ top: 0, behavior: "smooth" });
  };

  return (
    <div className="page">
      {/* ── Hero ── */}
      <header className="hero">
        <div className="hero-badge">✨ Powered by Sentence-BERT + spaCy</div>
        <h1 className="hero-title">
          AI Resume <span className="gradient-text">Analyzer</span>
          <br />& Job Matcher
        </h1>
        <p className="hero-subtitle">
          Get your match score, identify skill gaps, and receive personalized
          AI-powered recommendations to land your dream job.
        </p>
        <div className="hero-features">
          <span className="feature-chip">🎯 Semantic Scoring</span>
          <span className="feature-chip">🔍 Skill Gap Analysis</span>
          <span className="feature-chip">🤖 AI Suggestions</span>
          <span className="feature-chip">📊 Score Breakdown</span>
        </div>
      </header>

      {/* ── Input Section ── */}
      {(step === STEPS.INPUT || step === STEPS.LOADING) && (
        <section className="input-section">
          <div className="input-grid">
            {/* Resume Upload */}
            <div className="card">
              <div className="card-header">
                <span className="step-badge">1</span>
                <h2 className="card-title">Upload Your Resume</h2>
              </div>
              <ResumeUploader
                onTextExtracted={setResumeInput}
                isLoading={step === STEPS.LOADING}
              />
              {resumeInput && (
                <div className="input-ready">
                  <span className="ready-dot" />
                  Resume ready
                </div>
              )}
            </div>

            {/* Job Description */}
            <div className="card">
              <div className="card-header">
                <span className="step-badge">2</span>
                <h2 className="card-title">Paste Job Description</h2>
              </div>
              <JobDescriptionInput
                value={jobDescription}
                onChange={setJobDescription}
                isLoading={step === STEPS.LOADING}
              />
            </div>
          </div>

          {error && (
            <div className="error-banner">
              <span>⚠️</span>
              <span>{error}</span>
            </div>
          )}

          {step === STEPS.LOADING ? (
            <div className="loading-state">
              <div className="spinner" />
              <p className="loading-msg">{loadingMsg}</p>
              <p className="loading-hint">
                First-run may take 30–60 seconds while the AI model loads.
              </p>
            </div>
          ) : (
            <div className="cta-row">
              <button
                className="btn-analyze"
                onClick={handleAnalyze}
                disabled={!canAnalyze}
                id="analyze-btn"
              >
                <span>🚀</span>
                Analyze My Resume
              </button>
              {!canAnalyze && (
                <p className="cta-hint">
                  {!resumeInput
                    ? "Upload your resume to get started"
                    : "Paste a job description (at least 50 words)"}
                </p>
              )}
            </div>
          )}
        </section>
      )}

      {/* ── Results Section ── */}
      {step === STEPS.RESULTS && results && (
        <section className="results-section" ref={resultsRef}>
          <div className="results-header">
            <h2 className="results-title">Analysis Results</h2>
            <button className="btn-secondary" onClick={handleReset}>
              ← Analyze Another
            </button>
          </div>

          {/* Score Card */}
          <div className="results-score-row">
            <div className="card score-card-wrapper">
              <h3 className="section-label">Match Score</h3>
              <MatchScoreCard
                score={results.match_score}
                breakdown={results.score_breakdown}
              />
            </div>

            <div className="card stats-card">
              <h3 className="section-label">Quick Stats</h3>
              <div className="stats-grid">
                <Stat label="Resume Skills" value={results.resume_skills.count} icon="📌" />
                <Stat label="Job Skills" value={results.job_skills.count} icon="🎯" />
                <Stat label="Matched" value={results.skill_gap.matched_count} icon="✅" color="#10b981" />
                <Stat label="Missing" value={results.skill_gap.missing_count} icon="⚠️" color="#ef4444" />
                <Stat label="Resume Words" value={results.metadata.resume_word_count} icon="📄" />
                <Stat label="JD Words" value={results.metadata.job_word_count} icon="📋" />
              </div>
            </div>
          </div>

          {/* Skills Panel */}
          <div className="card">
            <h3 className="section-label">Skill Analysis</h3>
            <SkillsPanel
              resumeSkills={results.resume_skills}
              jobSkills={results.job_skills}
              skillGap={results.skill_gap}
            />
          </div>

          {/* Suggestions */}
          <div className="card">
            <h3 className="section-label">
              🤖 AI-Powered Recommendations
            </h3>
            <SuggestionsPanel suggestions={results.suggestions} />
          </div>
        </section>
      )}

      {/* ── Footer ── */}
      <footer className="footer">
        <p>
          Built with <span className="gradient-text">Sentence-BERT + spaCy + FastAPI + React</span>
        </p>
      </footer>
    </div>
  );
}

function Stat({ label, value, icon, color }) {
  return (
    <div className="stat-item">
      <span className="stat-icon">{icon}</span>
      <span className="stat-value" style={{ color: color || "inherit" }}>
        {value}
      </span>
      <span className="stat-label">{label}</span>
    </div>
  );
}
