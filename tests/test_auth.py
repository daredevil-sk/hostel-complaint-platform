"""
Tests for authorization — role-based access control.
"""

import pytest
from src.utils.auth import (
    hash_password, verify_password, register,
)
from src.utils.complaints import (
    create_complaint, update_status, mark_seen, acknowledge_complaint,
)
from src.db.models import UserRole, ComplaintStatus


def test_password_hash_verify():
    h = hash_password("secret123")
    assert verify_password("secret123", h)
    assert not verify_password("wrong", h)


def test_student_cannot_update_status_to_in_progress(db, demo_users):
    _, _, c = create_complaint(
        db, title="Auth test", description="desc", category="Other",
        hostel="Ganga", block="", floor="", location_detail="",
        submitter_id=demo_users["s1"].id)
    ok, _ = update_status(db, c.id, "In Progress",
                           actor_id=demo_users["s1"].id,
                           actor_role=UserRole.student)
    assert ok is False


def test_student_cannot_mark_seen(db, demo_users):
    _, _, c = create_complaint(
        db, title="Seen auth", description="desc", category="Other",
        hostel="Ganga", block="", floor="", location_detail="",
        submitter_id=demo_users["s1"].id)
    ok, _ = mark_seen(db, c.id, demo_users["s1"].id, UserRole.student)
    assert ok is False


def test_student_cannot_acknowledge(db, demo_users):
    _, _, c = create_complaint(
        db, title="Ack auth", description="desc", category="Other",
        hostel="Ganga", block="", floor="", location_detail="",
        submitter_id=demo_users["s1"].id)
    ok, _ = acknowledge_complaint(db, c.id, demo_users["s1"].id,
                                  UserRole.student)
    assert ok is False


def test_student_can_reopen_own_resolved_complaint(db, demo_users):
    _, _, c = create_complaint(
        db, title="Reopen", description="desc", category="Other",
        hostel="Ganga", block="", floor="", location_detail="",
        submitter_id=demo_users["s1"].id)
    # Move through lifecycle
    update_status(db, c.id, "Acknowledged", demo_users["caretaker"].id, UserRole.caretaker)
    update_status(db, c.id, "In Progress", demo_users["caretaker"].id, UserRole.caretaker)
    update_status(db, c.id, "Resolved", demo_users["caretaker"].id, UserRole.caretaker)

    ok, msg = update_status(db, c.id, "Reopened", demo_users["s1"].id,
                             UserRole.student, notes="Still broken.")
    assert ok is True
    db.refresh(c)
    assert c.status == ComplaintStatus.reopened


def test_caretaker_can_mark_seen_and_acknowledge(db, demo_users):
    _, _, c = create_complaint(
        db, title="CT auth", description="desc", category="Other",
        hostel="Ganga", block="", floor="", location_detail="",
        submitter_id=demo_users["s1"].id)
    ok_seen, _ = mark_seen(db, c.id, demo_users["caretaker"].id, UserRole.caretaker)
    ok_ack, _ = acknowledge_complaint(db, c.id, demo_users["caretaker"].id,
                                      UserRole.caretaker)
    assert ok_seen is True
    assert ok_ack is True


def test_admin_can_perform_all_privileged_actions(db, demo_users):
    _, _, c = create_complaint(
        db, title="Admin auth", description="desc", category="Other",
        hostel="Ganga", block="", floor="", location_detail="",
        submitter_id=demo_users["s1"].id)
    ok_seen, _ = mark_seen(db, c.id, demo_users["admin"].id, UserRole.admin)
    ok_ack, _ = acknowledge_complaint(db, c.id, demo_users["admin"].id, UserRole.admin)
    ok_prog, _ = update_status(db, c.id, "In Progress",
                                demo_users["admin"].id, UserRole.admin)
    assert ok_seen is True
    assert ok_ack is True
    assert ok_prog is True
