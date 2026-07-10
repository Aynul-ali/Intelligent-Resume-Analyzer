"""
Match router — simplified match endpoint returning score + top skills.
POST /match
"""

import logging

from fastapi import APIRouter, HTTPException, Request
from schemas import MatchRequest, MatchResponse, ErrorResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/match", tags=["Matching"])


@router.post(
    "",
    response_model=MatchResponse,
    responses={422: {"model": ErrorResponse}, 500: {"model": ErrorResponse}},
    summary="Quick resume-job match scoring",
)
async def match_resume(request_data: MatchRequest, request: Request) -> MatchResponse:
    """
    Lightweight match endpoint returning:
    - Overall match score (0-100)
    - Score breakdown
    - Matched and missing skills
    - Top 3 improvement suggestions
    """
    analyzer = request.app.state.analyzer

    try:
        result = analyzer.analyze(
            resume_text=request_data.resume_text,
            job_description=request_data.job_description,
        )
    except Exception as e:
        logger.exception("Match pipeline failed")
        raise HTTPException(status_code=500, detail=f"Match failed: {str(e)}")

    return MatchResponse(
        success=True,
        match_score=result["match_score"],
        score_breakdown=result["score_breakdown"],
        matched_skills=result["skill_gap"]["matched"],
        missing_skills=result["skill_gap"]["missing"],
        top_suggestions=result["suggestions"][:3],
    )
