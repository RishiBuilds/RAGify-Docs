from __future__ import annotations
import logging
import uuid
from qdrant_client.models import Distance, PayloadSchemaType, VectorParams
from app.schemas import SessionResponse
from app.services.embedding import get_embedding_dimension
from app.services.vectorstore import get_qdrant_client
from app.utils.sanitize import sanitize_collection_name

logger = logging.getLogger(__name__)

def create_session() -> SessionResponse:
    session_id = str(uuid.uuid4())
    collection_name = sanitize_collection_name(session_id)
    dim = get_embedding_dimension()
    client = get_qdrant_client()

    client.create_collection(
        collection_name=collection_name,
        vectors_config=VectorParams(size=dim, distance=Distance.COSINE),
    )

    client.create_payload_index(
        collection_name=collection_name,
        field_name="metadata.source",
        field_schema=PayloadSchemaType.KEYWORD,
    )

    logger.info(
        "Session created: session_id=%s  collection=%s  dim=%d",
        session_id,
        collection_name,
        dim,
    )
    return SessionResponse(
        session_id=session_id, collection_name=collection_name
    )

def delete_session(session_id: str) -> bool:
    collection_name = sanitize_collection_name(session_id)
    client = get_qdrant_client()

    if not client.collection_exists(collection_name):
        logger.warning(
            "delete_session: collection %s does not exist", collection_name
        )
        return False

    client.delete_collection(collection_name)
    logger.info(
        "Session deleted: session_id=%s  collection=%s",
        session_id,
        collection_name,
    )
    return True

def session_exists(session_id: str) -> bool:
    collection_name = sanitize_collection_name(session_id)
    return get_qdrant_client().collection_exists(collection_name)

def ensure_session(session_id: str) -> str:
    collection_name = sanitize_collection_name(session_id)
    client = get_qdrant_client()

    if client.collection_exists(collection_name):
        return collection_name

    dim = get_embedding_dimension()
    try:
        client.create_collection(
            collection_name=collection_name,
            vectors_config=VectorParams(size=dim, distance=Distance.COSINE),
        )
        client.create_payload_index(
            collection_name=collection_name,
            field_name="metadata.source",
            field_schema=PayloadSchemaType.KEYWORD,
        )
        logger.info(
            "ensure_session created collection %s (dim=%d)",
            collection_name,
            dim,
        )
    except Exception:
        if not client.collection_exists(collection_name):
            raise
        logger.debug(
            "ensure_session: collection %s was created by a concurrent request",
            collection_name,
        )

    return collection_name
