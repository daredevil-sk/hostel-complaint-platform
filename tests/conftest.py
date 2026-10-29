"""
Pytest configuration — sets up an in-memory SQLite test database.
"""

import os
import sys
import pytest

# Ensure project root is importable
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Use in-memory SQLite for tests (no file I/O)
os.environ["DATABASE_URL"] = "sqlite:///:memory:"
os.environ["APP_ENV"] = "test"
os.environ["UPLOAD_DIR"] = "/tmp/test_uploads"

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from src.db.models import Base

@pytest.fixture(scope="function")
def db():
    """Fresh in-memory database for each test."""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    from sqlalchemy import event as sqla_event
    @sqla_event.listens_for(engine, "connect")
    def set_pragma(conn, _):
        conn.execute("PRAGMA foreign_keys=ON")

    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def demo_users(db):
    """Create a set of demo users for tests."""
    import uuid
    from src.db.models import Profile, UserRole
    from src.utils.auth import hash_password

    admin = Profile(id=str(uuid.uuid4()), email="admin@test.local",
                    display_name="Test Admin", password_hash=hash_password("pass"),
                    role=UserRole.admin)
    caretaker = Profile(id=str(uuid.uuid4()), email="ct@test.local",
                        display_name="Test Caretaker", password_hash=hash_password("pass"),
                        role=UserRole.caretaker)
    student1 = Profile(id=str(uuid.uuid4()), email="s1@test.local",
                       display_name="Student One", password_hash=hash_password("pass"),
                       role=UserRole.student)
    student2 = Profile(id=str(uuid.uuid4()), email="s2@test.local",
                       display_name="Student Two", password_hash=hash_password("pass"),
                       role=UserRole.student)
    for u in [admin, caretaker, student1, student2]:
        db.add(u)
    db.commit()
    return {"admin": admin, "caretaker": caretaker, "s1": student1, "s2": student2}
