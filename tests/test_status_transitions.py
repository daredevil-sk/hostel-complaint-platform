"""
Tests for status transitions, lifecycle, and role-based authorization.
"""

import pytest
from src.utils.complaints import (
    create_complaint, update_status, acknowledge_complaint,
)
from src.db.models import ComplaintStatus, UserRole, ComplaintStatusHistory


def _make_complaint(db, submitter_id):
    _, _, c = create_complaint(
        db, title="Lifecycle test", description="desc", category="Electrical",
        hostel="Ganga", block="A", floor="1", location_detail="",
        submitter_id=submitter_id)
    return c


def test_full_lifecycle(db, demo_users):
    c = _make_complaint(db, demo_users["s1"].id)
    assert c.status == ComplaintStatus.submitted

    # Submitted → Acknowledged
    ok, msg = update_status(db, c.id, "Acknowledged",
                            actor_id=demo_users["caretaker"].id,
                            actor_role=UserRole.caretaker)
    assert ok is True
    db.refresh(c)
    assert c.status == ComplaintStatus.acknowledged

    # Acknowledged → In Progress
    ok, msg = update_status(db, c.id, "In Progress",
                            actor_id=demo_users["caretaker"].id,
                            actor_role=UserRole.caretaker)
    assert ok is True
    db.refresh(c)
    assert c.status == ComplaintStatus.in_progress

    # In Progress → Resolved
    ok, msg = update_status(db, c.id, "Resolved",
                            actor_id=demo_users["caretaker"].id,
                            actor_role=UserRole.caretaker)
    assert ok is True
    db.refresh(c)
    assert c.status == ComplaintStatus.resolved
    assert c.resolved_at is not None

    # Resolved → Reopened (by student)
    ok, msg = update_status(db, c.id, "Reopened",
                            actor_id=demo_users["s1"].id,
                            actor_role=UserRole.student,
                            notes="Issue persists.")
    assert ok is True
    db.refresh(c)
    assert c.status == ComplaintStatus.reopened


def test_student_cannot_change_status_arbitrarily(db, demo_users):
    c = _make_complaint(db, demo_users["s1"].id)
    # Student should not be able to move Submitted → In Progress
    ok, msg = update_status(db, c.id, "In Progress",
                            actor_id=demo_users["s1"].id,
                            actor_role=UserRole.student)
    assert ok is False
    db.refresh(c)
    assert c.status == ComplaintStatus.submitted  # unchanged


def test_invalid_transition_rejected(db, demo_users):
    c = _make_complaint(db, demo_users["s1"].id)
    # Cannot jump Submitted → Resolved
    ok, msg = update_status(db, c.id, "Resolved",
                            actor_id=demo_users["caretaker"].id,
                            actor_role=UserRole.caretaker)
    assert ok is False


def test_status_history_not_overwritten(db, demo_users):
    c = _make_complaint(db, demo_users["s1"].id)
    update_status(db, c.id, "Acknowledged",
                  actor_id=demo_users["caretaker"].id,
                  actor_role=UserRole.caretaker)
    update_status(db, c.id, "In Progress",
                  actor_id=demo_users["caretaker"].id,
                  actor_role=UserRole.caretaker)

    history = (
        db.query(ComplaintStatusHistory)
        .filter_by(complaint_id=c.id)
        .order_by(ComplaintStatusHistory.created_at)
        .all()
    )
    # initial + 2 transitions = 3 records
    assert len(history) >= 3
    statuses = [h.new_status for h in history]
    assert ComplaintStatus.submitted.value in statuses
    assert ComplaintStatus.acknowledged.value in statuses
    assert ComplaintStatus.in_progress.value in statuses


def test_reopen_records_reason(db, demo_users):
    c = _make_complaint(db, demo_users["s1"].id)
    update_status(db, c.id, "Acknowledged", actor_id=demo_users["caretaker"].id,
                  actor_role=UserRole.caretaker)
    update_status(db, c.id, "In Progress", actor_id=demo_users["caretaker"].id,
                  actor_role=UserRole.caretaker)
    update_status(db, c.id, "Resolved", actor_id=demo_users["caretaker"].id,
                  actor_role=UserRole.caretaker)
    update_status(db, c.id, "Reopened", actor_id=demo_users["s1"].id,
                  actor_role=UserRole.student, notes="Issue came back.")

    reopen_record = (
        db.query(ComplaintStatusHistory)
        .filter_by(complaint_id=c.id, new_status="Reopened")
        .first()
    )
    assert reopen_record is not None
    assert "Issue came back" in (reopen_record.notes or "")


def test_closed_complaint_has_no_transitions(db, demo_users):
    c = _make_complaint(db, demo_users["s1"].id)
    update_status(db, c.id, "Closed", actor_id=demo_users["admin"].id,
                  actor_role=UserRole.admin)
    db.refresh(c)
    assert c.status == ComplaintStatus.closed

    ok, msg = update_status(db, c.id, "Acknowledged",
                            actor_id=demo_users["caretaker"].id,
                            actor_role=UserRole.caretaker)
    assert ok is False
