"""
Skill extraction module using spaCy NER + taxonomy keyword matching.
Supports multi-word skill phrases and fuzzy matching.
"""

import json
import os
import re
from functools import lru_cache
from pathlib import Path
from typing import Optional

import spacy

_TAXONOMY_PATH = Path(__file__).parent / "skill_taxonomy.json"

# Lazy-loaded resources
_nlp: Optional[spacy.language.Language] = None
_taxonomy: Optional[dict] = None
_flat_skills: Optional[list[tuple[str, str]]] = None  # (skill, category)


def _get_nlp() -> spacy.language.Language:
    global _nlp
    if _nlp is None:
        try:
            _nlp = spacy.load("en_core_web_sm")
        except OSError:
            _nlp = spacy.blank("en")
    return _nlp


def _get_taxonomy() -> tuple[dict, list[tuple[str, str]]]:
    """Load and cache the skill taxonomy."""
    global _taxonomy, _flat_skills
    if _taxonomy is None:
        with open(_TAXONOMY_PATH, "r") as f:
            _taxonomy = json.load(f)
        # Flatten to (skill, category) pairs, sorted by length desc for greedy match
        _flat_skills = []
        for category, skills in _taxonomy.items():
            for skill in skills:
                _flat_skills.append((skill.lower(), category))
        _flat_skills.sort(key=lambda x: len(x[0]), reverse=True)
    return _taxonomy, _flat_skills


def extract_skills(text: str) -> dict:
    """
    Extract skills from text using multi-strategy approach:
    1. Taxonomy keyword matching (multi-word phrases first)
    2. spaCy NER for ORG/PRODUCT entities that may be tech tools

    Args:
        text: Cleaned text to extract skills from

    Returns:
        Dict with:
          - skills: list of unique identified skill names
          - skills_by_category: dict mapping category -> list of skills
          - entities: raw NER entities found
    """
    if not text:
        return {"skills": [], "skills_by_category": {}, "entities": []}

    _, flat_skills = _get_taxonomy()
    text_lower = text.lower()

    found: dict[str, str] = {}  # skill -> category

    # Strategy 1: Taxonomy matching (multi-word phrases prioritized by length)
    used_positions: set[int] = set()
    for skill, category in flat_skills:
        # Use word-boundary regex for accurate matching
        pattern = r"(?<!\w)" + re.escape(skill) + r"(?!\w)"
        for match in re.finditer(pattern, text_lower):
            start, end = match.start(), match.end()
            # Ensure no overlap with already-matched spans
            positions = set(range(start, end))
            if not positions.intersection(used_positions):
                found[skill] = category
                used_positions.update(positions)

    # Strategy 2: spaCy NER for tech entities not in taxonomy
    nlp = _get_nlp()
    doc = nlp(text[:50_000])  # Limit for performance

    ner_entities = []
    for ent in doc.ents:
        ner_entities.append({"text": ent.text, "label": ent.label_})
        # Only add NER entities that look like tech tools (ORG/PRODUCT, CamelCase or ALL_CAPS)
        if ent.label_ in ("ORG", "PRODUCT", "GPE") and len(ent.text) > 1:
            skill_candidate = ent.text.lower().strip()
            # Skip if already captured or if it's too generic
            if (
                skill_candidate not in found
                and len(skill_candidate) > 1
                and not any(c.isdigit() for c in skill_candidate)
            ):
                # Check if it looks like a real tech tool (has uppercase in original)
                if any(c.isupper() for c in ent.text) or ent.text.isupper():
                    found[skill_candidate] = "tools_practices"

    # Organize by category
    skills_by_category: dict[str, list[str]] = {}
    for skill, category in found.items():
        skills_by_category.setdefault(category, []).append(skill)

    return {
        "skills": sorted(found.keys()),
        "skills_by_category": skills_by_category,
        "entities": ner_entities[:50],  # Cap for response size
    }


def get_skill_importance(skills: list[str], text: str) -> dict[str, float]:
    """
    Rank skills by their frequency/prominence in the text.

    Returns dict mapping skill -> normalized importance score (0-1).
    """
    if not skills or not text:
        return {}

    text_lower = text.lower()
    counts: dict[str, int] = {}

    for skill in skills:
        pattern = r"(?<!\w)" + re.escape(skill.lower()) + r"(?!\w)"
        counts[skill] = len(re.findall(pattern, text_lower))

    max_count = max(counts.values()) if counts else 1
    return {skill: round(count / max_count, 3) for skill, count in counts.items()}
