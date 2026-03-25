import asyncio
import logging
import sys
import uuid

from langgraph.graph import END
from src.data.repositories.postgres.candidate_shortlist_crud import create_job_shortlist

from src.control.agents.scoring_agent.state import ScoringState
from src.control.agents.scoring_agent.utils import (
    aggregate_scores,
    calculate_ai_score,
    calculate_field_completion_score,
    calculate_recency_score,
    calculate_rule_based_score,
    calculate_skill_match_score,
    detect_flags,
    calculate_years_experience,
)
from src.data.clients.postgres_client import get_session_factory
from src.data.repositories.mongodb.scoring_crud import (
    save_candidate_scores_with_fresh_client,
)
from src.data.repositories.mongodb.sourced_candidate_crud import (
    get_candidate_data_with_fresh_client,
)

logger = logging.getLogger(__name__)

# Ensure logger is configured with console handler
if not logger.handlers:
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(logging.INFO)  # Changed from DEBUG to INFO for performance
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)  # Changed from DEBUG to INFO


async def load_candidates_node(state: ScoringState) -> ScoringState:
    logger.info(f"Loading candidates for job {state['job_id']}")
    total = len(state["candidates"])
    
    logger.info(f"[PROGRESS] Stage: loading | Total: {total} candidates")
    return {
        **state,
        "candidates": state["candidates"],
        "all_candidates": state.get("all_candidates", state["candidates"]),  # Preserve all candidates
        "current_candidate_idx": 0,
        "scores_to_save": [],
        "shortlist_candidates": [],
        "filtered_candidates": 0,
        "total_candidates": total,
        "processed_candidates": 0,
        "scored_candidates": 0,
        "current_stage": "loading",
    }


async def calculate_base_scores_node(state: ScoringState) -> ScoringState:
    """
    Calculate base scores (rule-based, completion, recency) for ALL candidates.
    No filtering - just scoring to evaluate how well candidates meet minimum criteria.
    """
    from src.control.agents.scoring_agent.launcher import push_progress_update
    
    logger.info(f"[PROGRESS] Stage: base_scoring | Starting base score calculation for all candidates")
    
    candidates = state["candidates"]
    total = len(candidates)
    
    if total == 0:
        logger.warning("No candidates to score")
        return {
            **state,
            "candidates": candidates,
            "current_stage": "base_scoring",
        }
    
    try:
        batch_size = 4
        candidates_with_scores = []
        
        for i in range(0, total, batch_size):
            batch = candidates[i:i+batch_size]
            batch_end = min(i + batch_size, total)
            
            logger.info(f"Scoring batch: {i+1}-{batch_end}/{total} (base scores)")
            
            # Calculate base scores concurrently
            results = await asyncio.gather(
                *[calculate_candidate_base_scores(c, state) for c in batch],
                return_exceptions=True
            )
            
            for idx, result in enumerate(results):
                if isinstance(result, Exception):
                    logger.error(f"Exception calculating base scores: {result}")
                    # Add candidate without scores if error
                    candidates_with_scores.append(batch[idx])
                else:
                    candidates_with_scores.append(result)
            
            progress = int(((i + len(batch)) / total) * 100)
            push_progress_update(
                state["job_id"],
                {
                    "status": "running",
                    "current_stage": "base_scoring",
                    "progress_percent": progress,
                    "message": f"Calculating base scores: {batch_end}/{total}",
                },
            )
        
        logger.info(f"[PROGRESS] Base scoring complete for all {total} candidates")
        
        return {
            **state,
            "candidates": candidates_with_scores,
            "current_stage": "base_scoring",
        }
        
    except Exception as e:
        logger.error(f"Error during base score calculation: {e}", exc_info=True)
        return {
            **state,
            "candidates": candidates,
            "current_stage": "base_scoring",
        }


