from fastapi import UploadFile, HTTPException
import asyncio
import fitz  # PyMuPDF
from data_cleanser import clean_text

def extract_text_from_pdf(data: bytes) -> str:
    """
    Extract text from a PDF byte stream using PyMuPDF.
    Uses a context manager to ensure the document is closed.
    """
    try:
        with fitz.open(stream=data, filetype="pdf") as doc:
            text = ""
            for page in doc:
                page_text = page.get_text()
                if page_text:
                    text += page_text + "\n"
        return text
    except fitz.FileDataError as e:
        raise Exception(f"The file data is invalid or corrupted: {e}")
    except fitz.PDFEncryptionError as e:
        raise Exception(f"The PDF is encrypted and cannot be processed: {e}")
    except fitz.FitzError as e:
        raise Exception(f"An error occurred processing the PDF: {e}")

async def process_pdf(file: UploadFile) -> str:
    """
    Asynchronously process a PDF file:
    - Read file bytes.
    - Extract text using PyMuPDF.
    - Clean the extracted text.
    Returns the cleaned text.
    """
    file_bytes = await file.read()
    
    if not file_bytes:
        raise HTTPException(status_code=400, detail="Uploaded PDF is empty.")
    
    try:
        # Run the blocking PDF extraction in a separate thread.
        extracted_text = await asyncio.to_thread(extract_text_from_pdf, file_bytes)
    except asyncio.TimeoutError:
        raise HTTPException(status_code=504, detail="Processing timed out.")
    except asyncio.CancelledError:
        # Optionally log or perform cleanup before re-raising
        raise HTTPException(status_code=503, detail="Processing was cancelled.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
    # Validate that the extracted text is not empty
    if not extracted_text.strip():
        raise HTTPException(status_code=400, detail="No text could be extracted from the PDF.")
    
    # Clean the extracted text.
    cleaned_text = clean_text(extracted_text.strip())
    
    if not cleaned_text:
        raise HTTPException(status_code=400, detail="No text could be extracted from the PDF.")
    
    print(cleaned_text)
    return cleaned_text

async def process_docx(file: UploadFile) -> str:
    """
    Asynchronously process a DOCX file and return the extracted text.
    TODO: Implement DOCX extraction logic using python-docx or similar.
    """
    # content = await file.read() # Not needed if using a library that accepts file-like objects.
    # TODO: Extract text from DOCX file.
    return "Extracted text from DOCX."

async def process_text(file: UploadFile) -> str:
    """
    Asynchronously process a plain text file and return its decoded content.
    """
    content = await file.read()
    return content.decode('utf-8')
