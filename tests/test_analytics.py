"""
Tests for analytics calculations — correct metric computation.
"""

import pytest
from datetime import datetime, timedelta
from src.utils.complaints import create_complaint, get_analytics_data, mark_seen, acknowledge_complaint, update_status
from src.db.models import UserRole, ComplaintStatus


def test_analytics_empty_db(db, demo_users):
    data = get_analytics_data(db)
    assert data["total"] == 0
    assert data["avg_seen_hours"] is None
    assert data["avg_ack_hours"] is None
    assert data["avg_resolution_hours"] is None


def test_analytics_counts_correctly(db, demo_users):
    for i in range(3):
        create_complaint(db, title=f"C{i}", description="d", category="Other",
                         hostel="Ganga", block="", floor="", location_detail="",
                         submitter_id=demo_users["s1"].id)
    data = get_analytics_data(db)
    assert data["total"] == 3


def test_unresolved_excluded_from_resolution_time(db, demo_users):
    """Unresolved complaints must not appear in avg resolution time."""
    _, _, c = create_complaint(
        db, title="Unresolved", description="d", category="Other",
        hostel="Ganga", block="", floor="", location_detail="",
        submitter_id=demo_users["s1"].id)
    # Do not resolve — complaint stays Submitted
    data = get_analytics_data(db)
    assert data["avg_resolution_hours"] is None  # no resolved complaints
