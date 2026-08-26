"""
Vector store layer using ChromaDB with local disk persistence.

Responsibilities:
- Store embedded document chunks
- Perform similarity searches
- List stored documents
- Delete documents
<<<<<<< HEAD

All operations are scoped to a single user via the "user_id" field
stored in each chunk's metadata. This keeps every account's documents
isolated inside one shared Chroma collection.
"""

from functools import lru_cache
from typing import List, Dict, Any, cast
import uuid

import chromadb
from chromadb.api.types import Embeddings, Include, Metadata
=======
"""

from functools import lru_cache
from typing import List, Dict, Any
import uuid

import chromadb
>>>>>>> c8d397a7424622aef1a2556a21e0a528e6306bb2
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
<<<<<<< HEAD
        user_id: int,
=======
>>>>>>> c8d397a7424622aef1a2556a21e0a528e6306bb2
    ) -> int:

        # Generate a unique ID for each chunk
        ids = [
<<<<<<< HEAD
            f"{user_id}::{document_name}::{i}::{uuid.uuid4().hex[:8]}"
            for i in range(len(chunks))
        ]

        # Store metadata for each chunk, tagged with its owner
        metadatas = [
            {
                "document_name": document_name,
                "chunk_index": i,
                "user_id": user_id,
=======
            f"{document_name}::{i}::{uuid.uuid4().hex[:8]}"
            for i in range(len(chunks))
        ]

        # Store metadata for each chunk
        metadatas = [
            {
                "document_name": document_name,
                "chunk_index": i
>>>>>>> c8d397a7424622aef1a2556a21e0a528e6306bb2
            }
            for i in range(len(chunks))
        ]

        # Add chunks, embeddings, IDs, and metadata to ChromaDB
        self.collection.add(
            ids=ids,
<<<<<<< HEAD
            embeddings=cast(Embeddings, embeddings),
            documents=chunks,
            metadatas=cast(List[Metadata], metadatas)
        )

        logger.info(
            f"{len(chunks)} chunks from document '{document_name}' "
            f"were stored for user {user_id}."
=======
            embeddings=embeddings,
            documents=chunks,
            metadatas=metadatas
        )

        logger.info(
            f"{len(chunks)} chunks from document '{document_name}' were stored."
>>>>>>> c8d397a7424622aef1a2556a21e0a528e6306bb2
        )

        return len(chunks)

    def similarity_search(
        self,
        query_embedding: List[float],
<<<<<<< HEAD
        top_k: int,
        user_id: int,
    ) -> List[Dict[str, Any]]:

        # Search for the most similar chunks, restricted to this user's docs
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k,
            where={"user_id": user_id},
=======
        top_k: int
    ) -> List[Dict[str, Any]]:

        # Search for the most similar chunks
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k,
>>>>>>> c8d397a7424622aef1a2556a21e0a528e6306bb2
        )

        output = []

        # Return an empty list if no results were found
<<<<<<< HEAD
        ids = results.get("ids")
        distances = results.get("distances")
        documents = results.get("documents")
        metadatas = results.get("metadatas")

        if not ids or not ids[0] or not distances or not distances[0]:
            return output

        if not documents or not documents[0] or not metadatas or not metadatas[0]:
            return output

        # Process each retrieved result
        for i in range(len(ids[0])):
            distance = distances[0][i]
=======
        if not results["ids"] or not results["ids"][0]:
            return output

        # Process each retrieved result
        for i in range(len(results["ids"][0])):
            distance = results["distances"][0][i]
>>>>>>> c8d397a7424622aef1a2556a21e0a528e6306bb2

            # Convert cosine distance into a similarity score
            score = 1 - distance

            output.append(
                {
<<<<<<< HEAD
                    "id": ids[0][i],
                    "content": documents[0][i],
                    "document_name": metadatas[0][i]["document_name"],
                    "chunk_index": metadatas[0][i]["chunk_index"],
=======
                    "id": results["ids"][0][i],
                    "content": results["documents"][0][i],
                    "document_name": results["metadatas"][0][i]["document_name"],
                    "chunk_index": results["metadatas"][0][i]["chunk_index"],
>>>>>>> c8d397a7424622aef1a2556a21e0a528e6306bb2
                    "score": round(float(score), 4),
                }
            )

        return output

<<<<<<< HEAD
    def list_documents(self, user_id: int) -> List[str]:
        # Retrieve metadata for all chunks belonging to this user
        all_items = self.collection.get(
            where={"user_id": user_id},
            include=cast(Include, ["metadatas"]),
        )

        # Extract unique document names
        stored_metadatas = all_items.get("metadatas") or []
        names = {
            m["document_name"]
            for m in stored_metadatas
            if m and isinstance(m.get("document_name"), str)
        }

        return sorted(cast(List[str], list(names)))

    def delete_document(self, document_name: str, user_id: int) -> None:
        # Delete all chunks belonging to the specified document AND this user,
        # so one account can never delete another account's document.
        self.collection.delete(
            where={
                "$and": [
                    {"document_name": document_name},
                    {"user_id": user_id},
                ]
            }
        )

        logger.info(
            f"Document '{document_name}' was deleted from the vector "
            f"store for user {user_id}."
=======
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
>>>>>>> c8d397a7424622aef1a2556a21e0a528e6306bb2
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
