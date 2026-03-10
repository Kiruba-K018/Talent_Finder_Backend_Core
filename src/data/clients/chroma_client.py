import logging

import chromadb
from chromadb.config import Settings

from src.config.settings import setting

logger = logging.getLogger(__name__)

_is_connected = False
chroma_client = None


async def init_chroma():
    """Initialize Chroma client at app startup."""
    global chroma_client, _is_connected

    try:
        if setting.chroma_mode == "persistent":
            chroma_client = chromadb.PersistentClient(
                path=setting.chroma_path,
                settings=Settings(
                    anonymized_telemetry=False,
                    allow_reset=False,
                ),
            )
            logger.info(f"Chroma initialized at {setting.chroma_path}")

        elif setting.chroma_mode == "ephemeral":
            chroma_client = chromadb.EphemeralClient(
                settings=Settings(anonymized_telemetry=False)
            )
            logger.info("Chroma initialized in ephemeral mode")

        elif setting.chroma_mode == "server":
            try:
                chroma_client = chromadb.HttpClient(
                    host=setting.chroma_host,
                    port=setting.chroma_port,
                    settings=Settings(anonymized_telemetry=False),
                )
                chroma_client.heartbeat()
            except Exception as e:
                logger.warning(f"Could not connect to Chroma server: {e}")
                chroma_client = chromadb.PersistentClient(
                    path=setting.chroma_path,
                    settings=Settings(anonymized_telemetry=False, allow_reset=False),
                )
                logger.info("Chroma fallback to persistent mode")

        else:
            raise ValueError(f"Invalid chroma_mode: {setting.chroma_mode}")

        _is_connected = True
        logger.info("Chroma client successfully initialized")

    except Exception as e:
        logger.error(f"Failed to initialize Chroma: {e}")
        # Try ephemeral as a fallback
        try:
            logger.info("Attempting ephemeral fallback for Chroma initialization")
            chroma_client = chromadb.EphemeralClient(
                settings=Settings(anonymized_telemetry=False)
            )
            _is_connected = True
            logger.info("Chroma fallback to ephemeral mode succeeded")
        except Exception as fallback_error:
            logger.error(f"Chroma fallback failed: {fallback_error}")
            _is_connected = False


def get_chroma_client():
    global chroma_client
    if not chroma_client or not _is_connected:
        raise RuntimeError("Chroma client not initialized")
    return chroma_client


def get_collection(name: str):
    client = get_chroma_client()
    return client.get_or_create_collection(
        name=name,
        metadata={"hnsw:space": "cosine"},
    )


def query_collection(collection_name: str, query_texts: list[str], n_results: int = 1):
    client = get_chroma_client()
    collection = client.get_or_create_collection(name=collection_name)
    return collection.query(query_texts=query_texts, n_results=n_results)


async def close_chroma():
    global chroma_client, _is_connected
    chroma_client = None
    _is_connected = False
    logger.info("Chroma client closed")
