"""
Tests for complaint merging — vote transfer, history preservation.
"""

import pytest
from src.utils.complaints import (
    create_complaint, toggle_vote, merge_complaints,
)
from src.db.models import ComplaintVote, ComplaintStatus


def _make(db, users, title):
    _, _, c = create_complaint(
        db, title=title, description="desc", category="Other",
        hostel="Ganga", block="", floor="", location_detail="",
        submitter_id=users["s1"].id)
    return c


def test_merge_transfers_votes_no_double_count(db, demo_users):
    orig = _make(db, demo_users, "Duplicate complaint")
    surv = _make(db, demo_users, "Surviving complaint")

    # Both students vote on original
    toggle_vote(db, orig.id, demo_users["s1"].id)
    toggle_vote(db, orig.id, demo_users["s2"].id)
    # s1 also votes on surviving
    toggle_vote(db, surv.id, demo_users["s1"].id)

    db.refresh(orig); db.refresh(surv)
    assert orig.vote_count == 2
    assert surv.vote_count == 1

    ok, msg = merge_complaints(db, orig.id, surv.id, demo_users["admin"].id,
                               "Duplicate issue")
    assert ok is True
    db.refresh(surv)

    # s1 already voted on surviving → not counted again. s2 transferred.
    assert surv.vote_count == 2

    # No duplicate vote rows for surviving complaint
    votes = db.query(ComplaintVote).filter_by(complaint_id=surv.id).all()
    student_ids = [v.student_id for v in votes]
    assert len(student_ids) == len(set(student_ids))  # no duplicates


def test_merge_closes_original(db, demo_users):
    orig = _make(db, demo_users, "Orig")
    surv = _make(db, demo_users, "Surv")
    merge_complaints(db, orig.id, surv.id, demo_users["admin"].id)
    db.refresh(orig)
    assert orig.status == ComplaintStatus.closed
    assert orig.merged_into_id == surv.id
    assert orig.is_public is False


def test_cannot_merge_complaint_with_itself(db, demo_users):
    c = _make(db, demo_users, "Self merge")
    ok, msg = merge_complaints(db, c.id, c.id, demo_users["admin"].id)
    assert ok is False


def test_merge_records_in_complaint_merges_table(db, demo_users):
    from src.db.models import ComplaintMerge
    orig = _make(db, demo_users, "Orig2")
    surv = _make(db, demo_users, "Surv2")
    merge_complaints(db, orig.id, surv.id, demo_users["admin"].id, "test reason")
    records = db.query(ComplaintMerge).filter_by(
        original_complaint_id=orig.id).all()
    assert len(records) == 1
    assert records[0].surviving_complaint_id == surv.id
