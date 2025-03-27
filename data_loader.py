# data_loader.py
import os
import json
from config import settings

def load_visa_data() -> dict:
    """
    Load the visa data from the configured JSON file.
    Raise an error if the file does not exist.
    """
    if not os.path.exists(settings.visa_data_path):
        raise FileNotFoundError(f"Visa data file not found: {settings.visa_data_path}")
    
    with open(settings.visa_data_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    return data