async def calculate_candidate_base_scores(candidate: dict, state: ScoringState) -> dict:
    """Calculate base scores for a single candidate."""
    try:
        # 1. Calculate rule-based score (no filtering, just scoring)
        rule_score, rule_details = await calculate_rule_based_score(
            candidate["parsed_data"],
            state["job_title"],
            state.get("min_educational_qualifications", ""),
            state.get("location_preference", ""),
            state.get("min_experience", 0),
        )
        
        # 2. Calculate field completion score
        completion_score = await calculate_field_completion_score(
            candidate["parsed_data"]
        )
        
        # 3. Calculate recency score
        recency_score = await calculate_recency_score(candidate["parsed_data"])
        
        logger.debug(
            f"Base scores for {candidate['candidate_id']}: "
            f"rule={round(rule_score, 2)}, completion={round(completion_score, 2)}, recency={round(recency_score, 2)}"
        )
        
        return {
            **candidate,
            "base_scores": {
                "rule_based_score": round(rule_score, 2),
                "completion_score": round(completion_score, 2),
                "recency_score": round(recency_score, 2),
            }
        }
    
    except Exception as e:
        logger.error(f"Error calculating base scores for {candidate.get('candidate_id')}: {e}", exc_info=True)
        return {
            **candidate,
            "base_scores": {
                "rule_based_score": 0,
                "completion_score": 0,
                "recency_score": 0,
            }
        }


