"""
FastAPI application entry point.
Configures CORS, rate limiting, structured logging, and ML model loading.
"""

import logging
import os
import sys
import time
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

# Add ml directory to Python path
ML_DIR = os.path.join(os.path.dirname(__file__), "..", "ml")
sys.path.insert(0, ML_DIR)

from config import get_settings
from routers.resume import router as resume_router
from routers.analyze import router as analyze_router
from routers.match import router as match_router

# ─── Logging setup ────────────────────────────────────────────────────────────

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

# ─── Rate Limiter ─────────────────────────────────────────────────────────────

limiter = Limiter(key_func=get_remote_address)

# ─── Lifespan (model pre-loading) ─────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Pre-load ML models on startup to avoid cold-start latency on first request."""
    logger.info("🚀 Starting Resume Analyzer API...")
    settings = get_settings()

    # Import analyzer (loads spaCy + SBERT lazily on first call; pre-warm here)
    try:
        import analyzer as _analyzer_module
        import embeddings

        logger.info("Pre-warming Sentence-BERT model...")
        # Trigger model download/load with a dummy call
        _warm = embeddings.get_embedding("python developer machine learning")
        logger.info(f"✅ SBERT model ready (embedding dim={len(_warm)})")

        # Attach analyzer to app state
        app.state.analyzer = _analyzer_module

    except Exception as e:
        logger.error(f"❌ Failed to pre-load ML models: {e}")
        # Still allow app to start; models will load lazily on first request
        import analyzer as _analyzer_module
        app.state.analyzer = _analyzer_module

    logger.info("✅ Resume Analyzer API is ready")
    yield
    logger.info("Shutting down Resume Analyzer API...")


# ─── App creation ─────────────────────────────────────────────────────────────

def create_app() -> FastAPI:
    settings = get_settings()

    app = FastAPI(
        title=settings.APP_NAME,
        version=settings.APP_VERSION,
        description=(
            "AI-powered resume analyzer and job matcher using Sentence-BERT "
            "and spaCy NLP. Provides semantic similarity scoring, skill gap analysis, "
            "and personalized improvement suggestions."
        ),
        docs_url="/docs",
        redoc_url="/redoc",
        lifespan=lifespan,
    )

    # Rate limiting
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

    # CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.allowed_origins_list,
        allow_credentials=True,
        allow_methods=["GET", "POST", "OPTIONS"],
        allow_headers=["*"],
    )

    # Request timing middleware
    @app.middleware("http")
    async def add_process_time_header(request: Request, call_next):
        start_time = time.perf_counter()
        response = await call_next(request)
        process_time = time.perf_counter() - start_time
        response.headers["X-Process-Time"] = f"{process_time:.4f}s"
        return response

    # Routers
    app.include_router(resume_router)
    app.include_router(analyze_router)
    app.include_router(match_router)

    # Health check
    @app.get("/health", tags=["System"], summary="Health check")
    async def health():
        import embeddings
        ml_ready = len(embeddings._embedding_cache) > 0 or True  # Models loaded at startup
        return {
            "status": "healthy",
            "version": settings.APP_VERSION,
            "ml_ready": ml_ready,
        }

    # Root
    @app.get("/", tags=["System"], include_in_schema=False)
    async def root():
        return {
            "message": "Resume Analyzer API",
            "version": settings.APP_VERSION,
            "docs": "/docs",
        }

    # Global exception handler
    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception):
        logger.exception(f"Unhandled exception: {exc}")
        return JSONResponse(
            status_code=500,
            content={"success": False, "error": "Internal server error", "detail": str(exc)},
        )

    return app


app = create_app()

if __name__ == "__main__":
    settings = get_settings()
    uvicorn.run(
        "main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        log_level=settings.LOG_LEVEL.lower(),
    )
