from typing import List, Dict, Optional, Generator
import json

from app.config import get_settings
from app.rag.embeddings import get_embedding_model
from app.rag.vector_store import get_vector_store
from app.rag.llm import get_llm_client
from app.schemas import ChatMessage, SourceChunk
from app.utils.logger import get_logger


# Initialize application logger
logger = get_logger(__name__)


# System instructions for the LLM
SYSTEM_PROMPT = """تو دستیار هوشمند دانشگاه صنعتی خواجه نصیرالدین طوسی هستی.

قوانین پاسخ‌دهی:
۱. فقط بر اساس «متن‌های مرجع» ارائه‌شده به سوال کاربر پاسخ بده.
۲. حتماً دقیقاً در انتهای هر جمله، بند یا ادعایی که مطرح می‌کنی، شماره منبع مربوط به همان جمله را بلافاصله بنویس (مثال: «شرایط ثبت‌نام برای ترم جدید اعلام شد [منبع ۱].»).
۳. از آوردن تمام منابع به صورت یک‌جا در انتهای کل پاسخ اکیداً خودداری کن؛ منابع باید به‌صورت درون‌متنی و دقیقاً جلوی همان نکته مرتبط ذکر شوند.
۴. اگر یک نکته از چند متن برآمده است، همه را کنار همان جمله ذکر کن (مثلاً: [منبع ۱][منبع ۲]).
۵. اگر پاسخ سوال در متن‌های مرجع موجود نیست، صادقانه بگو که اطلاعات کافی در اسناد موجود نیست و از خودت حدس نزن.
۶. پاسخ را به زبان فارسی روان، روشن و ساختاریافته بنویس."""


# Build a single context string from retrieved chunks
def _build_context_block(chunks: List[dict]) -> str:
    parts = []

    for idx, c in enumerate(chunks, start=1):
        parts.append(
            f"--- [منبع {idx}] (نام سند: {c['document_name']}) ---\n{c['content']}"
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

QUERY_REWRITE_PROMPT = """تو یک دستیار بازنویسی سوال برای سیستم‌های جستجوی دانشگاهی هستی.
وظیفه تو این است که سوال محاوره‌ای، مبهم یا کوتاه کاربر را به یک پرسش دقیق، رسمی و حاوی کلیدواژه‌های اصلی آیین‌نامه‌ها و قوانین دانشگاهی تبدیل کنی تا جستجو در پایگاه داده متنی بهتر انجام شود.

قوانین:
۱. فقط و فقط عبارت بازنویسی‌شده را خروجی بده و هیچ توضیحات اضافه، سلام یا مقدمه‌ای ننویس.
۲. مفاهیم و کلیدواژه‌های اصلی سوال را حفظ کن.
۳. اگر سوال از قبل کاملاً شفاف و رسمی است، همان را بدون تغییر برگردان.

سوال کاربر: {question}
پاسخ بازنویسی‌شده:"""


def rewrite_query(question: str) -> str:
    """Rewrite a user query into a formal, keyword-rich search query."""
    llm_client = get_llm_client()
    
    messages = [
        {
            "role": "user",
            "content": QUERY_REWRITE_PROMPT.format(question=question)
        }
    ]
    
    try:
        rewritten = llm_client.generate(messages).strip()
        logger.info(f"Original Query: '{question}' -> Rewritten Query: '{rewritten}'")
        return rewritten if rewritten else question
    except Exception as e:
        logger.warning(f"Query rewriting failed: {e}. Falling back to original question.")
        return question

# Answer a user question using the RAG pipeline (Non-streaming)
def answer_question(
    question: str,
    history: Optional[List[ChatMessage]] = None,
    top_k: Optional[int] = None
) -> Dict:

    settings = get_settings()
    k = top_k or settings.TOP_K

    embedding_model = get_embedding_model()
    vector_store = get_vector_store()
    llm_client = get_llm_client()

    search_query = rewrite_query(question)
    query_embedding = embedding_model.embed_query(search_query)

    retrieved_chunks = vector_store.similarity_search(
        query_embedding,
        top_k=k
    )

    logger.info(
        f"{len(retrieved_chunks)} relevant chunks retrieved for the question."
    )

    messages = _build_messages(
        question,
        retrieved_chunks,
        history
    )

    answer_text = llm_client.generate(messages)

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


# Streaming variant for live chunk-by-chunk response
def answer_question_stream(
    question: str,
    history: Optional[List[ChatMessage]] = None,
    top_k: Optional[int] = None
) -> Generator[str, None, None]:
    """Stream answer chunks along with initial metadata (sources) using NDJSON protocol."""
    
    settings = get_settings()
    k = top_k or settings.TOP_K

    embedding_model = get_embedding_model()
    vector_store = get_vector_store()
    llm_client = get_llm_client()

    # STEP 1: Status - Query Rewriting
    yield json.dumps({"type": "status", "data": "در حال بازنویسی و تحلیل پرسش..."}) + "\n"
    search_query = rewrite_query(question)

    # STEP 2: Status - Search
    yield json.dumps({"type": "status", "data": "در حال جستجو در اسناد و قوانین دانشگاه..."}) + "\n"
    query_embedding = embedding_model.embed_query(search_query)

    # Retrieve chunks from vector store
    retrieved_chunks = vector_store.similarity_search(
        query_embedding,
        top_k=k
    )

    logger.info(
        f"{len(retrieved_chunks)} relevant chunks retrieved for streaming response."
    )

    # Build message chain
    messages = _build_messages(
        question,
        retrieved_chunks,
        history
    )

    # Prepare sources list
    sources_data = [
        {
            "document_name": c["document_name"],
            "chunk_index": c["chunk_index"],
            "content": c["content"],
            "score": c["score"],
        }
        for c in retrieved_chunks
    ]

    # Frame: Send sources payload line
    yield json.dumps({"type": "sources", "data": sources_data}) + "\n"

    # STEP 3: Status - Generating Answer
    yield json.dumps({"type": "status", "data": "در حال نگارش پاسخ نهایی..."}) + "\n"

    # Stream response text chunks from LLM line by line
    for text_chunk in llm_client.generate_stream(messages):
        yield json.dumps({"type": "text", "data": text_chunk}) + "\n"


# Process a document and store its chunks in the vector database
def ingest_document(document_name: str, raw_text: str) -> int:
    from app.rag.chunking import chunk_text

    settings = get_settings()

    chunks = chunk_text(
        raw_text,
        chunk_size=settings.CHUNK_SIZE,
        chunk_overlap=settings.CHUNK_OVERLAP
    )

    if not chunks:
        logger.warning(
            f"No chunks were generated from document '{document_name}'."
        )
        return 0

    embedding_model = get_embedding_model()
    vector_store = get_vector_store()

    embeddings = embedding_model.embed_documents(chunks)

    return vector_store.add_chunks(
        document_name,
        chunks,
        embeddings
    )