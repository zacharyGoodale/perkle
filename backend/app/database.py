"""Database connection and session management."""
from collections.abc import Generator
from contextlib import contextmanager
import importlib
from urllib.parse import quote, urlencode

from sqlalchemy import create_engine, event
from sqlalchemy.dialects.sqlite import pysqlite as sqlite_pysqlite
from sqlalchemy.engine import make_url
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


def _build_sqlcipher_url(raw_url: str, database_key: str) -> str:
    parsed_url = make_url(raw_url)
    if parsed_url.password:
        return raw_url

    encoded_key = quote(database_key, safe="")
    database_path = parsed_url.database or ""
    query = f"?{urlencode(parsed_url.query)}" if parsed_url.query else ""
    return f"{parsed_url.drivername}://:{encoded_key}@/{database_path}{query}"


database_url = (
    _build_sqlcipher_url(settings.database_url, settings.database_key)
    if uses_sqlcipher
    else settings.database_url
)

# pysqlcipher3 does not support sqlite3's deterministic create_function kwarg.
# SQLAlchemy checks this through sqlite_pysqlite.util.py38 when creating dialect
# on-connect handlers, so we disable it only while creating this engine.
original_py38 = sqlite_pysqlite.util.py38
if uses_sqlcipher:
    sqlite_pysqlite.util.py38 = False
try:
    engine = create_engine(
        database_url,
        connect_args=connect_args,
        echo=settings.debug,
    )
finally:
    sqlite_pysqlite.util.py38 = original_py38

if "pysqlcipher" in settings.database_url:
    @event.listens_for(engine, "connect")
    def set_sqlcipher_key(dbapi_connection, connection_record) -> None:
        cursor = dbapi_connection.cursor()
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
