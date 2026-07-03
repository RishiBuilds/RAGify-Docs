from __future__ import annotations
import logging
from fastapi import APIRouter, HTTPException
from app.schemas import SessionResponse
from app.services import session_manager

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/session", tags=["session"])

@router.post("", response_model=SessionResponse, status_code=201)
async def create_session() -> SessionResponse:
    try:
        return session_manager.create_session()
    except Exception as exc:
        logger.exception("Failed to create session")
        raise HTTPException(status_code=500, detail=str(exc)) from exc

@router.delete("/{session_id}", status_code=200)
async def delete_session(session_id: str) -> dict[str, str]:
    try:
        deleted = session_manager.delete_session(session_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        logger.exception("Failed to delete session %s", session_id)
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    if not deleted:
        raise HTTPException(
            status_code=404,
            detail=f"Session '{session_id}' not found.",
        )

    return {"detail": f"Session '{session_id}' deleted."}
