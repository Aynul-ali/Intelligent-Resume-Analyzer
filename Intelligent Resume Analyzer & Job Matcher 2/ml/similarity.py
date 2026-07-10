"""
Semantic similarity scoring between resume and job description.
Uses cosine similarity on Sentence-BERT embeddings with section weighting.
"""

import re
from typing import Optional

import numpy as np
from sklearn.metrics.pairwise import cosine_similarity

from embeddings import get_embedding, get_batch_embeddings


def cosine_sim(vec_a: np.ndarray, vec_b: np.ndarray) -> float:
    """
    Compute cosine similarity between two 1D vectors.

    Returns:
        Float in [0, 1] (embeddings are L2-normalized by SBERT)
    """
    if vec_a is None or vec_b is None:
        return 0.0
    if np.all(vec_a == 0) or np.all(vec_b == 0):
        return 0.0

    # Already normalized → dot product == cosine similarity
    score = float(np.dot(vec_a, vec_b))
    # Clamp to [0, 1] to handle floating point edge cases
    return max(0.0, min(1.0, score))


def _extract_section(text: str, section_keywords: list[str], max_lines: int = 30) -> str:
    """
    Heuristically extract a section from resume/JD text by keyword headers.
    Falls back to returning a chunk of the full text if not found.
    """
    lines = text.split("\n")
    section_start = None

    for i, line in enumerate(lines):
        line_lower = line.lower().strip()
        if any(kw in line_lower for kw in section_keywords):
            if len(line_lower) < 60:  # Likely a heading, not body text
                section_start = i + 1
                break

    if section_start is not None:
        section_lines = lines[section_start : section_start + max_lines]
        return "\n".join(section_lines)

    # Fallback: return first 500 chars of text
    return text[:500]


def compute_similarity(resume_text: str, job_text: str) -> dict:
    """
    Compute multi-dimensional similarity between resume and job description.

    Scoring breakdown:
    - Overall semantic similarity: 40%
    - Skills section match: 40%
    - Experience/education match: 20%

    Args:
        resume_text: Cleaned resume text
        job_text: Cleaned job description text

    Returns:
        Dict with:
          - overall_score: float (0-100)
          - semantic_score: float (0-100)
          - skills_score: float (0-100)
          - experience_score: float (0-100)
          - component_scores: dict of individual scores
    """
    if not resume_text or not job_text:
        return {
            "overall_score": 0.0,
            "semantic_score": 0.0,
            "skills_score": 0.0,
            "experience_score": 0.0,
        }

    # 1. Full document semantic similarity
    resume_emb = get_embedding(resume_text)
    job_emb = get_embedding(job_text)
    semantic_score = cosine_sim(resume_emb, job_emb)

    # 2. Skills section similarity
    resume_skills_text = _extract_section(
        resume_text, ["skill", "technical", "competencies", "expertise", "technologies"]
    )
    job_skills_text = _extract_section(
        job_text, ["skill", "requirement", "qualification", "must have", "you will"]
    )

    if resume_skills_text and job_skills_text:
        resume_skills_emb = get_embedding(resume_skills_text)
        job_skills_emb = get_embedding(job_skills_text)
        skills_score = cosine_sim(resume_skills_emb, job_skills_emb)
    else:
        skills_score = semantic_score * 0.8  # Fallback

    # 3. Experience section similarity
    resume_exp_text = _extract_section(
        resume_text, ["experience", "work", "employment", "career", "history"]
    )
    job_exp_text = _extract_section(
        job_text, ["experience", "responsibility", "role", "duties", "what you'll"]
    )

    if resume_exp_text and job_exp_text:
        resume_exp_emb = get_embedding(resume_exp_text)
        job_exp_emb = get_embedding(job_exp_text)
        experience_score = cosine_sim(resume_exp_emb, job_exp_emb)
    else:
        experience_score = semantic_score * 0.7  # Fallback

    # Weighted final score
    overall = (
        semantic_score * 0.40
        + skills_score * 0.40
        + experience_score * 0.20
    )

    return {
        "overall_score": round(overall * 100, 1),
        "semantic_score": round(semantic_score * 100, 1),
        "skills_score": round(skills_score * 100, 1),
        "experience_score": round(experience_score * 100, 1),
    }


def compute_skill_gap(resume_skills: list[str], job_skills: list[str]) -> dict:
    """
    Compare resume skills against job requirements to find missing skills
    and compute a skill-based match score.

    Args:
        resume_skills: Skills extracted from resume
        job_skills: Skills required by job description

    Returns:
        Dict with matched, missing, extra skills and skill match percentage
    """
    resume_set = {s.lower() for s in resume_skills}
    job_set = {s.lower() for s in job_skills}

    matched = sorted(resume_set.intersection(job_set))
    missing = sorted(job_set - resume_set)
    extra = sorted(resume_set - job_set)

    skill_match_pct = (len(matched) / len(job_set) * 100) if job_set else 0.0

    return {
        "matched_skills": matched,
        "missing_skills": missing,
        "extra_skills": extra,
        "skill_match_percentage": round(skill_match_pct, 1),
        "resume_skill_count": len(resume_set),
        "job_skill_count": len(job_set),
        "matched_count": len(matched),
        "missing_count": len(missing),
    }
