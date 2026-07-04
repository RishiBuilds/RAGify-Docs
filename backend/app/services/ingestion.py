from __future__ import annotations
import logging
import tempfile
from pathlib import Path
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from qdrant_client import models as qdrant_models
from app.config import settings
from app.services.session_manager import ensure_session
from app.services.vectorstore import get_qdrant_client, get_vectorstore

logger = logging.getLogger(__name__)

def _save_temp_file(content: bytes, filename: str) -> Path:
    suffix = Path(filename).suffix
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
    tmp.write(content)
    tmp.close()
    return Path(tmp.name)

def _delete_existing_chunks(collection_name: str, filename: str) -> None:
    client = get_qdrant_client()
    client.delete(
        collection_name=collection_name,
        points_selector=qdrant_models.FilterSelector(
            filter=qdrant_models.Filter(
                must=[
                    qdrant_models.FieldCondition(
                        key="metadata.source",
                        match=qdrant_models.MatchValue(value=filename),
                    )
                ]
            )
        ),
    )
    logger.debug(
        "Deleted existing chunks for source='%s' in %s",
        filename,
        collection_name,
    )

async def ingest_pdf(content: bytes, filename: str, session_id: str) -> int:
    original_filename = filename or "unknown.pdf"
    collection_name = ensure_session(session_id)
    tmp_path: Path | None = None

    try:
        tmp_path = _save_temp_file(content, original_filename)
        logger.info(
            "Ingesting '%s' (session=%s, temp=%s)",
            original_filename,
            session_id,
            tmp_path,
        )

        documents = PyPDFLoader(str(tmp_path)).load()
        if not documents:
            raise ValueError(f"Failed to load pages or PDF is empty: '{original_filename}'")

        for idx, doc in enumerate(documents, 1):
            logger.debug(
                "Page %d of '%s': %d characters",
                idx,
                original_filename,
                len(doc.page_content),
            )

        total_chars = sum(len(doc.page_content.strip()) for doc in documents)
        if total_chars < 50:
            raise ValueError(
                f"No extractable text found in '{original_filename}'. This PDF may be a "
                f"scanned image or contain no text layer. OCR is not currently supported."
            )

        for doc in documents:
            doc.metadata["source"] = original_filename
            doc.metadata["page"] = doc.metadata.get("page", 0) + 1

        splitter = RecursiveCharacterTextSplitter(
            chunk_size=settings.chunk_size,
            chunk_overlap=settings.chunk_overlap,
        )
        chunks = splitter.split_documents(documents)
        if not chunks:
            raise ValueError(f"Text splitting produced 0 chunks for '{original_filename}'")

        _delete_existing_chunks(collection_name, original_filename)

        vectorstore = get_vectorstore(collection_name)
        vectorstore.add_documents(chunks)

        logger.info(
            "Ingested '%s': %d pages → %d chunks (session=%s)",
            original_filename,
            len(documents),
            len(chunks),
            session_id,
        )
        return len(chunks)

    finally:
        if tmp_path and tmp_path.exists():
            tmp_path.unlink()
            logger.debug("Cleaned up temp file %s", tmp_path)
