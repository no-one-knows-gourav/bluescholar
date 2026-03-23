"""Application configuration loaded from environment variables."""

from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """Central config — all values read from .env or environment."""

    # Supabase
    supabase_url: str = ""
    supabase_service_role_key: str = ""
    supabase_jwt_secret: str = ""

    # Qdrant
    qdrant_url: str = ""
    qdrant_api_key: str = ""

    # Cloudflare R2
    cloudflare_r2_account_id: str = ""
    cloudflare_r2_access_key_id: str = ""
    cloudflare_r2_secret_access_key: str = ""
    cloudflare_r2_bucket: str = "bluescholar-uploads"
    cloudflare_r2_public_url: str = ""

    # Upstash Redis
    upstash_redis_url: str = ""
    upstash_redis_token: str = ""

    # LLM Providers
    anthropic_api_key: str = ""
    openai_api_key: str = ""
    google_generative_ai_api_key: str = ""

    # Celery
    celery_broker_url: str = "redis://localhost:6379/0"

    # App
    frontend_url: str = "http://localhost:3000"
    environment: str = "development"

    @property
    def r2_endpoint_url(self) -> str:
        return f"https://{self.cloudflare_r2_account_id}.r2.cloudflarestorage.com"

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


@lru_cache()
def get_settings() -> Settings:
    return Settings()
