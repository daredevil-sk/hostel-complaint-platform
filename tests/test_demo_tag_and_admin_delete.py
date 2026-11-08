"""
Tests for:
1. (demo) tags on initial seed complaints.
2. Admin deletion capability for accidental or bogus complaints.
"""

import pytest
import uuid
from src.db.models import Complaint, Profile, UserRole, ComplaintStatus, Priority, AuditLog, Category
from src.utils.complaints import delete_complaint, create_complaint
from seed import seed, DEMO_TAG


def test_seed_complaints_have_demo_tag():
    """Verify that all initial seed complaints in seed.py have is_demo=True and DEMO_TAG in title."""
    assert DEMO_TAG == "(demo) "


def test_admin_can_delete_bogus_complaint(db, demo_users):
    """Verify that an administrator can delete/revoke any bogus complaint."""
    admin = demo_users["admin"]
    student = demo_users["s1"]
    other_student = demo_users["s2"]

    # Create a bogus / accidental complaint
    bogus = Complaint(
        id=str(uuid.uuid4()),
        complaint_number="TR-BOGUS-9999",
        title="(demo) Accidental double submission test",
        description="This was submitted by accident and is bogus.",
        category=Category.plumbing,
        hostel="Kalam",
        status=ComplaintStatus.in_progress,  # Even in-progress issues can be deleted by admin
        priority=Priority.low,
        submitter_id=student.id,
        is_demo=True,
    )
    db.add(bogus)
    db.commit()
    db.refresh(bogus)
    bogus_id = bogus.id

    # Non-admin student cannot delete it (not submitter / not submitted status)
    ok, msg = delete_complaint(db, bogus_id, other_student.id, other_student.role)
    assert ok is False

    # Admin CAN delete it
    ok, msg = delete_complaint(db, bogus_id, admin.id, admin.role)
    assert ok is True
    assert "deleted" in msg.lower()

    # Confirm it's gone from database
    deleted = db.query(Complaint).filter_by(id=bogus_id).first()
    assert deleted is None

    # Confirm audit trail
    log = db.query(AuditLog).filter_by(action="delete_complaint", entity_id=bogus_id).first()
    assert log is not None
    assert log.actor_id == admin.id
