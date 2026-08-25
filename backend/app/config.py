from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # Application settings
    APP_NAME: str = "KNTU RAG Assistant"
    APP_ENV: str = "development"

    # Allowed frontend origins for CORS
    CORS_ORIGINS: str = "*"

    # File storage paths
    UPLOAD_DIR: str = "data/uploads"
    CHROMA_DIR: str = "data/chroma_db"

    # Vector database collection name
    CHROMA_COLLECTION: str = "kntu_documents"

    # Embedding model configuration
    EMBEDDING_MODEL_NAME: str = "nomic-embed-text"
    EMBEDDING_DEVICE: str = "cpu"

    # LLM provider configuration
    LLM_PROVIDER: str = "openai_compatible"
    LLM_API_KEY: str = ""
    LLM_BASE_URL: str = "http://localhost:11434/v1"
    LLM_MODEL_NAME: str = "aya-expanse:8b-q4_K_S"

    # LLM generation parameters
    LLM_TEMPERATURE: float = 0.2
    LLM_MAX_TOKENS: int = 800

    # Text splitting settings for RAG chunks
    CHUNK_SIZE: int = 800
    CHUNK_OVERLAP: int = 150

    # Number of documents retrieved from vector database
    TOP_K: int = 4

    # ---------- ADD THIS LINE ----------
    model_config = SettingsConfigDict(
        env_file=".env", 
        env_file_encoding="utf-8",
        extra="ignore"   # <-- allows extra env vars like SECRET_KEY
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()