async def similarity_search_and_rank_node(state: ScoringState) -> ScoringState:
    """
    Find top-k candidates using embedding similarity between job post embeddings and candidate skills.
    k = number_of_candidates required for the job.
    Select 2x required to ensure enough scored candidates even if some scoring fails.
    """
    from src.control.agents.scoring_agent.launcher import push_progress_update
    from src.data.clients.pgvector_client import get_or_create_collection
    
    logger.info(f"[PROGRESS] Stage: similarity_search | Starting embedding-based similarity search")
    
    candidates = state["candidates"]
    total = len(candidates)
    number_required = state.get("number_of_candidates", 1)
    
    # Select 2x required or minimum 10, whichever is greater, capped at total
    number_to_score = min(max(number_required * 2, 10), total)
    
    logger.info(f"Total candidates available: {total}")
    logger.info(f"Number of candidates required: {number_required}")
    logger.info(f"Selecting {number_to_score} for scoring (minimum 10, or 2x required)")
    
    if total == 0:
        logger.warning("No candidates to search")
        return {
            **state,
            "candidates": [],
            "current_candidate_idx": 0,
            "current_stage": "similarity_search",
        }
    
    try:
        collection = await get_or_create_collection(name="candidate_skills_embeddings")
        
        # Try to use pre-computed combined job skills embedding first (optimization)
        from src.core.services.job_post.embeddings import get_combined_job_skills_embedding
        
        job_id = state.get("job_id")
        version = state.get("version", 1)
        job_embedding_vector = None
        job_embedding_text = None
        
        if job_id:
            job_embedding_vector, job_embedding_text = await get_combined_job_skills_embedding(job_id, version)
        
        ranked_candidates = []
        result = None
        
        # Try using embedding vector first (most efficient - no re-embedding)
        if job_embedding_vector:
            try:
                logger.info(f"Using pre-computed job skills embedding vector for query")
                result = await collection.query(
                    query_embeddings=[job_embedding_vector],  # Pass embedding vector directly
                    n_results=total  # Get all results
                )
                logger.info("Successfully queried using pre-computed embedding vector")
            except Exception as embed_error:
                logger.warning(f"Embedding vector query failed: {embed_error}, falling back to text query")
                job_embedding_vector = None  # Mark it as failed
        
        # Fallback: Use the job embedding text if available
        if not result and job_embedding_text:
            try:
                logger.info("Using pre-computed job skills text for query (fallback)")
                result = await collection.query(
                    query_texts=[job_embedding_text],
                    n_results=number_to_score  # Get all results
                )
                logger.info("Successfully queried using pre-computed embedding text")
            except Exception as text_error:
                logger.warning(f"Text query with pre-computed embedding failed: {text_error}, falling back to fresh compute")
                result = None
        
        # Last resort: Build search query from job skills and embed on-the-fly
        if not result:
            logger.info("No pre-computed job skills embedding available, computing on-the-fly")
            
            job_skills = state.get("job_skills", [])
            skills_list = []
            for skill_item in job_skills:
                if isinstance(skill_item, dict):
                    if "required" in skill_item:
                        skills_list.append(skill_item["required"])
                    elif "preferred" in skill_item:
                        skills_list.append(skill_item["preferred"])
                else:
                    skills_list.append(str(skill_item))
            
            search_query = " ".join(skills_list) if skills_list else state.get("job_title", "")
            logger.info(f"Search query: {search_query}")
            
            if not search_query:
                logger.warning("No job skills or title, using all candidates in order")
                ranked_candidates = candidates
                return {
                    **state,
                    "candidates": ranked_candidates[:number_to_score],
                    "current_candidate_idx": 0,
                    "current_stage": "similarity_search",
                }
            
            # Query candidates by similarity to job skills
            logger.info(f"Querying pgvector for candidates")
            result = await collection.query(
                query_texts=[search_query],
                n_results= number_to_score
            )
        
        if result and result.get("ids") and len(result["ids"]) > 0:
            ranked_candidate_ids = result["ids"]
            ranked_distances = result.get("distances", [])
            
            logger.info(f"pgvector query returned: {len(ranked_candidate_ids)} results")
            
            # Build map for lookup
            candidate_by_id = {str(c["candidate_id"]): c for c in candidates}
            
            ranked_candidates = []
            for cand_id, distance in zip(ranked_candidate_ids, ranked_distances):
                # Extract UUID from "candidate_{uuid}_skills" format
                if cand_id.startswith("candidate_") and cand_id.endswith("_skills"):
                    uuid_str = cand_id.replace("candidate_", "").replace("_skills", "")
                    
                    if uuid_str in candidate_by_id:
                        candidate = candidate_by_id[uuid_str]
                        candidate["similarity_score"] = max(0, 1 - distance)
                        ranked_candidates.append(candidate)
                        logger.debug(f"Matched {uuid_str}: similarity={candidate['similarity_score']:.3f}")
            
            logger.info(f"Successfully matched {len(ranked_candidates)}/{len(ranked_candidate_ids)} candidates from pgvector")
            
            # If no matches, use all candidates
            if len(ranked_candidates) == 0:
                logger.warning("No candidates matched from pgvector, using all candidates")
                ranked_candidates = candidates
        else:
            logger.warning("No pgvector results returned, using all candidates")
            ranked_candidates = candidates
        
        # Select top candidates for scoring
        # Sort by similarity score (desc), then by rule-based score (desc)
        ranked_candidates_sorted = sorted(
            ranked_candidates,
            key=lambda c: (
                -c.get("similarity_score", 0),  # Higher similarity first
                -c.get("base_scores", {}).get("rule_based_score", 0)  # Then higher rule score
            )
        )
        
        # Select 2x required for scoring to handle potential failures
        top_candidates = ranked_candidates_sorted[:number_to_score]
        
        logger.info(f"[PROGRESS] Similarity search complete: selected {len(top_candidates)}/{total} for scoring")
        logger.info(f"Will attempt to score {len(top_candidates)} to find {number_required} qualified candidates")
        push_progress_update(
            state["job_id"],
            {
                "status": "running",
                "current_stage": "similarity_search",
                "total_candidates": total,
                "top_k_selected": len(top_candidates),
                "progress_percent": 50,
                "message": f"Similarity search complete: {len(top_candidates)}/{total} candidates selected for scoring",
            },
        )
        
        return {
            **state,
            "candidates": top_candidates,
            "current_candidate_idx": 0,
            "current_stage": "similarity_search",
        }
        
    except Exception as e:
        logger.error(f"Error during similarity search: {e}", exc_info=True)
        logger.warning("Falling back to all candidates")
        return {
            **state,
            "candidates": candidates[:number_to_score],
            "current_candidate_idx": 0,
            "current_stage": "similarity_search",
        }


