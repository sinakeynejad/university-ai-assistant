from pathlib import Path
from typing import List

from fastapi import UploadFile, APIRouter, HTTPException, File

from app.config import get_settings
from app.utils.logger import get_logger
from app.schemas import (
    DocumentInfo,
    DocumentListResponse,
    DeleteResponse,
    UploadResponse,
)
from app.rag.loaders import extract_text
from app.rag.pipeline import ingest_document
from app.rag.vector_store import get_vector_store


# Create router for document-related endpoints
router = APIRouter(prefix="/api/documents", tags=["documents"])

# Initialize application logger
logger = get_logger(__name__)

# Supported document formats
ALLOWED_EXTENSIONS = {".txt", ".md"}


# Upload and process documents
@router.post("/upload", response_model=UploadResponse)
async def upload_documents(
    files: List[UploadFile] = File(...)
) -> UploadResponse:

    # Get application settings and create upload directory
    settings = get_settings()
    upload_dir = Path(settings.UPLOAD_DIR)
    upload_dir.mkdir(parents=True, exist_ok=True)

    # Store information about processed documents
    results: List[DocumentInfo] = []

    for file in files:

        # Get the file extension
        suffix = Path(file.filename).suffix.lower()

        # Check if the file format is supported
        if suffix not in ALLOWED_EXTENSIONS:
            raise HTTPException(
                status_code=400,
                detail=(
                    f"File format {file.filename} is not supported. "
                    f"Allowed formats: {sorted(ALLOWED_EXTENSIONS)}"
                )
            )

        # Save the uploaded file
        destination = upload_dir / file.filename
        content = await file.read()
        destination.write_bytes(content)

        try:
            # Extract text and add document chunks to vector database
            raw_text = extract_text(destination)
            chunks_count = ingest_document(file.filename, raw_text)

        except Exception as exc:
            # Log unexpected processing errors
            logger.exception(f"Error processing file: {file.filename}")

            raise HTTPException(
                status_code=500,
                detail=f"Error processing file {file.filename}: {exc}"
            ) from exc

        # Add document information to the response
        results.append(
            DocumentInfo(
                document_name=file.filename,
                chunks_count=chunks_count
            )
        )

    return UploadResponse(
        message=f"{len(results)} files added to vector database",
        documents=results
    )


# Get the list of stored documents
@router.get("", response_model=DocumentListResponse)
def list_documents() -> DocumentListResponse:

    # Get the vector store instance
    vector_store = get_vector_store()

    return DocumentListResponse(
        documents=vector_store.list_documents()
    )


# Delete a document from the vector database
@router.delete("/{document_name}", response_model=DeleteResponse)
def delete_document(document_name: str) -> DeleteResponse:

    # Get the vector store instance
    vector_store = get_vector_store()

    # Delete the document and its chunks
    vector_store.delete_document(document_name)

    return DeleteResponse(
        message=f"{document_name} deleted successfully"
    )
