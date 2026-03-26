import asyncio
import logging
import sys
import uuid

from src.data.clients.pgvector_client import get_or_create_collection
from src.data.repositories.mongodb.sourced_candidate_crud import get_sourced_candidates

logger = logging.getLogger(__name__)

# Ensure logger is configured with console handler
if not logger.handlers:
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(logging.INFO)
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)


async def embed_resume_skills(candidate_id: uuid.UUID, resume_skills: list[str]):
    """Embed resume skills for a single candidate.

    Skip if already embedded and unchanged.
    """
    logger.debug(f"Processing embedding for candidate {candidate_id}")
    try:
        collection = await get_or_create_collection(name="candidate_skills_embeddings")
        logger.debug(f"pgvector collection initialized for candidate {candidate_id}")
    except Exception as client_error:
        logger.error(
            f"Failed to initialize pgvector collection for "
            f"candidate {candidate_id}: {str(client_error)}"
        )
        return False

    try:
        if not resume_skills:
            logger.debug(f"No skills to embed for candidate {candidate_id}")
            return False

        # Combine all skills into a single document
        combined_skills_text = ", ".join(resume_skills)
        doc_id = f"candidate_{candidate_id}_skills"

        # Check if the embedding already exists
        try:
            existing_doc = await collection.get(ids=[doc_id])
            if (
                existing_doc
                and existing_doc.get("ids")
                and len(existing_doc["ids"]) > 0
            ):
                existing_text = existing_doc.get("documents", [None])[0]
                logger.debug(f"Embedding exists for candidate {candidate_id}")

                # Check if content is the same
                if existing_text == combined_skills_text:
                    logger.debug(
                        f"Skipping candidate {candidate_id}: content unchanged"
                    )
                    return False  # Already embedded, no change
                else:
                    logger.info(
                        f"Updating embedding for candidate {candidate_id}: "
                        f"content changed"
                    )
                    await collection.update(
                        ids=[doc_id],
                        documents=[combined_skills_text],
                        metadatas=[
                            {
                                "candidate_id": str(candidate_id),
                                "skill_count": len(resume_skills),
                            }
                        ],
                    )
                    logger.debug(
                        f"Updated {len(resume_skills)} skills for "
                        f"candidate {candidate_id}"
                    )
                    return False  # Updated, not new
        except Exception as check_error:
            logger.debug(f"Document check failed (expected if new): {str(check_error)}")

        # Add new embedding if it doesn't exist
        try:
            await collection.add(
                documents=[combined_skills_text],
                ids=[doc_id],
                metadatas=[
                    {
                        "candidate_id": str(candidate_id),
                        "skill_count": len(resume_skills),
                    }
                ],
            )
            logger.debug(f"Added new embedding for candidate {candidate_id}")
            return True  # New embedding added
        except Exception as add_error:
            logger.error(
                f"Failed to add embedding for candidate {candidate_id}: "
                f"{str(add_error)}"
            )
            return False

    except Exception as e:
        logger.error(
            f"Unexpected error embedding resume skills for "
            f"candidate {candidate_id}: {str(e)}",
            exc_info=True,
        )
        return False


async def bulk_embed_job_candidates(job_id: str):
    """Bulk embed all candidates for a job. Skips already embedded candidates."""
    logger.info(f"[START] Bulk embedding candidates for job {job_id}")

    try:
        candidates = await get_sourced_candidates(job_id=job_id)

        if not candidates:
            logger.warning(f"No candidates found for job {job_id}")
            return {"total": 0, "embedded": 0, "skipped": 0, "errors": 0}

        logger.info(f"Found {len(candidates)} candidates for job {job_id}")

        total = len(candidates)
        embedded_count = 0
        skipped_count = 0
        error_count = 0

        for idx, candidate in enumerate(candidates, 1):
            logger.debug(f"Processing candidate {idx}/{total} for job {job_id}")
            try:
                candidate_id = candidate.get("candidate_id")
                if not candidate_id:
                    logger.warning(
                        f"Candidate at index {idx} missing candidate_id, skipping"
                    )
                    error_count += 1
                    continue

                resume_skills = candidate.get("hard_skills", [])

                if not resume_skills:
                    logger.debug(
                        f"Candidate {candidate_id} ({idx}/{total}) has no "
                        f"skills, skipping"
                    )
                    skipped_count += 1
                    continue

                is_new = await embed_resume_skills(candidate_id, resume_skills)

                if is_new:
                    embedded_count += 1
                    logger.info(
                        f"[{idx}/{total}] Embedded {len(resume_skills)} "
                        f"skills for candidate {candidate_id}"
                    )
                else:
                    skipped_count += 1
                    logger.debug(
                        f"[{idx}/{total}] Skipped candidate {candidate_id} "
                        f"(already embedded)"
                    )

            except Exception as e:
                logger.error(f"Error processing candidate at index {idx}: {str(e)}")
                error_count += 1
                continue

        result = {
            "total": total,
            "embedded": embedded_count,
            "skipped": skipped_count,
            "errors": error_count,
        }

        logger.info(f"[END] Bulk embedding completed for job {job_id}")
        logger.info(
            f"Stats - Total: {total}, Embedded: {embedded_count}, "
            f"Skipped: {skipped_count}, Errors: {error_count}"
        )

        return result

    except Exception as e:
        logger.error(f"Failed bulk embedding for job {job_id}: {str(e)}", exc_info=True)
        return {"total": 0, "embedded": 0, "skipped": 0, "errors": 1}


async def main():
    """Test bulk embedding with sample job_id."""
    import sys

    from src.data.clients.pgvector_client import init_pgvector

    # Initialize pgvector before usage
    await init_pgvector()

    # Get job_id from command line argument or use default
    if len(sys.argv) > 1:
        job_id = sys.argv[1]
    else:
        job_id = "3fa85f64-5717-4562-b3fc-2c963f66afa6"

    logger.info(f"Starting bulk embedding for job: {job_id}")
    result = await bulk_embed_job_candidates(job_id)
    logger.info(f"Embedding result: {result}")


if __name__ == "__main__":
    asyncio.run(main())
