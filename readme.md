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
- Stores results in a Redis cache with a hashed CV ID.
- Returns a normalized CV text blob to downstream systems.

**Benefits**: Stateless, highly parallelizable, and auto-scales on demand.

### 3. **LLM Analysis Service (Serverless)**
- Triggered once preprocessing is complete.
- Loads the 8 O-1A criteria from MongoDB (or memory).
- Sends the CV text and criteria to the LLM API (e.g., OpenAI, or a future self-hosted model).
- Matches evidence to each criterion and returns structured results.
- Writes results to Redis cache keyed by CV ID for retry handling or follow-up.

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

### 6. **MongoDB (Read-Heavy, Local or Cloud)**
- Stores static reference data (visa types, criteria descriptions, legal text).
- Could store analysis history or user sessions later if needed.

## Flow Summary

1. User uploads CV → API Gateway
2. API Gateway routes to CV Preprocessor (serverless)
3. CV Preprocessor extracts text → saves to Redis → triggers LLM Analysis
4. LLM Analysis reads from Redis → calls LLM API with CV + criteria → saves result to Redis
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
  - Rating: `low`, `medium`, `high`
- **Pros**:
  - Can evaluate nuance across ambiguous language
  - Easy to fine-tune or prompt engineer
- **Cons**:
  - Needs token management
  - Sensitive to prompt structure
  - Expensive at scale (unless local model used)

Consider using LangChain or LlamaIndex if chaining prompts or using a vector DB later.

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

### MongoDB (Local)
- **Used for**:
  - Visa criteria documents
  - Parsed CVs and other evidence (optional)
- **Backup**: JSON export of visa requirement records

## Dev Tools & Libraries

- **Backend**: FastAPI, Pydantic
- **Parsing**: `PyMuPDF`, `python-docx`, `textract`
- **LLM Access**: `openai`, `llama-cpp-python` (optional)
- **DB**: `pymongo`
- **Testing**: `pytest`, `httpx`, `mongomock`

## Future Extensions

- Add **O-1B** support via additional visa profiles
- Add ability to explain **why** a criterion wasn’t met
- Upload **supporting documents** (e.g., PDFs of awards or press)
- Use **LLM fine-tuning** for custom scoring logic
- Add optional **web interface** for user input/review

