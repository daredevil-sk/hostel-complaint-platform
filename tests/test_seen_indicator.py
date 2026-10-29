"""
Tests for the caretaker seen/acknowledged indicator.
Critical feature — tests specified in Section 18 of the spec.
"""

import pytest
from datetime import datetime
from src.utils.complaints import (
    create_complaint, mark_seen, acknowledge_complaint, get_seen_status,
)
from src.db.models import ComplaintStatus, UserRole, CaretakerAcknowledgement


def _make_complaint(db, submitter_id):
    _, _, c = create_complaint(
        db, title="Test", description="Desc", category="Plumbing",
        hostel="Ganga", block="A", floor="1", location_detail="",
        submitter_id=submitter_id)
    return c


# ─── Spec requirement: new complaints begin unseen ────────────────────────────

def test_new_complaint_is_unseen(db, demo_users):
    c = _make_complaint(db, demo_users["s1"].id)
    is_seen, ack = get_seen_status(db, c.id)
    assert is_seen is False
    assert ack is None


# ─── Students cannot mark their own complaints as seen ────────────────────────

def test_student_cannot_mark_seen(db, demo_users):
    c = _make_complaint(db, demo_users["s1"].id)
    ok, msg = mark_seen(db, c.id, demo_users["s1"].id, UserRole.student)
    assert ok is False
    is_seen, ack = get_seen_status(db, c.id)
    assert is_seen is False


# ─── Authorized caretaker can mark as seen ────────────────────────────────────

def test_caretaker_can_mark_seen(db, demo_users):
    c = _make_complaint(db, demo_users["s1"].id)
    ok, msg = mark_seen(db, c.id, demo_users["caretaker"].id, UserRole.caretaker)
    assert ok is True
    is_seen, ack = get_seen_status(db, c.id)
    assert is_seen is True
    assert ack is not None
    assert ack.first_seen_at is not None


# ─── Admin can mark as seen ────────────────────────────────────────────────────

def test_admin_can_mark_seen(db, demo_users):
    c = _make_complaint(db, demo_users["s1"].id)
    ok, msg = mark_seen(db, c.id, demo_users["admin"].id, UserRole.admin)
    assert ok is True


# ─── first_seen_at is preserved (immutable) ───────────────────────────────────

def test_first_seen_timestamp_is_preserved(db, demo_users):
    c = _make_complaint(db, demo_users["s1"].id)
    mark_seen(db, c.id, demo_users["caretaker"].id, UserRole.caretaker)
    _, ack1 = get_seen_status(db, c.id)
    first_seen = ack1.first_seen_at

    # Mark seen again — should update last_seen but not first_seen
    import time; time.sleep(0.05)
    mark_seen(db, c.id, demo_users["caretaker"].id, UserRole.caretaker)
    db.expire_all()
    _, ack2 = get_seen_status(db, c.id)

    assert ack2.first_seen_at == first_seen  # immutable
    assert ack2.last_seen_at >= first_seen   # updated


# ─── Seen ≠ Acknowledged (separate states) ────────────────────────────────────

def test_seen_and_acknowledged_are_separate(db, demo_users):
    c = _make_complaint(db, demo_users["s1"].id)
    mark_seen(db, c.id, demo_users["caretaker"].id, UserRole.caretaker)

    is_seen, ack = get_seen_status(db, c.id)
    assert is_seen is True
    assert ack.acknowledged_at is None   # NOT acknowledged yet

    acknowledge_complaint(db, c.id, demo_users["caretaker"].id,
                          UserRole.caretaker, work_notes="Will fix soon.")
    db.expire_all()
    _, ack2 = get_seen_status(db, c.id)
    assert ack2.acknowledged_at is not None  # now acknowledged


# ─── Acknowledgement transitions status to Acknowledged ───────────────────────

def test_acknowledge_transitions_status(db, demo_users):
    c = _make_complaint(db, demo_users["s1"].id)
    assert c.status == ComplaintStatus.submitted

    acknowledge_complaint(db, c.id, demo_users["caretaker"].id,
                          UserRole.caretaker)
    db.refresh(c)
    assert c.status == ComplaintStatus.acknowledged


# ─── Student cannot acknowledge ───────────────────────────────────────────────

def test_student_cannot_acknowledge(db, demo_users):
    c = _make_complaint(db, demo_users["s1"].id)
    ok, msg = acknowledge_complaint(db, c.id, demo_users["s1"].id,
                                    UserRole.student)
    assert ok is False
    db.refresh(c)
    assert c.status == ComplaintStatus.submitted   # unchanged


# ─── Multiple caretakers get separate acknowledgement records ──────────────────

def test_multiple_caretakers_separate_records(db, demo_users):
    """Each caretaker gets their own acknowledgement row."""
    import uuid
    from src.db.models import Profile
    caretaker2 = Profile(id=str(uuid.uuid4()), email="ct2@test.local",
                         display_name="CT2", password_hash="x",
                         role=UserRole.caretaker)
    db.add(caretaker2)
    db.commit()

    c = _make_complaint(db, demo_users["s1"].id)
    mark_seen(db, c.id, demo_users["caretaker"].id, UserRole.caretaker)
    mark_seen(db, c.id, caretaker2.id, UserRole.caretaker)

    acks = db.query(CaretakerAcknowledgement).filter_by(complaint_id=c.id).all()
    assert len(acks) == 2
    caretaker_ids = {a.caretaker_id for a in acks}
    assert demo_users["caretaker"].id in caretaker_ids
    assert caretaker2.id in caretaker_ids
