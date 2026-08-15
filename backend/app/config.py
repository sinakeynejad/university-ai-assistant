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
    EMBEDDING_MODEL_NAME: str = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
    EMBEDDING_DEVICE: str = "cpu"

    # LLM provider configuration
    # Supported providers: "openai_compatible" or "mock"
    LLM_PROVIDER: str = "mock"

    # LLM API settings
    LLM_API_KEY: str = ""
    LLM_BASE_URL: str = "https://api.openai.com/v1"
    LLM_MODEL_NAME: str = "gpt-4o-mini"

    # LLM generation parameters
    LLM_TEMPERATURE: float = 0.2
    LLM_MAX_TOKENS: int = 800

    # Text splitting settings for RAG chunks
    CHUNK_SIZE: int = 800
    CHUNK_OVERLAP: int = 150

    # Number of documents retrieved from vector database
    TOP_K: int = 4

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8")


@lru_cache
def get_settings() -> Settings:
    # Create and return application settings.
    # lru_cache ensures that settings are loaded only once.
    return Settings()
