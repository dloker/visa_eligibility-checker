# data_cleanser.py
import re

# This cleansing could become very complex if we needed it to be, including building
# extraction scripts for education, work experience, etc. For now, since we have
# limited time and are feeding this to an LLM, we will allow the LLM to parse it for us.
# NOTE: For PII - we may want to also stripe names, emails, phone numbers, etc.

def clean_text(text: str) -> str:
    """
    Clean the input text by:
    - Removing non-ASCII characters (thus stripping non-English characters).
    - Collapsing extra whitespace (newlines, tabs, multiple spaces).
    - Stripping leading and trailing whitespace.
    
    :param text: The raw text string to be cleaned.
    :return: A cleaned version of the text.
    """
    # Remove non-ASCII characters (this strips out non-English letters)
    text = text.encode('ascii', errors='ignore').decode('ascii')
    
    # Remove email addresses
    text = re.sub(r'\S+@\S+', '', text)
    
    # Remove phone numbers (naively matches formats like 123-456-7890, (123) 456-7890, 1234567890)
    text = re.sub(r'\(?\b\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b', '', text)
    
    # Remove physical addresses (naively matches patterns like "123 Main St", "456 Elm Avenue")
    # This pattern looks for one or more digits, followed by up to 3 words, then a common street keyword.
    text = re.sub(
        r'\b\d+\s+(?:[A-Za-z]+\s){0,3}(?:Street|St|Avenue|Ave|Road|Rd|Boulevard|Blvd|Lane|Ln|Drive|Dr)\b',
        '',
        text,
        flags=re.IGNORECASE
    )
    
    # Collapse multiple consecutive spaces (but preserve newlines and tabs)
    text = re.sub(r' {2,}', ' ', text)
    
    # If needed, remove any other "strange" characters
    allowed_chars = re.compile(r'[^A-Za-z0-9\s.,!+%$?;:/\-\'"\n\t]')
    text = allowed_chars.sub('', text)
    
    # Strip leading/trailing whitespace from each line while preserving line breaks and tabs.
    lines = text.splitlines()
    lines = [line.strip() for line in lines]
    text = "\n".join(lines)
    
    return text
