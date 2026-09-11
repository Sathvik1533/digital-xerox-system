"""
Configuration and settings management.

Uses pydantic-settings to load from environment variables.
Never hard-code secrets. In production, AWS provides
credentials through IAM roles attached to the ECS task.
"""
from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


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

    # Document Upload Constraints (FR-DOC-001)
    max_upload_size_bytes: int = 25 * 1024 * 1024  # 25 MB
    allowed_file_extensions: list[str] = ["pdf", "docx", "doc", "txt", "png", "jpg", "jpeg"]

    # Pricing (in paise / cents — smallest unit to avoid float errors)
    price_per_page_bw: int = 100        # ₹1.00 per page B&W
    price_per_page_color: int = 500     # ₹5.00 per page color
    supported_paper_sizes: list[str] = ["A4", "A3", "Letter"]
    supported_color_modes: list[str] = ["bw", "color"]
    paper_size_multipliers: dict[str, float] = {"a4": 1.0, "letter": 1.0, "a3": 2.0}
    double_sided_discount_factor: float = 0.8  # 20% discount for double-sided printing

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )


@lru_cache()
def get_settings() -> Settings:
    """
    Return cached settings instance.
    Using lru_cache means settings are read once and reused —
    safe for FastAPI dependency injection.
    """
    return Settings()
