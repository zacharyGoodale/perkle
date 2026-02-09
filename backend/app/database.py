"""Database connection and session management."""
from collections.abc import Generator
from contextlib import contextmanager
import importlib

from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session, declarative_base, sessionmaker

from app.config import get_settings

settings = get_settings()

if not settings.database_key:
    raise ValueError("DATABASE_KEY must be set.")

if "pysqlcipher" in settings.database_url:
    try:
        importlib.import_module("pysqlcipher3")
    except ImportError as exc:
        raise RuntimeError("pysqlcipher3 is required but failed to import.") from exc

# SQLite requires check_same_thread=False for FastAPI
connect_args = {"check_same_thread": False} if "sqlite" in settings.database_url else {}

uses_sqlcipher = "pysqlcipher" in settings.database_url

if uses_sqlcipher and not settings.database_key:
    raise RuntimeError("DATABASE_KEY must be set when using SQLCipher.")

engine = create_engine(
    settings.database_url,
    connect_args=connect_args,
    echo=settings.debug,
)

if "pysqlcipher" in settings.database_url:
    @event.listens_for(engine, "connect")
    def set_sqlcipher_key(dbapi_connection, connection_record) -> None:
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA key = ?", (settings.database_key,))
        cursor.execute("PRAGMA cipher_memory_security = ON;")
        cursor.close()

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db() -> Generator[Session, None, None]:
    """Dependency that provides a database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@contextmanager
def get_db_context() -> Generator[Session, None, None]:
    """Context manager for database session (for use outside of FastAPI)."""
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()