async def score_final_candidate(candidate: dict, state: ScoringState) -> tuple[dict | None, str, int]:
    """
    Calculate final scores (skill match + AI) for top-k candidates.
    Combines with base scores already calculated.
    Returns (score_doc, candidate_id, status)
    """
    candidate_id_str = None
    try:
        candidate_id_str = str(candidate["candidate_id"])
        logger.debug(f"Starting scoring for candidate {candidate_id_str}")
        
        # Ensure we have base scores
        base_scores = candidate.get("base_scores", {})
        if not base_scores:
            logger.warning(f"Candidate {candidate_id_str} missing base_scores, using defaults")
            base_scores = {
                "rule_based_score": 0,
                "completion_score": 0,
                "recency_score": 0,
            }
        
        # Ensure we have parsed_data
        parsed_data = candidate.get("parsed_data", {})
        if not parsed_data:
            logger.warning(f"Candidate {candidate_id_str} missing parsed_data")
            # Return basic score without detailed processing
            score_doc = {
                "_id": str(uuid.uuid4()),
                "candidate_id": candidate_id_str,
                "job_id": str(state["job_id"]),
                "rule_based_score": base_scores.get("rule_based_score", 0),
                "completion_score": base_scores.get("completion_score", 0),
                "recency_score": base_scores.get("recency_score", 0),
                "skill_match_score": 0,
                "ai_score": 0,
                "strengths": [],
                "weaknesses": [],
                "considerations": [],
                "confidence_score": 0,
                "aggregation_score": base_scores.get("rule_based_score", 0),
                "flags": [],
                "similarity_score": candidate.get("similarity_score", 0),
            }
            return score_doc, candidate_id_str, 0
        
        # 1. Calculate skill match score
        skill_score = 0
        try:
            skill_score, skill_details = await calculate_skill_match_score(
                candidate["candidate_id"], state["job_skills"]
            )
        except Exception as skill_error:
            logger.warning(f"Skill match calc failed for {candidate_id_str}: {skill_error}")
            skill_score = 0
        
        # 2. Calculate AI score (with fallback to defaults if fails)
        ai_score = 0
        confidence_score = 0
        strengths = []
        weaknesses = []
        considerations = []
        flags_from_ai = []
        
        try:
            (
                ai_score,
                confidence_score,
                strengths,
                weaknesses,
                considerations,
                flags_from_ai,
            ) = await calculate_ai_score(
                parsed_data,
                state["job_title"],
                state["job_description"],
                state.get("min_experience", 0),
                state.get("min_educational_qualifications", ""),
            )
        except Exception as ai_error:
            logger.warning(f"AI scoring failed for {candidate_id_str}, using defaults: {ai_error}")
            ai_score = 0
            confidence_score = 0
            strengths = []
            weaknesses = []
            considerations = []
            flags_from_ai = []
        
        # 3. Detect flags
        flags = []
        try:
            flags = await detect_flags(
                parsed_data,
                {
                    "min_experience": state.get("min_experience", 0),
                    "max_experience": state.get("max_experience", 100),
                    "min_educational_qualifications": state.get(
                        "min_educational_qualifications", ""
                    ),
                    "location_preference": state.get("location_preference", ""),
                },
            )
        except Exception as flag_error:
            logger.warning(f"Flag detection failed for {candidate_id_str}: {flag_error}")
            flags = []
        
        # 4. Calculate aggregate score (combining all scores)
        aggregate_score = await aggregate_scores(
            base_scores.get("completion_score", 0),
            base_scores.get("rule_based_score", 0),
            base_scores.get("recency_score", 0),
            skill_score,
            ai_score_value=ai_score
        )
        
        score_doc = {
            "_id": str(uuid.uuid4()),
            "candidate_id": candidate_id_str,
            "job_id": str(state["job_id"]),
            "rule_based_score": base_scores.get("rule_based_score", 0),
            "completion_score": base_scores.get("completion_score", 0),
            "recency_score": base_scores.get("recency_score", 0),
            "skill_match_score": round(skill_score, 2),
            "ai_score": round(ai_score, 2),
            "strengths": strengths[:2] if strengths else [],
            "weaknesses": weaknesses[:2] if weaknesses else [],
            "considerations": considerations[:2] if considerations else [],
            "confidence_score": round(confidence_score * 0.9, 2),
            "aggregation_score": round(aggregate_score, 2),
            "flags": [{"flag": f["flag"], "reason": f.get("reason")} for f in flags]
                    + [{"flag": f, "reason": ""} for f in flags_from_ai if isinstance(f, str)],
            "similarity_score": candidate.get("similarity_score", 0),
        }
        
        logger.info(
            f"Candidate {candidate_id_str} final score: "
            f"skill={round(skill_score, 2)}, ai={round(ai_score, 2)}, aggregate={round(aggregate_score, 2)}"
        )
        return score_doc, candidate_id_str, 0  # 0 = success
        
    except Exception as e:
        logger.error(f"Error scoring candidate {candidate_id_str}: {e}", exc_info=True)
        return None, candidate_id_str or str(candidate.get("candidate_id", "unknown")), 3  # 3 = error


