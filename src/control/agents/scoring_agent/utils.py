import asyncio
import logging
import uuid
from datetime import datetime
from typing import Any

from src.control.agents.scoring_agent.llm import invoke_llm
from src.data.clients.pgvector_client import get_or_create_collection
from src.data.repositories.mongodb.sourced_candidate_crud import get_candidate_data

logger = logging.getLogger(__name__)


async def batch_fetch_candidate_data(candidate_ids: list[str]) -> dict[str, dict]:
    """Fetch multiple candidates' data concurrently."""
    tasks = [get_candidate_data(cid) for cid in candidate_ids]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    data_map = {}
    for cid, result in zip(candidate_ids, results):
        if isinstance(result, Exception):
            logger.warning(f"Failed to fetch candidate {cid}: {result}")
        else:
            data_map[cid] = result
    return data_map


def calculate_years_experience(experience_list: Any) -> float:
    if not experience_list or not isinstance(experience_list, list):
        return 0.0

    total_months = 0
    for exp in experience_list:
        try:
            if isinstance(exp, dict):
                start_str = exp.get("start_date", "")
                end_str = exp.get("end_date", "")

                if not start_str:
                    continue

                try:
                    start = (
                        datetime.fromisoformat(start_str.replace("Z", "+00:00"))
                        if isinstance(start_str, str)
                        else start_str
                    )
                    end = (
                        datetime.fromisoformat(end_str.replace("Z", "+00:00"))
                        if end_str and isinstance(end_str, str)
                        else (datetime.now() if not end_str else end_str)
                    )

                    duration = (end - start).days / 30 if end else 0
                    total_months += duration
                except Exception as e:
                    logger.debug(f"Error calculating experience duration: {e}")
                    continue
        except Exception as e:
            logger.debug(f"Error processing experience entry: {e}")
            continue

    return total_months / 12


async def calculate_field_completion_score(candidate_data: dict) -> float:
    fields = [
        "experience",
        "education",
        "hard_skills",
        "certifications",
        "contact_linkedin_url",
    ]
    filled_fields = sum(1 for field in fields if candidate_data.get(field))
    return (filled_fields / len(fields)) * 100


async def calculate_rule_based_score(
    candidate_data: dict,
    job_title: str,
    required_education: str,
    location: str,
    min_experience: int,
) -> tuple[float, dict]:
    score = 0
    details = {}

    # Calculate years of experience from experience list
    candidate_exp = calculate_years_experience(candidate_data.get("experience", []))
    experience_score = (
        max(0, (candidate_exp / max(min_experience, 1)) * 25)
        if min_experience > 0
        else (25 if candidate_exp > 0 else 0)
    )
    if candidate_exp >= min_experience:
        experience_score = 25
    score += experience_score
    details["experience"] = experience_score
    logger.debug(
        f"""Experience score: {experience_score} 
        (candidate has {candidate_exp:.1f} years, job requires {min_experience})"""
    )

    # Check education - look for degree in education list
    candidate_edu = ""
    education_list = candidate_data.get("education", [])
    if isinstance(education_list, list):
        candidate_edu = " ".join(
            [
                str(edu.get("degree", ""))
                for edu in education_list
                if isinstance(edu, dict)
            ]
        )
    else:
        candidate_edu = str(education_list)

    edu_score = 0
    if required_education and required_education.lower() in candidate_edu.lower():
        edu_score = 25
    score += edu_score
    details["education"] = edu_score
    logger.debug(
        f"Education score: {edu_score} (candidate edu: '{candidate_edu}', job requires: '{required_education}')"
    )

    candidate_location = candidate_data.get("location", "")
    location_score = 0
    if location and location.lower() in candidate_location.lower():
        location_score = 20
    score += location_score
    details["location"] = location_score
    logger.debug(
        f"Location score: {location_score} (candidate: '{candidate_location}', job: '{location}')"
    )

    # Title matching using embeddings for semantic similarity
    candidate_title = candidate_data.get("title", "")
    title_score = 0
    if job_title and candidate_title:
        try:
            collection = await get_or_create_collection(name="candidate_skills_embeddings")
            
            # Query job title against candidate title using embeddings
            result = await collection.query(query_texts=[job_title], n_results=1)
            
            if result.get("distances") and len(result["distances"]) > 0:
                distance = result["distances"][0]
                # Convert distance to similarity score (1 - distance) and scale to 30 max
                title_similarity = max(0, 1 - distance)
                if title_similarity > 0.4:  # Only give points if similarity > 0.4
                    title_score = min(30, title_similarity * 30)
                logger.info(
                    f"Title embedding match: candidate='{candidate_title}', job='{job_title}', similarity={title_similarity:.2f}, score={title_score:.1f}"
                )
            # Fallback: exact string matching
            elif job_title and candidate_title and job_title.lower() in candidate_title.lower():
                title_score = 30
                logger.info(f"Title exact match: candidate='{candidate_title}', job='{job_title}', score={title_score}")
        except Exception as e:
            logger.debug(f"Embedding-based title matching failed, falling back to exact match: {e}")
            # Fallback to exact string matching
            if job_title and candidate_title and job_title.lower() in candidate_title.lower():
                title_score = 30
    
    score += title_score
    details["title_match"] = title_score
    logger.debug(
        f"Title score: {title_score} (candidate: '{candidate_title}', job: '{job_title}')"
    )

    other_score = 15
    score += other_score
    details["other"] = other_score

    final_score = min(score, 100)
    logger.info(
        f"""Rule-based score: {final_score} (breakdown: exp={experience_score}, 
        edu={edu_score}, loc={location_score}, title={title_score}, other={other_score})"""
    )

    return final_score, details


