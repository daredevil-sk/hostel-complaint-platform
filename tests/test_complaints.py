"""
Tests for complaint creation, validation, and unique IDs.
"""

import pytest
from src.utils.complaints import create_complaint, get_complaint_by_number
from src.db.models import ComplaintStatus


def test_create_complaint_success(db, demo_users):
    ok, result, complaint = create_complaint(
        db,
        title="Test complaint",
        description="A detailed description of the problem",
        category="Water Supply",
        hostel="Ganga",
        block="Block A",
        floor="2nd",
        location_detail="Near room 201",
        submitter_id=demo_users["s1"].id,
    )
    assert ok is True
    assert complaint is not None
    assert result.startswith("TR-")
    assert complaint.status == ComplaintStatus.submitted
    assert complaint.vote_count == 0


def test_complaint_number_is_unique(db, demo_users):
    _, num1, c1 = create_complaint(
        db, title="A", description="Desc A", category="Plumbing",
        hostel="Ganga", block="", floor="", location_detail="",
        submitter_id=demo_users["s1"].id)
    _, num2, c2 = create_complaint(
        db, title="B", description="Desc B", category="Electrical",
        hostel="Barak", block="", floor="", location_detail="",
        submitter_id=demo_users["s1"].id)
    assert num1 != num2
    assert c1.id != c2.id


def test_complaint_number_format(db, demo_users):
    _, num, _ = create_complaint(
        db, title="C", description="desc", category="Other",
        hostel="Ganga", block="", floor="", location_detail="",
        submitter_id=demo_users["s1"].id)
    # Format: TR-YYYY-NNNN
    parts = num.split("-")
    assert parts[0] == "TR"
    assert len(parts[1]) == 4  # year
    assert parts[2].isdigit()


def test_complaint_requires_title(db, demo_users):
    ok, msg, c = create_complaint(
        db, title="", description="desc", category="Other",
        hostel="Ganga", block="", floor="", location_detail="",
        submitter_id=demo_users["s1"].id)
    assert ok is False
    assert c is None


def test_complaint_requires_description(db, demo_users):
    ok, msg, c = create_complaint(
        db, title="Title", description="", category="Other",
        hostel="Ganga", block="", floor="", location_detail="",
        submitter_id=demo_users["s1"].id)
    assert ok is False


def test_complaint_requires_hostel(db, demo_users):
    ok, msg, c = create_complaint(
        db, title="Title", description="desc", category="Other",
        hostel="", block="", floor="", location_detail="",
        submitter_id=demo_users["s1"].id)
    assert ok is False


def test_complaint_initial_status_is_submitted(db, demo_users):
    _, _, c = create_complaint(
        db, title="T", description="D", category="Safety & Security",
        hostel="Ganga", block="", floor="", location_detail="",
        submitter_id=demo_users["s1"].id)
    assert c.status == ComplaintStatus.submitted


def test_get_complaint_by_number(db, demo_users):
    _, num, _ = create_complaint(
        db, title="X", description="Y", category="Cleaning & Waste",
        hostel="Ganga", block="", floor="", location_detail="",
        submitter_id=demo_users["s1"].id)
    fetched = get_complaint_by_number(db, num)
    assert fetched is not None
    assert fetched.complaint_number == num


def test_complaint_status_history_created(db, demo_users):
    from src.db.models import ComplaintStatusHistory
    _, num, c = create_complaint(
        db, title="Status test", description="desc", category="Other",
        hostel="Ganga", block="", floor="", location_detail="",
        submitter_id=demo_users["s1"].id)
    history = db.query(ComplaintStatusHistory).filter_by(
        complaint_id=c.id).all()
    assert len(history) == 1
    assert history[0].new_status == ComplaintStatus.submitted.value
    assert history[0].old_status is None
