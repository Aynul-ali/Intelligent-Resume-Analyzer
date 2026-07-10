"""
Application configuration using pydantic-settings.
Reads from environment variables and .env file.
"""

from functools import lru_cache
from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    # Application
    APP_NAME: str = "Resume Analyzer API"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False

    # Server
    HOST: str = "0.0.0.0"
    PORT: int = 8000

    # CORS — comma-separated origins
    ALLOWED_ORIGINS: str = "http://localhost:3000,http://localhost:5173"

    # File upload
    MAX_FILE_SIZE_MB: int = 5
    UPLOAD_DIR: str = "/tmp/resume_uploads"

    # Rate limiting (requests per minute)
    RATE_LIMIT: str = "20/minute"

    # ML model
    SBERT_MODEL: str = "all-MiniLM-L6-v2"

    # Logging
    LOG_LEVEL: str = "INFO"

    @property
    def allowed_origins_list(self) -> list[str]:
        return [o.strip() for o in self.ALLOWED_ORIGINS.split(",") if o.strip()]

    @property
    def max_file_size_bytes(self) -> int:
        return self.MAX_FILE_SIZE_MB * 1024 * 1024

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    """Return cached settings singleton."""
    return Settings()
