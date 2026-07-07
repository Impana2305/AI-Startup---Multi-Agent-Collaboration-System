"""PDF parsing utility for pitch decks and business plans."""

from __future__ import annotations

import io
import logging

logger = logging.getLogger(__name__)


def extract_text_from_pdf(file_bytes: bytes) -> str:
    """Extract text from a PDF file using pdfplumber (primary) or PyPDF2 (fallback).

    Returns the extracted text as a single string.
    """
    text = ""

    # Try pdfplumber first (better quality)
    try:
        import pdfplumber

        with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n\n"

        if text.strip():
            logger.info("Extracted %d characters via pdfplumber", len(text))
            return text.strip()

    except Exception as e:
        logger.warning("pdfplumber extraction failed: %s", e)

    # Fallback to PyPDF2
    try:
        from PyPDF2 import PdfReader

        reader = PdfReader(io.BytesIO(file_bytes))
        for page in reader.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n\n"

        if text.strip():
            logger.info("Extracted %d characters via PyPDF2", len(text))
            return text.strip()

    except Exception as e:
        logger.warning("PyPDF2 extraction failed: %s", e)

    logger.error("Could not extract any text from PDF")
    return ""
