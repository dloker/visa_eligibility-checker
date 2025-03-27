import pytest
from io import BytesIO
from fastapi import UploadFile, HTTPException
from file_processing import process_text

@pytest.mark.asyncio
async def test_process_text_bad_characters():
    """
    Test process_text with a file that has invalid UTF-8 bytes.
    The high count of invalid characters should trigger an HTTPException.
    """
    # Create a bytes object with many invalid bytes (0xFF is invalid in UTF-8)
    invalid_bytes = b'\xff' * 100  # 100 bytes of 0xFF; likely >20% replacements
    dummy_file = UploadFile(filename="bad.txt", file=BytesIO(invalid_bytes))
    
    with pytest.raises(HTTPException) as exc_info:
        await process_text(dummy_file)
    
    # Verify the error message mentions too many invalid characters.
    assert "Text file contains too many invalid characters" in str(exc_info.value.detail)

@pytest.mark.asyncio
async def test_process_text_valid():
    """
    Test process_text with a valid text file.
    The function should decode the text and clean up extra spaces while preserving newlines and tabs.
    """
    # Create a sample valid text with extra spaces, newline, and a tab.
    valid_text = "This   is a   sample text.\nIt contains\ttabs and   multiple spaces."
    file_bytes = valid_text.encode('utf-8')
    dummy_file = UploadFile(filename="good.txt", file=BytesIO(file_bytes))
    
    result = await process_text(dummy_file)
    
    # Verify that the cleaned text is not empty.
    assert result.strip(), "Cleaned text should not be empty."
    
    # Check that extra spaces within lines are collapsed.
    # For instance, "This   is a   sample text." should become "This is a sample text."
    assert "This is a sample text." in result
    
    # Verify that newline characters are preserved.
    assert "\n" in result
    
    # Optionally check for tab preservation (if the cleanser is meant to preserve them).
    # You might also check for specific keywords that indicate tabs were not removed.
    assert "\t" in result or "tabs" in result
