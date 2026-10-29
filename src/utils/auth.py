"""
Authentication utilities — password hashing, session management, authorization.
"""

from __future__ import annotations

import bcrypt
import streamlit as st

from src.db.database import get_db
from src.db.models import Profile, UserRole, AuditLog
from datetime import datetime, timezone


# ─── Password helpers ────────────────────────────────────────────────────────

def hash_password(plain: str) -> str:
    return bcrypt.hashpw(plain.encode(), bcrypt.gensalt()).decode()


def verify_password(plain: str, hashed: str) -> bool:
    try:
        return bcrypt.checkpw(plain.encode(), hashed.encode())
    except Exception:
        return False


from dataclasses import dataclass

@dataclass
class UserInfo:
    id: str
    email: str
    display_name: str
    role: UserRole
    hostel: str | None = None
    is_active: bool = True

    @classmethod
    def from_profile(cls, profile: Profile) -> UserInfo:
        return cls(
            id=profile.id,
            email=profile.email,
            display_name=profile.display_name,
            role=profile.role,
            hostel=profile.hostel,
            is_active=profile.is_active,
        )


# ─── Session helpers ─────────────────────────────────────────────────────────

def get_current_user() -> UserInfo | None:
    """Return the currently logged-in user from session state, or None."""
    val = st.session_state.get("current_user")
    if val is None:
        return None
    if isinstance(val, UserInfo):
        return val
    if hasattr(val, "id") and hasattr(val, "role"):
        try:
            return UserInfo.from_profile(val)
        except Exception:
            return val
    return val


def is_logged_in() -> bool:
    return get_current_user() is not None


def get_role() -> UserRole | None:
    user = get_current_user()
    return user.role if user else None


def require_login():
    """Halt page rendering if the user is not logged in."""
    if not is_logged_in():
        st.error("🔒 You must be logged in to view this page.")
        st.stop()


def require_role(*roles: UserRole):
    """Halt page rendering if the user does not hold one of the given roles."""
    require_login()
    if get_role() not in roles:
        st.error("⛔ You do not have permission to perform this action.")
        st.stop()


# ─── Login / logout ──────────────────────────────────────────────────────────

def login(email: str, password: str) -> tuple[bool, str]:
    """
    Verify credentials and store the user in session state.
    Returns (success, message).
    """
    db = get_db()
    try:
        user: Profile | None = (
            db.query(Profile)
            .filter(Profile.email == email.lower().strip(), Profile.is_active == True)
            .first()
        )
        if user is None or not verify_password(password, user.password_hash):
            return False, "Invalid email or password."
        st.session_state["current_user"] = UserInfo.from_profile(user)
        st.session_state["user_id"] = user.id
        st.session_state["user_role"] = user.role
        _audit(db, actor_id=user.id, action="login", entity_type="user", entity_id=user.id)
        return True, f"Welcome, {user.display_name}!"
    except Exception as e:
        return False, f"Login error: {e}"
    finally:
        db.close()


def logout():
    user = get_current_user()
    if user:
        db = get_db()
        try:
            _audit(db, actor_id=user.id, action="logout", entity_type="user",
                   entity_id=user.id)
        finally:
            db.close()
    for key in ["current_user", "user_id", "user_role"]:
        st.session_state.pop(key, None)


def register(email: str, display_name: str, password: str,
             role: UserRole = UserRole.student,
             hostel: str | None = None) -> tuple[bool, str]:
    """
    Register a new user. Returns (success, message or user_id).
    Only admins should be able to create caretaker/admin accounts;
    this function is also called from the seed script.
    """
    import uuid
    db = get_db()
    try:
        existing = db.query(Profile).filter(
            Profile.email == email.lower().strip()).first()
        if existing:
            return False, "An account with this email already exists."
        user = Profile(
            id=str(uuid.uuid4()),
            email=email.lower().strip(),
            display_name=display_name.strip(),
            password_hash=hash_password(password),
            role=role,
            hostel=hostel,
        )
        db.add(user)
        db.commit()
        _audit(db, actor_id=user.id, action="register", entity_type="user",
               entity_id=user.id)
        return True, user.id
    except Exception as e:
        db.rollback()
        return False, str(e)
    finally:
        db.close()


# ─── Authorization helpers ───────────────────────────────────────────────────

def is_student() -> bool:
    return get_role() == UserRole.student


def is_caretaker() -> bool:
    return get_role() == UserRole.caretaker


def is_admin() -> bool:
    return get_role() == UserRole.admin


def can_submit_complaint() -> bool:
    return get_role() in (UserRole.student, UserRole.admin)


def can_vote() -> bool:
    return get_role() == UserRole.student


def can_acknowledge(complaint) -> bool:
    """Caretaker may acknowledge if assigned to the complaint or if admin."""
    user = get_current_user()
    if user is None:
        return False
    if user.role == UserRole.admin:
        return True
    if user.role == UserRole.caretaker:
        return (complaint.assigned_caretaker_id == user.id or
                complaint.assigned_caretaker_id is None)
    return False


def can_assign() -> bool:
    return get_role() == UserRole.admin


def can_moderate() -> bool:
    return get_role() in (UserRole.admin, UserRole.caretaker)


# ─── Internal ────────────────────────────────────────────────────────────────

def _audit(db, actor_id: str, action: str, entity_type: str,
           entity_id: str | None = None, metadata: dict | None = None):
    import json
    log = AuditLog(
        actor_id=actor_id,
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        metadata_json=json.dumps(metadata) if metadata else None,
    )
    db.add(log)
    try:
        db.commit()
    except Exception:
        db.rollback()
