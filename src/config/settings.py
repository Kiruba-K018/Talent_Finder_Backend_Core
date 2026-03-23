import secrets

from pydantic import Field
from pydantic_settings import BaseSettings


def _get_env_file() -> str:
    """Determine which .env file to load based on APP_ENV variable."""
    import os
    app_env = os.getenv("APP_ENV", "development")
    
    if app_env.lower() == "local":
        return ".env.local"
    return ".env"


class Settings(BaseSettings):
    """Application configuration settings."""

    # PostgreSQL settings - field names match environment variables (with case_sensitive=False)
    db_host: str = Field(default="34.23.138.181")
    db_port: str = Field(default="5432")
    db_name: str = Field(default="talentfinder")
    db_user: str = Field(default="devakirubak")
    db_password: str
    db_url: str = Field(default="")
    postgres_ssl_mode: str = "prefer"
    postgres_pool_size: int = 3  # Reduced for Cloud SQL (was 10)
    postgres_pool_min_size: int = 1  # Minimum connections (was not set)

    # MongoDB settings
    mongo_host: str = "mongodb"
    mongo_port: str = "27017"
    mongo_user: str = "mongo"
    mongo_password: str = "mongo"
    mongo_db: str = Field(default="talentfinder")
    mongo_authsource: str = "admin"
    atlas_connection_string: str = Field(default="")  # For MongoDB Atlas

    @property
    def mongo_uri(self) -> str:
        """Get MongoDB connection URI, preferring Atlas URL if provided."""
        if self.atlas_connection_string:
            # Use provided MongoDB Atlas URI
            return self.atlas_connection_string
        # Fall back to local MongoDB connection string
        return f"mongodb://{self.mongo_user}:{self.mongo_password}@{self.mongo_host}:{self.mongo_port}/{self.mongo_db}?authSource={self.mongo_authsource}"

    # Backward compatibility properties for existing code
    @property
    def postgres_host(self) -> str:
        return self.db_host
    
    @property
    def postgres_port(self) -> str:
        return self.db_port
    
    @property
    def postgres_db(self) -> str:
        return self.db_name
    
    @property
    def postgres_user(self) -> str:
        return self.db_user
    
    @property
    def postgres_password(self) -> str:
        return self.db_password
    
    @property
    def postgres_url(self) -> str:
        return self.db_url

    @property
    def database_url(self) -> str:
        """
        Construct PostgreSQL connection URL for psycopg3.
        Uses psycopg3 format (not SQLAlchemy format).
        """
        if self.db_url:
            url = self.db_url
            # Convert SQLAlchemy format to psycopg3 format if needed
            if "postgresql+psycopg://" in url:
                url = url.replace("postgresql+psycopg://", "postgresql://")
            return url
        
        from urllib.parse import quote
        
        # URL-encode password to handle special characters
        encoded_password = quote(self.db_password, safe="")
        
        # Use postgresql:// format (not postgresql+psycopg://) for psycopg3
        return f"postgresql://{self.db_user}:{encoded_password}@{self.db_host}:{self.db_port}/{self.db_name}?sslmode={self.postgres_ssl_mode}"

    openai_api_key: str = ""
    groq_api_key: str = ""
    groq_api_key_secondary: str = ""
    cerebras_api_key: str = ""

    # JWT settings with development defaults
    access_secret: str = secrets.token_urlsafe(32)
    refresh_secret: str = secrets.token_urlsafe(32)
    algorithm: str = "HS256"
    access_expire_min: int = 60  # Increased from 15 to 60 minutes for development
    refresh_expire_min: int = 10080

    github_pat: str = Field(default="")

    # email / smtp settings (defaults send to a fixed recipient)
    email_host: str = "localhost"
    email_port: int = 587
    email_user: str = ""
    email_password: str = ""
    email_from: str = ""
    # by default all messages go to this address; override via .env
    email_default_recipient: str = "devakiruba1804@gmail.com"

    model_config = {
        "env_file": _get_env_file(), 
        "extra": "ignore", 
        "case_sensitive": False,
        "populate_by_name": True
    }


setting = Settings()
