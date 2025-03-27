import os
import yaml
from pydantic import BaseModel, ValidationError
from dotenv import load_dotenv

# Load environment variables from .env file (if present)
load_dotenv(override=True)

class Settings(BaseModel):
    visa_data_path: str
    llm_api_endpoint: str
    llm_model: str
    openai_api_key: str

def load_settings() -> Settings:
    # Path to YAML configuration file.
    config_file = os.path.join(os.path.dirname(__file__), "config.yaml")
    
    if not os.path.exists(config_file):
        raise FileNotFoundError(f"Configuration file not found: {config_file}")
    
    with open(config_file, "r", encoding="utf-8") as f:
        try:
            config_dict = yaml.safe_load(f)
        except yaml.YAMLError as e:
            raise Exception(f"Error parsing configuration file: {e}")
    
    # Do not load the OpenAI API key from YAML.
    # Instead, load it from the environment.
    openai_api_key = os.environ.get("OPENAI_API_KEY")
    if not openai_api_key:
        raise EnvironmentError("OPENAI_API_KEY not found in environment variables or .env file.")
    
    config_dict["openai_api_key"] = openai_api_key
    
    try:
        settings = Settings(**config_dict)
    except ValidationError as e:
        raise Exception(f"Configuration validation error: {e}")
    
    return settings

settings = load_settings()
