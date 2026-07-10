"""
PDF and text extraction utilities.
Primary: pdfplumber (accurate text, table-aware)
Fallback: PyMuPDF (fitz) for malformed PDFs
"""

import io
import logging
import os
import re
from pathlib import Path
from typing import Union

logger = logging.getLogger(__name__)


def _extract_with_pdfplumber(file_bytes: bytes) -> tuple[str, int]:
    """Extract text using pdfplumber."""
    import pdfplumber

    pages_text = []
    with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
        page_count = len(pdf.pages)
        for page in pdf.pages:
            text = page.extract_text(x_tolerance=2, y_tolerance=2)
            if text:
                pages_text.append(text)

    return "\n\n".join(pages_text), page_count


def _extract_with_pymupdf(file_bytes: bytes) -> tuple[str, int]:
    """Extract text using PyMuPDF as fallback."""
    import fitz  # PyMuPDF

    pages_text = []
    doc = fitz.open(stream=file_bytes, filetype="pdf")
    page_count = doc.page_count

    for page in doc:
        text = page.get_text("text")
        if text:
            pages_text.append(text)

    doc.close()
    return "\n\n".join(pages_text), page_count


def _clean_extracted_text(text: str) -> str:
    """Post-process extracted PDF text to fix common artifacts."""
    # Fix hyphenation from line breaks
    text = re.sub(r"-\n(\w)", r"\1", text)
    # Remove excessive blank lines
    text = re.sub(r"\n{3,}", "\n\n", text)
    # Remove form-feed characters
    text = text.replace("\x0c", "\n")
    # Normalize unicode dashes/quotes
    text = text.replace("\u2013", "-").replace("\u2014", "-")
    text = text.replace("\u2018", "'").replace("\u2019", "'")
    text = text.replace("\u201c", '"').replace("\u201d", '"')
    return text.strip()


def extract_text_from_pdf(file_bytes: bytes) -> dict:
    """
    Extract text from PDF bytes using pdfplumber with PyMuPDF fallback.

    Args:
        file_bytes: Raw PDF file bytes

    Returns:
        Dict with:
          - text: extracted text string
          - page_count: number of pages
          - extractor: which library was used
          - success: bool
    """
    # Try pdfplumber first
    try:
        text, page_count = _extract_with_pdfplumber(file_bytes)
        if text.strip():
            logger.info(f"pdfplumber extracted {len(text)} chars from {page_count} pages")
            return {
                "text": _clean_extracted_text(text),
                "page_count": page_count,
                "extractor": "pdfplumber",
                "success": True,
            }
        logger.warning("pdfplumber returned empty text, trying PyMuPDF")
    except Exception as e:
        logger.warning(f"pdfplumber failed: {e}, falling back to PyMuPDF")

    # Fallback to PyMuPDF
    try:
        text, page_count = _extract_with_pymupdf(file_bytes)
        return {
            "text": _clean_extracted_text(text),
            "page_count": page_count,
            "extractor": "pymupdf",
            "success": bool(text.strip()),
        }
    except Exception as e:
        logger.error(f"PyMuPDF also failed: {e}")
        return {
            "text": "",
            "page_count": 0,
            "extractor": "none",
            "success": False,
        }


def extract_text_from_string(text: str) -> dict:
    """
    Process plain-text resume input (already extracted or pasted).

    Returns the same dict shape as extract_text_from_pdf.
    """
    cleaned = _clean_extracted_text(text)
    return {
        "text": cleaned,
        "page_count": 1,
        "extractor": "plaintext",
        "success": bool(cleaned.strip()),
    }
