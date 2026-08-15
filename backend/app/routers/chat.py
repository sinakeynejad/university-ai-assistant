from fastapi import APIRouter, HTTPException

from app.rag.pipeline import answer_question

from app.schemas import ChatRequest, ChatResponse


from app.utils.logger import get_logger


# Create router for chat-related endpoints
router = APIRouter(prefix="/api/chat", tags=["chat"])

# Initialize application logger
logger = get_logger(__name__)


# Chat endpoint
@router.post("", response_model=ChatResponse)
def chat(request: ChatRequest) -> ChatResponse:
    try:
        # Generate answer using RAG pipeline
        result = answer_question(
            question=request.question,
            history=request.history,
            top_k=request.top_k
        )

        # Return formatted chat response
        return ChatResponse(
            answer=result["answer"],
            sources=result["sources"]
        )

    except Exception as exc:
        # Log unexpected errors
        logger.exception("Error in processing chat request")

        # Return HTTP 500 response
        raise HTTPException(
            status_code=500,
            detail=f"Internal Server Error: {exc}"
        ) from exc
