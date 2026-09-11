"""
Configuration and settings management.

Uses pydantic-settings to load from environment variables.
Never hard-code secrets. In production, AWS provides
credentials through IAM roles attached to the ECS task.
"""
from functools import lru_cache
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Application
    app_name: str = "Digital Xerox & Stationery Ordering System"
    app_version: str = "0.1.0"
    environment: str = "development"
    debug: bool = False

    # AWS — credentials come from IAM role in production, never hard-coded
    aws_region: str = "ap-south-1"
    aws_access_key_id: str | None = None      # Only for local dev, not production
    aws_secret_access_key: str | None = None  # Only for local dev, not production

    # DynamoDB
    dynamodb_table_name: str = "digital-xerox-orders"
    dynamodb_endpoint_url: str | None = None  # Set to local endpoint for dev/test

    # S3
    s3_bucket_name: str = "digital-xerox-documents"
    s3_endpoint_url: str | None = None  # Set to local endpoint for dev/test

    # Pricing (in paise / cents — smallest unit to avoid float errors)
    price_per_page_bw: int = 100        # ₹1.00 per page B&W
    price_per_page_color: int = 500     # ₹5.00 per page color

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


@lru_cache()
def get_settings() -> Settings:
    """
    Return cached settings instance.
    Using lru_cache means settings are read once and reused —
    safe for FastAPI dependency injection.
    """
    return Settings()
