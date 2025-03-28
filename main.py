# main.py
import asyncio
import sys
from fastapi import FastAPI, UploadFile, File, HTTPException, Request
from fastapi.responses import Response
import uvicorn
import json
import time
import logging
from config import settings
from data_loader import load_visa_data
from file_processing import process_pdf, process_docx, process_text
from analysis import perform_analysis

# Attempt to load visa data; exit if the file is missing.
try:
    o1a_criteria = load_visa_data()
except FileNotFoundError as e:
    print(str(e))
    sys.exit(1)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)
app = FastAPI()

@app.middleware("http")
async def log_requests(request: Request, call_next):
    logger.info(f"New request: {request.method} {request.url}")
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    logger.info(f"Completed in {process_time:.2f}s with status code {response.status_code}")
    return response

async def process_cv_and_analysis(cv: UploadFile) -> dict:
    """
    Process the CV file based on its type and run analysis against O1-A criteria.
    """
    file_type = cv.filename.split('.')[-1].lower()
    logger.info(f"Processing CV from {cv.filename}")

    if file_type == "pdf":
        cv_text = await process_pdf(cv)
    elif file_type == "docx":
        cv_text = await process_docx(cv)
    elif file_type in ["txt", "text"]:
        cv_text = await process_text(cv)
    else:
        raise HTTPException(status_code=400, detail="Unsupported file type.")
    
    analysis_result = await perform_analysis(cv_text, o1a_criteria)
    return analysis_result

def filter_analysis_results(full_result: dict) -> dict:
    """
    Filter the analysis results to remove chain-of-thought reasoning.
    
    Args:
        full_result (dict): The complete result from perform_analysis, including each criterion's rating,
                            chain_of_thought, and evidence_list.
        
    Returns:
        dict: A dictionary with criteria_results containing only rating and evidence_list,
              along with the overall eligibility_rating.
    """
    filtered_results = {}
    for criterion, details in full_result.get("criteria_results", {}).items():
        if isinstance(details, dict):
            filtered_results[criterion] = {
                "rating": details.get("rating"),
                "evidence_list": details.get("evidence_list")
            }
        else:
            filtered_results[criterion] = details

    return {
        "criteria_results": filtered_results,
        "eligibility_rating": full_result.get("eligibility_rating")
    }


@app.post("/analyze_cv")
async def analyze_cv_endpoint(cv: UploadFile = File(...), verbose: bool = False):
    """
    Endpoint to analyze a CV file for O1-A visa eligibility.
    Times out after 60 seconds if processing takes too long.
    If verbose is False, chain-of-thought reasoning will be removed from the output.
    """
    try:
        full_result = await asyncio.wait_for(process_cv_and_analysis(cv), timeout=60)
    except asyncio.TimeoutError:
        raise HTTPException(status_code=504, detail="Processing timed out.")
    
    if not verbose:
        final_output = filter_analysis_results(full_result)
    else:
        final_output = full_result
    
    # Slightly unnecessary, but useful for parsing by human eye for this exercise
    pretty_json = json.dumps(final_output, indent=4)
    return Response(content=pretty_json, media_type="application/json")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
