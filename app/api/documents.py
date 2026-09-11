from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status

from app.schemas.document import DocumentAccessResponse, DocumentResponse
from app.services.document_service import (
    DocumentNotFoundError,
    DocumentService,
    DocumentValidationError,
)

router = APIRouter()


def get_document_service() -> DocumentService:
    return DocumentService()


@router.post(
    "",
    response_model=DocumentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Upload a student document",
)
@router.post(
    "/",
    response_model=DocumentResponse,
    status_code=status.HTTP_201_CREATED,
    include_in_schema=False,
)
@router.post(
    "/upload",
    response_model=DocumentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Upload a student document (alias)",
)
def upload_document(
    file: UploadFile = File(...),
    student_id: str = Form("anonymous"),
    service: DocumentService = Depends(get_document_service),
):
    """
    Vertical Slice 1: Student Document Upload.
    Flow: Validate file → Store in S3 → Save metadata in DynamoDB → Return DocumentResponse.
    """
    try:
        document = service.upload_document(file, student_id)
        # Optionally generate presigned download URL for immediate preview/access
        _, download_url = service.get_document_access(document.document_id)
        response_data = document.model_dump()
        response_data["download_url"] = download_url
        return DocumentResponse(**response_data)
    except DocumentValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error": {"code": e.code, "message": e.message}},
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": {"code": "UPLOAD_FAILED", "message": f"Document upload failed: {str(e)}"}},
        )


@router.get(
    "/{document_id}",
    response_model=DocumentResponse,
    summary="Get document metadata from DynamoDB",
)
def get_document(
    document_id: str,
    service: DocumentService = Depends(get_document_service),
):
    """Retrieve document metadata by document ID from DynamoDB."""
    try:
        document = service.get_document(document_id)
        _, download_url = service.get_document_access(document.document_id)
        response_data = document.model_dump()
        response_data["download_url"] = download_url
        return DocumentResponse(**response_data)
    except DocumentNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": {"code": e.code, "message": e.message}},
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": {"code": "INTERNAL_ERROR", "message": str(e)}},
        )


@router.get(
    "/{document_id}/access",
    response_model=DocumentAccessResponse,
    summary="Get secure presigned URL for document access",
)
def get_document_access(
    document_id: str,
    service: DocumentService = Depends(get_document_service),
):
    """Generate a secure, time-limited presigned S3 URL for controlled document access (FR-DOC-003)."""
    try:
        document, download_url = service.get_document_access(document_id)
        return DocumentAccessResponse(
            document_id=document.document_id,
            filename=document.filename,
            download_url=download_url,
            expires_in_seconds=3600,
        )
    except DocumentNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": {"code": e.code, "message": e.message}},
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": {"code": "INTERNAL_ERROR", "message": str(e)}},
        )
