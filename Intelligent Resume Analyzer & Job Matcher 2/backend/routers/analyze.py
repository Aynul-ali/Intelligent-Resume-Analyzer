"""
Analyze router — full resume analysis pipeline.
POST /analyze
"""

import logging

from fastapi import APIRouter, HTTPException, Request
from schemas import AnalyzeRequest, AnalyzeResponse, ErrorResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/analyze", tags=["Analysis"])


@router.post(
    "",
    response_model=AnalyzeResponse,
    responses={422: {"model": ErrorResponse}, 500: {"model": ErrorResponse}},
    summary="Analyze resume against job description",
)
async def analyze_resume(request_data: AnalyzeRequest, request: Request) -> AnalyzeResponse:
    """
    Full AI-powered analysis:
    - Semantic similarity scoring via Sentence-BERT
    - Skill extraction and gap analysis
    - Personalized improvement suggestions
    """
    analyzer = request.app.state.analyzer

    try:
        result = analyzer.analyze(
            resume_text=request_data.resume_text,
            job_description=request_data.job_description,
        )
    except Exception as e:
        logger.exception("Analysis pipeline failed")
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")

    return AnalyzeResponse(
        success=True,
        match_score=result["match_score"],
        score_breakdown=result["score_breakdown"],
        resume_skills=result["resume_skills"],
        job_skills=result["job_skills"],
        skill_gap=result["skill_gap"],
        suggestions=result["suggestions"],
        metadata=result["metadata"],
    )
