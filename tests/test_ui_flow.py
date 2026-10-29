"""
UI and navigation smoke tests using Streamlit AppTest.
Verifies that all pages load and render without exceptions.
"""

import pytest
from streamlit.testing.v1 import AppTest


def test_home_page_renders_cleanly():
    at = AppTest.from_file("app.py", default_timeout=20)
    at.run()
    assert len(at.exception) == 0


def test_board_page_renders_cleanly():
    at = AppTest.from_file("app.py", default_timeout=20)
    at.session_state["page"] = "board"
    at.run()
    assert len(at.exception) == 0


def test_login_page_renders_cleanly():
    at = AppTest.from_file("app.py", default_timeout=20)
    at.session_state["page"] = "login"
    at.run()
    assert len(at.exception) == 0


def test_register_page_renders_cleanly():
    at = AppTest.from_file("app.py", default_timeout=20)
    at.session_state["page"] = "register"
    at.run()
    assert len(at.exception) == 0


def test_student_dashboard_renders_for_logged_in_student():
    from src.db.database import get_db, init_db
    from src.db.models import Profile, UserRole
    from src.utils.auth import hash_password
    import uuid
    init_db()
    db = get_db()
    student = db.query(Profile).filter_by(role=UserRole.student).first()
    if not student:
        student = Profile(
            id=str(uuid.uuid4()),
            email="test_student@flow.local",
            display_name="Test Student",
            password_hash=hash_password("pass"),
            role=UserRole.student,
        )
        db.add(student)
        db.commit()
    db.close()

    at = AppTest.from_file("app.py", default_timeout=20)
    at.session_state["current_user"] = student
    at.session_state["page"] = "my_complaints"
    at.run()
    assert len(at.exception) == 0


def test_caretaker_dashboard_renders_for_logged_in_caretaker():
    from src.db.database import get_db, init_db
    from src.db.models import Profile, UserRole
    from src.utils.auth import hash_password
    import uuid
    init_db()
    db = get_db()
    ct = db.query(Profile).filter_by(role=UserRole.caretaker).first()
    if not ct:
        ct = Profile(
            id=str(uuid.uuid4()),
            email="test_ct@flow.local",
            display_name="Test Caretaker",
            password_hash=hash_password("pass"),
            role=UserRole.caretaker,
        )
        db.add(ct)
        db.commit()
    db.close()

    at = AppTest.from_file("app.py", default_timeout=20)
    at.session_state["current_user"] = ct
    at.session_state["page"] = "caretaker_dashboard"
    at.run()
    assert len(at.exception) == 0


def test_admin_dashboard_renders_for_logged_in_admin():
    from src.db.database import get_db, init_db
    from src.db.models import Profile, UserRole
    from src.utils.auth import hash_password
    import uuid
    init_db()
    db = get_db()
    admin = db.query(Profile).filter_by(role=UserRole.admin).first()
    if not admin:
        admin = Profile(
            id=str(uuid.uuid4()),
            email="test_admin@flow.local",
            display_name="Test Admin",
            password_hash=hash_password("pass"),
            role=UserRole.admin,
        )
        db.add(admin)
        db.commit()
    db.close()

    at = AppTest.from_file("app.py", default_timeout=20)
    at.session_state["current_user"] = admin
    at.session_state["page"] = "admin_dashboard"
    at.run()
    assert len(at.exception) == 0


def test_analytics_renders_for_logged_in_admin():
    from src.db.database import get_db, init_db
    from src.db.models import Profile, UserRole
    from src.utils.auth import hash_password
    import uuid
    init_db()
    db = get_db()
    admin = db.query(Profile).filter_by(role=UserRole.admin).first()
    if not admin:
        admin = Profile(
            id=str(uuid.uuid4()),
            email="test_admin2@flow.local",
            display_name="Test Admin 2",
            password_hash=hash_password("pass"),
            role=UserRole.admin,
        )
        db.add(admin)
        db.commit()
    db.close()

    at = AppTest.from_file("app.py", default_timeout=20)
    at.session_state["current_user"] = admin
    at.session_state["page"] = "analytics"
    at.run()
    assert len(at.exception) == 0


def test_complaint_detail_renders():
    from src.db.database import get_db, init_db
    from src.db.models import Complaint, Profile, UserRole
    from src.utils.complaints import create_complaint
    from src.utils.auth import hash_password
    import uuid
    init_db()
    db = get_db()
    complaint = db.query(Complaint).first()
    if not complaint:
        student = db.query(Profile).filter_by(role=UserRole.student).first()
        if not student:
            student = Profile(
                id=str(uuid.uuid4()),
                email="test_sub@flow.local",
                display_name="Submitter",
                password_hash=hash_password("pass"),
                role=UserRole.student,
            )
            db.add(student)
            db.commit()
        ok, num, complaint = create_complaint(
            db,
            title="Flow test complaint",
            description="Detail description test",
            category="Water Supply",
            hostel="Ganga",
            block="A",
            floor="1",
            location_detail="Room 101",
            submitter_id=student.id,
        )
    cid = complaint.id
    db.close()

    at = AppTest.from_file("app.py", default_timeout=20)
    at.session_state["selected_complaint_id"] = cid
    at.session_state["page"] = "complaint_detail"
    at.run()
    assert len(at.exception) == 0
