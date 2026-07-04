from __future__ import annotations
import os

os.environ["OMP_NUM_THREADS"] = "1"
os.environ["MKL_NUM_THREADS"] = "1"
os.environ["OPENBLAS_NUM_THREADS"] = "1"
os.environ["VECLIB_MAXIMUM_THREADS"] = "1"
os.environ["NUMEXPR_NUM_THREADS"] = "1"

try:
    import torch
    torch.set_num_threads(1)
except ImportError:
    pass

import logging
from contextlib import asynccontextmanager
from typing import AsyncIterator
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.routes import ask, health, session, upload

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(name)s  %(message)s",
)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    logger.info("RAGify-Docs backend starting up.")
    logger.info("Qdrant URL:       %s", settings.qdrant_url)
    logger.info("Embedding model:  %s", settings.hf_embedding_model)
    logger.info("Groq model:       %s", settings.groq_model)
    logger.info("Frontend origin:  %s", settings.frontend_origin)

    try:
        logger.info("Pre-warming embedding model: %s", settings.hf_embedding_model)
        from app.services.embedding import get_embedding_dimension
        dim = get_embedding_dimension()
        logger.info("Embedding model pre-warmed successfully. Dimension: %d", dim)
    except Exception as exc:
        logger.error("Failed to pre-warm embedding model: %s", exc)
        
    yield
    logger.info("RAGify-Docs backend shutting down.")

app = FastAPI(
    title="RAGify-Docs API",
    description="RAG-powered PDF Q&A with session-scoped Qdrant collections",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_origin],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router)
app.include_router(session.router)
app.include_router(upload.router)
app.include_router(ask.router)
