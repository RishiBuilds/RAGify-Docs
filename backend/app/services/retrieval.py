from __future__ import annotations
import logging
from fastapi import HTTPException
from app.config import settings
from app.schemas import QAResponse
from app.services.llm_client import generate_answer
from app.services.session_manager import session_exists
from app.services.vectorstore import get_vectorstore
from app.utils.sanitize import sanitize_collection_name

logger = logging.getLogger(__name__)

def retrieve_and_answer(
    session_id: str,
    question: str,
    top_k: int | None = None,
) -> QAResponse:
    if not session_exists(session_id):
        raise HTTPException(
            status_code=404,
            detail=(
                f"Session '{session_id}' not found. "
                "Please upload documents first or create a new session."
            ),
        )

    k = top_k or settings.top_k
    collection_name = sanitize_collection_name(session_id)
    vectorstore = get_vectorstore(collection_name)

    logger.info(
        "Retrieving top-%d chunks for question (session=%s): %.80s…",
        k,
        session_id,
        question,
    )

    results = vectorstore.similarity_search(query=question, k=k)

    if not results:
        logger.info("No chunks returned from similarity search.")
        return QAResponse(
            answer="No relevant information was found in the uploaded documents for your question.",
            sources=[],
            confidence="low",
        )

    logger.info(
        "Retrieved %d chunks; sending to LLM (model=%s).",
        len(results),
        settings.groq_model,
    )

    return generate_answer(question, results)
