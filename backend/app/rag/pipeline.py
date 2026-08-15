from typing import List, Dict, Optional

from app.config import get_settings
from app.rag.embeddings import get_embedding_model
from app.rag.vector_store import get_vector_store
from app.rag.llm import get_llm_client
from app.schemas import ChatMessage, SourceChunk
from app.utils.logger import get_logger


# Initialize application logger
logger = get_logger(__name__)


# System instructions for the LLM
SYSTEM_PROMPT = """تو دستیار هوشمند دانشگاه خواجه نصیرالدین طوسی هستی.
فقط بر اساس «متن‌های مرجع» ارائه‌شده به سوال کاربر پاسخ بده.
اگر پاسخ سوال در متن‌های مرجع موجود نیست، صادقانه بگو که اطلاعات کافی
در اسناد موجود نیست و حدس نزن.
پاسخ را به زبان فارسی، روشن و مختصر بنویس."""


# Build a single context string from retrieved chunks
def _build_context_block(chunks: List[dict]) -> str:
    parts = []

    for idx, c in enumerate(chunks, start=1):
        parts.append(
            f"[متن مرجع {idx} - سند: {c['document_name']}]\n{c['content']}"
        )

    return "\n\n".join(parts)


# Build the message list sent to the LLM
def _build_messages(
    question: str,
    context_chunks: List[dict],
    history: Optional[List[ChatMessage]]
) -> List[Dict[str, str]]:

    # Start with the system prompt
    messages: List[Dict[str, str]] = [
        {"role": "system", "content": SYSTEM_PROMPT}
    ]

    # Add the last few conversation messages to preserve context
    if history:
        for h in history[-6:]:
            messages.append({
                "role": h.role,
                "content": h.content
            })

    # Build context from retrieved chunks
    context_block = _build_context_block(context_chunks)

    # Combine retrieved context and user's question
    user_content = (
        f"متن‌های مرجع:\n{context_block}\n\n"
        f"سوال کاربر: {question}"
        if context_chunks
        else f"هیچ متن مرجعی یافت نشد.\n\nسوال کاربر: {question}"
    )

    messages.append({
        "role": "user",
        "content": user_content
    })

    return messages


# Answer a user question using the RAG pipeline
def answer_question(
    question: str,
    history: Optional[List[ChatMessage]] = None,
    top_k: Optional[int] = None
) -> Dict:

    # Load application settings
    settings = get_settings()

    # Use the provided top_k or fall back to the default setting
    k = top_k or settings.TOP_K

    # Initialize RAG components
    embedding_model = get_embedding_model()
    vector_store = get_vector_store()
    llm_client = get_llm_client()

    # Convert the user's question into an embedding vector
    query_embedding = embedding_model.embed_query(question)

    # Retrieve the most relevant chunks from the vector database
    retrieved_chunks = vector_store.similarity_search(
        query_embedding,
        top_k=k
    )

    logger.info(
        f"{len(retrieved_chunks)} relevant chunks retrieved for the question."
    )

    # Build the prompt messages using context and conversation history
    messages = _build_messages(
        question,
        retrieved_chunks,
        history
    )

    # Generate the final answer using the LLM
    answer_text = llm_client.generate(messages)

    # Convert retrieved chunks into SourceChunk objects
    sources = [
        SourceChunk(
            document_name=c["document_name"],
            chunk_index=c["chunk_index"],
            content=c["content"],
            score=c["score"],
        )
        for c in retrieved_chunks
    ]

    return {
        "answer": answer_text,
        "sources": sources
    }


# Process a document and store its chunks in the vector database
def ingest_document(document_name: str, raw_text: str) -> int:
    from app.rag.chunking import chunk_text

    # Load application settings
    settings = get_settings()

    # Split document text into smaller chunks
    chunks = chunk_text(
        raw_text,
        chunk_size=settings.CHUNK_SIZE,
        chunk_overlap=settings.CHUNK_OVERLAP
    )

    # Stop if no chunks were generated
    if not chunks:
        logger.warning(
            f"No chunks were generated from document '{document_name}'."
        )
        return 0

    # Initialize embedding model and vector store
    embedding_model = get_embedding_model()
    vector_store = get_vector_store()

    # Convert chunks into embedding vectors
    embeddings = embedding_model.embed_documents(chunks)

    # Store chunks and embeddings in the vector database
    return vector_store.add_chunks(
        document_name,
        chunks,
        embeddings
    )
