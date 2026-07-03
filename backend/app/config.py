from pydantic_settings import BaseSettings, SettingsConfigDict
from pathlib import Path

_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(_PROJECT_ROOT / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    qdrant_url: str
    qdrant_api_key: str
    hf_embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"
    groq_api_key: str = ""
    groq_base_url: str = "https://api.groq.com/openai/v1"
    groq_model: str = "llama-3.1-8b-instant"
    chunk_size: int = 600
    chunk_overlap: int = 120
    top_k: int = 5
    max_file_size_mb: int = 10
    max_files_per_upload: int = 10
    frontend_origin: str = "http://localhost:8501"
    snippet_max_length: int = 200

    @property
    def max_file_size_bytes(self) -> int:
        return self.max_file_size_mb * 1024 * 1024

settings = Settings()
