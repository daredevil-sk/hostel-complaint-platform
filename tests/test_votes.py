"""
Tests for the voting system — uniqueness, toggle, count integrity.
"""

import pytest
from src.utils.complaints import create_complaint, toggle_vote, has_voted
from src.db.models import ComplaintVote


def _make_complaint(db, users, title="Complaint"):
    _, _, c = create_complaint(
        db, title=title, description="Test description", category="Water Supply",
        hostel="Ganga", block="A", floor="1", location_detail="",
        submitter_id=users["s1"].id)
    return c


def test_student_can_vote(db, demo_users):
    c = _make_complaint(db, demo_users)
    added, msg, count = toggle_vote(db, c.id, demo_users["s1"].id)
    assert added is True
    assert count == 1
    assert has_voted(db, c.id, demo_users["s1"].id)


def test_student_cannot_vote_twice(db, demo_users):
    c = _make_complaint(db, demo_users)
    toggle_vote(db, c.id, demo_users["s1"].id)
    # Second attempt should remove the vote (toggle), not add a duplicate
    added, msg, count = toggle_vote(db, c.id, demo_users["s1"].id)
    assert added is False   # vote was removed
    assert count == 0


def test_db_enforces_vote_uniqueness(db, demo_users):
    """Directly test that the DB unique constraint prevents duplicate vote rows."""
    import uuid
    from sqlalchemy.exc import IntegrityError
    c = _make_complaint(db, demo_users)
    v1 = ComplaintVote(complaint_id=c.id, student_id=demo_users["s1"].id)
    db.add(v1)
    db.flush()
    v2 = ComplaintVote(complaint_id=c.id, student_id=demo_users["s1"].id)
    db.add(v2)
    with pytest.raises(IntegrityError):
        db.flush()
    db.rollback()


def test_two_students_can_vote_independently(db, demo_users):
    c = _make_complaint(db, demo_users)
    toggle_vote(db, c.id, demo_users["s1"].id)
    toggle_vote(db, c.id, demo_users["s2"].id)
    db.refresh(c)
    assert c.vote_count == 2


def test_remove_vote_decrements_count(db, demo_users):
    c = _make_complaint(db, demo_users)
    toggle_vote(db, c.id, demo_users["s1"].id)
    toggle_vote(db, c.id, demo_users["s2"].id)
    toggle_vote(db, c.id, demo_users["s1"].id)  # remove s1's vote
    db.refresh(c)
    assert c.vote_count == 1
    assert not has_voted(db, c.id, demo_users["s1"].id)
    assert has_voted(db, c.id, demo_users["s2"].id)


def test_vote_count_never_goes_negative(db, demo_users):
    c = _make_complaint(db, demo_users)
    # Try removing a vote that doesn't exist
    added, msg, count = toggle_vote(db, c.id, demo_users["s1"].id)
    toggle_vote(db, c.id, demo_users["s1"].id)  # remove
    db.refresh(c)
    assert c.vote_count >= 0
