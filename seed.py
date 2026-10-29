"""
Seed script — creates demo accounts and fictional complaint data.

IMPORTANT: All data here is fictional and for demonstration only.
           These are NOT real IIT Patna students, staff, or complaints.

Usage:
    python seed.py           # seed (skip if already seeded)
    python seed.py --reset   # drop all data and re-seed
"""

from __future__ import annotations

import argparse
import sys
import os
from datetime import datetime, timedelta
import uuid

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault("DATABASE_URL", "sqlite:///./hostel_complaints.db")

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    try:
        from src.utils.env_loader import load_env
        load_env()
    except Exception:
        pass

from src.db.database import init_db, get_db, engine
from src.db.models import (
    Base, Profile, Complaint, ComplaintStatus, ComplaintVote,
    ComplaintStatusHistory, CaretakerAcknowledgement, ComplaintComment,
    ComplaintAssignment, AuditLog, UserRole, Category, Priority,
)
from src.utils.auth import hash_password

DEMO_LABEL = "[DEMO] "


def reset_db():
    print("⚠️  Dropping all tables…")
    Base.metadata.drop_all(bind=engine)
    print("✅ Tables dropped.")
    init_db()
    print("✅ Tables re-created.")


def seed():
    init_db()
    db = get_db()
    try:
        # Skip if already seeded
        if db.query(Profile).filter(Profile.email == "admin@demo.teamr").first():
            print("ℹ️  Demo data already present. Use --reset to re-seed.")
            return

        print("🌱 Seeding demo data…")

        # ─── Demo users ──────────────────────────────────────────────────────
        now = datetime.utcnow()

        admin = Profile(
            id=str(uuid.uuid4()),
            email="admin@demo.teamr",
            display_name="Demo Admin",
            password_hash=hash_password("demo1234"),
            role=UserRole.admin,
            is_active=True,
            created_at=now - timedelta(days=30),
            updated_at=now - timedelta(days=30),
        )
        caretaker = Profile(
            id=str(uuid.uuid4()),
            email="caretaker@demo.teamr",
            display_name="Demo Caretaker (Ramesh)",
            password_hash=hash_password("demo1234"),
            role=UserRole.caretaker,
            is_active=True,
            created_at=now - timedelta(days=30),
            updated_at=now - timedelta(days=30),
        )
        student1 = Profile(
            id=str(uuid.uuid4()),
            email="student1@demo.teamr",
            display_name="Demo Student 1",
            password_hash=hash_password("demo1234"),
            role=UserRole.student,
            hostel="Ganga",
            is_active=True,
            created_at=now - timedelta(days=20),
            updated_at=now - timedelta(days=20),
        )
        student2 = Profile(
            id=str(uuid.uuid4()),
            email="student2@demo.teamr",
            display_name="Demo Student 2",
            password_hash=hash_password("demo1234"),
            role=UserRole.student,
            hostel="Ganga",
            is_active=True,
            created_at=now - timedelta(days=18),
            updated_at=now - timedelta(days=18),
        )
        student3 = Profile(
            id=str(uuid.uuid4()),
            email="student3@demo.teamr",
            display_name="Demo Student 3",
            password_hash=hash_password("demo1234"),
            role=UserRole.student,
            hostel="Barak",
            is_active=True,
            created_at=now - timedelta(days=10),
            updated_at=now - timedelta(days=10),
        )
        for u in [admin, caretaker, student1, student2, student3]:
            db.add(u)
        db.flush()

        # ─── Complaints ──────────────────────────────────────────────────────

        def make_complaint(number, title, category, hostel, block, floor,
                           location, description, submitter_id, status,
                           priority, days_ago, vote_count=0):
            created = now - timedelta(days=days_ago)
            c = Complaint(
                id=str(uuid.uuid4()),
                complaint_number=number,
                title=title,
                description=description,
                category=category,
                hostel=hostel,
                block=block,
                floor=floor,
                location_detail=location,
                status=status,
                priority=priority,
                submitter_id=submitter_id,
                assigned_caretaker_id=None,
                is_public=True,
                is_demo=True,
                vote_count=vote_count,
                created_at=created,
                updated_at=created,
            )
            db.add(c)
            db.flush()
            # Initial status history
            h = ComplaintStatusHistory(
                complaint_id=c.id,
                old_status=None,
                new_status=ComplaintStatus.submitted.value,
                actor_id=submitter_id,
                notes=DEMO_LABEL + "Complaint submitted.",
                created_at=created,
            )
            db.add(h)
            return c

        c1 = make_complaint(
            "TR-2026-0001",
            "Water cooler not working — Block B common area",
            Category.water_supply, "Ganga", "Block B", "Ground",
            "Near common room entrance",
            DEMO_LABEL + "The water cooler in Block B common area has not been functioning "
            "for the past 5 days. Water is warm and the cooling unit makes a loud noise. "
            "This is a shared resource used by 40+ students.",
            student1.id, ComplaintStatus.resolved, Priority.high, 10, vote_count=12,
        )

        c2 = make_complaint(
            "TR-2026-0002",
            "No water supply in 2nd floor washrooms — Block A",
            Category.washroom, "Ganga", "Block A", "2nd",
            "Washrooms 201–204",
            DEMO_LABEL + "Water supply has been completely absent in all 2nd floor washrooms "
            "since yesterday morning. Students are unable to use the facilities. "
            "This affects approximately 30 students.",
            student1.id, ComplaintStatus.in_progress, Priority.urgent, 5, vote_count=24,
        )

        c3 = make_complaint(
            "TR-2026-0003",
            "Broken door hinge — Room 312",
            Category.furniture, "Ganga", "Block C", "3rd",
            "Room 312",
            DEMO_LABEL + "The door hinge in room 312 is completely broken. The door cannot "
            "be properly closed or locked, creating a security and privacy concern.",
            student2.id, ComplaintStatus.acknowledged, Priority.medium, 3, vote_count=5,
        )

        c4 = make_complaint(
            "TR-2026-0004",
            "Wi-Fi disconnecting repeatedly in Block D",
            Category.internet, "Barak", "Block D", "All",
            "Block D, all floors",
            DEMO_LABEL + "Wi-Fi has been dropping every 10–15 minutes throughout Block D "
            "for the past week. Reconnecting temporarily fixes it but it drops again. "
            "This is severely affecting study and assignment submissions.",
            student3.id, ComplaintStatus.submitted, Priority.high, 1, vote_count=18,
        )

        c5 = make_complaint(
            "TR-2026-0005",
            "Overflowing dustbins near mess entrance",
            Category.cleaning, "Ganga", "Main Block", "Ground",
            "Near mess entrance on east side",
            DEMO_LABEL + "The dustbins near the mess entrance have been overflowing for "
            "3 days. Garbage is spilling onto the walkway and attracting insects. "
            "This is a hygiene hazard.",
            student2.id, ComplaintStatus.assigned, Priority.high, 2, vote_count=9,
        )

        c6 = make_complaint(
            "TR-2026-0006",
            "Flickering lights in corridor — Block A 3rd floor",
            Category.electrical, "Ganga", "Block A", "3rd",
            "Full corridor, 3rd floor",
            DEMO_LABEL + "The corridor lights on Block A 3rd floor have been flickering "
            "intermittently. At night the corridor is sometimes pitch dark, which is a "
            "safety concern.",
            student1.id, ComplaintStatus.submitted, Priority.medium, 2, vote_count=7,
        )

        db.flush()

        # ─── Votes ────────────────────────────────────────────────────────────
        vote_data = [
            (c1.id, student2.id), (c1.id, student3.id),
            (c2.id, student2.id), (c2.id, student3.id),
            (c3.id, student1.id),
            (c4.id, student1.id), (c4.id, student2.id),
            (c5.id, student1.id), (c5.id, student3.id),
            (c6.id, student2.id),
        ]
        for cid, sid in vote_data:
            v = ComplaintVote(complaint_id=cid, student_id=sid,
                              created_at=now - timedelta(days=1))
            db.add(v)
        db.flush()

        # ─── Caretaker acknowledgements (TR-2026-0001, 0002, 0003) ───────────

        # c1: seen + acknowledged + resolved
        seen_t = now - timedelta(days=9, hours=2)
        ack1 = CaretakerAcknowledgement(
            complaint_id=c1.id,
            caretaker_id=caretaker.id,
            first_seen_at=seen_t,
            last_seen_at=seen_t,
            acknowledged_at=seen_t + timedelta(hours=1),
            work_notes=DEMO_LABEL + "Checked cooler. Compressor unit needs replacement. "
                        "Ordering part.",
            estimated_completion=now - timedelta(days=6),
        )
        db.add(ack1)

        # c2: seen + acknowledged
        seen_t2 = now - timedelta(days=4, hours=3)
        ack2 = CaretakerAcknowledgement(
            complaint_id=c2.id,
            caretaker_id=caretaker.id,
            first_seen_at=seen_t2,
            last_seen_at=seen_t2,
            acknowledged_at=seen_t2 + timedelta(minutes=40),
            work_notes=DEMO_LABEL + "Main valve closed due to a pipe repair. "
                        "Work is in progress. Expected resolution: tomorrow.",
        )
        db.add(ack2)

        # c3: seen only (not acknowledged yet)
        seen_t3 = now - timedelta(days=2, hours=1)
        ack3 = CaretakerAcknowledgement(
            complaint_id=c3.id,
            caretaker_id=caretaker.id,
            first_seen_at=seen_t3,
            last_seen_at=seen_t3,
            acknowledged_at=None,
        )
        db.add(ack3)
        db.flush()

        # ─── Assignments ──────────────────────────────────────────────────────
        for c, days in [(c1, 9), (c2, 4), (c3, 2), (c5, 2)]:
            c.assigned_caretaker_id = caretaker.id
            a = ComplaintAssignment(
                complaint_id=c.id,
                assigned_to_id=caretaker.id,
                department="Maintenance Wing",
                assigned_by_id=admin.id,
                notes=DEMO_LABEL + "Assigned for action.",
                created_at=now - timedelta(days=days),
                is_active=True,
            )
            db.add(a)
        db.flush()

        # ─── Status histories (extended) ──────────────────────────────────────
        # c1: full journey
        extra_history_c1 = [
            (now - timedelta(days=9), ComplaintStatus.submitted.value,
             ComplaintStatus.acknowledged.value, caretaker.id,
             DEMO_LABEL + "Acknowledged by caretaker."),
            (now - timedelta(days=9), ComplaintStatus.acknowledged.value,
             ComplaintStatus.assigned.value, admin.id,
             DEMO_LABEL + "Assigned to maintenance."),
            (now - timedelta(days=8), ComplaintStatus.assigned.value,
             ComplaintStatus.in_progress.value, caretaker.id,
             DEMO_LABEL + "Replacement part ordered. Work started."),
            (now - timedelta(days=7), ComplaintStatus.in_progress.value,
             ComplaintStatus.resolved.value, caretaker.id,
             DEMO_LABEL + "Compressor replaced. Cooler functioning normally."),
        ]
        for ts, old, new, actor, note in extra_history_c1:
            h = ComplaintStatusHistory(
                complaint_id=c1.id, old_status=old, new_status=new,
                actor_id=actor, notes=note, created_at=ts)
            db.add(h)
        c1.status = ComplaintStatus.resolved
        c1.resolved_at = now - timedelta(days=7)
        c1.updated_at = now - timedelta(days=7)

        # c2: in-progress history
        extra_c2 = [
            (now - timedelta(days=4), ComplaintStatus.submitted.value,
             ComplaintStatus.acknowledged.value, caretaker.id,
             DEMO_LABEL + "Caretaker acknowledged."),
            (now - timedelta(days=4), ComplaintStatus.acknowledged.value,
             ComplaintStatus.assigned.value, admin.id,
             DEMO_LABEL + "Assigned to plumbing team."),
            (now - timedelta(days=3), ComplaintStatus.assigned.value,
             ComplaintStatus.in_progress.value, caretaker.id,
             DEMO_LABEL + "Pipe repair underway."),
        ]
        for ts, old, new, actor, note in extra_c2:
            h = ComplaintStatusHistory(
                complaint_id=c2.id, old_status=old, new_status=new,
                actor_id=actor, notes=note, created_at=ts)
            db.add(h)
        c2.status = ComplaintStatus.in_progress
        c2.updated_at = now - timedelta(days=3)

        # c3: acknowledged only
        h3 = ComplaintStatusHistory(
            complaint_id=c3.id,
            old_status=ComplaintStatus.submitted.value,
            new_status=ComplaintStatus.acknowledged.value,
            actor_id=caretaker.id,
            notes=DEMO_LABEL + "Will schedule door repair this week.",
            created_at=now - timedelta(days=2),
        )
        db.add(h3)
        c3.status = ComplaintStatus.acknowledged

        # c5: assigned
        h5a = ComplaintStatusHistory(
            complaint_id=c5.id,
            old_status=ComplaintStatus.submitted.value,
            new_status=ComplaintStatus.assigned.value,
            actor_id=admin.id,
            notes=DEMO_LABEL + "Assigned to cleaning team.",
            created_at=now - timedelta(days=1),
        )
        db.add(h5a)
        c5.status = ComplaintStatus.assigned

        db.flush()

        # ─── Comments ─────────────────────────────────────────────────────────
        comments_data = [
            (c2.id, student2.id, False,
             DEMO_LABEL + "This is really urgent! We can't use the washrooms at all."),
            (c2.id, caretaker.id, True,
             DEMO_LABEL + "The main pipe is being repaired. Water supply will be restored by tomorrow evening."),
            (c1.id, student1.id, False,
             DEMO_LABEL + "Thank you for fixing this so quickly!"),
            (c4.id, student1.id, False,
             DEMO_LABEL + "Same issue here — drops every 15 minutes during evening hours."),
            (c4.id, student3.id, False,
             DEMO_LABEL + "Exam week coming up and Wi-Fi keeps failing. Please prioritize!"),
        ]
        for cid, aid, official, content in comments_data:
            cm = ComplaintComment(
                complaint_id=cid, author_id=aid, content=content,
                is_official=official,
                created_at=now - timedelta(hours=12),
            )
            db.add(cm)

        db.commit()
        print("✅ Seed data created successfully!")
        print()
        print("─── Demo Accounts ───────────────────────────────────────")
        print("  Admin:      admin@demo.teamr      / demo1234")
        print("  Caretaker:  caretaker@demo.teamr  / demo1234")
        print("  Student 1:  student1@demo.teamr   / demo1234")
        print("  Student 2:  student2@demo.teamr   / demo1234")
        print("  Student 3:  student3@demo.teamr   / demo1234")
        print("─────────────────────────────────────────────────────────")
        print("⚠️  All users and complaints are fictional demo data.")

    except Exception as e:
        db.rollback()
        print(f"❌ Seed failed: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Seed Team R demo data")
    parser.add_argument("--reset", action="store_true",
                        help="Drop and recreate all tables before seeding")
    args = parser.parse_args()

    if args.reset:
        reset_db()
    seed()
