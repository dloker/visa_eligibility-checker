# analysis.py
import asyncio
import json
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate, HumanMessagePromptTemplate
from pydantic import BaseModel
from langchain.output_parsers import PydanticOutputParser

from config import settings

# Initialize the LLM using LangChain with our configuration.
llm = ChatOpenAI(
    openai_api_key=settings.openai_api_key,
    model=settings.llm_model,
    temperature=0.2,  
    max_tokens=500
)

class CriterionResult(BaseModel):
    rating: int
    chain_of_thought: str
    evidence_list: list

# Create a parser using your Pydantic model.
output_parser = PydanticOutputParser(pydantic_object=CriterionResult)

def build_criterion_prompt(criterion_text: str, cv_text: str, general_instructions: str, comparable_evidence: str) -> str:
    """
    Build a prompt using ChatPromptTemplate and HumanMessagePromptTemplate.
    The prompt instructs the LLM to return a JSON object with keys:
    'rating', 'chain_of_thought', and 'evidence_list'.
    """
    prompt_template = ChatPromptTemplate.from_messages([
        HumanMessagePromptTemplate.from_template(
            """
            <start_instructions>
            You are a USCIS officer evaluating an O-1A visa petition. Follow these instructions:
            1. Analyze the applicant's resume content for the given criterion.
            2. Provide detailed chain-of-thought reasoning.
            3. Assign a rating from 1 (no evidence) to 10 (overwhelming evidence).
            4. List specific supporting evidence from the resume that justify your rating.
            Return your output as a valid JSON object with keys "rating", "chain_of_thought", and "evidence_list". Do not include any extra text.
            <end_instructions>
            <start_criterion>
            {criterion_text}
            <end_criterion>
            <start_resume>
            {cv_text}
            <end_resume>
            <start_general_instructions>
            {general_instructions}
            <end_general_instructions>
            <start_comparable_evidence>
            {comparable_evidence}
            <end_comparable_evidence>
            """
        )
    ])
    
    prompt = prompt_template.format(
        criterion_text=criterion_text,
        cv_text=cv_text,
        general_instructions=general_instructions,
        comparable_evidence=comparable_evidence
    )
    return prompt

def build_super_criteria_prompt(cv_text: str, general_instructions: str, super_award_examples: str) -> str:
    """
    Build a prompt for evaluating super-criteria using a LangChain prompt template.
    The prompt instructs the LLM to analyze the resume for evidence of a major internationally recognized award,
    provide detailed chain-of-thought reasoning, assign a rating (1-10), and list supporting evidence.
    """
    prompt_template = ChatPromptTemplate.from_messages([
        HumanMessagePromptTemplate.from_template(
            """
            <start_instructions>
            You are a USCIS officer evaluating an O-1A visa petition. Follow these instructions:
            1. Analyze the applicant's resume for evidence of a major internationally recognized award.
            2. Provide detailed chain-of-thought reasoning for your evaluation.
            3. Assign a rating from 1 to 10, where 1 indicates no evidence and 10 indicates overwhelming evidence.
            4. List specific supporting evidence from the resume that justify your rating.
            Return your output as a valid JSON object with keys "rating", "chain_of_thought", and "evidence_list". Do not include any extra text.
            <end_instructions>
            <start_super_examples>
            {super_award_examples}
            <end_super_examples>
            <start_resume>
            {cv_text}
            <end_resume>
            <start_general_instructions>
            {general_instructions}
            <end_general_instructions>
            """
        )
    ])
    prompt = prompt_template.format(
        super_award_examples=super_award_examples,
        cv_text=cv_text,
        general_instructions=general_instructions
    )
    return prompt

async def query_llm(prompt: str) -> dict:
    """
    Query the LLM using the given prompt and return the parsed JSON output.
    Uses LangChain's PydanticOutputParser to enforce JSON formatting.
    """
    def _query():
        return llm.predict(prompt)
    
    response_text = await asyncio.to_thread(_query)
    
    try:
        # Use the output parser to parse the response.
        # The parser automatically strips markdown formatting if necessary.
        parsed_result = output_parser.parse(response_text)
        return parsed_result.model_dump()
    except Exception as e:
        return {"error": f"Could not parse response: {e}", "raw_response": response_text}


