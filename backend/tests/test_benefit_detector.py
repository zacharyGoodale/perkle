import json
import os
import sys
from datetime import date

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

os.environ.setdefault("DATABASE_KEY", "test-key")
os.environ.setdefault("DATABASE_URL", "sqlite:///./data/perkle.db")

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.database import Base
from app.models.benefit import BenefitPeriod
from app.models.card import CardConfig, UserCard
from app.models.transaction import Transaction
from app.models.user import User
from app.services.benefit_detector import detect_benefits_for_user


def test_detect_benefits_does_not_reapply_same_transaction():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    session = sessionmaker(bind=engine)()

    user = User(username="tester", email="tester@example.com", password_hash="hashed")
    session.add(user)
    session.flush()

    benefit = {
        "slug": "dining-credit",
        "name": "Dining Credit",
        "value": 50,
        "cadence": "monthly",
        "reset_type": "calendar_year",
        "tracking_mode": "auto",
        "detection_rules": {"credit_patterns": ["Dining Credit"], "lookback_days": 30},
    }
    card_config = CardConfig(
        slug="test-card",
        name="Test Card",
        issuer="Test Bank",
        annual_fee=0,
        benefits_url="https://example.com/benefits",
        account_patterns=json.dumps(["Test Card"]),
        benefits=json.dumps([benefit]),
    )
    session.add(card_config)
    session.flush()

    user_card = UserCard(user_id=user.id, card_config_id=card_config.id, active=1)
    session.add(user_card)
    session.flush()

    credit_txn = Transaction(
        user_id=user.id,
        card_config_id=card_config.id,
        date=date.today().isoformat(),
        name="Dining Credit - Test Merchant",
        amount=-20.0,
        account="Test Card",
    )
    session.add(credit_txn)
    session.commit()

    first_result = detect_benefits_for_user(session, user.id)
    session.commit()

    assert first_result["detected"] == 1
    session.refresh(credit_txn)
    assert credit_txn.benefit_slug == "dining-credit"

    second_result = detect_benefits_for_user(session, user.id)
    session.commit()

    assert second_result["detected"] == 0
    benefit_period = (
        session.query(BenefitPeriod)
        .filter_by(user_card_id=user_card.id, benefit_slug="dining-credit")
        .one()
    )
    assert benefit_period.amount_used == 20.0
    assert benefit_period.usage_count == 1
