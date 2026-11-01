"""
Database models for Team R — Hostel Grievance Platform.
SQLAlchemy ORM models with PostgreSQL-compatible schema.
SQLite is used by default; switch DATABASE_URL to use PostgreSQL/Supabase.
"""

from __future__ import annotations

import enum
import uuid
from datetime import datetime, timezone

from sqlalchemy import (
    Boolean, Column, DateTime, Enum, ForeignKey, Index,
    Integer, String, Text, UniqueConstraint, event, text,
)
from sqlalchemy.orm import DeclarativeBase, relationship


def _utcnow() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)  # naive UTC for SQLite compat


class Base(DeclarativeBase):
    pass


# ─── Enums ──────────────────────────────────────────────────────────────────

class UserRole(str, enum.Enum):
    student = "student"
    caretaker = "caretaker"
    admin = "admin"


class ComplaintStatus(str, enum.Enum):
    submitted = "Submitted"
    acknowledged = "Acknowledged"
    assigned = "Assigned"
    in_progress = "In Progress"
    resolved = "Resolved"
    reopened = "Reopened"
    closed = "Closed"


class Priority(str, enum.Enum):
    low = "Low"
    medium = "Medium"
    high = "High"
    urgent = "Urgent"


class Category(str, enum.Enum):
    water_supply = "Water Supply"
    plumbing = "Plumbing"
    electrical = "Electrical"
    washroom = "Washroom & Hygiene"
    cleaning = "Cleaning & Waste"
    furniture = "Furniture & Fixtures"
    internet = "Internet & Wi-Fi"
    safety = "Safety & Security"
    other = "Other"


# ─── Tables ─────────────────────────────────────────────────────────────────

class Profile(Base):
    """User profiles — one row per registered user."""
    __tablename__ = "profiles"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    email = Column(String(255), unique=True, nullable=False)
    display_name = Column(String(100), nullable=False)
    password_hash = Column(String(255), nullable=False)
    role = Column(Enum(UserRole), nullable=False, default=UserRole.student)
    hostel = Column(String(100))          # optional default hostel for students
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=_utcnow, nullable=False)
    updated_at = Column(DateTime, default=_utcnow, onupdate=_utcnow, nullable=False)

    complaints = relationship("Complaint", back_populates="submitter",
                              foreign_keys="Complaint.submitter_id")
    votes = relationship("ComplaintVote", back_populates="student")
    comments = relationship("ComplaintComment", back_populates="author",
                            foreign_keys="ComplaintComment.author_id")
    notifications = relationship("Notification", back_populates="recipient")

    __table_args__ = (Index("ix_profiles_email", "email"),)


class Complaint(Base):
    """Core complaint record."""
    __tablename__ = "complaints"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    complaint_number = Column(String(20), unique=True, nullable=False)  # e.g. TR-2026-0001
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=False)
    category = Column(Enum(Category), nullable=False)
    hostel = Column(String(100), nullable=False)
    block = Column(String(50))
    floor = Column(String(20))
    location_detail = Column(String(200))
    status = Column(Enum(ComplaintStatus), nullable=False, default=ComplaintStatus.submitted)
    priority = Column(Enum(Priority), nullable=False, default=Priority.medium)
    submitter_id = Column(String(36), ForeignKey("profiles.id"), nullable=False)
    assigned_caretaker_id = Column(String(36), ForeignKey("profiles.id"), nullable=True)
    is_public = Column(Boolean, default=True, nullable=False)
    is_demo = Column(Boolean, default=False, nullable=False)
    is_anonymous = Column(Boolean, default=False, nullable=False)
    merged_into_id = Column(String(36), ForeignKey("complaints.id"), nullable=True)
    vote_count = Column(Integer, default=0, nullable=False)  # denormalized cache
    created_at = Column(DateTime, default=_utcnow, nullable=False)
    updated_at = Column(DateTime, default=_utcnow, onupdate=_utcnow, nullable=False)
    resolved_at = Column(DateTime, nullable=True)
    student_confirmed_resolved = Column(Boolean, default=False, nullable=False)

    submitter = relationship("Profile", back_populates="complaints",
                             foreign_keys=[submitter_id])
    assigned_caretaker = relationship("Profile", foreign_keys=[assigned_caretaker_id])
    votes = relationship("ComplaintVote", back_populates="complaint",
                         cascade="all, delete-orphan")
    comments = relationship("ComplaintComment", back_populates="complaint",
                            order_by="ComplaintComment.created_at",
                            cascade="all, delete-orphan")
    status_history = relationship("ComplaintStatusHistory", back_populates="complaint",
                                  order_by="ComplaintStatusHistory.created_at",
                                  cascade="all, delete-orphan")
    acknowledgements = relationship("CaretakerAcknowledgement", back_populates="complaint",
                                    cascade="all, delete-orphan")
    attachments = relationship("ComplaintAttachment", back_populates="complaint",
                               cascade="all, delete-orphan")
    assignments = relationship("ComplaintAssignment", back_populates="complaint",
                               cascade="all, delete-orphan")
    merged_complaint = relationship("Complaint", remote_side=[id])

    __table_args__ = (
        Index("ix_complaints_status", "status"),
        Index("ix_complaints_category", "category"),
        Index("ix_complaints_hostel", "hostel"),
        Index("ix_complaints_created_at", "created_at"),
        Index("ix_complaints_vote_count", "vote_count"),
    )