async def evaluate_criterion(cv_text: str, criterion: dict, general_instructions: list, comparable_evidence: str) -> dict:
    """
    Build a prompt for a single criterion using a prompt template and call the LLM API.
    """
    # Convert the general instructions list to a single string.
    general_instructions_str = " ".join(general_instructions)
    prompt = build_criterion_prompt(
        criterion_text=criterion["full_text"],
        cv_text=cv_text,
        general_instructions=general_instructions_str,
        comparable_evidence=comparable_evidence
    )
    return await query_llm(prompt)

async def evaluate_super_criteria(cv_text: str, general_instructions: list) -> dict:
    """
    Build and send a prompt to evaluate the super-criteria.
    The super-criteria check is intended to determine whether the applicant's resume clearly meets an exceptionally high standard,
    by providing evidence of a major internationally recognized award.
    """
    super_award_examples = (
        "Examples of major internationally recognized awards include:\n"
        "- Nobel Prize\n"
        "- Fields Medal\n"
        "- Turing Award\n"
        "- Abel Prize\n"
        "- Breakthrough Prize\n"
        "- Lasker Award\n"
        "- Kavli Prize\n"
        "- Shaw Prize\n"
        "- Wolf Prize\n"
        "- Kyoto Prize"
    )
    
    general_instructions_str = " ".join(general_instructions)
    prompt = build_super_criteria_prompt(cv_text, general_instructions_str, super_award_examples)
    return await query_llm(prompt)

def score_eligibility(criteria_responses: list) -> str:
    """
    Aggregate individual criterion responses to determine overall eligibility.
    A simple heuristic is applied:
      - High: 6 or more criteria with rating >= 6.
      - Medium: 3 to 5 criteria with rating >= 6.
      - Low: Fewer than 3 criteria with rating >= 6.
    """
    positive_count = 0
    for response in criteria_responses:
        if isinstance(response, dict):
            rating = response.get("rating", 0)
            if isinstance(rating, int) and rating >= 6:
                positive_count += 1
    if positive_count >= 6:
        return "high"
    elif 3 <= positive_count < 6:
        return "medium"
    else:
        return "low"

async def perform_analysis(cv_text: str, visa_info: dict) -> dict:
    """
    Analyze the CV text against the O-1A visa criteria concurrently.
    First, check for super-criteria. If met, return 'high' eligibility immediately.
    Otherwise, concurrently evaluate each criterion using LLM calls and aggregate the results.
    Returns a dictionary with:
      - "criteria_results": A mapping of criterion names to their individual responses.
      - "eligibility_rating": Overall eligibility rating ("low", "medium", "high").
    """
    general_instructions = visa_info.get("general_instructions", [])
    comparable_evidence = visa_info.get("comparable_evidence", "")
    super_criteria = visa_info.get("super_criteria", None)
    
    # Evaluate super-criteria if provided.
    if super_criteria:
        super_result = await evaluate_super_criteria(cv_text, general_instructions)
        if "rating" in super_result and isinstance(super_result["rating"], int) and super_result["rating"] >= 9:
            return {
                "criteria_results": {"super_criteria": super_result},
                "eligibility_rating": "high"
            }
    
    # Evaluate individual criteria concurrently.
    tasks = [
        evaluate_criterion(cv_text, crit, general_instructions, comparable_evidence)
        for crit in visa_info.get("criteria", [])
    ]
    criteria_responses = await asyncio.gather(*tasks, return_exceptions=True)
    
    # Collect responses and count criteria that are strongly met.
    results = {}
    for idx, response in enumerate(criteria_responses):
        criterion_name = visa_info["criteria"][idx]["name"]
        if isinstance(response, Exception):
            results[criterion_name] = {"error": str(response)}
        else:
            results[criterion_name] = response

    overall_rating = score_eligibility(criteria_responses)
    
    return {
        "criteria_results": results,
        "eligibility_rating": overall_rating
    }
    
