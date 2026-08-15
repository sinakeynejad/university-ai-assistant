"""
Embedding layer for converting text into vector representations.

A local SentenceTransformer model is used, so no external API key is
required. The selected model is multilingual and supports Persian.

The embedding implementation can be replaced with another provider,
such as OpenAI, as long as it provides the same embed_documents()
and embed_query() methods.
"""

from functools import lru_cache
from typing import List

from sentence_transformers import SentenceTransformer

from app.config import get_settings
from app.utils.logger import get_logger


# Initialize application logger
logger = get_logger(__name__)


class EmbeddingModel:
    """Wrapper around the SentenceTransformer embedding model."""

    def __init__(self, model_name: str, device: str = "cpu"):
        # Load the embedding model
        logger.info(f"Loading embedding model: {model_name}")
        self.model = SentenceTransformer(model_name, device=device)

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        # Convert multiple texts into embedding vectors
        embeddings = self.model.encode(
            texts,
            show_progress_bar=False,
            normalize_embeddings=True
        )

        return embeddings.tolist()

    def embed_query(self, text: str) -> List[float]:
        # Convert a single query into an embedding vector
        embedding = self.model.encode(
            [text],
            show_progress_bar=False,
            normalize_embeddings=True
        )

        return embedding[0].tolist()


@lru_cache
def get_embedding_model() -> EmbeddingModel:
    # Load settings and create the embedding model
    settings = get_settings()

    return EmbeddingModel(
        model_name=settings.EMBEDDING_MODEL_NAME,
        device=settings.EMBEDDING_DEVICE
    )
