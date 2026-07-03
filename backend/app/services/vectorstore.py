from __future__ import annotations
import logging
from langchain_qdrant import QdrantVectorStore
from qdrant_client import QdrantClient
from app.config import settings
from app.services.embedding import get_embeddings

logger = logging.getLogger(__name__)

_client: QdrantClient | None = None

def get_qdrant_client() -> QdrantClient:
    global _client
    if _client is None:
        if settings.qdrant_url == ":memory:":
            logger.info("Using Qdrant in-memory mode (no server required).")
            _client = QdrantClient(location=":memory:")
        else:
            logger.info("Connecting to Qdrant at %s", settings.qdrant_url)
            _client = QdrantClient(
                url=settings.qdrant_url,
                api_key=settings.qdrant_api_key,
                timeout=5,
            )
        logger.info("Qdrant client initialised.")
    return _client

def get_vectorstore(collection_name: str) -> QdrantVectorStore:
    client = get_qdrant_client()
    embeddings = get_embeddings()
    return QdrantVectorStore(
        client=client,
        collection_name=collection_name,
        embedding=embeddings,
    )
