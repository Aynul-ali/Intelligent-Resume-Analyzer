# ── Stage 1: Build ──────────────────────────────────────────────────────────
FROM python:3.11-slim AS builder

WORKDIR /app

# Install system dependencies for pdfplumber / PyMuPDF
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc g++ libmupdf-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# Download spaCy model
RUN python -m spacy download en_core_web_sm

# Pre-download Sentence-BERT model to bake into image
RUN python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('all-MiniLM-L6-v2')"

# ── Stage 2: Runtime ─────────────────────────────────────────────────────────
FROM python:3.11-slim AS runtime

WORKDIR /app

# Copy installed packages from builder
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin
# Copy spaCy model data
COPY --from=builder /usr/local/lib/python3.11/site-packages/en_core_web_sm /usr/local/lib/python3.11/site-packages/en_core_web_sm
# Copy cached Sentence-BERT model
COPY --from=builder /root/.cache /root/.cache

# Copy backend source
COPY . .

# Copy ml module (needed at runtime)
COPY ../ml /app/../ml

EXPOSE 8000

ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "2"]
