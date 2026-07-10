"""
Resume upload router — handles PDF and text file ingestion.
POST /upload-resume
"""

import logging
import os
from pathlib import Path

from fastapi import APIRouter, File, HTTPException, UploadFile, Depends
from fastapi.responses import JSONResponse

from config import get_settings, Settings
from pdf_parser import extract_text_from_pdf, extract_text_from_string
from schemas import ResumeUploadResponse, ErrorResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/upload-resume", tags=["Resume Upload"])

ALLOWED_CONTENT_TYPES = {
    "application/pdf",
    "text/plain",
    "application/octet-stream",  # Some browsers send this for PDFs
}

ALLOWED_EXTENSIONS = {".pdf", ".txt"}


@router.post(
    "",
    response_model=ResumeUploadResponse,
    responses={400: {"model": ErrorResponse}, 413: {"model": ErrorResponse}},
    summary="Upload and parse a resume file (PDF or TXT)",
)
async def upload_resume(
    file: UploadFile = File(..., description="Resume file — PDF or plain text"),
    settings: Settings = Depends(get_settings),
) -> ResumeUploadResponse:
    """
    Upload a resume file (PDF or TXT), extract its text content,
    and return the raw text for use in the /analyze endpoint.
    """
    # Validate filename
    if not file.filename:
        raise HTTPException(status_code=400, detail="No filename provided.")

    suffix = Path(file.filename).suffix.lower()
    if suffix not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type '{suffix}'. Only .pdf and .txt are accepted.",
        )

    # Read file bytes
    file_bytes = await file.read()

    # Validate file size
    if len(file_bytes) > settings.max_file_size_bytes:
        raise HTTPException(
            status_code=413,
            detail=f"File too large. Maximum size is {settings.MAX_FILE_SIZE_MB} MB.",
        )

    if len(file_bytes) == 0:
        raise HTTPException(status_code=400, detail="Uploaded file is empty.")

    logger.info(f"Processing upload: {file.filename}, {len(file_bytes)} bytes")

    # Extract text based on file type
    if suffix == ".pdf":
        result = extract_text_from_pdf(file_bytes)
    else:
        text_content = file_bytes.decode("utf-8", errors="replace")
        result = extract_text_from_string(text_content)

    if not result["success"] or not result["text"].strip():
        raise HTTPException(
            status_code=422,
            detail="Could not extract readable text from the uploaded file. "
            "Please ensure the PDF is not scanned/image-based, or paste text directly.",
        )

    extracted_text = result["text"]
    word_count = len(extracted_text.split())

    logger.info(
        f"Successfully extracted {word_count} words from {file.filename} "
        f"using {result['extractor']}"
    )

    return ResumeUploadResponse(
        success=True,
        filename=file.filename,
        extracted_text=extracted_text,
        word_count=word_count,
        page_count=result["page_count"],
        message=f"Resume parsed successfully using {result['extractor']}.",
    )