class ComplaintVote(Base):
    """One vote per student per complaint — enforced by unique constraint."""
    __tablename__ = "complaint_votes"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    complaint_id = Column(String(36), ForeignKey("complaints.id", ondelete="CASCADE"),
                          nullable=False)
    student_id = Column(String(36), ForeignKey("profiles.id", ondelete="CASCADE"),
                        nullable=False)
    created_at = Column(DateTime, default=_utcnow, nullable=False)

    complaint = relationship("Complaint", back_populates="votes")
    student = relationship("Profile", back_populates="votes")

    __table_args__ = (
        UniqueConstraint("complaint_id", "student_id", name="uq_one_vote_per_student"),
        Index("ix_votes_complaint_id", "complaint_id"),
    )


class ComplaintComment(Base):
    """Comments and official progress updates on a complaint."""
    __tablename__ = "complaint_comments"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    complaint_id = Column(String(36), ForeignKey("complaints.id", ondelete="CASCADE"),
                          nullable=False)
    author_id = Column(String(36), ForeignKey("profiles.id"), nullable=False)
    content = Column(Text, nullable=False)
    is_official = Column(Boolean, default=False, nullable=False)  # caretaker/admin update
    is_moderated = Column(Boolean, default=False, nullable=False)  # hidden by moderator
    moderated_by_id = Column(String(36), ForeignKey("profiles.id"), nullable=True)
    moderated_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=_utcnow, nullable=False)

    complaint = relationship("Complaint", back_populates="comments")
    author = relationship("Profile", back_populates="comments", foreign_keys=[author_id])
    moderator = relationship("Profile", foreign_keys=[moderated_by_id])

    __table_args__ = (Index("ix_comments_complaint_id", "complaint_id"),)


class ComplaintStatusHistory(Base):
    """Immutable log of every status transition."""
    __tablename__ = "complaint_status_history"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    complaint_id = Column(String(36), ForeignKey("complaints.id", ondelete="CASCADE"),
                          nullable=False)
    old_status = Column(String(50), nullable=True)   # None for initial submission
    new_status = Column(String(50), nullable=False)
    actor_id = Column(String(36), ForeignKey("profiles.id"), nullable=False)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=_utcnow, nullable=False)

    complaint = relationship("Complaint", back_populates="status_history")
    actor = relationship("Profile", foreign_keys=[actor_id])

    __table_args__ = (Index("ix_status_history_complaint_id", "complaint_id"),)


class CaretakerAcknowledgement(Base):
    """Tracks when a caretaker first sees and explicitly acknowledges a complaint.
    Seen and Acknowledged are separate events.
    """
    __tablename__ = "caretaker_acknowledgements"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    complaint_id = Column(String(36), ForeignKey("complaints.id", ondelete="CASCADE"),
                          nullable=False)
    caretaker_id = Column(String(36), ForeignKey("profiles.id"), nullable=False)
    first_seen_at = Column(DateTime, nullable=True)      # set on first explicit mark-seen
    last_seen_at = Column(DateTime, nullable=True)       # updated on subsequent views
    acknowledged_at = Column(DateTime, nullable=True)    # set on explicit acknowledgement
    work_notes = Column(Text, nullable=True)
    estimated_completion = Column(DateTime, nullable=True)

    complaint = relationship("Complaint", back_populates="acknowledgements")
    caretaker = relationship("Profile", foreign_keys=[caretaker_id])

    __table_args__ = (
        UniqueConstraint("complaint_id", "caretaker_id",
                         name="uq_one_ack_per_caretaker"),
        Index("ix_ack_complaint_id", "complaint_id"),
    )


