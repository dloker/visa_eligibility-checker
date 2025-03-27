# test_main.py
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_analyze_cv_unsupported_file():
    response = client.post(
        "/analyze_cv",
        files={"cv": ("test.exe", b"dummy data")}
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "Unsupported file type."

def test_analyze_cv_pdf_empty():
    # This test simulates an empty PDF file.
    response = client.post("/analyze_cv", files={"cv": ("empty.pdf", b"")})
    assert response.status_code == 400
    assert "Uploaded PDF is empty" in response.json()["detail"]