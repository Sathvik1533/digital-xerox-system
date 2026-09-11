import io
from fastapi.testclient import TestClient


def test_upload_document_success(client: TestClient, aws_env):
    """Test successful document upload with S3 and DynamoDB persistence."""
    file_content = b"%PDF-1.4 Mock PDF file content for testing"
    files = {
        "file": ("syllabus.pdf", io.BytesIO(file_content), "application/pdf")
    }
    data = {
        "student_id": "STU-2026-001"
    }

    response = client.post("/documents/", files=files, data=data)
    assert response.status_code == 201

    resp_data = response.json()
    doc_id = resp_data["document_id"]
    assert doc_id.startswith("") and len(doc_id) > 10
    assert resp_data["student_id"] == "STU-2026-001"
    assert resp_data["filename"] == "syllabus.pdf"
    assert resp_data["content_type"] == "application/pdf"
    assert resp_data["size_bytes"] == len(file_content)
    assert "download_url" in resp_data
    assert resp_data["s3_key"] == f"documents/STU-2026-001/{doc_id}_syllabus.pdf"

    # Verify S3 actual file storage directly
    s3 = aws_env["s3"]
    s3_obj = s3.get_object(Bucket="digital-xerox-documents", Key=resp_data["s3_key"])
    assert s3_obj["Body"].read() == file_content
    assert s3_obj["ContentType"] == "application/pdf"

    # Verify DynamoDB document metadata directly
    table = aws_env["table"]
    ddb_res = table.get_item(Key={"PK": f"DOC#{doc_id}", "SK": f"DOC#{doc_id}"})
    assert "Item" in ddb_res
    item = ddb_res["Item"]
    assert item["document_id"] == doc_id
    assert item["student_id"] == "STU-2026-001"
    assert item["filename"] == "syllabus.pdf"
    assert item["size_bytes"] == len(file_content)
    assert item["s3_key"] == resp_data["s3_key"]


def test_upload_alias_endpoint(client: TestClient):
    """Test POST /documents/upload alias endpoint."""
    file_content = b"Sample text document for printing."
    files = {
        "file": ("notes.txt", io.BytesIO(file_content), "text/plain")
    }
    data = {"student_id": "STU-2026-002"}

    response = client.post("/documents/upload", files=files, data=data)
    assert response.status_code == 201
    assert response.json()["filename"] == "notes.txt"


def test_upload_image_document(client: TestClient):
    """Test image upload (e.g. ID card or handwritten notes photo)."""
    file_content = b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDRmock"
    files = {
        "file": ("id_card.png", io.BytesIO(file_content), "image/png")
    }
    response = client.post("/documents/", files=files, data={"student_id": "STU-003"})
    assert response.status_code == 201
    assert response.json()["content_type"] == "image/png"


def test_upload_empty_file_rejected(client: TestClient):
    """Test that empty file (0 bytes) is rejected with 400."""
    files = {
        "file": ("empty.pdf", io.BytesIO(b""), "application/pdf")
    }
    response = client.post("/documents/", files=files, data={"student_id": "STU-001"})
    assert response.status_code == 400
    detail = response.json()["detail"]
    assert detail["error"]["code"] == "EMPTY_FILE"


def test_upload_unsupported_file_type(client: TestClient):
    """Test that unsupported file type (.exe) is rejected with 400."""
    files = {
        "file": ("malicious.exe", io.BytesIO(b"MZ\x90\x00\x03\x00\x00\x00"), "application/x-msdownload")
    }
    response = client.post("/documents/", files=files, data={"student_id": "STU-001"})
    assert response.status_code == 400
    detail = response.json()["detail"]
    assert detail["error"]["code"] == "UNSUPPORTED_FILE_TYPE"


def test_upload_oversized_file_rejected(client: TestClient, monkeypatch):
    """Test that file exceeding max_upload_size_bytes is rejected with 400."""
    from app.core.config import get_settings
    # Set limit temporarily to 50 bytes
    settings = get_settings()
    monkeypatch.setattr(settings, "max_upload_size_bytes", 50)

    files = {
        "file": ("large.pdf", io.BytesIO(b"A" * 100), "application/pdf")
    }
    response = client.post("/documents/", files=files, data={"student_id": "STU-001"})
    assert response.status_code == 400
    detail = response.json()["detail"]
    assert detail["error"]["code"] == "FILE_TOO_LARGE"


def test_get_document_metadata_success(client: TestClient):
    """Test retrieving document metadata by ID via GET /documents/{id}."""
    # First upload
    files = {
        "file": ("lab_report.docx", io.BytesIO(b"Docx binary mock content"), "application/vnd.openxmlformats-officedocument.wordprocessingml.document")
    }
    upload_res = client.post("/documents/", files=files, data={"student_id": "STU-LAB-01"})
    assert upload_res.status_code == 201
    doc_id = upload_res.json()["document_id"]

    # Retrieve by ID
    get_res = client.get(f"/documents/{doc_id}")
    assert get_res.status_code == 200
    data = get_res.json()
    assert data["document_id"] == doc_id
    assert data["filename"] == "lab_report.docx"
    assert data["student_id"] == "STU-LAB-01"
    assert "download_url" in data


def test_get_document_metadata_not_found(client: TestClient):
    """Test retrieving a non-existent document ID returns 404."""
    response = client.get("/documents/non-existent-doc-999")
    assert response.status_code == 404
    detail = response.json()["detail"]
    assert detail["error"]["code"] == "DOCUMENT_NOT_FOUND"


def test_get_document_access_url(client: TestClient):
    """Test generating a secure presigned access URL via GET /documents/{id}/access."""
    files = {
        "file": ("assignment.pdf", io.BytesIO(b"%PDF mock"), "application/pdf")
    }
    upload_res = client.post("/documents/", files=files, data={"student_id": "STU-001"})
    doc_id = upload_res.json()["document_id"]

    access_res = client.get(f"/documents/{doc_id}/access")
    assert access_res.status_code == 200
    data = access_res.json()
    assert data["document_id"] == doc_id
    assert data["filename"] == "assignment.pdf"
    assert "download_url" in data
    assert data["expires_in_seconds"] == 3600


def test_student_ui_served(client: TestClient):
    """Test that the Student UI HTML is served at GET / and GET /upload."""
    res_root = client.get("/")
    assert res_root.status_code == 200
    assert "text/html" in res_root.headers.get("content-type", "")
    assert "Digital Xerox &amp; Stationery System" in res_root.text or "Digital Xerox" in res_root.text
    assert "Slice 1: Document Upload" in res_root.text

    res_upload = client.get("/upload")
    assert res_upload.status_code == 200
    assert "text/html" in res_upload.headers.get("content-type", "")
