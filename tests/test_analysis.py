# tests/test_evaluate_super_criteria.py
import asyncio
import pytest
from analysis import evaluate_super_criteria, build_super_criteria_prompt, build_criterion_prompt

@pytest.mark.asyncio
async def test_evaluate_super_criteria(monkeypatch):
    # Define dummy input values.
    dummy_cv = "This is a dummy resume content that mentions a major award such as the Nobel Prize and other achievements."
    dummy_instructions = ["Follow USCIS guidelines.", "Evaluate super criteria carefully."]
    
    # Define a dummy LLM response that our dummy query_llm function will return.
    dummy_response = {
       "rating": 10,
       "chain_of_thought": "The resume clearly mentions a Nobel Prize, which is a major internationally recognized award.",
       "evidence_list": ["Nobel Prize mention", "Outstanding research record"]
    }
    
    # Define a dummy query_llm function that always returns our dummy_response.
    async def dummy_query_llm(prompt: str) -> dict:
         return dummy_response

    # Use monkeypatch to override query_llm in the analysis module.
    monkeypatch.setattr("analysis.query_llm", dummy_query_llm)
    
    # Call the evaluate_super_criteria function with our dummy data.
    result = await evaluate_super_criteria(dummy_cv, dummy_instructions)
    
    # Assert that the returned result matches our dummy_response.
    assert result["rating"] == 10
    assert isinstance(result["evidence_list"], list)
    assert "Nobel Prize" in result["chain_of_thought"]

def test_super_criteria_prompt_contains_keywords():
    cv_text = "This is a dummy resume with notable achievements and awards."
    general_instructions = "Follow USCIS guidelines carefully."
    super_award_examples = "Nobel Prize, Fields Medal, Turing Award"
    
    prompt = build_super_criteria_prompt(cv_text, general_instructions, super_award_examples)
    
    # Assert that the prompt includes the expected XML-like tags.
    assert "<start_instructions>" in prompt
    assert "<end_instructions>" in prompt
    assert "<start_super_examples>" in prompt
    assert "<end_super_examples>" in prompt
    assert "<start_resume>" in prompt
    assert "<end_resume>" in prompt
    assert "<start_general_instructions>" in prompt
    assert "<end_general_instructions>" in prompt

    # Assert that the prompt contains some of the key text from the inputs.
    assert "Nobel Prize" in prompt
    assert "Follow USCIS guidelines carefully." in prompt
    assert "This is a dummy resume" in prompt
    
def test_criterion_prompt_contains_keywords():
    criterion_text = "This criterion requires evidence of significant awards and recognitions."
    cv_text = "The applicant has won multiple prestigious awards including a Fields Medal."
    general_instructions = "Ensure you follow USCIS evaluation guidelines."
    comparable_evidence = "Comparable evidence may include major industry awards."
    
    prompt = build_criterion_prompt(criterion_text, cv_text, general_instructions, comparable_evidence)
    
    # Check for XML-like tags in the prompt.
    assert "<start_instructions>" in prompt
    assert "<end_instructions>" in prompt
    assert "<start_criterion>" in prompt
    assert "<end_criterion>" in prompt
    assert "<start_resume>" in prompt
    assert "<end_resume>" in prompt
    assert "<start_general_instructions>" in prompt
    assert "<end_general_instructions>" in prompt
    assert "<start_comparable_evidence>" in prompt
    assert "<end_comparable_evidence>" in prompt
    
    # Verify that the prompt contains key input text.
    assert "This criterion requires evidence of significant awards" in prompt
    assert "The applicant has won multiple prestigious awards" in prompt
    assert "Ensure you follow USCIS evaluation guidelines." in prompt
    assert "Comparable evidence may include major industry awards." in prompt
    
