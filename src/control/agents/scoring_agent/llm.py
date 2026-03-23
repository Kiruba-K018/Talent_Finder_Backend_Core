import hashlib
import json
import logging
import re

from langchain.chat_models import init_chat_model
from tenacity import retry, stop_after_attempt, wait_exponential

from src.config.settings import setting

logger = logging.getLogger(__name__)

_llm_response_cache = {}


def _get_cache_key(candidate_data: dict, job_title: str, job_description: str) -> str:
    """Generate a cache key based on candidate and job data."""
    key_str = json.dumps(
        {
            "candidate_id": candidate_data.get("id") or candidate_data.get("_id"),
            "candidate_skills": sorted(candidate_data.get("hard_skills", []))
            if isinstance(candidate_data.get("hard_skills"), list)
            else "",
            "job_title": job_title,
            "job_desc_hash": hashlib.md5(job_description.encode()).hexdigest()
            if job_description
            else "",
        },
        sort_keys=True,
        default=str,
    )
    return hashlib.md5(key_str.encode()).hexdigest()


candidate_json = dict()
job_data = dict()

System_Prompt = """You are a senior technical hiring analyst and recruitment evaluator.
        Your task is to objectively evaluate a candidate against a job requirement using structured reasoning.
    Rules:
    - Base your evaluation strictly on the provided data.
    - Use ONLY the provided data.
    - Do NOT assume missing information.
    - Be analytical, not generous.
    - Follow the scoring rubric strictly.
    - If data is missing, treat it as neutral or zero — do not infer.
    - Identify risk signals clearly.
    - Output must strictly follow the JSON format provided.- Do not add extra commentary outside JSON.
        - For each section, provide crisp, meaningful points (not generic statements).
        - Strengths: list of one paragraph of 2-3 lines mentioning the candidate's strengths.
        - Weaknesses: list of one paragraph of 2-3 lines mentioning the candidate's weaknesses.
        - Considerations: List 2 specific points for recruiter consideration (e.g., risk, fit, potential concerns).
        - Do not output a summary.
        - Output only the JSON structure below."""

Human_Prompt = """Evaluate the candidate for the given job.

JOB DATA
Job Title: {job_title}
Job Description: {job_description}
Experience Required (years): {job_experience_required}
Education Required: {job_education_required}

CANDIDATE DATA
{candidate_json}

EVALUATION FRAMEWORK

Score the candidate out of 100 using this strict weighting:

1) Core Technical Skill Match (30 points)
2) Domain & Role Alignment (15 points)
3) Experience Alignment (20 points)
4) Education Fit (10 points)
5) Project & Impact Relevance (10 points)
6) Certifications & Professional Signals (5 points)
7) Soft Skills & Collaboration Signals (5 points)]
8) Stability & Risk Analysis (5 points)

 FLAG IDENTIFICATION RULES

Identify if any of the following apply:

- OVERQUALIFIED (significantly exceeds experience + seniority mismatch)
- UNDERQUALIFIED (lacks core required skill or experience)
- EDUCATION_MISMATCH
- EXPERIENCE_GAP (>12 months without employment)
- JOB_HOPPING (multiple roles under 1 year)
- IRRELEVANT_EXPERIENCE
- TITLE_MISMATCH
- LOCATION_MISMATCH (if relevant)
- INCONSISTENT_PROFILE (conflicting titles or summaries)

If none apply, return: "NONE"

OUTPUT FORMAT (STRICT JSON ONLY)
{{
  "fitness_score": <integer 0-100>,
  "confidence_score":<float 0-100> //return the rate of how confidence you are about the score and explanation
    "strengths": [
        "<crisp, meaningful point>"
    ],
    "weaknesses": [
        "<crisp, meaningful point>"
    ],
    "considerations": [
        "<crisp, meaningful point>"
    ],
  "flags": [
    "<flag_name or NONE>"
  ]
}}
Do not output anything outside this JSON structure."""


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    reraise=True,
)
async def invoke_llm(
    candidate_data: dict,
    job_title: str,
    job_description: str,
    min_experience: int,
    min_educational_qualifications: list,
) -> dict:
    """Synchronous LLM invocation with retry logic."""

    # Validate API key is configured
    if not setting.groq_api_key or setting.groq_api_key.strip() == "":
        logger.error(
            "GROQ_API_KEY is not configured. Please set the GROQ_API_KEY environment variable in .env file"
        )
        raise ValueError(
            "GROQ_API_KEY environment variable is not set. Please configure it in the .env file."
        )

    # Convert candidate_data to JSON string for proper formatting
    candidate_json_str = json.dumps(candidate_data, indent=2, default=str)

    logger.debug(
        f"Invoking LLM with candidate data keys: {list(candidate_data.keys()) if isinstance(candidate_data, dict) else 'N/A'}"
    )

    messages = [
        {"role": "system", "content": System_Prompt},
        {
            "role": "user",
            "content": Human_Prompt.format(
                job_title=job_title,
                job_description=job_description
                if isinstance(job_description, str)
                else str(job_description),
                job_experience_required=str(min_experience),
                job_education_required=min_educational_qualifications
                if isinstance(min_educational_qualifications, str)
                else ", ".join(min_educational_qualifications)
                if isinstance(min_educational_qualifications, list)
                else "Not specified",
                candidate_json=candidate_json_str,
            ),
        },
    ]

    logger.debug(f"User message preview: {messages[1]['content'][:500]}...")
    try :
        chat_model = init_chat_model(
            "openai/gpt-oss-120b",
            temperature=0.0,
            api_key=setting.groq_api_key_secondary,
            model_provider="groq",
        )
        response = chat_model.invoke(input=messages)
    except Exception as e:
        chat_model = init_chat_model(
            "openai/gpt-oss-120b",
            temperature=0.0,
            api_key=setting.groq_api_key,
            model_provider="groq",
        )
        response = chat_model.invoke(input=messages)
        
    # Extract the content from the response
    response_content = response.content
    logger.debug(f"LLM Response: {response_content}")

    try:
        parsed_response = json.loads(response_content)
        logger.info(
            f"LLM returned fitness_score: {parsed_response.get('fitness_score')}"
        )
        return parsed_response
    except json.JSONDecodeError:
        # Try extracting JSON from response using regex
        json_match = re.search(r"\{.*\}", response_content, re.DOTALL)
        if json_match:
            try:
                parsed_response = json.loads(json_match.group())
                return parsed_response
            except json.JSONDecodeError:
                pass
        logger.error(f"Failed to parse LLM response: {response_content}")
        return {
            "fitness_score": 50,
            "confidence_score": 0,
                "strengths": ["Parse error: strengths unavailable"],
                "weaknesses": ["Parse error: weaknesses unavailable"],
                "considerations": ["Parse error: considerations unavailable"],
            "flags": ["PARSE_ERROR"],
        }


if __name__ == "__main__":
    import asyncio
    async def main():
        result = await invoke_llm({}, "", "", 0, [])
        if result:
            print("\nFinal Result:")
            print(f"  Fitness Score: {result['fitness_score']}")
            print(f"  Strengths: {result['strengths']}")
            print(f"  Weaknesses: {result['weaknesses']}")
            print(f"  Considerations: {result['considerations']}")
            print(f"  Flags: {result['flags']}")
    asyncio.run(main())
    if result:
        print("\nFinal Result:")
        print(f"  Fitness Score: {result['fitness_score']}")
        print(f"  Summary: {result['summary']}")
        print(f"  Flags: {result['flags']}")
