from __future__ import annotations
import logging
from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from app.config import settings
from app.schemas import UploadResponse
from app.services.ingestion import ingest_pdf

logger = logging.getLogger(__name__)
router = APIRouter(tags=["upload"])

@router.post("/upload", response_model=UploadResponse)
async def upload_documents(
    session_id: str = Form(..., description="Session UUID"),
    files: list[UploadFile] = File(..., description="PDF files to ingest"),
) -> UploadResponse:
    if len(files) > settings.max_files_per_upload:
        raise HTTPException(
            status_code=400,
            detail=(
                f"Too many files: {len(files)} uploaded, "
                f"max {settings.max_files_per_upload} per request."
            ),
        )

    if not session_id or not session_id.strip():
        raise HTTPException(status_code=400, detail="session_id is required.")

    contents: list[bytes] = []
    for file in files:
        filename = file.filename or "unknown.pdf"

        if file.content_type and file.content_type != "application/pdf":
            raise HTTPException(
                status_code=400,
                detail=f"{filename} is not a PDF (got {file.content_type}).",
            )

        if file.size and file.size > settings.max_file_size_bytes:
            raise HTTPException(
                status_code=413,
                detail=f"{filename} ({file.size / (1024 * 1024):.1f}MB) exceeds the {settings.max_file_size_mb}MB limit and was skipped.",
            )

        content = await file.read()
        if len(content) > settings.max_file_size_bytes:
            raise HTTPException(
                status_code=413,
                detail=f"{filename} ({len(content) / (1024 * 1024):.1f}MB) exceeds the {settings.max_file_size_mb}MB limit and was skipped.",
            )
        contents.append(content)

    total_chunks = 0
    files_processed = 0
    errors: list[str] = []

    for file, content in zip(files, contents):
        filename = file.filename or "unknown.pdf"

        try:
            chunks = await ingest_pdf(content, filename, session_id)
            total_chunks += chunks
            files_processed += 1
            logger.info(
                "Uploaded '%s': %d chunks (session=%s)",
                filename,
                chunks,
                session_id,
            )
        except Exception as exc:
            logger.exception("Failed to ingest '%s'", filename)
            errors.append(f"'{filename}': {exc}")

    status = "success" if not errors else "partial_failure"

    return UploadResponse(
        session_id=session_id,
        files_processed=files_processed,
        total_chunks=total_chunks,
        status=status,
        errors=errors,
    )
