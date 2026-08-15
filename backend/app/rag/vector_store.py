"""
Vector store layer using ChromaDB with local disk persistence.

Responsibilities:
- Store embedded document chunks
- Perform similarity searches
- List stored documents
- Delete documents
"""

from functools import lru_cache
from typing import List, Dict, Any
import uuid

import chromadb
from chromadb.config import Settings as ChromaSettings

from app.config import get_settings
from app.utils.logger import get_logger


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
        chunks: List[str],
        embeddings: List[List[float]],
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
            embeddings=embeddings,
            documents=chunks,
            metadatas=metadatas
        )

        logger.info(
            f"{len(chunks)} chunks from document '{document_name}' were stored."
        )

        return len(chunks)

    def similarity_search(
        self,
        query_embedding: List[float],
        top_k: int
    ) -> List[Dict[str, Any]]:

        # Search for the most similar chunks
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k,
        )

        output = []

        # Return an empty list if no results were found
        if not results["ids"] or not results["ids"][0]:
            return output

        # Process each retrieved result
        for i in range(len(results["ids"][0])):
            distance = results["distances"][0][i]

            # Convert cosine distance into a similarity score
            score = 1 - distance

            output.append(
                {
                    "content": results["documents"][0][i],
                    "document_name": results["metadatas"][0][i]["document_name"],
                    "chunk_index": results["metadatas"][0][i]["chunk_index"],
                    "score": round(float(score), 4),
                }
            )

        return output

    def list_documents(self) -> List[str]:
        # Retrieve metadata for all stored chunks
        all_items = self.collection.get(include=["metadatas"])

        # Extract unique document names
        names = {
            m["document_name"]
            for m in all_items["metadatas"]
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