async def calculate_recency_score(candidate_data: dict) -> float:
    # Try multiple field names for profile update date
    profile_update = (
        candidate_data.get("updated_on")
        or candidate_data.get("profile_last_updated")
        or candidate_data.get("sourced_at")
    )

    if not profile_update:
        return 0

    if isinstance(profile_update, str):
        try:
            update_date = datetime.fromisoformat(profile_update.replace("Z", "+00:00"))
        except Exception as e:
            logger.debug(f"Failed to parse date: {e}")
            return 0
    else:
        update_date = profile_update

    days_since_update = (datetime.now(update_date.tzinfo) - update_date).days

    if days_since_update <= 30:
        return 100.0
    elif days_since_update <= 90:
        return 70.0
    elif days_since_update <= 180:
        return 40.0
    else:
        return 10.0

    if not profile_update:
        return 50.0


async def calculate_skill_match_score(
    candidate_id: uuid.UUID,
    job_skills: list[str],
) -> tuple[float, dict]:
    collection = await get_or_create_collection(name="candidate_skills_embeddings")
    try:
        # Collection is already created, just use it
        pass
    except Exception as e:
        logger.warning(
            f"Skill embeddings collection not found for candidate {candidate_id}: {e}"
        )
        return 0.0, {}

    # Retrieve the specific candidate's embedded skills
    doc_id = f"candidate_{candidate_id}_skills"
    try:
        candidate_doc = await collection.get(ids=[doc_id])
        if (
            not candidate_doc
            or not candidate_doc.get("documents")
            or not candidate_doc["documents"][0]
        ):
            logger.warning(f"No skills found for candidate {candidate_id}")
            return 0.0, {}

        candidate_skills_text = candidate_doc["documents"][0]
        logger.debug(
            f"Retrieved candidate {candidate_id} skills: {candidate_skills_text}"
        )
    except Exception as e:
        logger.warning(f"Failed to retrieve skills for candidate {candidate_id}: {e}")
        return 0.0, {}
    

    
    required_score = 0.0
    preferred_score = 0.0
    skill_details = {"required": [], "preferred": []}
        # Separate required and preferred skills for batch processing
    required_skills = []
    preferred_skills = []

    for skill_item in job_skills:
        if isinstance(skill_item, dict):
            if "required" in skill_item:
                required_skills.append(skill_item["required"])
            elif "preferred" in skill_item:
                preferred_skills.append(skill_item["preferred"])

    # Batch query for required skills
    if required_skills:
        try:
            logger.debug(
                f"Batch querying {len(required_skills)} required skills for candidate {candidate_id}"
            )
            result = await collection.query(query_texts=required_skills, n_results=1)

            if result.get("distances") and len(result["distances"]) > 0:
                for skill_name, distance in zip(required_skills, result["distances"]):
                    if distance is not None:
                        score = max(0, 1 - distance)  # Ensure score is never negative
                        if score:
                            required_score += score
                            skill_details["required"].append(
                                {"skill": skill_name, "score": score}
                            )
                            logger.info(
                                f"Candidate {candidate_id} - Required skill '{skill_name}' -> distance: {distance:.3f}, score: {score:.3f}"
                            )
                        else:
                            logger.debug(
                                f"Candidate {candidate_id} - Required skill '{skill_name}' -> no match (distance: {distance:.3f})"
                            )
        except Exception as e:
            logger.warning(
                f"Error batch querying required skills for candidate {candidate_id}: {e}"
            )

    # Batch query for preferred skills
    if preferred_skills:
        try:
            logger.debug(
                f"Batch querying {len(preferred_skills)} preferred skills for candidate {candidate_id}"
            )
            result = await collection.query(query_texts=preferred_skills, n_results=1)

            if result.get("distances") and len(result["distances"]) > 0:
                for skill_name, distance in zip(preferred_skills, result["distances"]):
                    if distance is not None:
                        score = max(
                            0, (1 - distance) * 0.5
                        )  # Preferential skills are weighted less, ensure non-negative
                        if score:
                            preferred_score += score
                            skill_details["preferred"].append(
                                {"skill": skill_name, "score": score}
                            )
                            logger.info(
                                f"""Candidate {candidate_id} - Preferred skill 
                                '{skill_name}' -> distance: {distance:.3f}, score: {score:.3f}"""
                            )
                        else:
                            logger.debug(
                                f"""Candidate {candidate_id} - Preferred skill '{skill_name}' 
                                -> no match (distance: {distance:.3f})"""
                            )
        except Exception as e:
            logger.warning(
                f"Error batch querying preferred skills for candidate {candidate_id}: {e}"
            )

    final_score = 0.7 * required_score + 0.3 * preferred_score 
    logger.info(
        f"""Final skill match score for candidate {candidate_id}: {final_score:.2f} 
        (required: {required_score:.2f}, preferred: {preferred_score:.2f})"""
    )
    return final_score, skill_details


