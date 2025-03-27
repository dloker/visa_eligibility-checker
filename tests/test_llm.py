import pytest
import asyncio
from analysis import evaluate_super_criteria
from data_loader import load_visa_data

@pytest.fixture
def criteria_data():
    try:
        data = load_visa_data()
    except Exception as e:
        pytest.skip(f"Could not load visa data: {e}")
    return data

@pytest.mark.asyncio
async def test_super_criteria_without_nobel(criteria_data):
    """
    Test the super-criteria evaluation when the resume does not mention a major award.
    Expect the rating to be less than 9.
    """
    cv_text = (
        "The applicant has contributed to many open source projects, published several papers, "
        "and has a strong academic record in computer science."
    )
    general_instructions = criteria_data.get("general_instructions", ["Follow USCIS guidelines carefully."])
    
    result = await evaluate_super_criteria(cv_text, general_instructions)
    
    # Check that the result includes a rating.
    assert "rating" in result, "Missing 'rating' key in response."
    rating = result["rating"]
    assert isinstance(rating, int), f"Rating should be an integer, got {type(rating)}"
    
    # We expect the rating to be below 9 since there's no mention of a major internationally recognized award.
    assert rating < 9, f"Expected rating < 9 for resume without major award, got {rating}"

@pytest.mark.asyncio
async def test_super_criteria_with_nobel(criteria_data):
    """
    Test the super-criteria evaluation when the resume mentions a major internationally recognized award.
    Expect the rating to be 9 or higher.
    """
    cv_text = (
        "The applicant was awarded the Nobel Prize in Mathematics for groundbreaking research in number theory. "
        "This achievement demonstrates an extraordinary level of international recognition."
    )
    general_instructions = criteria_data.get("general_instructions", ["Follow USCIS guidelines carefully."])
    
    result = await evaluate_super_criteria(cv_text, general_instructions)
    
    # Check that the result includes a rating.
    assert "rating" in result, "Missing 'rating' key in response."
    rating = result["rating"]
    assert isinstance(rating, int), f"Rating should be an integer, got {type(rating)}"
    
    # We expect the rating to be 9 or above since the resume mentions a Nobel Prize.
    assert rating >= 9, f"Expected rating >= 9 for resume with Nobel Prize, got {rating}"