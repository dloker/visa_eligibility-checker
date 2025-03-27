# tests/test_file_processing.py
import os
import pytest
from io import BytesIO
from fastapi import UploadFile
from file_processing import process_pdf

@pytest.mark.asyncio
async def test_resume_parsing_pdf():
    # Path to the test PDF file in the tests folder.
    pdf_path = os.path.join(os.path.dirname(__file__), "testResume.pdf")
    if not os.path.exists(pdf_path):
        pytest.skip("testResume.pdf file not found in tests folder.")
    
    # Read the PDF file bytes.
    with open(pdf_path, "rb") as f:
        content = f.read()
    
    # Create a dummy UploadFile instance using an in-memory BytesIO stream.
    dummy_file = UploadFile(filename="testResume.pdf", file=BytesIO(content))
    
    # Call process_pdf to extract text from the PDF.
    extracted_text = await process_pdf(dummy_file)
    
    # Assert that some text is extracted.
    assert extracted_text.strip(), "Extracted text should not be empty."
    
    # Further assertions can be made to check for expected keywords
    # in the resume, e.g.:
    assert "Experience" in extracted_text or "Education" in extracted_text
