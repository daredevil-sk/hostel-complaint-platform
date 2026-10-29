"""
Database connection and session management.
"""

import os
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy import create_engine, event, text
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./hostel_complaints.db")

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