class ComplaintAttachment(Base):
    """File attachments — photos for complaints and resolution evidence."""
    __tablename__ = "complaint_attachments"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    complaint_id = Column(String(36), ForeignKey("complaints.id", ondelete="CASCADE"),
                          nullable=False)
    uploader_id = Column(String(36), ForeignKey("profiles.id"), nullable=False)
    filename = Column(String(255), nullable=False)
    storage_path = Column(String(500), nullable=False)   # local path or Supabase key
    attachment_type = Column(String(50), default="complaint_photo")  # complaint_photo | resolution_photo
    mime_type = Column(String(100))
    size_bytes = Column(Integer)
    created_at = Column(DateTime, default=_utcnow, nullable=False)

    complaint = relationship("Complaint", back_populates="attachments")
    uploader = relationship("Profile", foreign_keys=[uploader_id])

    __table_args__ = (Index("ix_attachments_complaint_id", "complaint_id"),)


class ComplaintAssignment(Base):
    """Assignment of a complaint to a caretaker or department."""
    __tablename__ = "complaint_assignments"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    complaint_id = Column(String(36), ForeignKey("complaints.id", ondelete="CASCADE"),
                          nullable=False)
    assigned_to_id = Column(String(36), ForeignKey("profiles.id"), nullable=True)
    department = Column(String(100), nullable=True)
    assigned_by_id = Column(String(36), ForeignKey("profiles.id"), nullable=False)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=_utcnow, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)

    complaint = relationship("Complaint", back_populates="assignments")
    assigned_to = relationship("Profile", foreign_keys=[assigned_to_id])
    assigned_by = relationship("Profile", foreign_keys=[assigned_by_id])

    __table_args__ = (Index("ix_assignments_complaint_id", "complaint_id"),)


class Notification(Base):
    """In-app notifications for users."""
    __tablename__ = "notifications"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    recipient_id = Column(String(36), ForeignKey("profiles.id", ondelete="CASCADE"),
                          nullable=False)
    event_type = Column(String(50), nullable=False)   # submitted, acknowledged, assigned, etc.
    complaint_id = Column(String(36), ForeignKey("complaints.id", ondelete="CASCADE"),
                          nullable=True)
    message = Column(String(500), nullable=False)
    is_read = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=_utcnow, nullable=False)

    recipient = relationship("Profile", back_populates="notifications")
    complaint = relationship("Complaint", foreign_keys=[complaint_id])

    __table_args__ = (
        Index("ix_notifications_recipient_id", "recipient_id"),
        Index("ix_notifications_is_read", "is_read"),
    )


class AuditLog(Base):
    """Audit trail for privileged actions."""
    __tablename__ = "audit_logs"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    actor_id = Column(String(36), ForeignKey("profiles.id"), nullable=True)
    action = Column(String(100), nullable=False)   # e.g. "mark_seen", "assign", "merge"
    entity_type = Column(String(50), nullable=False)   # "complaint", "user", etc.
    entity_id = Column(String(36), nullable=True)
    metadata_json = Column(Text, nullable=True)        # JSON string of non-sensitive context
    ip_address = Column(String(45), nullable=True)
    created_at = Column(DateTime, default=_utcnow, nullable=False)

    actor = relationship("Profile", foreign_keys=[actor_id])

    __table_args__ = (
        Index("ix_audit_logs_entity", "entity_type", "entity_id"),
        Index("ix_audit_logs_created_at", "created_at"),
    )


class ComplaintMerge(Base):
    """Records when a duplicate complaint is merged into a surviving complaint."""
    __tablename__ = "complaint_merges"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    original_complaint_id = Column(String(36), ForeignKey("complaints.id"), nullable=False)
    surviving_complaint_id = Column(String(36), ForeignKey("complaints.id"), nullable=False)
    merged_by_id = Column(String(36), ForeignKey("profiles.id"), nullable=False)
    reason = Column(Text, nullable=True)
    created_at = Column(DateTime, default=_utcnow, nullable=False)

    merged_by = relationship("Profile", foreign_keys=[merged_by_id])

    __table_args__ = (Index("ix_merges_original", "original_complaint_id"),)
