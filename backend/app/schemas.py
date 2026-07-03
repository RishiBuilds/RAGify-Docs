from __future__ import annotations
from pydantic import BaseModel, Field, ConfigDict

class AskRequest(BaseModel):
    model_config = ConfigDict(extra="ignore", str_strip_whitespace=True)
    session_id: str = Field(..., min_length=1)
    question: str = Field(..., min_length=1)

class SessionResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")
    session_id: str
    collection_name: str

class UploadResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")
    session_id: str
    files_processed: int = Field(..., ge=0)
    total_chunks: int = Field(..., ge=0)
    status: str
    errors: list[str] = Field(default_factory=list)

class SourceReference(BaseModel):
    model_config = ConfigDict(extra="ignore")
    filename: str
    page_number: int = Field(..., ge=1)
    snippet: str

class QAResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")
    answer: str
    sources: list[SourceReference] = Field(default_factory=list)
    confidence: str | None = None

class HealthResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")
    status: str
    qdrant_connected: bool

class ErrorResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")
    detail: str