async def process_candidate_node(state: ScoringState) -> ScoringState:
    """
    Process top-k candidates to calculate skill match + AI scores.
    Combines with already-calculated base scores.
    """
    from src.control.agents.scoring_agent.launcher import push_progress_update
    
    batch_size = 4
    candidates = state["candidates"]
    start_idx = state["current_candidate_idx"]
    total = len(candidates)

    logger.info(f"Processing candidates: start_idx={start_idx}, total={total}, batch_size={batch_size}")

    if start_idx >= total:
        logger.info(f"All {total} candidates processed for job {state['job_id']}")
        logger.info(f"Total shortlist candidates accumulated: {len(state['shortlist_candidates'])}")
        return state

    end_idx = min(start_idx + batch_size, total)
    batch = candidates[start_idx:end_idx]

    logger.info(f"Processing batch: {start_idx + 1}-{end_idx}/{total} (batch size: {len(batch)})")
    logger.info(f"[PROGRESS] Stage: scoring | Batch: {start_idx + 1}-{end_idx}/{total} | Progress: {int((end_idx / total) * 100)}%")

    # Score all candidates in batch concurrently
    results = await asyncio.gather(
        *[score_final_candidate(c, state) for c in batch], return_exceptions=True
    )

    scores_to_add = []
    shortlist_to_add = []
    scored_count = state.get("scored_candidates", 0)

    for result in results:
        # Check if result is an exception
        if isinstance(result, Exception):
            logger.error(f"Exception during scoring: {result}", exc_info=False)
            continue
        
        # Unpack the tuple
        score_doc, candidate_id, status = result
        logger.debug(f"Candidate {candidate_id}: status={status}, score_doc={bool(score_doc)}")
        
        if status == 0:  # Success - scored
            scores_to_add.append(score_doc)
            shortlist_to_add.append(
                {
                    "candidate_id": candidate_id,
                    "aggregation_score": score_doc["aggregation_score"],
                    "score_doc_id": score_doc["_id"],
                }
            )
            scored_count += 1
            logger.info(f"Added to shortlist: {candidate_id}, score={score_doc['aggregation_score']}")
        else:
            logger.warning(f"Candidate {candidate_id} not scored: status={status}")

    processed = end_idx
    progress_percent = int((processed / total) * 100)
    logger.info(
        f"[PROGRESS-DETAIL] Processed: {processed}/{total} | Scored in this batch: {len(scores_to_add)} | Total scored so far: {scored_count}"
    )
    logger.info(
        f"Shortlist candidates before merge: {len(state['shortlist_candidates'])}, adding {len(shortlist_to_add)}"
    )
    
    push_progress_update(
        state["job_id"],
        {
            "status": "running",
            "current_stage": "scoring",
            "processed_candidates": processed,
            "total_candidates": total,
            "scored_candidates": scored_count,
            "progress_percent": progress_percent,
            "message": f"Scoring candidates: {processed}/{total} ({progress_percent}%)",
        },
    )

    new_shortlist = state["shortlist_candidates"] + shortlist_to_add
    logger.info(f"Shortlist candidates after merge: {len(new_shortlist)}")

    return {
        **state,
        "current_candidate_idx": end_idx,
        "scores_to_save": state["scores_to_save"] + scores_to_add,
        "shortlist_candidates": new_shortlist,
        "processed_candidates": processed,
        "scored_candidates": scored_count,
        "current_stage": "scoring",
    }


