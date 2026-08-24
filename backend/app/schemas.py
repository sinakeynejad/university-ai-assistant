from typing import List, Optional
from pydantic import Field, BaseModel


# Represents a single message in a conversation
class ChatMessage(BaseModel):
    # Message sender: "user" or "assistant"
    role: str = Field(..., description="user or assistant")

    # Message text content
    content: str


# Request model for sending a question to the chatbot
class ChatRequest(BaseModel):
    # User's question
    question: str = Field(..., min_length=1, description="User question")

    # Previous conversation messages for maintaining context
    history: Optional[List[ChatMessage]] = Field(
        default=None,
        description="Optional conversation history to preserve context"
    )

    # Number of relevant chunks retrieved from vector database
    top_k: Optional[int] = Field(
        default=None,
        description="Number of chunks retrieved from the vector database"
    )


# Represents a retrieved document chunk from the vector database
class SourceChunk(BaseModel):
    # Name of the original document
    document_name: str

    # Index of the chunk inside the document
    chunk_index: int

    # Text content of the chunk
    content: str

    # Similarity score between query and chunk
    score: float


# Response model returned by the chatbot
class ChatResponse(BaseModel):
    # Generated answer from the LLM
    answer: str

    # Retrieved sources used to generate the answer
    sources: List[SourceChunk]


# Information about an uploaded document
class DocumentInfo(BaseModel):
    # Document file name
    document_name: str

    # Number of chunks created from the document
    chunks_count: int


# Response after uploading documents
class UploadResponse(BaseModel):
    # Upload operation result message
    message: str

    # Information about uploaded documents
    documents: List[DocumentInfo]


# Response containing a list of available documents
class DocumentListResponse(BaseModel):
    # Names of stored documents
    documents: List[str]


# Response after deleting a document
class DeleteResponse(BaseModel):
    # Delete operation result message
    message: str
