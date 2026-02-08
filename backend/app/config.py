"""Application configuration."""
from functools import lru_cache
from pathlib import Path

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
    secret_key: str = "changeme-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 15
    refresh_token_expire_days: int = 7
    
    # Paths
    base_dir: Path = Path(__file__).parent
    configs_dir: Path = base_dir / "configs" / "cards"
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