async def continue_processing(state: ScoringState) -> str:
    if state["current_candidate_idx"] < len(state["candidates"]):
        return "process_candidate"
    return END


async def save_scores_node(state: ScoringState) -> ScoringState:
    total_candidates = len(state.get("candidates", []))
    scored_candidates = len(state["scores_to_save"])

    logger.info(
        f"[PROGRESS] Stage: save_scores | Completed: {scored_candidates}/{total_candidates} candidates scored"
    )

    if scored_candidates == 0:
        logger.warning(
            f"No candidates scored for job {state['job_id']}"
        )
        return {**state, "current_stage": "save_scores"}

    logger.info(f"Saving {scored_candidates} scores for job {state['job_id']}")
    try:
        await save_candidate_scores_with_fresh_client(state["scores_to_save"])
        logger.info(f"Successfully saved scores for job {state['job_id']}")
    except Exception as e:
        logger.error(f"Failed to save scores for job {state['job_id']}: {e}", exc_info=True)

    return {**state, "current_stage": "save_scores"}


async def create_shortlist_node(state: ScoringState) -> ScoringState:
    """
    Create final shortlist from scored candidates.
    The candidates are already selected (top-k from similarity search).
    If not enough scored, use unscored candidates to meet the required number.
    """
    logger.info(f"Creating shortlist for job {state['job_id']}")
    
    shortlist = state["shortlist_candidates"]
    candidates = state.get("candidates", [])
    number_required = state.get("number_of_candidates", 1)
    
    logger.info(f"Shortlist candidates available: {len(shortlist)}")
    logger.info(f"Total candidates in pool: {len(candidates)}")
    logger.info(f"Number of candidates required: {number_required}")
    
    # Build score mapping
    scores_by_id = {str(s["candidate_id"]): s for s in state["scores_to_save"]}
    
    # Prepare candidates with flag info for sorting
    candidates_with_flags = []
    for candidate in shortlist:
        score_doc = scores_by_id.get(str(candidate["candidate_id"]))
        flags = score_doc.get("flags", []) if score_doc else []
        aggregation_score = score_doc.get("aggregation_score", candidate.get("aggregation_score", 0)) if score_doc else candidate.get("aggregation_score", 0)
        
        candidates_with_flags.append({
            "candidate": candidate,
            "flag_count": len(flags),
            "score": aggregation_score,
            "flags": flags,
        })
    
    # Sort by flag count (fewer first), then by score (higher first)
    candidates_sorted = sorted(
        candidates_with_flags,
        key=lambda x: (x["flag_count"], -x["score"])
    )
    
    # Select up to requested number
    final_shortlist = [cf["candidate"] for cf in candidates_sorted[:number_required]]
    
    # FALLBACK: If not enough scored candidates, add unscored candidates from the pool
    if len(final_shortlist) < number_required:
        logger.warning(
            f"Not enough scored candidates ({len(final_shortlist)}/{number_required}). "
            f"Adding unscored candidates to meet quota."
        )
        scored_ids = {str(c["candidate_id"]) for c in final_shortlist}
        
        # Add remaining candidates from the pool
        for candidate in candidates:
            if len(final_shortlist) >= number_required:
                break
            if str(candidate["candidate_id"]) not in scored_ids:
                final_shortlist.append({
                    "candidate_id": candidate["candidate_id"],
                    "aggregation_score": candidate.get("base_scores", {}).get("rule_based_score", 0),
                    "score_doc_id": None,
                })
                logger.info(f"Added unscored fallback candidate: {candidate['candidate_id']}")
    
    logger.info(f"[PROGRESS] Stage: shortlisting | Selected {len(final_shortlist)} candidates for shortlist")
    logger.info(f"Final shortlist: {[str(c['candidate_id']) for c in final_shortlist]}")
    
    return {
        **state,
        "shortlist_candidates": final_shortlist,
        "current_stage": "shortlisting",
    }


