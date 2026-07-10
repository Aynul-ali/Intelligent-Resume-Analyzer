# 🤖 ResumeAI — Intelligent Resume Analyzer & Job Matcher

An AI-powered full-stack web application that analyzes your resume against a job description and provides:
- **Match Score (0–100%)** — blended semantic + skill match
- **Skill Gap Analysis** — extracted, required, matched, and missing skills
- **AI Recommendations** — personalized improvement suggestions

**Stack:** FastAPI · Python · spaCy · Sentence-BERT · React 18 · Vite · Vanilla CSS · Docker

---

## 📁 Project Structure

```
.
├── backend/          # FastAPI REST API
│   ├── main.py       # App entry point
│   ├── config.py     # Settings (pydantic-settings)
│   ├── schemas.py    # Pydantic request/response models
│   ├── pdf_parser.py # PDF text extraction
│   ├── routers/
│   │   ├── resume.py # POST /upload-resume
│   │   ├── analyze.py# POST /analyze
│   │   └── match.py  # POST /match
│   ├── requirements.txt
│   ├── Dockerfile
│   └── .env
├── frontend/         # React + Vite SPA
│   ├── src/
│   │   ├── components/  # UI components
│   │   ├── pages/       # Page layouts
│   │   └── api/         # Axios client
│   ├── Dockerfile
│   └── nginx.conf
├── ml/               # AI/ML logic
│   ├── analyzer.py       # Orchestrator
│   ├── text_preprocessor.py
│   ├── skill_extractor.py
│   ├── embeddings.py     # Sentence-BERT
│   ├── similarity.py     # Cosine similarity
│   └── skill_taxonomy.json
├── docker-compose.yml
└── .env.example
```

---

## ⚡ Quick Start

### Option 1: Docker (Recommended)

```bash
# Clone and enter
git clone <repo-url>
cd resume-analyzer

# Copy env file
cp .env.example backend/.env

# Build and run (first build downloads AI models — ~3 min)
docker-compose up --build

# Access
# Frontend → http://localhost:3000
# Backend API → http://localhost:8000
# API Docs → http://localhost:8000/docs
```

### Option 2: Local Development

#### Backend

```bash
# Create virtual environment
python -m venv venv && source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
cd backend
pip install -r requirements.txt

# Download spaCy model
python -m spacy download en_core_web_sm

# Start the server (from project root)
cd ..
PYTHONPATH=ml uvicorn backend.main:app --reload --port 8000
```

> **Note:** Sentence-BERT (`all-MiniLM-L6-v2`, ~90 MB) auto-downloads on first startup.

#### Frontend

```bash
cd frontend
npm install
npm run dev   # Starts at http://localhost:3000
```

---

## 🔌 API Reference

### `GET /health`
Health check.
```json
{"status": "healthy", "version": "1.0.0", "ml_ready": true}
```

---

### `POST /upload-resume`
Upload a PDF or TXT resume file.

**Request:** `multipart/form-data`
| Field | Type | Description |
|-------|------|-------------|
| `file` | File | PDF or TXT, max 5 MB |

**Response:**
```json
{
  "success": true,
  "filename": "john_doe_resume.pdf",
  "extracted_text": "John Doe\nSoftware Engineer...",
  "word_count": 423,
  "page_count": 2,
  "message": "Resume parsed successfully using pdfplumber."
}
```

**cURL Example:**
```bash
curl -X POST http://localhost:8000/upload-resume \
  -F "file=@/path/to/resume.pdf"
```

---

### `POST /analyze`
Full AI analysis of resume vs job description.

**Request:**
```json
{
  "resume_text": "Python developer with 5 years experience in FastAPI, PostgreSQL...",
  "job_description": "We are hiring a Senior Backend Engineer with Python, AWS, Docker..."
}
```

