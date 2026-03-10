import logging
from collections.abc import AsyncGenerator

from motor.motor_asyncio import AsyncIOMotorClient

from src.config.settings import setting

logger = logging.getLogger(__name__)

client: AsyncIOMotorClient | None = None


async def connect_to_mongo():
    global client
    try:
        logger.info("Connecting to MongoDB...")
        client = AsyncIOMotorClient(
            setting.mongo_uri,
            maxPoolSize=50,
            minPoolSize=5,
            serverSelectionTimeoutMS=5000,
            connectTimeoutMS=10000,
            socketTimeoutMS=10000,
            retryWrites=True,
            retryReads=True,
            uuidRepresentation="standard",
        )
        # Verify connection
        await client.admin.command("ping")
        logger.info("Successfully connected to MongoDB")
    except Exception as e:
        logger.error(f"Failed to connect to MongoDB: {e}")
        raise


async def close_mongo_connection():
    global client
    if client:
        client.close()
        logger.info("MongoDB connection closed")


async def get_database():
    global client
    if client is None:
        logger.warning("MongoDB client not initialized, attempting to connect...")
        await connect_to_mongo()
    return client[setting.mongo_db]


async def get_db() -> AsyncGenerator:
    db = await get_database()
    try:
        yield db
    finally:
        pass
