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
    """Apply incremental schema migrations for new columns and seed primary caretakers."""
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

                p_result = conn.execute(text("PRAGMA table_info(profiles)"))
                p_cols = {row[1] for row in p_result}
                if "gender" not in p_cols:
                    conn.execute(text("ALTER TABLE profiles ADD COLUMN gender VARCHAR(20)"))
                    conn.commit()
                if "block" not in p_cols:
                    conn.execute(text("ALTER TABLE profiles ADD COLUMN block VARCHAR(50)"))
                    conn.commit()
            except Exception:
                pass
        else:
            try:
                conn.execute(text(
                    "ALTER TABLE complaints ADD COLUMN IF NOT EXISTS "
                    "is_anonymous BOOLEAN NOT NULL DEFAULT FALSE"
                ))
                conn.execute(text(
                    "ALTER TABLE profiles ADD COLUMN IF NOT EXISTS "
                    "gender VARCHAR(20)"
                ))
                conn.execute(text(
                    "ALTER TABLE profiles ADD COLUMN IF NOT EXISTS "
                    "block VARCHAR(50)"
                ))
                conn.commit()
            except Exception:
                pass

    _ensure_primary_accounts()


def _ensure_primary_accounts():
    """Ensure primary caretakers and admins exist in the database."""
    try:
        from src.db.models import Profile, UserRole, Complaint
        from src.utils.auth import hash_password
        from src.utils.hostel_rules import PRIMARY_CARETAKERS, DEFAULT_CARETAKER_PASSWORD, DEFAULT_ADMIN_PASSWORD, get_caretaker_email_for_complaint
        import uuid

        db = SessionLocal()
        try:
            # 1. Primary Caretakers
            caretaker_profiles = {}
            for email, data in PRIMARY_CARETAKERS.items():
                p = db.query(Profile).filter(Profile.email == email).first()
                if not p:
                    p = Profile(
                        id=str(uuid.uuid4()),
                        email=email,
                        display_name=data["display_name"],
                        password_hash=hash_password(DEFAULT_CARETAKER_PASSWORD),
                        role=UserRole.caretaker,
                        hostel=data["hostel"],
                        gender=data["gender"],
                        block=",".join(data["blocks"]) if isinstance(data["blocks"], list) else "",
                        is_active=True,
                    )
                    db.add(p)
                    db.flush()
                else:
                    # Keep hostel/gender consistent
                    p.hostel = data["hostel"]
                    p.gender = data["gender"]
                    p.role = UserRole.caretaker
                caretaker_profiles[email] = p

            # 2. Admin accounts
            admin_iitp = db.query(Profile).filter(Profile.email == "admin@iitp.ac.in").first()
            if not admin_iitp:
                admin_iitp = Profile(
                    id=str(uuid.uuid4()),
                    email="admin@iitp.ac.in",
                    display_name="IIT Patna Hostel Admin",
                    password_hash=hash_password(DEFAULT_ADMIN_PASSWORD),
                    role=UserRole.admin,
                    is_active=True,
                )
                db.add(admin_iitp)

            admin_demo = db.query(Profile).filter(Profile.email == "admin@demo.teamr").first()
            if not admin_demo:
                admin_demo = Profile(
                    id=str(uuid.uuid4()),
                    email="admin@demo.teamr",
                    display_name="Demo Admin",
                    password_hash=hash_password("demo1234"),
                    role=UserRole.admin,
                    is_active=True,
                )
                db.add(admin_demo)

            ct_demo = db.query(Profile).filter(Profile.email == "caretaker@demo.teamr").first()
            if not ct_demo:
                ct_demo = Profile(
                    id=str(uuid.uuid4()),
                    email="caretaker@demo.teamr",
                    display_name="Demo Caretaker (Ramesh)",
                    password_hash=hash_password("demo1234"),
                    role=UserRole.caretaker,
                    is_active=True,
                )
                db.add(ct_demo)

            # 3. Student accounts
            student_defaults = {
                "student1@demo.teamr": {"name": "Pooja Sharma (Asima)", "gender": "Female", "hostel": "Asima", "block": ""},
                "student2@demo.teamr": {"name": "Ananya Verma (Aryabhatta C)", "gender": "Female", "hostel": "Aryabhatta", "block": "Block C"},
                "student3@demo.teamr": {"name": "Rahul Kumar (Kalam)", "gender": "Male", "hostel": "Kalam", "block": "Block B"},
                "student4@demo.teamr": {"name": "Amit Singh (CV Raman)", "gender": "Male", "hostel": "CV Raman", "block": ""},
                "student5@demo.teamr": {"name": "Rohan Mehta (Aryabhatta A)", "gender": "Male", "hostel": "Aryabhatta", "block": "Block A"},
            }
            for s_email, s_data in student_defaults.items():
                stu = db.query(Profile).filter(Profile.email == s_email).first()
                if not stu:
                    stu = Profile(
                        id=str(uuid.uuid4()),
                        email=s_email,
                        display_name=s_data["name"],
                        password_hash=hash_password("demo1234"),
                        role=UserRole.student,
                        gender=s_data["gender"],
                        hostel=s_data["hostel"],
                        block=s_data["block"],
                        is_active=True,
                    )
                    db.add(stu)
                else:
                    if not stu.gender:
                        stu.gender = s_data["gender"]
                    if not stu.block:
                        stu.block = s_data["block"]
                    if not stu.hostel:
                        stu.hostel = s_data["hostel"]

            # 4. Auto-assign complaints to respective primary caretaker if not set
            complaints = db.query(Complaint).all()
            for c in complaints:
                target_email = get_caretaker_email_for_complaint(c.hostel, c.block)
                ct = caretaker_profiles.get(target_email)
                if ct and not c.assigned_caretaker_id:
                    c.assigned_caretaker_id = ct.id

            db.commit()
        except Exception as ex:
            db.rollback()
        finally:
            db.close()
    except Exception:
        pass
