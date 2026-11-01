"""
Database connection and session management.
"""

import os
from pathlib import Path

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    try:
        from src.utils.env_loader import load_env
        load_env()
    except Exception:
        pass

from sqlalchemy import create_engine, event, text
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool

def normalize_db_url(url: str) -> str:
    """Normalize database URL for SQLAlchemy compatibility."""
    if not url:
        return url
    url = url.strip()
    if url.startswith("postgres://"):
        url = "postgresql://" + url[len("postgres://"):]
    if url.startswith("postgresql://"):
        # Auto-detect modern psycopg (v3) vs psycopg2
        try:
            import psycopg  # noqa: F401
            return "postgresql+psycopg://" + url[len("postgresql://"):]
        except ImportError:
            try:
                import psycopg2  # noqa: F401
                return "postgresql+psycopg2://" + url[len("postgresql://"):]
            except ImportError:
                return url
    return url


RAW_DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./hostel_complaints.db")
DATABASE_URL = normalize_db_url(RAW_DATABASE_URL)

# SQLite-specific settings for thread safety in Streamlit
_connect_args = {}
_poolclass = None

if DATABASE_URL.startswith("sqlite"):
    _connect_args = {"check_same_thread": False}
    _poolclass = StaticPool
    engine = create_engine(
        DATABASE_URL,
        connect_args=_connect_args,
        poolclass=_poolclass,
        echo=False,
    )

    @event.listens_for(engine, "connect")
    def _set_sqlite_pragma(dbapi_conn, connection_record):
        cursor = dbapi_conn.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.close()
else:
    engine = create_engine(DATABASE_URL, pool_pre_ping=True, echo=False)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, expire_on_commit=False, bind=engine)


def get_db() -> Session:
    """Return a new database session. Caller is responsible for closing it."""
    return SessionLocal()


def init_db():
    """Create all tables defined in the models."""
    from src.db.models import Base  # noqa: F401 – import to register models
    Base.metadata.create_all(bind=engine)
    _migrate_db()


def _migrate_db():
    """Apply incremental schema migrations for new columns."""
    with engine.connect() as conn:
        if DATABASE_URL.startswith("sqlite"):
            try:
                result = conn.execute(text("PRAGMA table_info(complaints)"))
                cols = {row[1] for row in result}
                if "is_anonymous" not in cols:
                    conn.execute(text(
                        "ALTER TABLE complaints ADD COLUMN is_anonymous BOOLEAN NOT NULL DEFAULT 0"
                    ))
                    conn.commit()
            except Exception:
                pass
        else:
            try:
                conn.execute(text(
                    "ALTER TABLE complaints ADD COLUMN IF NOT EXISTS "
                    "is_anonymous BOOLEAN NOT NULL DEFAULT FALSE"
                ))
                conn.commit()
            except Exception:
                pass