**Response:**
```json
{
  "success": true,
  "match_score": 73.4,
  "score_breakdown": {
    "semantic_similarity": 78.1,
    "skill_match_percentage": 66.7,
    "skills_section_score": 80.2,
    "experience_section_score": 71.5
  },
  "resume_skills": {
    "all": ["python", "fastapi", "postgresql", "docker"],
    "by_category": {"web_frameworks": ["fastapi"], "databases": ["postgresql"]},
    "count": 4
  },
  "job_skills": {
    "all": ["python", "aws", "docker", "kubernetes", "postgresql"],
    "by_category": {"cloud_devops": ["aws", "docker", "kubernetes"]},
    "count": 5
  },
  "skill_gap": {
    "matched": ["docker", "postgresql", "python"],
    "missing": ["aws", "kubernetes"],
    "extra": ["fastapi"],
    "matched_count": 3,
    "missing_count": 2
  },
  "suggestions": [
    {
      "priority": "high",
      "category": "Skills",
      "title": "Add 2 missing skills to your resume",
      "description": "The job requires: `aws`, `kubernetes`. Include these in your skills section..."
    }
  ],
  "metadata": {"resume_word_count": 312, "job_word_count": 187}
}
```

**cURL Example:**
```bash
curl -X POST http://localhost:8000/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "resume_text": "Python developer with FastAPI experience...",
    "job_description": "We need a Python backend engineer with AWS and Docker skills..."
  }'
```

---

### `POST /match`
Quick match — returns score + top skills + 3 suggestions.

**Request:** Same as `/analyze`

**Response:**
```json
{
  "success": true,
  "match_score": 73.4,
  "score_breakdown": { "..." },
  "matched_skills": ["docker", "python"],
  "missing_skills": ["aws", "kubernetes"],
  "top_suggestions": [{ "..." }]
}
```

---

## 🧠 ML Architecture

```
Resume Text ──┐
              ├──► Text Preprocessor ──► Skill Extractor ──► Skill Gap
Job Desc   ──┘         │                                         │
                       │                                         ▼
                       └──► Sentence-BERT Embeddings ──► Cosine Similarity
                                                              │
                                                              ▼
                                                    Weighted Score (0-100)
                                                       ↓40%  ↓40%  ↓20%
                                                    Semantic Skills  Exp
```

**Scoring Formula:**
```
final_score = semantic_score × 0.60 + skill_match_pct × 0.40
```

Where `semantic_score` = `overall_semantic × 0.40 + skills_section × 0.40 + experience_section × 0.20`

---

## ☁️ Cloud Deployment

### AWS (ECS + ECR)

```bash
# Build and push images
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin <account>.dkr.ecr.us-east-1.amazonaws.com

docker build -t resume-backend ./backend
docker tag resume-backend:latest <account>.dkr.ecr.us-east-1.amazonaws.com/resume-backend:latest
docker push <account>.dkr.ecr.us-east-1.amazonaws.com/resume-backend:latest

# Deploy using ECS task definition (add your task-definition.json)
aws ecs update-service --cluster resume-cluster --service backend --force-new-deployment
```

### GCP (Cloud Run)

```bash
gcloud builds submit --tag gcr.io/<project>/resume-backend ./backend
gcloud run deploy resume-backend \
  --image gcr.io/<project>/resume-backend \
  --platform managed \
  --region us-central1 \
  --memory 2Gi \
  --timeout 120
```

---

## 🔧 Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `DEBUG` | `false` | Enable debug mode + hot reload |
| `ALLOWED_ORIGINS` | `http://localhost:3000` | Comma-separated CORS origins |
| `MAX_FILE_SIZE_MB` | `5` | Max upload size in MB |
| `RATE_LIMIT` | `20/minute` | API rate limit per IP |
| `SBERT_MODEL` | `all-MiniLM-L6-v2` | Sentence-BERT model name |
| `LOG_LEVEL` | `INFO` | Logging level |

---

## 🧪 Running Tests

```bash
# Backend smoke test
cd backend
python -c "
import sys; sys.path.insert(0, '../ml')
from analyzer import analyze
result = analyze(
    'Python developer with 3 years experience. Skills: Python, FastAPI, PostgreSQL, Docker.',
    'We need a Python engineer with FastAPI, AWS, Docker, and Kubernetes.'
)
print(f'Score: {result[\"match_score\"]}%')
print(f'Missing: {result[\"skill_gap\"][\"missing\"]}')
"
```

---

## 📝 License

MIT
