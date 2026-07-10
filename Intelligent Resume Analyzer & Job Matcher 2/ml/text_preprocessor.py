"""
Text preprocessing utilities for resume and job description analysis.
Handles cleaning, tokenization, and lemmatization using spaCy.
"""

import re
import string
import unicodedata
from typing import Optional

import spacy

# Lazy-loaded spaCy model
_nlp: Optional[spacy.language.Language] = None


def _get_nlp() -> spacy.language.Language:
    """Lazy-load spaCy model to avoid startup cost."""
    global _nlp
    if _nlp is None:
        try:
            _nlp = spacy.load("en_core_web_sm", disable=["parser"])
        except OSError:
            # Fallback: blank English model with tagger
            _nlp = spacy.blank("en")
    return _nlp


def clean_text(text: str) -> str:
    """
    Clean raw text by removing HTML tags, special characters, and normalizing whitespace.

    Args:
        text: Raw text (from PDF extraction or user input)

    Returns:
        Cleaned text string
    """
    if not text or not text.strip():
        return ""

    # Normalize unicode characters
    text = unicodedata.normalize("NFKD", text)

    # Remove HTML/XML tags
    text = re.sub(r"<[^>]+>", " ", text)

    # Remove URLs
    text = re.sub(r"https?://\S+|www\.\S+", " ", text)

    # Remove email addresses (preserve domain words)
    text = re.sub(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b", " ", text)

    # Remove phone numbers
    text = re.sub(r"\b(\+?\d[\d\s\-().]{7,}\d)\b", " ", text)

    # Replace bullet points and special list markers
    text = re.sub(r"[•●▪▸►◆◇→✓✔✗✘▶]", " ", text)

    # Remove non-ASCII characters but keep alphanumeric and common punctuation
    text = re.sub(r"[^\x00-\x7F]+", " ", text)

    # Remove excessive punctuation (keep . , + # @ for context)
    text = re.sub(r"[|\\\"'`~^&*<>{}\[\]=_]", " ", text)

    # Normalize whitespace
    text = re.sub(r"\s+", " ", text).strip()

    return text


def tokenize_and_lemmatize(text: str) -> list[str]:
    """
    Tokenize and lemmatize text, removing stopwords and punctuation.

    Args:
        text: Cleaned text string

    Returns:
        List of lemmatized tokens
    """
    if not text:
        return []

    nlp = _get_nlp()
    # Process in chunks to avoid spaCy max_length limit
    chunk_size = 100_000
    all_tokens = []

    for i in range(0, len(text), chunk_size):
        chunk = text[i : i + chunk_size]
        doc = nlp(chunk)

        tokens = [
            token.lemma_.lower()
            for token in doc
            if not token.is_stop
            and not token.is_punct
            and not token.is_space
            and len(token.lemma_) > 1
            and token.lemma_.lower() not in string.punctuation
        ]
        all_tokens.extend(tokens)

    return all_tokens


def extract_sentences(text: str) -> list[str]:
    """
    Split text into sentences for embedding-level analysis.

    Args:
        text: Cleaned text string

    Returns:
        List of non-empty sentence strings
    """
    if not text:
        return []

    # Simple sentence splitting (avoids parser overhead)
    sentences = re.split(r"(?<=[.!?])\s+|\n{2,}", text)
    return [s.strip() for s in sentences if len(s.strip()) > 15]


def preprocess(text: str) -> dict:
    """
    Full preprocessing pipeline.

    Args:
        text: Raw text

    Returns:
        Dict with keys: cleaned_text, tokens, sentences
    """
    cleaned = clean_text(text)
    return {
        "cleaned_text": cleaned,
        "tokens": tokenize_and_lemmatize(cleaned),
        "sentences": extract_sentences(cleaned),
        "word_count": len(cleaned.split()),
    }
