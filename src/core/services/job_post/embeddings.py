import logging
import sys
import uuid

from src.data.clients.pgvector_client import get_or_create_collection

logger = logging.getLogger(__name__)

# Ensure logger is configured with console handler
if not logger.handlers:
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(logging.DEBUG)
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(logging.DEBUG)


async def embed_job_skills(
    job_id: uuid.UUID,
    required_skills: list[str],
    preferred_skills: list[str],
    job_data: dict = None,
):
    logger.info(f"[START] Embedding skills for job {job_id}")
    logger.debug(f"Required skills: {required_skills}")
    logger.debug(f"Preferred skills: {preferred_skills}")
    logger.debug(f"Job data provided: {job_data is not None}")

    try:
        logger.debug(f"Initializing pgvector client for job {job_id}")
        collection = await get_or_create_collection(name="job_skills_embeddings")
        logger.debug("pgvector collection initialized successfully")

        documents_to_add = []
        ids_to_add = []
        metadatas_to_add = []

        logger.debug(
            f"Checking {len(required_skills)} required skills for existing embeddings"
        )
        for skill in required_skills:
            doc_id = f"job_{job_id}_required_{skill.lower().replace(' ', '_')}"

            # Check if skill already exists
            try:
                existing = await collection.get(ids=[doc_id])
                if existing and existing.get("ids") and len(existing["ids"]) > 0:
                    logger.debug(
                        f"Skipping required skill (already embedded): {skill} (id: {doc_id})"
                    )
                    continue
            except Exception as e:
                logger.debug(
                    f"Skill check for {skill} failed (expected if new): {str(e)}"
                )

            documents_to_add.append(skill)
            ids_to_add.append(doc_id)
            metadatas_to_add.append({"job_id": str(job_id), "skill_type": "required"})
            logger.debug(f"Added required skill for embedding: {skill} (id: {doc_id})")

        logger.debug(
            f"Checking {len(preferred_skills)} preferred skills for existing embeddings"
        )
        for skill in preferred_skills:
            doc_id = f"job_{job_id}_preferred_{skill.lower().replace(' ', '_')}"

            # Check if skill already exists
            try:
                existing = await collection.get(ids=[doc_id])
                if existing and existing.get("ids") and len(existing["ids"]) > 0:
                    logger.debug(
                        f"Skipping preferred skill (already embedded): {skill} (id: {doc_id})"
                    )
                    continue
            except Exception as e:
                logger.debug(
                    f"Skill check for {skill} failed (expected if new): {str(e)}"
                )

            documents_to_add.append(skill)
            ids_to_add.append(doc_id)
            metadatas_to_add.append({"job_id": str(job_id), "skill_type": "preferred"})
            logger.debug(f"Added preferred skill for embedding: {skill} (id: {doc_id})")

        if documents_to_add:
            logger.info(
                f"Adding {len(documents_to_add)} new skill documents to pgvector collection"
            )
            await collection.add(
                documents=documents_to_add, ids=ids_to_add, metadatas=metadatas_to_add
            )
            logger.info(
                f"Successfully added {len(documents_to_add)} skill documents to pgvector"
            )
        else:
            logger.info(
                f"All skills for job {job_id} are already embedded, skipping batch add"
            )

        if job_data:
            logger.info(f"Launching scoring agent for job {job_id}")
            from src.control.agents.scoring_agent.prepare_states import prepare_state

            await prepare_state(job_id, job_data)
            logger.info(f"Scoring agent launched successfully for job {job_id}")
        else:
            logger.warning(
                f"No job_data provided, skipping scoring agent launch for job {job_id}"
            )

        logger.info(f"[END] Successfully completed embedding skills for job {job_id}")

    except Exception as e:
        logger.error(
            f"[ERROR] Failed to embed job skills for job {job_id}: {str(e)}",
            exc_info=True,
        )


async def embed_resume_skills(candidate_id: uuid.UUID, resume_skills: list[str]):
    """Embed resume skills for a single candidate. Skip if already embedded and unchanged."""
    logger.debug(f"Processing embedding for candidate {candidate_id}")

    try:
        # Initialize pgvector collection
        try:
            collection = await get_or_create_collection(name="candidate_skills_embeddings")
            logger.debug(f"pgvector collection initialized for candidate {candidate_id}")
        except Exception as client_error:
            logger.error(
                f"Failed to initialize pgvector collection for candidate {candidate_id}: {str(client_error)}"
            )
            return False

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
                        f"Updating embedding for candidate {candidate_id}: content changed"
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
                        f"Updated {len(resume_skills)} skills for candidate {candidate_id}"
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
                f"Failed to add embedding for candidate {candidate_id}: {str(add_error)}"
            )
            return False

    except Exception as e:
        logger.error(
            f"Unexpected error embedding resume skills for candidate {candidate_id}: {str(e)}",
            exc_info=True,
        )
        return False
