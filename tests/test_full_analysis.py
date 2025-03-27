# tests/test_full_analysis.py
import pytest
from data_loader import load_visa_data
from analysis import perform_analysis

@pytest.mark.asyncio
async def test_perform_analysis_resume_not_passing():
    # Load criteria from the existing data loader.
    criteria = load_visa_data()

    # Sample resume text that appears decent but lacks major internationally recognized awards.
    resume_text = (
        "The applicant holds a Ph.D. in Computer Science from a reputable university and has published several research papers in moderately "
        "well-known journals. He has contributed to various open source projects and has been an active member of a professional association. "
        "However, he has not received any major international awards or recognitions such as the Nobel Prize, Fields Medal, or Turing Award. "
        "While his academic and professional record is solid, his accomplishments do not reach the extraordinary level required for an O-1A visa."
    )

    # Run the complete analysis.
    result = await perform_analysis(resume_text, criteria)

    # Check that the overall eligibility rating is present.
    assert "eligibility_rating" in result, "Missing overall eligibility rating in result."

    overall_rating = result["eligibility_rating"]
    
    # Assert that the rating is not 'high'
    assert overall_rating != "high", f"Expected overall rating not to be 'high', got '{overall_rating}'"
    
    # Optionally, print the result for debugging purposes:
    print("Test result:", result)
