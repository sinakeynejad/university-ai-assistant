"""
Embedding layer for converting text into vector representations.

Ollama embedding models are used, running fully locally.
Recommended models for Persian: nomic-embed-text, batai/qwen3-embedding:0.6b
"""

from functools import lru_cache
from typing import List

from langchain_community.embeddings import OllamaEmbeddings

from app.config import get_settings
from app.utils.logger import get_logger


# Initialize application logger
logger = get_logger(__name__)


class EmbeddingModel:
    """Wrapper around Ollama's embedding models."""

    def __init__(self, model_name: str):
        logger.info(f"Loading Ollama embedding model: {model_name}")
        
        # Initialize the Ollama embeddings client
        # base_url points to Ollama's default API (no /v1 needed for embeddings)
        self.model = OllamaEmbeddings(
            model=model_name,
            base_url="http://localhost:11434"
        )

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """Convert multiple texts into embedding vectors."""
        # OllamaEmbeddings returns List[List[float]] directly
        return self.model.embed_documents(texts)

    def embed_query(self, text: str) -> List[float]:
        """Convert a single query into an embedding vector."""
        # OllamaEmbeddings returns List[float] directly
        return self.model.embed_query(text)


@lru_cache
def get_embedding_model() -> EmbeddingModel:
    # Load settings and create the embedding model
    settings = get_settings()
    
    return EmbeddingModel(
        model_name=settings.EMBEDDING_MODEL_NAME
    )