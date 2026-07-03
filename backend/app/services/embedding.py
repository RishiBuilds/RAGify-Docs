from __future__ import annotations
import logging
from langchain_huggingface import HuggingFaceEmbeddings
from app.config import settings

logger = logging.getLogger(__name__)

_embedding_model: HuggingFaceEmbeddings | None = None
_embedding_dim: int | None = None

def get_embeddings() -> HuggingFaceEmbeddings:
    global _embedding_model
    if _embedding_model is None:
        logger.info(
            "Loading embedding model: %s", settings.hf_embedding_model
        )
        _embedding_model = HuggingFaceEmbeddings(
            model_name=settings.hf_embedding_model,
        )
        logger.info("Embedding model loaded successfully.")
    return _embedding_model

def get_embedding_dimension() -> int:
    global _embedding_dim
    if _embedding_dim is None:
        model = get_embeddings()
        _embedding_dim = len(model.embed_query("dimension probe"))
        logger.info(
            "Detected embedding dimension: %d (model: %s)",
            _embedding_dim,
            settings.hf_embedding_model,
        )
    return _embedding_dim
