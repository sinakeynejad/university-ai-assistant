from fastapi import APIRouter, HTTPException

from fastapi.responses import StreamingResponse

from app.rag.pipeline import answer_question_stream

from app.schemas import ChatRequest

from app.utils.logger import get_logger

router = APIRouter(prefix="/api/chat", tags=["chat"])
logger = get_logger(__name__)

@router.post("")
def chat(request: ChatRequest):
    try:
        logger.info(f"Incoming query: {request.question}")
        
        return StreamingResponse(
            answer_question_stream(
                question=request.question,
                history=request.history,
                top_k=request.top_k
            ),
            media_type="application/x-ndjson"
        )

    except Exception as exc:
        logger.exception("Error in processing streaming chat request")
        raise HTTPException(
            status_code=500,
            detail=f"Internal Server Error: {exc}"
        ) from exc