async def calculate_ai_score(
    candidate_data: dict,
    job_title: str,
    job_description: str,
    min_experience: int,
    min_educational_qualifications: list,
) -> tuple[float, float, list[str], list[str], list[str], list[str]]:
    """
    Calculate AI score for a candidate.
    Returns a tuple of (fitness_score: float, confidence_score: float,  strengths: list[str], weaknesses: list[str], considerations: list[str], flags: list[str])
    """
    result = await invoke_llm(
        candidate_data,
        job_title,
        job_description,
        min_experience,
        min_educational_qualifications,
    )
    logger.info(
        f"LLM result for candidate {candidate_data.get('id', candidate_data.get('_id', 'unknown'))}: {result}"
    )

    # Extract and convert the result from invoke_llm into the expected tuple format
    fitness_score = float(result.get("fitness_score", 0))
    confidence_score = float(result.get("confidence_score", 0))
    strength = result.get("strengths", [])
    weakness = result.get("weaknesses", [])
    considerations = result.get("considerations", [])
    flags = result.get("flags", [])

    # Ensure flags is a list
    if not isinstance(flags, list):
        flags = [flags] if flags else []

    return fitness_score, confidence_score, strength, weakness, considerations, flags


async def detect_flags(candidate_data: dict, job_data: dict) -> list[dict]:
    flags = []

    # Calculate years of experience from experience list
    candidate_exp = calculate_years_experience(candidate_data.get("experience", []))
    min_exp = job_data.get("min_experience", 0)
    max_exp = job_data.get("max_experience", 100)

    if candidate_exp > max_exp * 1.5:
        flags.append(
            {
                "flag": "OVERQUALIFIED",
                "reason": f"Experience ({candidate_exp:.1f}y) exceeds max requirement ({max_exp}y)",
            }
        )

    # Check education level
    education_list = candidate_data.get("education", [])
    candidate_edu_str = ""
    if isinstance(education_list, list):
        candidate_edu_str = " ".join(
            [
                str(edu.get("degree", ""))
                for edu in education_list
                if isinstance(edu, dict)
            ]
        ).lower()
    else:
        candidate_edu_str = str(education_list).lower()

    required_edu = job_data.get("min_educational_qualifications", "").lower()
    if (
        "phd" in candidate_edu_str or "master's" in candidate_edu_str
    ) and "bachelor" in required_edu:
        flags.append(
            {
                "flag": "EDUCATION_MISMATCH",
                "reason": "Candidate overqualified in education",
            }
        )

    candidate_location = candidate_data.get("location", "").lower()
    required_location = job_data.get("location_preference", "").lower()
    if (
        candidate_location
        and required_location
        and candidate_location not in required_location
    ):
        flags.append(
            {
                "flag": "LOCATION_MISMATCH",
                "reason": f"Candidate in {candidate_location}, job in {required_location}",
            }
        )

    # Check for frequent job changes (jobs with duration < 6 months)
    experience_list = candidate_data.get("experience", [])
    if isinstance(experience_list, list) and len(experience_list) > 0:
        recent_exp = (
            experience_list[0] if isinstance(experience_list[0], dict) else None
        )
        if recent_exp:
            start_str = recent_exp.get("start_date", "")
            end_str = recent_exp.get("end_date", "")
            try:
                if start_str and end_str:
                    start = (
                        datetime.fromisoformat(start_str.replace("Z", "+00:00"))
                        if isinstance(start_str, str)
                        else start_str
                    )
                    end = (
                        datetime.fromisoformat(end_str.replace("Z", "+00:00"))
                        if isinstance(end_str, str)
                        else end_str
                    )
                    duration_months = (end - start).days / 30
                    if 0 < duration_months < 6:
                        flags.append(
                            {
                                "flag": "FREQUENT_JOB_CHANGES",
                                "reason": f"Last job duration: {duration_months:.1f} months",
                            }
                        )
            except Exception as e:
                logger.debug(f"Error checking job duration: {e}")

    # Check for employment gaps in experience
    employment_gaps = []
    experience_list = candidate_data.get("experience", [])
    if isinstance(experience_list, list) and len(experience_list) > 1:
        for i in range(len(experience_list) - 1):
            try:
                curr_exp = experience_list[i]
                next_exp = experience_list[i + 1]

                if isinstance(curr_exp, dict) and isinstance(next_exp, dict):
                    curr_start = curr_exp.get("start_date", "")
                    next_end = next_exp.get("end_date", "")

                    if curr_start and next_end:
                        start = (
                            datetime.fromisoformat(curr_start.replace("Z", "+00:00"))
                            if isinstance(curr_start, str)
                            else curr_start
                        )
                        end = (
                            datetime.fromisoformat(next_end.replace("Z", "+00:00"))
                            if isinstance(next_end, str)
                            else next_end
                        )
                        gap_months = (start - end).days / 30
                        if gap_months > 0:
                            employment_gaps.append(gap_months)
            except Exception as e:
                logger.debug(f"Error checking employment gap: {e}")
                continue

    if employment_gaps:
        for gap in employment_gaps:
            if gap > 12:
                flags.append(
                    {
                        "flag": "CAREER_GAP",
                        "reason": f"Employment gap of {gap:.1f} months detected",
                    }
                )
                break

    return flags


async def aggregate_scores(
    completion_score: float,
    rule_based_score: float,
    recency_score: float,
    skill_match_score: float,
    ai_score_value: float = 0,
) -> float:
    """
    Aggregate scores for the candidate.
    
    Score breakdown:
    - completion_score: 15% (field completion)
    - rule_based_score: 20% (minimum criteria compliance)
    - recency_score: 15% (profile freshness)
    - skill_match_score: 50% (skill matching)
    - ai_score_value: replaces rule_based_score weight (20%) if provided
    
    When AI score is provided, it replaces rule_based_score (both 20% weight).
    """
    if ai_score_value > 0:
        # Include AI score with 20% weight (replacing rule-based score weight)
        return (
            completion_score * 0.15
            + recency_score * 0.15
            + skill_match_score * 0.50
            + ai_score_value * 0.20
        )
    else:
        # Use original weights with rule-based score
        return (
            completion_score * 0.15
            + rule_based_score * 0.20
            + recency_score * 0.15
            + skill_match_score * 0.50
        )
