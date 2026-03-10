import secrets

from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application configuration settings."""

    # PostgreSQL settings
    postgres_host: str = "localhost"
    postgres_port: str = "5432"
    postgres_db: str
    postgres_user: str
    postgres_password: str
    postgres_ssl_mode: str = "prefer"
    postgres_pool_size: int = 10

    # MongoDB settings
    mongo_host: str = "localhost"
    mongo_port: str = "27017"
    mongo_user: str = "mongo"
    mongo_password: str = "mongo"
    mongo_db: str
    mongo_authsource: str = "admin"

    @property
    def mongo_uri(self) -> str:
        """Construct MongoDB connection URI from settings."""
        return f"mongodb://{self.mongo_user}:{self.mongo_password}@{self.mongo_host}:{self.mongo_port}/{self.mongo_db}?authSource={self.mongo_authsource}"

    # ChromaDB settings
    chroma_mode: str = "persistent"
    chroma_host: str = "localhost"
    chroma_port: int = 8000
    chroma_path: str = "./chroma_data"
    chroma_timeout: int = 30
    chroma_max_retries: int = 3

    openai_api_key: str = ""
    groq_api_key: str = "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"
    cerebras_api_key: str = ""

    # JWT settings with development defaults
    access_secret: str = secrets.token_urlsafe(32)
    refresh_secret: str = secrets.token_urlsafe(32)
    algorithm: str = "HS256"
    access_expire_min: int = 60  # Increased from 15 to 60 minutes for development
    refresh_expire_min: int = 10080

    github_pat: str = Field(default="")

    model_config = {"env_file": ".env", "extra": "ignore", "case_sensitive": False}


setting = Settings()
