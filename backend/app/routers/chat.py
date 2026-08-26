<<<<<<< HEAD
=======
<<<<<<< HEAD
>>>>>>> c8d397a7424622aef1a2556a21e0a528e6306bb2
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.rag.pipeline import answer_question_stream
from app.schemas import ChatRequest
from app.utils.logger import get_logger

# Auth dependencies
from ..auth.deps import get_current_user, get_db
from ..auth.database import User
<<<<<<< HEAD
=======
=======
from fastapi import APIRouter, HTTPException

from fastapi.responses import StreamingResponse

from app.rag.pipeline import answer_question_stream

from app.schemas import ChatRequest

from app.utils.logger import get_logger
>>>>>>> 0dc051b2d9e72a4d21d7512f38cfc10a442035df
>>>>>>> c8d397a7424622aef1a2556a21e0a528e6306bb2

router = APIRouter(prefix="/api/chat", tags=["chat"])
logger = get_logger(__name__)

<<<<<<< HEAD
=======
<<<<<<< HEAD
>>>>>>> c8d397a7424622aef1a2556a21e0a528e6306bb2

@router.post("")
def chat(
    request: ChatRequest,
<<<<<<< HEAD
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
=======
    current_user: User = Depends(get_current_user),   # <-- requires login
    db: Session = Depends(get_db)                     # optional, for saving history
>>>>>>> c8d397a7424622aef1a2556a21e0a528e6306bb2
):
    try:
        logger.info(f"User {current_user.id} asked: {request.question}")

<<<<<<< HEAD
        return StreamingResponse(
            answer_question_stream(
                question=request.question,
                user_id=current_user.id,
=======
=======
@router.post("")
def chat(request: ChatRequest):
    try:
        logger.info(f"Incoming query: {request.question}")
        
>>>>>>> 0dc051b2d9e72a4d21d7512f38cfc10a442035df
        return StreamingResponse(
            answer_question_stream(
                question=request.question,
>>>>>>> c8d397a7424622aef1a2556a21e0a528e6306bb2
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
<<<<<<< HEAD
        ) from exc
=======
        ) from exc
>>>>>>> c8d397a7424622aef1a2556a21e0a528e6306bb2
