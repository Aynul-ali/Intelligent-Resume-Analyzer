"""
Pydantic schemas for all request/response models.
Provides strict validation and clear API contracts.
"""

from typing import Any, Optional
from pydantic import BaseModel, Field, validator


# ─── Upload Resume ─────────────────────────────────────────────────────────────

class ResumeUploadResponse(BaseModel):
    success: bool
    filename: str
    extracted_text: str
    word_count: int
    page_count: int
    message: str


# ─── Analyze ──────────────────────────────────────────────────────────────────

class AnalyzeRequest(BaseModel):
    resume_text: str = Field(..., min_length=50, description="Extracted resume text")
    job_description: str = Field(..., min_length=50, description="Job description text")

    @validator("resume_text", "job_description")
    def must_not_be_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Field must not be blank")
        return v.strip()


class SkillsDetail(BaseModel):
    all: list[str]
    by_category: dict[str, list[str]]
    count: int


class SkillGap(BaseModel):
    matched: list[str]
    missing: list[str]
    extra: list[str]
    matched_count: int
    missing_count: int


class ScoreBreakdown(BaseModel):
    semantic_similarity: float
    skill_match_percentage: float
    skills_section_score: float
    experience_section_score: float


class Suggestion(BaseModel):
    priority: str  # "high" | "medium" | "low"
    category: str
    title: str
    description: str


class Metadata(BaseModel):
    resume_word_count: int
    job_word_count: int


class AnalyzeResponse(BaseModel):
    success: bool = True
    match_score: float = Field(..., ge=0, le=100, description="Overall match score 0-100")
    score_breakdown: ScoreBreakdown
    resume_skills: SkillsDetail
    job_skills: SkillsDetail
    skill_gap: SkillGap
    suggestions: list[Suggestion]
    metadata: Metadata


# ─── Match (simple) ───────────────────────────────────────────────────────────

class MatchRequest(BaseModel):
    resume_text: str = Field(..., min_length=50)
    job_description: str = Field(..., min_length=50)

    @validator("resume_text", "job_description")
    def must_not_be_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Field must not be blank")
        return v.strip()


class MatchResponse(BaseModel):
    success: bool = True
    match_score: float
    score_breakdown: ScoreBreakdown
    matched_skills: list[str]
    missing_skills: list[str]
    top_suggestions: list[Suggestion]


# ─── Health ───────────────────────────────────────────────────────────────────

class HealthResponse(BaseModel):
    status: str
    version: str
    ml_ready: bool


# ─── Error ────────────────────────────────────────────────────────────────────

class ErrorResponse(BaseModel):
    success: bool = False
    error: str
    detail: Optional[str] = None
