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
    Asynchronously process a plain text file.
    
    - Reads file content asynchronously.
    - Decodes the content using UTF-8 with error replacement to remove problematic characters.
    - If the replacement causes a significant reduction in length (indicating heavy corruption),
      raises an HTTPException.
    - Otherwise, cleans the decoded text to normalize spacing and remove unwanted elements.
    
    Returns:
        A cleaned version of the plain text content.
    """
    content = await file.read()
    # Decode with error replacement
    decoded = content.decode('utf-8', errors='replace')
    
    # Heuristically check if the decoded text is significantly shorter than the raw decoded version without errors.
    # Here we assume that if more than 20% of characters were replaced, it's likely a bad decode.
    # For a more robust solution, you could compare counts of the replacement character (�).
    replacement_char = "�"
    if decoded.count(replacement_char) > 0.2 * len(decoded):
        raise HTTPException(status_code=400, detail="Text file contains too many invalid characters.")
    
    # Clean the text (this step normalizes spacing while preserving newlines/tabs)
    cleaned = clean_text(decoded)
    return cleaned