async def save_shortlist_to_db(state: ScoringState) -> ScoringState:
    try:
        session_factory = get_session_factory()
        async with session_factory() as db:
            logger.debug(f"Saving shortlist to database for job {state['job_id']}")
            # Ensure version is set correctly; default to 2 for version 2 workflows
            version = state.get("version")
            if version is None:
                version = 2
                state["version"] = version
            logger.debug(f"Using version: {version} for job {state['job_id']}")
            await create_job_shortlist(
                db=db,
                job_id=state["job_id"],
                version=version,
                sorted_shortlist=state["shortlist_candidates"],
            )
        logger.info(f"Successfully created shortlist for job {state['job_id']} with version {version}")
        logger.info(
            f"[PROGRESS] Stage: completed | Shortlist created successfully with {len(state['shortlist_candidates'])} candidates"
        )
        
        # Schedule background task to score overflow candidates
        try:
            from src.core.utils.background_task_manager import get_background_task_manager
            # Check if there are remaining candidates beyond the scored ones
            overflow_candidates = get_overflow_candidates(state)
            if overflow_candidates and len(overflow_candidates) > 0:  # Schedule if any overflow exists
                logger.info(f"Scheduling background task to score {len(overflow_candidates)} overflow candidates for job {state['job_id']}")
                task_manager = get_background_task_manager()
                task_manager.add_async_task(
                    score_overflow_candidates_task(
                        job_id=state["job_id"],
                        overflow_candidates=overflow_candidates,
                        state_context={
                            "job_title": state.get("job_title"),
                            "job_description": state.get("job_description"),
                            "job_skills": state.get("job_skills", []),
                            "min_experience": state.get("min_experience"),
                            "max_experience": state.get("max_experience"),
                            "min_educational_qualifications": state.get("min_educational_qualifications"),
                            "location_preference": state.get("location_preference"),
                            "version": version,
                        }
                    )
                )
                logger.info(f"Background task scheduled for job {state['job_id']}")
            else:
                logger.info(f"No overflow candidates to score (found {len(overflow_candidates) if overflow_candidates else 0})")
        except Exception as overflow_error:
            logger.warning(f"Failed to schedule overflow scoring task for job {state['job_id']}: {overflow_error}")
    
    except Exception as e:
        logger.error(f"Failed to create shortlist for job {state['job_id']}: {e}")

    return {**state, "current_stage": "completed"}


def get_overflow_candidates(state: ScoringState) -> list[dict]:
    """
    Get candidates that were selected for scoring but NOT selected for the final shortlist.
    Overflow = (candidates selected for scoring) - (candidates in final shortlist)
    """
    # Candidates selected for scoring (top-k from similarity search)
    scored_candidates = state.get("candidates", [])
    
    # Candidates in final shortlist
    shortlist_candidate_ids = {str(c["candidate_id"]) for c in state.get("shortlist_candidates", [])}
    
    # Overflow candidates are those scored but not in final shortlist
    overflow = [c for c in scored_candidates if str(c.get("candidate_id")) not in shortlist_candidate_ids]
    return overflow


