from __future__ import annotations
import logging
from fastapi import APIRouter
from app.schemas import HealthResponse
from app.services.vectorstore import get_qdrant_client

logger = logging.getLogger(__name__)
router = APIRouter(tags=["health"])

@router.get("/health", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    qdrant_ok = False
    try:
        client = get_qdrant_client()
        client.get_collections()
        qdrant_ok = True
    except Exception as exc:
        logger.error("Qdrant health check failed: %s", exc)

    return HealthResponse(
        status="ok" if qdrant_ok else "degraded",
        qdrant_connected=qdrant_ok,
    )
