"""Document upload routes — PDF pitch deck and business plan."""

from __future__ import annotations

from fastapi import APIRouter, UploadFile, File, HTTPException

from utils.pdf_parser import extract_text_from_pdf

router = APIRouter(prefix="/api/documents", tags=["documents"])


@router.post("/upload-pdf")
async def upload_pdf(file: UploadFile = File(...)):
    """Upload a PDF file and extract its text content.

    Returns the extracted text that can be included in the startup proposal.
    """
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are accepted")

    # Read file content
    content = await file.read()
    if len(content) > 10 * 1024 * 1024:  # 10 MB limit
        raise HTTPException(status_code=400, detail="File too large (max 10MB)")

    extracted_text = extract_text_from_pdf(content)

    if not extracted_text:
        raise HTTPException(
            status_code=422,
            detail="Could not extract text from the PDF. The file may be image-based.",
        )

    return {
        "filename": file.filename,
        "text_length": len(extracted_text),
        "extracted_text": extracted_text,
    }
