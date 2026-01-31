"""Service to load card configs from YAML files into database."""
import json
import logging
from pathlib import Path

import yaml
from sqlalchemy.orm import Session

from app.config import get_settings
from app.models.card import CardConfig

logger = logging.getLogger(__name__)
settings = get_settings()


def load_card_configs(db: Session) -> list[CardConfig]:
    """Load all card configs from YAML files and upsert to database.
    
    Returns list of loaded/updated CardConfig objects.
    """
    configs_dir = settings.configs_dir
    if not configs_dir.exists():
        logger.warning(f"Card configs directory not found: {configs_dir}")
        return []
    
    loaded_configs = []
    
    for yaml_file in configs_dir.glob("*.yaml"):
        try:
            config = _load_single_config(db, yaml_file)
            if config:
                loaded_configs.append(config)
        except Exception as e:
            logger.error(f"Failed to load card config from {yaml_file}: {e}")
    
    db.commit()
    logger.info(f"Loaded {len(loaded_configs)} card configs")
    return loaded_configs


def _load_single_config(db: Session, yaml_path: Path) -> CardConfig | None:
    """Load a single card config from YAML file."""
    with open(yaml_path, "r") as f:
        data = yaml.safe_load(f)
    
    slug = data.get("slug")
    if not slug:
        logger.warning(f"Card config missing slug: {yaml_path}")
        return None
    
    # Check if config already exists
    existing = db.query(CardConfig).filter(CardConfig.slug == slug).first()
    
    # Serialize patterns and benefits to JSON
    account_patterns_json = json.dumps(data.get("account_patterns", []))
    benefits_json = json.dumps(data.get("benefits", []))
    
    if existing:
        # Update existing config
        existing.name = data.get("name", existing.name)
        existing.issuer = data.get("issuer", existing.issuer)
        existing.annual_fee = data.get("annual_fee", existing.annual_fee)
        existing.benefits_url = data.get("benefits_url")
        existing.account_patterns = account_patterns_json
        existing.benefits = benefits_json
        logger.debug(f"Updated card config: {slug}")
        return existing
    else:
        # Create new config
        config = CardConfig(
            slug=slug,
            name=data.get("name", slug),
            issuer=data.get("issuer", "Unknown"),
            annual_fee=data.get("annual_fee", 0),
            benefits_url=data.get("benefits_url"),
            account_patterns=account_patterns_json,
            benefits=benefits_json,
        )
        db.add(config)
        logger.debug(f"Created card config: {slug}")
        return config


def get_card_configs(db: Session) -> list[CardConfig]:
    """Get all card configs from database."""
    return db.query(CardConfig).all()


def get_card_config_by_slug(db: Session, slug: str) -> CardConfig | None:
    """Get a card config by its slug."""
    return db.query(CardConfig).filter(CardConfig.slug == slug).first()