async def score_overflow_candidates_task(
    job_id: uuid.UUID,
    overflow_candidates: list[dict],
    state_context: dict
) -> None:
    """
    Background task to score remaining candidates (those beyond top-k).
    Saves scores and appends to shortlist table.
    """
    logger.info(f"[OVERFLOW] Starting background scoring for {len(overflow_candidates)} candidates for job {job_id}")
    
    try:
        # Score all overflow candidates (no maximum limit)
        candidates_to_score = overflow_candidates
        
        logger.info(f"[OVERFLOW] Will score {len(candidates_to_score)} overflow candidates")
        
        # Calculate base scores for all overflow candidates
        overflow_with_base_scores = []
        batch_size = 4
        
        for i in range(0, len(candidates_to_score), batch_size):
            batch = candidates_to_score[i:i+batch_size]
            results = await asyncio.gather(
                *[calculate_overflow_base_scores(c, state_context) for c in batch],
                return_exceptions=True
            )
            for result in results:
                if not isinstance(result, Exception):
                    overflow_with_base_scores.append(result)
        
        logger.info(f"[OVERFLOW] Calculated base scores for {len(overflow_with_base_scores)} candidates")
        
        # Score overflow candidates (skill match + AI)
        scores_to_save = []
        shortlist_to_add = []
        
        for i in range(0, len(overflow_with_base_scores), batch_size):
            batch = overflow_with_base_scores[i:i+batch_size]
            
            # Create temporary state for scoring
            temp_state = ScoringState(
                job_id=job_id,
                job_title=state_context.get("job_title", ""),
                job_description=state_context.get("job_description", ""),
                job_skills=state_context.get("job_skills", []),
                candidates=[],
                current_candidate_idx=0,
                current_candidate_score={},
                scores_to_save=[],
                shortlist_candidates=[],
                number_of_candidates=None,
                min_experience=state_context.get("min_experience"),
                max_experience=state_context.get("max_experience"),
                min_educational_qualifications=state_context.get("min_educational_qualifications"),
                location_preference=state_context.get("location_preference"),
                db=None,
                version=state_context.get("version", 1),
                total_candidates=len(overflow_with_base_scores),
                processed_candidates=0,
                filtered_candidates=0,
                scored_candidates=0,
                current_stage="overflow_scoring",
            )
            
            # Score batch
            results = await asyncio.gather(
                *[score_final_candidate(c, temp_state) for c in batch],
                return_exceptions=True
            )
            
            for result in results:
                if isinstance(result, Exception):
                    logger.warning(f"Exception during overflow scoring: {result}")
                    continue
                
                score_doc, candidate_id, status = result
                if status == 0 and score_doc:  # Success
                    scores_to_save.append(score_doc)
                    shortlist_to_add.append({
                        "candidate_id": candidate_id,
                        "aggregation_score": score_doc["aggregation_score"],
                        "score_doc_id": score_doc["_id"],
                    })
        
        logger.info(f"[OVERFLOW] Scored {len(scores_to_save)} overflow candidates")
        
        # Save scores to MongoDB
        if scores_to_save:
            try:
                await save_candidate_scores_with_fresh_client(scores_to_save)
                logger.info(f"[OVERFLOW] Saved {len(scores_to_save)} overflow scores to MongoDB")
            except Exception as mongo_error:
                logger.error(f"[OVERFLOW] Failed to save scores to MongoDB: {mongo_error}", exc_info=True)
        
        # Add overflow candidates to shortlist table
        if shortlist_to_add:
            try:
                session_factory = get_session_factory()
                async with session_factory() as db:
                    version = state_context.get("version", 1)
                    await create_job_shortlist(
                        db=db,
                        job_id=job_id,
                        version=version,
                        sorted_shortlist=shortlist_to_add,
                    )
                logger.info(f"[OVERFLOW] Added {len(shortlist_to_add)} overflow candidates to shortlist table")
            except Exception as db_error:
                logger.error(f"[OVERFLOW] Failed to add overflow candidates to shortlist: {db_error}", exc_info=True)
        
        logger.info(f"[OVERFLOW] Completed background scoring task for job {job_id}")
    
    except Exception as e:
        logger.error(f"[OVERFLOW] Failed to score overflow candidates for job {job_id}: {e}", exc_info=True)


async def calculate_overflow_base_scores(candidate: dict, state_context: dict) -> dict:
    """Calculate base scores for overflow candidates."""
    try:
        rule_score, _ = await calculate_rule_based_score(
            candidate.get("parsed_data", {}),
            state_context.get("job_title", ""),
            state_context.get("min_educational_qualifications", ""),
            state_context.get("location_preference", ""),
            state_context.get("min_experience", 0),
        )
        
        completion_score = await calculate_field_completion_score(
            candidate.get("parsed_data", {})
        )
        
        recency_score = await calculate_recency_score(
            candidate.get("parsed_data", {})
        )
        
        return {
            **candidate,
            "base_scores": {
                "rule_based_score": round(rule_score, 2),
                "completion_score": round(completion_score, 2),
                "recency_score": round(recency_score, 2),
            }
        }
    except Exception as e:
        logger.warning(f"Error calculating base scores for overflow candidate {candidate.get('candidate_id')}: {e}")
        return {
            **candidate,
            "base_scores": {
                "rule_based_score": 0,
                "completion_score": 0,
                "recency_score": 0,
            }
        }
