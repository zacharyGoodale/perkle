"""Application configuration."""
from collections import Counter
from functools import lru_cache
import math
from pathlib import Path

from pydantic import field_validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # App
    app_name: str = "Perkle"
    debug: bool = False
    
    # Database
    database_url: str = "sqlite:///./data/perkle.db"
    database_key: str
    
    # Auth
    secret_key: str
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 15
    refresh_token_expire_days: int = 7
    refresh_cookie_name: str = "perkle_refresh"
    refresh_cookie_path: str = "/api/auth"
    refresh_cookie_samesite: str = "lax"
    refresh_cookie_secure: bool = True
    
    # Paths
    base_dir: Path = Path(__file__).parent
    configs_dir: Path = base_dir / "configs" / "cards"
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

    @field_validator("secret_key")
    @classmethod
    def validate_secret_key(cls, value: str) -> str:
        """Fail closed if SECRET_KEY is weak or placeholder quality."""
        if not value:
            raise ValueError("SECRET_KEY must be set.")

        if len(value) < 32:
            raise ValueError("SECRET_KEY must be at least 32 characters.")

        weak_values = {"changeme", "changeme-in-production", "secret", "password", "test"}
        lowered = value.lower()
        if lowered in weak_values or "changeme" in lowered:
            raise ValueError("SECRET_KEY must not be a placeholder value.")

        counts = Counter(value)
        entropy_per_char = -sum((count / len(value)) * math.log2(count / len(value)) for count in counts.values())
        estimated_entropy_bits = entropy_per_char * len(value)
        if estimated_entropy_bits < 100:
            raise ValueError("SECRET_KEY entropy is too low; use a cryptographically random value.")

        return value


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
