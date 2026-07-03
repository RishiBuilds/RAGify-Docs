from __future__ import annotations
import logging
from fastapi import APIRouter, HTTPException
from app.schemas import AskRequest, QAResponse
from app.services.retrieval import retrieve_and_answer

logger = logging.getLogger(__name__)
router = APIRouter(tags=["ask"])

@router.post("/ask", response_model=QAResponse)
async def ask_question(body: AskRequest) -> QAResponse:
    if not body.question.strip():
        raise HTTPException(status_code=400, detail="Question cannot be empty.")

    try:
        return retrieve_and_answer(
            session_id=body.session_id,
            question=body.question,
        )
    except HTTPException:
        raise
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        logger.exception("Error answering question (session=%s)", body.session_id)
        raise HTTPException(status_code=500, detail=str(exc)) from exc
