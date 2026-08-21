"""
Vector store layer using ChromaDB with local disk persistence.

Responsibilities:
- Store embedded document chunks
- Perform similarity searches
- List stored documents
- Delete documents
"""

from functools import lru_cache
from typing import Any, cast
import uuid

import chromadb
from chromadb.config import Settings as ChromaSettings

try:
    from app.config import get_settings
    from app.utils.logger import get_logger
except ModuleNotFoundError:  # pragma: no cover - supports repo-root execution
    from backend.app.config import get_settings
    from backend.app.utils.logger import get_logger


# Initialize application logger
logger = get_logger(__name__)


class VectorStore:
    """Wrapper around ChromaDB for storing and retrieving document chunks."""

    def __init__(self, persist_dir: str, collection_name: str):
        # Create a persistent ChromaDB client
        self.client = chromadb.PersistentClient(
            path=persist_dir,
            settings=ChromaSettings(
                anonymized_telemetry=False
            )
        )

        # Get the collection or create it if it does not exist
        self.collection = self.client.get_or_create_collection(
            name=collection_name,
            metadata={"hnsw:space": "cosine"}
        )

    def add_chunks(
        self,
        document_name: str,
        chunks: list[str],
        embeddings: list[list[float]],
    ) -> int:

        # Generate a unique ID for each chunk
        ids = [
            f"{document_name}::{i}::{uuid.uuid4().hex[:8]}"
            for i in range(len(chunks))
        ]

        # Store metadata for each chunk
        metadatas = [
            {
                "document_name": document_name,
                "chunk_index": i
            }
            for i in range(len(chunks))
        ]

        # Add chunks, embeddings, IDs, and metadata to ChromaDB
        self.collection.add(
            ids=ids,
            embeddings=cast(Any, embeddings),
            documents=chunks,
            metadatas=cast(Any, metadatas),
        )

        logger.info(
            f"{len(chunks)} chunks from document '{document_name}' were stored."
        )

        return len(chunks)

    def similarity_search(
        self,
        query_embedding: list[float],
        top_k: int,
    ) -> list[dict[str, Any]]:

        # Search for the most similar chunks
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k,
        )

        output: list[dict[str, Any]] = []

        ids = results.get("ids") or []
        documents = results.get("documents") or []
        metadatas = results.get("metadatas") or []
        distances = results.get("distances") or []

        if not ids or not ids[0]:
            return output

        first_ids = ids[0]
        first_documents = documents[0] if documents and documents[0] else []
        first_metadatas = metadatas[0] if metadatas and metadatas[0] else []
        first_distances = distances[0] if distances and distances[0] else []

        # Process each retrieved result
        for i in range(len(first_ids)):
            if i >= len(first_distances):
                break

            distance = first_distances[i]
            score = 1 - distance

            if i >= len(first_documents):
                content = ""
            else:
                content = first_documents[i]

            metadata = first_metadatas[i] if i < len(first_metadatas) else {}

            output.append(
                {
                    "content": content,
                    "document_name": metadata.get("document_name", ""),
                    "chunk_index": metadata.get("chunk_index", 0),
                    "score": round(float(score), 4),
                }
            )

        return output

    def list_documents(self) -> list[str]:
        # Retrieve metadata for all stored chunks
        all_items = self.collection.get(include=["metadatas"])
        stored_metadatas = all_items.get("metadatas") or []

        # Extract unique document names
        names = {
            str(m.get("document_name"))
            for m in stored_metadatas
            if isinstance(m, dict) and m.get("document_name") is not None
        }

        return sorted(names)

    def delete_document(self, document_name: str) -> None:
        # Delete all chunks belonging to the specified document
        self.collection.delete(
            where={"document_name": document_name}
        )

        logger.info(
            f"Document '{document_name}' was deleted from the vector store."
        )


@lru_cache
def get_vector_store() -> VectorStore:
    # Load application settings
    settings = get_settings()

    # Create and cache the vector store instance
    return VectorStore(
        persist_dir=settings.CHROMA_DIR,
        collection_name=settings.CHROMA_COLLECTION
    )
