"""
Main analyzer orchestrator — coordinates preprocessing, skill extraction,
embedding, similarity scoring, and generates personalized suggestions.
"""

import logging
from typing import Any

from text_preprocessor import preprocess
from skill_extractor import extract_skills, get_skill_importance
from similarity import compute_similarity, compute_skill_gap

logger = logging.getLogger(__name__)


def _generate_suggestions(
    missing_skills: list[str],
    skill_gap: dict,
    similarity_scores: dict,
    resume_text: str,
) -> list[dict]:
    """
    Generate personalized improvement suggestions based on analysis results.

    Returns a list of suggestion dicts with:
      - priority: "high" | "medium" | "low"
      - category: str
      - title: str
      - description: str
    """
    suggestions = []
    overall_score = similarity_scores.get("overall_score", 0)
    missing_count = len(missing_skills)

    # --- Skill gap suggestions ---
    if missing_count > 0:
        top_missing = missing_skills[:5]
        skill_list = ", ".join(f"`{s}`" for s in top_missing)
        suggestions.append({
            "priority": "high" if missing_count > 5 else "medium",
            "category": "Skills",
            "title": f"Add {missing_count} missing skill{'s' if missing_count > 1 else ''} to your resume",
            "description": (
                f"The job description requires skills you haven't listed: {skill_list}. "
                "Include these in your skills section and, where possible, demonstrate them in your work experience bullet points."
            ),
        })

    # --- Low semantic similarity ---
    if overall_score < 50:
        suggestions.append({
            "priority": "high",
            "category": "Language Alignment",
            "title": "Mirror the job description language",
            "description": (
                "Your resume's wording differs significantly from the job description. "
                "Identify 5-10 key phrases from the JD and naturally incorporate them into your experience descriptions and summary."
            ),
        })
    elif overall_score < 70:
        suggestions.append({
            "priority": "medium",
            "category": "Language Alignment",
            "title": "Improve keyword alignment with the role",
            "description": (
                "Tailor your professional summary and experience bullets to use terminology "
                "from the job posting. Focus on matching the specific tech stack and responsibilities mentioned."
            ),
        })

    # --- Skills section completeness ---
    resume_skill_count = skill_gap.get("resume_skill_count", 0)
    if resume_skill_count < 8:
        suggestions.append({
            "priority": "medium",
            "category": "Resume Completeness",
            "title": "Expand your skills section",
            "description": (
                f"Only {resume_skill_count} skills were detected on your resume. "
                "A comprehensive skills section (15-25 skills) significantly improves both ATS ranking and recruiter confidence."
            ),
        })

    # --- Quantification prompt ---
    import re
    quantity_pattern = r"\b\d+%|\b\d+x\b|\$\d+|\d+ (users|customers|million|thousand|team)"
    has_numbers = bool(re.search(quantity_pattern, resume_text, re.IGNORECASE))
    if not has_numbers:
        suggestions.append({
            "priority": "high",
            "category": "Impact",
            "title": "Quantify your achievements",
            "description": (
                "No measurable results were found in your resume. Add quantified achievements "
                '(e.g., "Reduced load time by 40%", "Grew user base from 10K to 100K") to make a stronger impression.'
            ),
        })

    # --- Missing common resume sections ---
    lower_resume = resume_text.lower()
    if "summary" not in lower_resume and "objective" not in lower_resume and "profile" not in lower_resume:
        suggestions.append({
            "priority": "medium",
            "category": "Structure",
            "title": "Add a professional summary",
            "description": (
                "A 3-4 sentence professional summary at the top of your resume immediately communicates your value. "
                "Tailor it to highlight why you are the ideal candidate for this specific role."
            ),
        })

    if len(suggestions) < 3:
        suggestions.append({
            "priority": "low",
            "category": "General",
            "title": "Keep your resume concise and ATS-friendly",
            "description": (
                "Ensure your resume is 1-2 pages, uses a clean single-column format with standard section headings, "
                "and avoids tables, graphics, or unusual fonts that may confuse applicant tracking systems."
            ),
        })

    # Sort: high → medium → low
    priority_order = {"high": 0, "medium": 1, "low": 2}
    suggestions.sort(key=lambda x: priority_order.get(x["priority"], 2))

    return suggestions[:6]  # Cap at 6 suggestions


def analyze(resume_text: str, job_description: str) -> dict[str, Any]:
    """
    Full analysis pipeline:
    1. Preprocess both texts
    2. Extract skills from both
    3. Compute semantic similarity
    4. Compute skill gap
    5. Rank missing skills by JD importance
    6. Generate personalized suggestions

    Args:
        resume_text: Raw or extracted resume text
        job_description: Raw job description text

    Returns:
        Comprehensive analysis dict
    """
    logger.info("Starting resume analysis pipeline")

    # Step 1: Preprocess
    resume_processed = preprocess(resume_text)
    job_processed = preprocess(job_description)

    resume_clean = resume_processed["cleaned_text"]
    job_clean = job_processed["cleaned_text"]

    logger.info(
        f"Preprocessed: resume={resume_processed['word_count']} words, "
        f"job={job_processed['word_count']} words"
    )

    # Step 2: Extract skills
    resume_skills_data = extract_skills(resume_clean)
    job_skills_data = extract_skills(job_clean)

    resume_skills = resume_skills_data["skills"]
    job_skills = job_skills_data["skills"]

    logger.info(f"Skills found: resume={len(resume_skills)}, job={len(job_skills)}")

    # Step 3: Semantic similarity (embedding-based)
    similarity_scores = compute_similarity(resume_clean, job_clean)

    # Step 4: Skill gap analysis
    skill_gap = compute_skill_gap(resume_skills, job_skills)

    # Step 5: Rank missing skills by importance in job description
    missing_skills = skill_gap["missing_skills"]
    if missing_skills:
        importance_map = get_skill_importance(missing_skills, job_clean)
        missing_skills_ranked = sorted(
            missing_skills,
            key=lambda s: importance_map.get(s, 0),
            reverse=True,
        )
    else:
        missing_skills_ranked = []

    # Step 6: Generate suggestions
    suggestions = _generate_suggestions(
        missing_skills_ranked, skill_gap, similarity_scores, resume_clean
    )

    # Compute blended final score
    # 60% semantic similarity + 40% skill match overlap
    skill_match_pct = skill_gap["skill_match_percentage"]
    semantic_score = similarity_scores["overall_score"]
    final_score = round(semantic_score * 0.60 + skill_match_pct * 0.40, 1)

    logger.info(
        f"Analysis complete: score={final_score}, "
        f"matched={skill_gap['matched_count']}, missing={skill_gap['missing_count']}"
    )

    return {
        "match_score": final_score,
        "score_breakdown": {
            "semantic_similarity": semantic_score,
            "skill_match_percentage": skill_match_pct,
            "skills_section_score": similarity_scores["skills_score"],
            "experience_section_score": similarity_scores["experience_score"],
        },
        "resume_skills": {
            "all": resume_skills,
            "by_category": resume_skills_data["skills_by_category"],
            "count": len(resume_skills),
        },
        "job_skills": {
            "all": job_skills,
            "by_category": job_skills_data["skills_by_category"],
            "count": len(job_skills),
        },
        "skill_gap": {
            "matched": skill_gap["matched_skills"],
            "missing": missing_skills_ranked,
            "extra": skill_gap["extra_skills"],
            "matched_count": skill_gap["matched_count"],
            "missing_count": skill_gap["missing_count"],
        },
        "suggestions": suggestions,
        "metadata": {
            "resume_word_count": resume_processed["word_count"],
            "job_word_count": job_processed["word_count"],
        },
    }
