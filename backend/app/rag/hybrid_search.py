"""
Hybrid search layer.

Combines semantic search results from ChromaDB
with lexical search results using Reciprocal Rank Fusion.
"""

from typing import Any, Dict, List

from app.rag.lexical_search import LexicalIndex
from functools import lru_cache
from app.rag.vector_store import get_vector_store


def reciprocal_rank_fusion(
    result_lists: List[List[Dict[str, Any]]],
    top_k: int,
    rrf_k: int = 60,
) -> List[Dict[str, Any]]:
    """
    Combine multiple ranked result lists using RRF.

    RRF does not require semantic and lexical scores
    to have the same numerical scale.
    """

    # Final results indexed by chunk ID
    fused: Dict[str, Dict[str, Any]] = {}

    # Process each search result list
    for result_list in result_lists:

        # rank starts at 1
        for rank, result in enumerate(
            result_list,
            start=1,
        ):

            # Use the real Chroma ID if available.
            #
            # For lexical results this ID is also stored
            # when the lexical index is built.
            chunk_id = result.get("id")

            # Fallback ID for old/legacy data
            if not chunk_id:
                chunk_id = (
                    f"{result.get('document_name', '')}"
                    f"::{result.get('chunk_index', '')}"
                )

            # Create entry if this chunk has not
            # appeared in another search result list.
            if chunk_id not in fused:
                fused[chunk_id] = {
                    **result,
                    "rrf_score": 0.0,
                }
            # RRF formula
            fused[chunk_id]["rrf_score"] += (
                1.0
                / (rrf_k + rank)
            )

    # Sort by final RRF score
    ranked_results = sorted(
        fused.values(),
        key=lambda result: result["rrf_score"],
        reverse=True,
    )

    # Return only final top-K results
    ranked_results = ranked_results[:top_k]

    for result in ranked_results:
        result["hybrid_score"] = round(
            result["rrf_score"],
            4,
        )
        result["score"] = result["hybrid_score"]

    return ranked_results


class HybridSearch:
    """
    Coordinates semantic and lexical retrieval.
    """

    def __init__(
        self,
        vector_store,
    ):
        # Existing ChromaDB VectorStore
        self.vector_store = vector_store

        # Build lexical index from ChromaDB
        self.lexical_index = LexicalIndex()

        self.refresh()

    def refresh(self) -> None:
        """
        Rebuild lexical index from the current
        contents of ChromaDB.
        """

        # Retrieve all stored chunks
        data = self.vector_store.collection.get(
            include=[
                "documents",
                "metadatas",
            ]
        )

        ids = data.get(
            "ids",
            [],
        )

        documents = data.get(
            "documents",
            [],
        )

        metadatas = data.get(
            "metadatas",
            [],
        )

        chunks = []

        # Convert Chroma data into our index format
        for index, content in enumerate(
            documents
        ):

            metadata = (
                metadatas[index]
                if index < len(metadatas)
                else {}
            )

            chunk_id = (
                ids[index]
                if index < len(ids)
                else None
            )

            chunks.append(
                {
                    "id": chunk_id,

                    "content": content,

                    "document_name": metadata.get(
                        "document_name",
                        "",
                    ),

                    "chunk_index": metadata.get(
                        "chunk_index",
                        index,
                    ),
                }
            )

        # Rebuild lexical index
        self.lexical_index.build(
            chunks
        )

    def search(
        self,
        query_text: str,
        query_embedding: List[float],
        top_k: int = 4,
    ) -> List[Dict[str, Any]]:
        """
        Perform hybrid search.

        1. Semantic search
        2. Lexical search
        3. RRF fusion
        """

        # Retrieve more candidates from each search
        # before fusion.
        candidate_k = max(
            top_k * 5,
            20,
        )

        # -----------------------------
        # Semantic Search
        # -----------------------------

        semantic_results = (
            self.vector_store.similarity_search(
                query_embedding=query_embedding,
                top_k=candidate_k,
            )
        )

        # -----------------------------
        # Lexical Search
        # -----------------------------

        lexical_results = (
            self.lexical_index.search(
                query=query_text,
                top_k=candidate_k,
            )
        )

        # -----------------------------
        # Combine results
        # -----------------------------

        fused_results = (
            reciprocal_rank_fusion(
                [
                    semantic_results,
                    lexical_results,
                ],
                top_k=top_k,
            )
        )

        return fused_results


@lru_cache
def get_hybrid_search() -> HybridSearch:
    """
    Create and cache the HybridSearch instance.
    """

    vector_store = get_vector_store()

    return HybridSearch(vector_store)
