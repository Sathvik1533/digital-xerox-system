import io
import os
import re
import uuid
from datetime import datetime, timezone
from fastapi import UploadFile

from app.core.config import get_settings
from app.models.document import Document
from app.repositories.dynamodb_repo import DynamoDBRepository
from app.repositories.s3_repo import S3Repository


class DocumentValidationError(Exception):
    """Raised when document validation fails (size, type, empty content)."""

    def __init__(self, code: str, message: str):
        self.code = code
        self.message = message
        super().__init__(message)


class DocumentNotFoundError(Exception):
    """Raised when a requested document is not found."""

    def __init__(self, document_id: str):
        self.code = "DOCUMENT_NOT_FOUND"
        self.message = f"Document '{document_id}' not found"
        super().__init__(self.message)


class DocumentService:
    def __init__(
        self,
        s3_repo: S3Repository | None = None,
        db_repo: DynamoDBRepository | None = None,
    ):
        self.s3_repo = s3_repo or S3Repository()
        self.db_repo = db_repo or DynamoDBRepository()
        self.settings = get_settings()

    def _sanitize_filename(self, filename: str) -> str:
        """Sanitize filename to prevent path traversal and unwanted characters."""
        base = os.path.basename(filename)
        # Keep alphanumeric, dot, dash, underscore
        sanitized = re.sub(r"[^a-zA-Z0-9._-]", "_", base)
        return sanitized or "document"

    def _validate_file(self, filename: str, content: bytes, content_type: str | None) -> None:
        """Validate file according to FR-DOC-001 (supported types, max size, non-empty)."""
        if not content or len(content) == 0:
            raise DocumentValidationError("EMPTY_FILE", "Uploaded document cannot be empty.")

        if len(content) > self.settings.max_upload_size_bytes:
            max_mb = self.settings.max_upload_size_bytes / (1024 * 1024)
            raise DocumentValidationError(
                "FILE_TOO_LARGE",
                f"File size exceeds maximum allowed limit of {max_mb:.0f} MB.",
            )

        # Check extension
        ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
        if ext not in self.settings.allowed_file_extensions:
            allowed = ", ".join(self.settings.allowed_file_extensions)
            raise DocumentValidationError(
                "UNSUPPORTED_FILE_TYPE",
                f"File extension '.{ext}' is not supported. Allowed formats: {allowed}.",
            )

    def upload_document(self, file: UploadFile, student_id: str = "anonymous") -> Document:
        """
        Validate, store document in S3, and record metadata in DynamoDB.
        Full end-to-end slice implementation for Vertical Slice 1.
        """
        raw_filename = file.filename or "unknown"
        sanitized_filename = self._sanitize_filename(raw_filename)

        # Read content to validate size and non-emptiness reliably
        file.file.seek(0)
        content = file.file.read()

        # Validate file
        self._validate_file(sanitized_filename, content, file.content_type)

        document_id = str(uuid.uuid4())
        s3_key = f"documents/{student_id}/{document_id}_{sanitized_filename}"
        content_type = file.content_type or "application/octet-stream"

        # 1. S3 actual file storage
        self.s3_repo.upload_file(io.BytesIO(content), s3_key, content_type=content_type)

        # 2. DynamoDB document metadata
        document = Document(
            document_id=document_id,
            student_id=student_id,
            filename=sanitized_filename,
            s3_key=s3_key,
            content_type=content_type,
            size_bytes=len(content),
            uploaded_at=datetime.now(timezone.utc),
        )
        self.db_repo.save_document(document)

        return document

    def get_document(self, document_id: str) -> Document:
        """Retrieve document metadata from DynamoDB."""
        doc = self.db_repo.get_document(document_id)
        if not doc:
            raise DocumentNotFoundError(document_id)
        return doc

    def get_document_access(self, document_id: str, expiration: int = 3600) -> tuple[Document, str]:
        """Generate a secure presigned access URL for the document (FR-DOC-003)."""
        doc = self.get_document(document_id)
        download_url = self.s3_repo.generate_presigned_url(doc.s3_key, expiration=expiration)
        return doc, download_url
