import { useState, useCallback } from "react";

const MAX_FILE_SIZE = 5 * 1024 * 1024; // 5MB

export default function ResumeUploader({ onTextExtracted, isLoading }) {
  const [dragActive, setDragActive] = useState(false);
  const [fileName, setFileName] = useState(null);
  const [error, setError] = useState(null);
  const [textMode, setTextMode] = useState(false);
  const [pastedText, setPastedText] = useState("");

  const validateFile = (file) => {
    if (!file) return "No file selected.";
    if (file.size > MAX_FILE_SIZE) return `File too large. Max size is 5 MB.`;
    const ext = file.name.split(".").pop().toLowerCase();
    if (!["pdf", "txt"].includes(ext))
      return "Only PDF and TXT files are supported.";
    return null;
  };

  const handleFile = useCallback(
    (file) => {
      const err = validateFile(file);
      if (err) {
        setError(err);
        return;
      }
      setError(null);
      setFileName(file.name);
      onTextExtracted({ type: "file", file });
    },
    [onTextExtracted]
  );

  const handleDrop = useCallback(
    (e) => {
      e.preventDefault();
      setDragActive(false);
      const file = e.dataTransfer.files?.[0];
      if (file) handleFile(file);
    },
    [handleFile]
  );

  const handleChange = (e) => {
    const file = e.target.files?.[0];
    if (file) handleFile(file);
  };

  const handlePasteSubmit = () => {
    if (pastedText.trim().length < 50) {
      setError("Please paste at least 50 characters of resume text.");
      return;
    }
    setError(null);
    setFileName(`Pasted text (${pastedText.split(" ").length} words)`);
    onTextExtracted({ type: "text", text: pastedText.trim() });
  };

  return (
    <div className="resume-uploader">
      <div className="mode-toggle">
        <button
          className={`toggle-btn ${!textMode ? "active" : ""}`}
          onClick={() => setTextMode(false)}
        >
          📎 Upload File
        </button>
        <button
          className={`toggle-btn ${textMode ? "active" : ""}`}
          onClick={() => setTextMode(true)}
        >
          ✏️ Paste Text
        </button>
      </div>

      {!textMode ? (
        <label
          className={`drop-zone ${dragActive ? "drag-active" : ""} ${
            fileName ? "has-file" : ""
          } ${isLoading ? "disabled" : ""}`}
          onDragEnter={() => setDragActive(true)}
          onDragLeave={() => setDragActive(false)}
          onDragOver={(e) => e.preventDefault()}
          onDrop={handleDrop}
        >
          <input
            type="file"
            accept=".pdf,.txt"
            onChange={handleChange}
            disabled={isLoading}
            style={{ display: "none" }}
          />
          <div className="drop-zone-content">
            {fileName ? (
              <>
                <div className="file-icon">✅</div>
                <p className="file-name">{fileName}</p>
                <p className="file-hint">Click or drop to replace</p>
              </>
            ) : (
              <>
                <div className="file-icon">📄</div>
                <p className="drop-title">Drop your resume here</p>
                <p className="drop-subtitle">
                  or <span className="link-text">browse to upload</span>
                </p>
                <p className="file-hint">PDF or TXT · Max 5 MB</p>
              </>
            )}
          </div>
        </label>
      ) : (
        <div className="text-paste-area">
          <textarea
            className="paste-textarea"
            placeholder="Paste your resume text here..."
            value={pastedText}
            onChange={(e) => setPastedText(e.target.value)}
            rows={10}
            disabled={isLoading}
          />
          <div className="paste-footer">
            <span className="char-count">{pastedText.split(/\s+/).filter(Boolean).length} words</span>
            <button
              className="btn-primary"
              onClick={handlePasteSubmit}
              disabled={isLoading || pastedText.trim().length < 50}
            >
              Use This Text →
            </button>
          </div>
        </div>
      )}

      {error && <p className="error-msg">⚠️ {error}</p>}
    </div>
  );
}
