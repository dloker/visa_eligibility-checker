System design and choices start around line 112.

# Visa Eligibility Checker

An AI-powered tool to analyze resumes for O‑1A visa eligibility. This project uses FastAPI, LangChain with OpenAI's GPT-4o, and various processing modules to extract, clean, and evaluate resume data based on USCIS criteria.

## Features

- **Resume Parsing:** Supports PDF, and TXT files.
- **Text Cleaning:** Removes non-ASCII characters, emails, phone numbers, and physical addresses while preserving formatting.
- **LLM Analysis:** Uses chain-of-thought prompting to evaluate resume evidence against 8 criteria (plus super-criteria) for O‑1A eligibility.
- **Asynchronous Execution:** Processes criteria concurrently for improved performance.
- **Configurable:** Uses a YAML file and a .env file (for the OpenAI API key) to configure the system.
- **Testing:** Comprehensive test suite using pytest and pytest-asyncio.

## Requirements

- Python 3.8+
- [FastAPI](https://fastapi.tiangolo.com/)
- [Uvicorn](https://www.uvicorn.org/)
- [LangChain](https://github.com/hwchase17/langchain) & [langchain-openai](https://pypi.org/project/langchain-openai/)
- [PyMuPDF (fitz)](https://pymupdf.readthedocs.io/)
- [python-dotenv](https://pypi.org/project/python-dotenv/)
- [PyYAML](https://pyyaml.org/)
- [Pydantic](https://pydantic-docs.helpmanual.io/)
- [pytest](https://docs.pytest.org/), [pytest-asyncio](https://pypi.org/project/pytest-asyncio/)

## Setup

1. **Clone the Repository:**
   ```bash
   git clone https://github.com/<your-username>/visa-eligibility-checker.git
   cd visa-eligibility-checker


2. **Create & Activate a Virtual Environment:**
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # Windows: .venv\Scripts\activate
   ```

3. **Install Dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure Environment Variables:**
   Create a `.env` file in the project root (do not commit this file). For example:
   ```
   OPENAI_API_KEY=your_openai_api_key_here
   ```

5. **Configure YAML Settings:**
   Ensure your `config.yaml` is set up correctly:
   ```yaml
   visa_data_path: "data/O1-A-visa.json"
   llm_api_endpoint: "https://api.openai.com/v1/chat/completions"
   llm_model: "gpt-4o"
   ```

## Running the Application

1. **Start the Server:**
   ```bash
   uvicorn main:app --reload
   ```
2. **Access the API Docs:**
   - Swagger UI: [http://localhost:8000/docs](http://localhost:8000/docs)
   - Redoc: [http://localhost:8000/redoc](http://localhost:8000/redoc)

## Using the API

- **Endpoint:** `/analyze_cv`
- **Method:** `POST`
- **Parameters:**
  - `cv` (file): The resume to analyze (supports PDF and TXT (and soon DOCX)).
  - `verbose` (query, boolean): Optional. Set to `true` to include detailed chain-of-thought reasoning.
- **Response:** Returns a JSON object with:
  - `eligibility_rating`: Overall eligibility ("low", "medium", or "high").
  - `criteria_results`: For each criterion, a rating (1–10) and a list of qualifying evidence (and optionally the chain-of-thought if `verbose` is `true`).

**Example cURL Request:**
```bash
curl -X POST "http://localhost:8000/analyze_cv?verbose=false" -F "cv=@/path/to/resume.pdf"
```

## Running Tests

Run the complete test suite using:
```bash
pytest tests/
```
This command will run all unit and integration tests, including tests for resume parsing, prompt generation, and LLM integration.

## Project Structure

```
visa-eligibility-checker/
├── main.py                # FastAPI app and endpoint definitions
├── config.py              # Configuration loader (YAML + .env)
├── data_loader.py         # Loader for O1-A-visa.json criteria data
├── file_processing.py     # Resume parsing functions (PDF, DOCX, TXT)
├── analysis.py            # LLM analysis and prompt building functions
├── data_cleanser.py       # Text cleaning utilities
├── data/
│   └── O1-A-visa.json     # Visa eligibility criteria and instructions
├── config.yaml            # YAML configuration file
├── .env                   # Environment file (contains OPENAI_API_KEY)
└── tests/                 # Test suite (unit and integration tests)
```

# System Design Document: O-1A Visa Eligibility Analysis Platform

## Objective

Build a local AI-driven application to assess a candidate’s eligibility for the O-1A nonimmigrant visa, based on their CV. The system should:

- Ingest and process CVs (PDF, DOCX, TXT)
- Compare accomplishments against USCIS’s 8 evidentiary criteria
- Return:
  - A list of matched criteria with supporting justification
  - A high-level **eligibility rating** (low, medium, high)

Non-functional requirements:
- Heavy read on the DB but not much write
- Handle 1000s of simultaneous requests, with ease of scaling as needed
- Latency - users may be OK with waiting for a few seconds

Beyond the scope:
- User creation and data upload over time, stored into encrypted data store
- Be modular, extendable (e.g., to O-1B or other visas)
- Should allow for additional evidence to be submitted
- Support for multiple languages
- Logging, monitoring

## Architecture Overview

### 1. **API Gateway**
- Fronts the entire system.
- Handles authentication, routing, and throttling.
- Receives client requests (CV uploads, analysis requests) and forwards them to backend services.

### 2. **CV Preprocessor (Serverless)**
- Triggered by the API Gateway upon file upload.
- Extracts and cleans text from PDF, DOCX, or TXT formats.
- Returns a normalized CV text blob to downstream systems.

**Benefits**: Stateless, highly parallelizable, and auto-scales on demand.

### 3. **LLM Analysis Service (Serverless)**
- Triggered once preprocessing is complete.
- Loads the 8 O-1A criteria from MongoDB (or memory).
- Sends the CV text and criteria to the LLM API (e.g., OpenAI, or a future self-hosted model).
- Matches evidence to each criterion and returns structured results.
- Writes results to Redis cache keyed by CV ID or file hash for retry handling or follow-up.

**Scalable, modular, and LLM-agnostic** — future-ready for running on a local GPU cluster or model farm.

### 4. **Eligibility Service (Serverless)**
- Receives structured criterion match results from the LLM Analysis.
- Applies deterministic rules (e.g., number of matched criteria) to assign an eligibility rating: `low`, `medium`, or `high`.
- Optionally logs or stores results in a persistent store

Can also return explanations or criteria justifications in a clean, user-facing format.

### 5. **Redis Caching Layer** - once we scale up
- Shared cache between services to:
  - Avoid recomputation on retry.
  - Persist intermediate outputs (CV text, LLM results).
  - Enable graceful recovery from network or downstream API errors.

Ensures idempotent, fault-tolerant service flow.

### 6. **MongoDB (Read-Heavy, Cloud)**
- Stores static reference data (visa types, criteria descriptions, legal text).
- Could store analysis history or user sessions later if needed.

## Flow Summary

1. User uploads CV → API Gateway
2. API Gateway routes to CV Preprocessor (serverless)
3. CV Preprocessor extracts text → triggers LLM Analysis
4. LLM Analysis reads from Redis → calls LLM API with CV + criteria → saves result to Redis with Md5 hash of resume, TTL 24 hours and LFU
5. Eligibility Service reads structured matches → scores eligibility → returns result to client


## Components and Design Decisions

**For the purposes of this exercise, I am implementing the FastAPI component as a singular endpoint for MVP purposes. I will also be loading the data for the O1-A visa from JSON directly.**

### 1. **CV Upload & API Layer**
- **Tech**: FastAPI
- **Pros**:
  - Async and performant
  - Easy to define file endpoints
  - Swagger docs included
- **Cons**:
  - Requires explicit error handling (vs something like Flask)

### 2. **Preprocessing Layer**
- **Tech**: `python-docx`, `PyMuPDF`, `textract`, or similar
- **Function**:
  - Normalize and clean CV text
- **Pros**:
  - Flexible; can preprocess various file formats
- **Cons**:
  - OCR and layout-heavy docs may degrade performance
  - Multilingual CVs not fully supported out-of-the-box

### 3. **Structured Criteria Store**
- **Tech**: MongoDB
- **Schema**:
  ```json
  {
    "visa_type": "O-1A",
    "general_info": "...",
    "criteria": [
      {
        "name": "Awards",
        "description": "...",
        "full_text": "..."
      },
      ...
    ]
  }
  ```
- **Pros**:
  - Flexible document schema
  - Optimized for read-heavy access
- **Cons**:
  - Slightly more setup than SQLite
  - Requires discipline around structure enforcement

Tradeoff: Chose MongoDB over SQLite for better handling of nested criteria text and flexibility in future visa types.

### 4. **LLM Matching & Reasoning Core**
- **Tech**: OpenAI GPT, local LLM, or hosted provider
- **Inputs**:
  - Cleaned CV text
  - Criteria text from DB
- **Output**:
  - List of matched criteria with rationale
  - Rating: 1 - 10 (1 low, 10 high)
- **Pros**:
  - Can evaluate nuance across ambiguous language
  - Easy to fine-tune or prompt engineer
- **Cons**:
  - Needs token management
  - Sensitive to prompt structure
  - Expensive at scale (unless local model used)

I used LangChain to enforce response pattern and also to streamline prompting.

### 5. **Eligibility Scorer**
- **Logic**:
  - “High” = 6–8 criteria strongly matched
  - “Medium” = 3–5 matched
  - “Low” = <3 matched or weak evidence
- **Pros**:
  - Simple, explainable logic
  - Can be made probabilistic later
- **Cons**:
  - Heuristic-based; no confidence interval

## Data Storage

### MongoDB
- **Used for**:
  - Visa criteria documents
  - Parsed CVs and other evidence (optional)
- **Backup**: JSON export of visa requirement records

## Dev Tools & Libraries

- **Backend**: FastAPI, Pydantic
- **Parsing**: `PyMuPDF`, `python-docx`, `textract`
- **LLM Access**: `openai`, `langchain`
- **DB**: `pymongo`
- **Testing**: `pytest`, `httpx`

## Future Extensions

- Add **O-1B** support via additional visa profiles
- Add ability to explain **why** a criterion wasn’t met
- Upload **supporting documents** (e.g., PDFs of awards or press)
- Use **LLM fine-tuning** for custom scoring logic
- Add optional **web interface** for user input/review
- Distill larger model reasoning and evaluations to fine-tune smaller model for this specific purpose
- Test out new prompting with multiple criteria being evluated simultaneously
- If using local LLM, leverage KV-caching and fine-tuning to store majority of prompt data
    - Mixture of CAG vs RAG
- Keep fresh data regarding salaries for various jobs in order to better handle "High Remuneration" criteria without having to hit the internet to search for each evaluation

