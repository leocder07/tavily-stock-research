"""Configuration settings for the Stock Research System."""

from typing import List, Optional
from pydantic_settings import BaseSettings
import json


class Settings(BaseSettings):
    """Application settings."""

    # API Keys
    TAVILY_API_KEY: str
    OPENAI_API_KEY: str

    # Multi-Source Sentiment API Keys (Optional)
    TWITTER_BEARER_TOKEN: Optional[str] = None
    REDDIT_CLIENT_ID: Optional[str] = None
    REDDIT_CLIENT_SECRET: Optional[str] = None
    ALPHA_VANTAGE_API_KEY: Optional[str] = None
    NEWS_API_KEY: Optional[str] = None

    # Sentiment Configuration
    SENTIMENT_USE_MULTI_SOURCE: bool = True
    SENTIMENT_USE_LEGACY_FALLBACK: bool = True
    SENTIMENT_WEIGHT_TWITTER: float = 0.30
    SENTIMENT_WEIGHT_REDDIT: float = 0.20
    SENTIMENT_WEIGHT_NEWS: float = 0.30
    SENTIMENT_WEIGHT_TAVILY: float = 0.20

    # MongoDB Configuration
    MONGODB_URL: str
    DATABASE_NAME: str = "stock_research"

    # Redis Configuration (optional)
    REDIS_URL: Optional[str] = None

    # JWT Configuration
    JWT_SECRET: str = "your-secret-key"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRATION_MINUTES: int = 1440

    # Application Configuration
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    API_V1_PREFIX: str = "/api/v1"
    PROJECT_NAME: str = "Stock Research System"
    PROJECT_VERSION: str = "1.0.0"

    # CORS Settings - parse JSON string from env
    BACKEND_CORS_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:8000"]

    # Rate Limiting
    RATE_LIMIT_PER_MINUTE: int = 60
    RATE_LIMIT_PER_HOUR: int = 1000

    # Agent Configuration
    MAX_AGENT_RETRIES: int = 3
    AGENT_TIMEOUT_SECONDS: int = 60
    MAX_CONCURRENT_AGENTS: int = 8

    # AWS Configuration
    AWS_REGION: Optional[str] = "us-east-1"
    AWS_ACCESS_KEY_ID: Optional[str] = None
    AWS_SECRET_ACCESS_KEY: Optional[str] = None

    # Logging
    LOG_LEVEL: str = "INFO"
    SENTRY_DSN: Optional[str] = None

    class Config:
        env_file = ".env"
        case_sensitive = True

    @classmethod
    def parse_env_list(cls, v):
        """Parse JSON list from environment variable."""
        if isinstance(v, str):
            try:
                return json.loads(v)
            except:
                return [v]
        return v


# Create settings instance
settings = Settings()