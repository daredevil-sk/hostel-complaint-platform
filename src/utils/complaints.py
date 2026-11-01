"""
Complaint CRUD operations and business logic.
All privileged operations verify the caller's role before proceeding.
"""

from __future__ import annotations

import json
import os
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from sqlalchemy.orm import Session

from src.db.models import (
    AuditLog, CaretakerAcknowledgement, Complaint, ComplaintAssignment,
    ComplaintAttachment, ComplaintComment, ComplaintMerge, ComplaintStatus,
    ComplaintStatusHistory, ComplaintVote, Notification, Priority, Profile,
    UserRole,
)


def _utcnow() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


# ─── Complaint ID generator ──────────────────────────────────────────────────

def generate_complaint_number(db: Session) -> str:
    """Generate a human-readable complaint ID like TR-2026-0001."""
    year = datetime.now().year
    prefix = f"TR-{year}-"
    last: Complaint | None = (
        db.query(Complaint)
        .filter(Complaint.complaint_number.like(f"{prefix}%"))
        .order_by(Complaint.complaint_number.desc())
        .first()
    )
    if last:
        try:
            seq = int(last.complaint_number.split("-")[-1]) + 1
        except ValueError:
            seq = 1
    else:
        seq = 1
    return f"{prefix}{seq:04d}"


# ─── Create complaint ────────────────────────────────────────────────────────

def create_complaint(
    db: Session,
    *,
    title: str,
    description: str,
    category: str,
    hostel: str,
    block: str,
    floor: str,
    location_detail: str,
    submitter_id: str,
    priority: str = "Medium",
    is_public: bool = True,
    is_demo: bool = False,
    is_anonymous: bool = False,
) -> tuple[bool, str, Optional[Complaint]]:
    """
    Create a new complaint. Returns (success, message, complaint_or_None).
    Validates required fields and generates a unique complaint number.
    """
    if not title.strip():
        return False, "Title is required.", None
    if not description.strip():
        return False, "Description is required.", None
    if not hostel.strip():
        return False, "Hostel is required.", None

    try:
        complaint_number = generate_complaint_number(db)
        complaint = Complaint(
            id=str(uuid.uuid4()),
            complaint_number=complaint_number,
            title=title.strip(),
            description=description.strip(),
            category=category,
            hostel=hostel.strip(),
            block=block.strip() if block else None,
            floor=floor.strip() if floor else None,
            location_detail=location_detail.strip() if location_detail else None,
            submitter_id=submitter_id,
            status=ComplaintStatus.submitted,
            priority=priority,
            is_public=is_public,
            is_demo=is_demo,
            is_anonymous=is_anonymous,
            vote_count=0,
        )
        db.add(complaint)
        db.flush()  # get the id without committing

        # Record initial status history
        history = ComplaintStatusHistory(
            complaint_id=complaint.id,
            old_status=None,
            new_status=ComplaintStatus.submitted.value,
            actor_id=submitter_id,
            notes="Complaint submitted.",
        )
        db.add(history)

        # Audit log
        _audit(db, actor_id=submitter_id, action="create_complaint",
               entity_type="complaint", entity_id=complaint.id,
               metadata={"complaint_number": complaint_number})

        db.commit()
        db.refresh(complaint)
        return True, complaint_number, complaint
    except Exception as e:
        db.rollback()
        return False, str(e), None


# ─── Query complaints ────────────────────────────────────────────────────────

def get_complaint_by_number(db: Session, complaint_number: str) -> Optional[Complaint]:
    return db.query(Complaint).filter(
        Complaint.complaint_number == complaint_number).first()


def get_complaint_by_id(db: Session, complaint_id: str) -> Optional[Complaint]:
    return db.query(Complaint).filter(Complaint.id == complaint_id).first()


def delete_complaint(db: Session, complaint_id: str, requester_id: str,
                     requester_role: UserRole) -> tuple[bool, str]:
    """
    Delete a complaint. Students may only delete their own complaints that are
    still in 'Submitted' status. Admins may delete any complaint.
    """
    complaint = get_complaint_by_id(db, complaint_id)
    if not complaint:
        return False, "Complaint not found."

    if requester_role == UserRole.student:
        if complaint.submitter_id != requester_id:
            return False, "You can only delete your own complaints."
        if complaint.status != ComplaintStatus.submitted:
            return False, "You can only delete complaints that are still in 'Submitted' status (not yet acknowledged by a caretaker)."

    try:
        db.delete(complaint)
        _audit(db, actor_id=requester_id, action="delete_complaint",
               entity_type="complaint", entity_id=complaint_id,
               metadata={"complaint_number": complaint.complaint_number})
        db.commit()
        return True, f"Complaint {complaint.complaint_number} deleted."
    except Exception as e:
        db.rollback()
        return False, str(e)


def list_complaints(
    db: Session,
    *,
    search: str = "",
    category: str = "",
    hostel: str = "",
    block: str = "",
    status: str = "",
    priority: str = "",
    sort_by: str = "newest",
    page: int = 1,
    page_size: int = 15,
    include_private: bool = False,
    submitter_id: str | None = None,
    assigned_caretaker_id: str | None = None,
    exclude_merged: bool = True,
) -> tuple[list[Complaint], int]:
    """
    Return paginated list of complaints with total count.
    """
    q = db.query(Complaint)

    if not include_private:
        q = q.filter(Complaint.is_public == True)
    if exclude_merged:
        q = q.filter(Complaint.merged_into_id == None)
    if search:
        like = f"%{search}%"
        q = q.filter(
            Complaint.title.ilike(like) |
            Complaint.description.ilike(like) |
            Complaint.complaint_number.ilike(like)
        )
    if category:
        q = q.filter(Complaint.category == category)
    if hostel:
        q = q.filter(Complaint.hostel == hostel)
    if block:
        q = q.filter(Complaint.block == block)
    if status:
        q = q.filter(Complaint.status == status)
    if priority:
        q = q.filter(Complaint.priority == priority)
    if submitter_id:
        q = q.filter(Complaint.submitter_id == submitter_id)
    if assigned_caretaker_id:
        q = q.filter(Complaint.assigned_caretaker_id == assigned_caretaker_id)

    total = q.count()

    if sort_by == "newest":
        q = q.order_by(Complaint.created_at.desc())
    elif sort_by == "oldest":
        q = q.order_by(Complaint.created_at.asc())
    elif sort_by == "most_supported":
        q = q.order_by(Complaint.vote_count.desc(), Complaint.created_at.desc())
    elif sort_by == "priority":
        from sqlalchemy import case
        priority_order = case(
            (Complaint.priority == "Urgent", 1),
            (Complaint.priority == "High", 2),
            (Complaint.priority == "Medium", 3),
            (Complaint.priority == "Low", 4),
            else_=5,
        )
        q = q.order_by(priority_order, Complaint.created_at.desc())

    offset = (page - 1) * page_size
    complaints = q.offset(offset).limit(page_size).all()
    return complaints, total


# ─── Voting ──────────────────────────────────────────────────────────────────

def toggle_vote(db: Session, complaint_id: str, student_id: str
                ) -> tuple[bool, str, int]:
    """
    Add or remove a vote. Enforces one vote per student per complaint via DB constraint.
    Returns (added, message, new_vote_count).
    """
    complaint = get_complaint_by_id(db, complaint_id)
    if not complaint:
        return False, "Complaint not found.", 0
    if complaint.merged_into_id:
        return False, "This complaint has been merged. Vote on the surviving complaint.", 0

    existing = db.query(ComplaintVote).filter_by(
        complaint_id=complaint_id, student_id=student_id).first()

    try:
        if existing:
            db.delete(existing)
            complaint.vote_count = max(0, (complaint.vote_count or 0) - 1)
            db.commit()
            return False, "Support removed.", complaint.vote_count
        else:
            vote = ComplaintVote(complaint_id=complaint_id, student_id=student_id)
            db.add(vote)
            complaint.vote_count = (complaint.vote_count or 0) + 1
            db.commit()
            return True, "Support added!", complaint.vote_count
    except Exception as e:
        db.rollback()
        return False, str(e), complaint.vote_count or 0


def has_voted(db: Session, complaint_id: str, student_id: str) -> bool:
    return db.query(ComplaintVote).filter_by(
        complaint_id=complaint_id, student_id=student_id).first() is not None


# ─── Comments ────────────────────────────────────────────────────────────────

def add_comment(db: Session, complaint_id: str, author_id: str,
                content: str, is_official: bool = False) -> tuple[bool, str]:
    if not content.strip():
        return False, "Comment cannot be empty."
    try:
        comment = ComplaintComment(
            complaint_id=complaint_id,
            author_id=author_id,
            content=content.strip(),
            is_official=is_official,
        )
        db.add(comment)
        _notify_complaint_participants(
            db, complaint_id=complaint_id, actor_id=author_id,
            event_type="comment_added",
            message=f"New {'official update' if is_official else 'comment'} on your complaint.")
        db.commit()
        return True, "Comment added."
    except Exception as e:
        db.rollback()
        return False, str(e)


def moderate_comment(db: Session, comment_id: str, moderator_id: str) -> tuple[bool, str]:
    comment = db.query(ComplaintComment).filter_by(id=comment_id).first()
    if not comment:
        return False, "Comment not found."
    comment.is_moderated = True
    comment.moderated_by_id = moderator_id
    comment.moderated_at = _utcnow()
    try:
        db.commit()
        return True, "Comment moderated."
    except Exception as e:
        db.rollback()
        return False, str(e)


# ─── Caretaker seen / acknowledged ───────────────────────────────────────────

def mark_seen(db: Session, complaint_id: str, caretaker_id: str,
              actor_role: UserRole) -> tuple[bool, str]:
    """
    Record that a caretaker has seen a complaint.
    Only caretakers and admins may call this. Students cannot set this.
    first_seen_at is set once and never overwritten.
    """
    if actor_role not in (UserRole.caretaker, UserRole.admin):
        return False, "Only caretakers and admins can mark a complaint as seen."

    try:
        now = _utcnow()
        ack = db.query(CaretakerAcknowledgement).filter_by(
            complaint_id=complaint_id, caretaker_id=caretaker_id).first()

        if ack is None:
            ack = CaretakerAcknowledgement(
                complaint_id=complaint_id,
                caretaker_id=caretaker_id,
                first_seen_at=now,
                last_seen_at=now,
            )
            db.add(ack)
        else:
            ack.last_seen_at = now   # update only last_seen; first_seen is immutable

        _audit(db, actor_id=caretaker_id, action="mark_seen",
               entity_type="complaint", entity_id=complaint_id,
               metadata={"first_seen": ack.first_seen_at is None})
        db.commit()
        return True, "Marked as seen."
    except Exception as e:
        db.rollback()
        return False, str(e)


def acknowledge_complaint(db: Session, complaint_id: str, caretaker_id: str,
                          actor_role: UserRole,
                          work_notes: str = "",
                          estimated_completion: datetime | None = None
                          ) -> tuple[bool, str]:
    """
    Explicit acknowledgement — separate from seen.
    Also transitions status to Acknowledged.
    """
    if actor_role not in (UserRole.caretaker, UserRole.admin):
        return False, "Only caretakers and admins can acknowledge complaints."

    try:
        now = _utcnow()
        ack = db.query(CaretakerAcknowledgement).filter_by(
            complaint_id=complaint_id, caretaker_id=caretaker_id).first()

        if ack is None:
            ack = CaretakerAcknowledgement(
                complaint_id=complaint_id,
                caretaker_id=caretaker_id,
                first_seen_at=now,
                last_seen_at=now,
                acknowledged_at=now,
                work_notes=work_notes,
                estimated_completion=estimated_completion,
            )
            db.add(ack)
        else:
            if ack.acknowledged_at is None:
                ack.acknowledged_at = now
            ack.work_notes = work_notes or ack.work_notes
            if estimated_completion:
                ack.estimated_completion = estimated_completion

        # Status transition
        complaint = get_complaint_by_id(db, complaint_id)
        if complaint and complaint.status == ComplaintStatus.submitted:
            _transition_status(db, complaint, ComplaintStatus.acknowledged,
                               actor_id=caretaker_id,
                               notes=work_notes or "Acknowledged by caretaker.")

        _audit(db, actor_id=caretaker_id, action="acknowledge",
               entity_type="complaint", entity_id=complaint_id)
        _notify_complaint_participants(
            db, complaint_id=complaint_id, actor_id=caretaker_id,
            event_type="acknowledged",
            message="Your complaint has been acknowledged by the caretaker.")
        db.commit()
        return True, "Complaint acknowledged."
    except Exception as e:
        db.rollback()
        return False, str(e)


def get_seen_status(db: Session, complaint_id: str
                    ) -> tuple[bool, Optional[CaretakerAcknowledgement]]:
    """Return (is_seen, acknowledgement_row_or_None)."""
    ack = db.query(CaretakerAcknowledgement).filter(
        CaretakerAcknowledgement.complaint_id == complaint_id,
        CaretakerAcknowledgement.first_seen_at != None,
    ).order_by(CaretakerAcknowledgement.first_seen_at).first()
    return (ack is not None), ack


# ─── Status transitions ───────────────────────────────────────────────────────

ALLOWED_TRANSITIONS: dict[ComplaintStatus, list[ComplaintStatus]] = {
    ComplaintStatus.submitted: [ComplaintStatus.acknowledged, ComplaintStatus.assigned,
                                ComplaintStatus.closed],
    ComplaintStatus.acknowledged: [ComplaintStatus.assigned, ComplaintStatus.in_progress,
                                   ComplaintStatus.closed],
    ComplaintStatus.assigned: [ComplaintStatus.in_progress, ComplaintStatus.closed],
    ComplaintStatus.in_progress: [ComplaintStatus.resolved, ComplaintStatus.closed],
    ComplaintStatus.resolved: [ComplaintStatus.reopened, ComplaintStatus.closed],
    ComplaintStatus.reopened: [ComplaintStatus.acknowledged, ComplaintStatus.assigned,
                               ComplaintStatus.in_progress, ComplaintStatus.closed],
    ComplaintStatus.closed: [],
}


def update_status(db: Session, complaint_id: str, new_status: str,
                  actor_id: str, actor_role: UserRole,
                  notes: str = "") -> tuple[bool, str]:
    """
    Transition a complaint's status. Validates allowed transitions and roles.
    Students may only reopen; caretakers/admins may perform other transitions.
    """
    complaint = get_complaint_by_id(db, complaint_id)
    if not complaint:
        return False, "Complaint not found."

    try:
        new = ComplaintStatus(new_status)
    except ValueError:
        return False, f"Unknown status: {new_status}"

    allowed = ALLOWED_TRANSITIONS.get(complaint.status, [])
    if new not in allowed:
        return False, (f"Cannot transition from {complaint.status.value} to {new.value}. "
                       f"Allowed: {[s.value for s in allowed]}")

    # Role check
    if new == ComplaintStatus.reopened:
        if actor_role not in (UserRole.student, UserRole.admin):
            return False, "Only students or admins can reopen complaints."
    elif actor_role == UserRole.student:
        return False, "Students may only reopen complaints."

    try:
        _transition_status(db, complaint, new, actor_id=actor_id, notes=notes)
        _notify_complaint_participants(
            db, complaint_id=complaint_id, actor_id=actor_id,
            event_type="status_updated",
            message=f"Complaint status updated to: {new.value}")
        db.commit()
        return True, f"Status updated to {new.value}."
    except Exception as e:
        db.rollback()
        return False, str(e)


def _transition_status(db: Session, complaint: Complaint,
                       new_status: ComplaintStatus,
                       actor_id: str, notes: str = ""):
    old_status = complaint.status.value if complaint.status else None
    complaint.status = new_status
    complaint.updated_at = _utcnow()
    if new_status == ComplaintStatus.resolved:
        complaint.resolved_at = _utcnow()

    history = ComplaintStatusHistory(
        complaint_id=complaint.id,
        old_status=old_status,
        new_status=new_status.value,
        actor_id=actor_id,
        notes=notes,
    )
    db.add(history)
    _audit(db, actor_id=actor_id, action="status_change",
           entity_type="complaint", entity_id=complaint.id,
           metadata={"old": old_status, "new": new_status.value})


# ─── Assignment ───────────────────────────────────────────────────────────────

def assign_complaint(db: Session, complaint_id: str, assigning_admin_id: str,
                     caretaker_id: str | None = None,
                     department: str | None = None,
                     priority: str | None = None,
                     notes: str = "") -> tuple[bool, str]:
    complaint = get_complaint_by_id(db, complaint_id)
    if not complaint:
        return False, "Complaint not found."

    try:
        # Deactivate previous assignments
        db.query(ComplaintAssignment).filter_by(
            complaint_id=complaint_id, is_active=True
        ).update({"is_active": False})

        assignment = ComplaintAssignment(
            complaint_id=complaint_id,
            assigned_to_id=caretaker_id,
            department=department,
            assigned_by_id=assigning_admin_id,
            notes=notes,
        )
        db.add(assignment)

        # Update complaint's caretaker field for quick access
        if caretaker_id:
            complaint.assigned_caretaker_id = caretaker_id

        if priority:
            complaint.priority = priority

        # Status transition to Assigned if currently Submitted/Acknowledged
        if complaint.status in (ComplaintStatus.submitted, ComplaintStatus.acknowledged):
            _transition_status(db, complaint, ComplaintStatus.assigned,
                               actor_id=assigning_admin_id,
                               notes=notes or f"Assigned by admin.")

        _audit(db, actor_id=assigning_admin_id, action="assign",
               entity_type="complaint", entity_id=complaint_id,
               metadata={"caretaker_id": caretaker_id, "department": department})

        if caretaker_id:
            _create_notification(
                db, recipient_id=caretaker_id, event_type="assigned",
                complaint_id=complaint_id,
                message=f"Complaint {complaint.complaint_number} has been assigned to you.")

        db.commit()
        return True, "Complaint assigned."
    except Exception as e:
        db.rollback()
        return False, str(e)


# ─── Merge ────────────────────────────────────────────────────────────────────

def merge_complaints(db: Session, original_id: str, surviving_id: str,
                     admin_id: str, reason: str = "") -> tuple[bool, str]:
    """
    Merge original into surviving. Transfers votes (without double-counting),
    preserves comments and history.
    """
    original = get_complaint_by_id(db, original_id)
    surviving = get_complaint_by_id(db, surviving_id)
    if not original or not surviving:
        return False, "One or both complaints not found."
    if original_id == surviving_id:
        return False, "Cannot merge a complaint with itself."

    try:
        # Transfer votes (skip duplicates)
        for vote in original.votes:
            already = db.query(ComplaintVote).filter_by(
                complaint_id=surviving_id, student_id=vote.student_id).first()
            if not already:
                new_vote = ComplaintVote(
                    complaint_id=surviving_id, student_id=vote.student_id,
                    created_at=vote.created_at)
                db.add(new_vote)
                surviving.vote_count = (surviving.vote_count or 0) + 1

        # Mark original as merged
        original.merged_into_id = surviving_id
        original.status = ComplaintStatus.closed
        original.is_public = False

        # Record merge
        merge_record = ComplaintMerge(
            original_complaint_id=original_id,
            surviving_complaint_id=surviving_id,
            merged_by_id=admin_id,
            reason=reason,
        )
        db.add(merge_record)

        _audit(db, actor_id=admin_id, action="merge",
               entity_type="complaint", entity_id=original_id,
               metadata={"surviving_id": surviving_id, "reason": reason})

        db.commit()
        return True, f"Merged into {surviving.complaint_number}."
    except Exception as e:
        db.rollback()
        return False, str(e)


# ─── Attachments ─────────────────────────────────────────────────────────────

ALLOWED_MIME_TYPES = {"image/jpeg", "image/png", "image/gif", "image/webp"}
MAX_SIZE_BYTES = int(os.getenv("MAX_UPLOAD_SIZE_MB", "5")) * 1024 * 1024


def save_attachment(db: Session, complaint_id: str, uploader_id: str,
                    file_bytes: bytes, filename: str, mime_type: str,
                    attachment_type: str = "complaint_photo") -> tuple[bool, str]:
    if mime_type not in ALLOWED_MIME_TYPES:
        return False, f"Unsupported file type: {mime_type}. Allowed: JPEG, PNG, GIF, WebP."
    if len(file_bytes) > MAX_SIZE_BYTES:
        return False, f"File too large. Maximum {os.getenv('MAX_UPLOAD_SIZE_MB', '5')} MB."

    upload_dir = Path(os.getenv("UPLOAD_DIR", "uploads")) / complaint_id
    upload_dir.mkdir(parents=True, exist_ok=True)
    safe_name = f"{uuid.uuid4()}_{filename}"
    path = upload_dir / safe_name
    path.write_bytes(file_bytes)

    attachment = ComplaintAttachment(
        complaint_id=complaint_id,
        uploader_id=uploader_id,
        filename=filename,
        storage_path=str(path),
        attachment_type=attachment_type,
        mime_type=mime_type,
        size_bytes=len(file_bytes),
    )
    db.add(attachment)
    try:
        db.commit()
        return True, str(path)
    except Exception as e:
        db.rollback()
        path.unlink(missing_ok=True)
        return False, str(e)


# ─── Notifications ────────────────────────────────────────────────────────────

def _create_notification(db: Session, recipient_id: str, event_type: str,
                         complaint_id: str | None, message: str):
    notif = Notification(
        recipient_id=recipient_id,
        event_type=event_type,
        complaint_id=complaint_id,
        message=message,
    )
    db.add(notif)


def _notify_complaint_participants(db: Session, complaint_id: str, actor_id: str,
                                   event_type: str, message: str):
    """Notify the submitter and assigned caretaker (excluding the actor)."""
    complaint = get_complaint_by_id(db, complaint_id)
    if not complaint:
        return
    recipients = set()
    if complaint.submitter_id and complaint.submitter_id != actor_id:
        recipients.add(complaint.submitter_id)
    if complaint.assigned_caretaker_id and complaint.assigned_caretaker_id != actor_id:
        recipients.add(complaint.assigned_caretaker_id)
    for rid in recipients:
        _create_notification(db, recipient_id=rid, event_type=event_type,
                             complaint_id=complaint_id, message=message)


def get_notifications(db: Session, user_id: str, unread_only: bool = False,
                      limit: int = 20) -> list[Notification]:
    q = db.query(Notification).filter(Notification.recipient_id == user_id)
    if unread_only:
        q = q.filter(Notification.is_read == False)
    return q.order_by(Notification.created_at.desc()).limit(limit).all()


def mark_notifications_read(db: Session, user_id: str):
    db.query(Notification).filter(
        Notification.recipient_id == user_id,
        Notification.is_read == False,
    ).update({"is_read": True})
    db.commit()


# ─── Audit ────────────────────────────────────────────────────────────────────

def _audit(db: Session, actor_id: str, action: str, entity_type: str,
           entity_id: str | None = None, metadata: dict | None = None):
    log = AuditLog(
        actor_id=actor_id,
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        metadata_json=json.dumps(metadata) if metadata else None,
    )
    db.add(log)


def get_audit_logs(db: Session, entity_id: str | None = None,
                   limit: int = 50) -> list[AuditLog]:
    q = db.query(AuditLog)
    if entity_id:
        q = q.filter(AuditLog.entity_id == entity_id)
    return q.order_by(AuditLog.created_at.desc()).limit(limit).all()


# ─── Analytics helpers ────────────────────────────────────────────────────────

def get_analytics_data(db: Session) -> dict:
    """Compute analytics metrics from actual database records."""
    from sqlalchemy import func, case as sa_case
    from src.db.models import ComplaintStatusHistory

    total = db.query(Complaint).filter(Complaint.merged_into_id == None).count()
    by_status = dict(
        db.query(Complaint.status, func.count(Complaint.id))
        .filter(Complaint.merged_into_id == None)
        .group_by(Complaint.status).all()
    )
    by_category = dict(
        db.query(Complaint.category, func.count(Complaint.id))
        .filter(Complaint.merged_into_id == None)
        .group_by(Complaint.category).all()
    )
    by_hostel = dict(
        db.query(Complaint.hostel, func.count(Complaint.id))
        .filter(Complaint.merged_into_id == None)
        .group_by(Complaint.hostel).all()
    )
    by_priority = dict(
        db.query(Complaint.priority, func.count(Complaint.id))
        .filter(Complaint.merged_into_id == None)
        .group_by(Complaint.priority).all()
    )

    # Avg time to first seen (hours)
    seen_pairs = (
        db.query(Complaint.created_at, CaretakerAcknowledgement.first_seen_at)
        .join(CaretakerAcknowledgement,
              CaretakerAcknowledgement.complaint_id == Complaint.id)
        .filter(CaretakerAcknowledgement.first_seen_at != None)
        .all()
    )
    seen_hours = [
        (s - c).total_seconds() / 3600
        for c, s in seen_pairs
        if s and c and s > c
    ]
    avg_seen_hours = sum(seen_hours) / len(seen_hours) if seen_hours else None

    # Avg time to acknowledgement (hours)
    ack_pairs = (
        db.query(Complaint.created_at, CaretakerAcknowledgement.acknowledged_at)
        .join(CaretakerAcknowledgement,
              CaretakerAcknowledgement.complaint_id == Complaint.id)
        .filter(CaretakerAcknowledgement.acknowledged_at != None)
        .all()
    )
    ack_hours = [
        (a - c).total_seconds() / 3600
        for c, a in ack_pairs
        if a and c and a > c
    ]
    avg_ack_hours = sum(ack_hours) / len(ack_hours) if ack_hours else None

    # Avg resolution time (hours) — only for resolved complaints
    resolved = (
        db.query(Complaint)
        .filter(Complaint.status == ComplaintStatus.resolved,
                Complaint.resolved_at != None,
                Complaint.merged_into_id == None)
        .all()
    )
    res_hours = [
        (c.resolved_at - c.created_at).total_seconds() / 3600
        for c in resolved
        if c.resolved_at and c.created_at and c.resolved_at > c.created_at
    ]
    avg_res_hours = sum(res_hours) / len(res_hours) if res_hours else None

    # Top supported issues
    top_voted = (
        db.query(Complaint)
        .filter(Complaint.merged_into_id == None, Complaint.vote_count > 0)
        .order_by(Complaint.vote_count.desc())
        .limit(5)
        .all()
    )

    return {
        "total": total,
        "by_status": {str(k): v for k, v in by_status.items()},
        "by_category": {str(k): v for k, v in by_category.items()},
        "by_hostel": {str(k): v for k, v in by_hostel.items()},
        "by_priority": {str(k): v for k, v in by_priority.items()},
        "avg_seen_hours": avg_seen_hours,
        "avg_ack_hours": avg_ack_hours,
        "avg_resolution_hours": avg_res_hours,
        "top_voted": top_voted,
    }


def export_complaints_csv(db: Session) -> str:
    """Return CSV string of all non-merged complaints."""
    import pandas as pd
    complaints = db.query(Complaint).filter(
        Complaint.merged_into_id == None).order_by(Complaint.created_at.desc()).all()
    rows = []
    for c in complaints:
        is_seen, ack = get_seen_status(db, c.id)
        rows.append({
            "complaint_number": c.complaint_number,
            "title": c.title,
            "category": str(c.category.value) if c.category else "",
            "hostel": c.hostel,
            "block": c.block or "",
            "floor": c.floor or "",
            "location_detail": c.location_detail or "",
            "status": str(c.status.value) if c.status else "",
            "priority": str(c.priority.value) if c.priority else "",
            "vote_count": c.vote_count,
            "is_seen": is_seen,
            "first_seen_at": ack.first_seen_at.isoformat() if ack and ack.first_seen_at else "",
            "acknowledged_at": ack.acknowledged_at.isoformat() if ack and ack.acknowledged_at else "",
            "created_at": c.created_at.isoformat(),
            "updated_at": c.updated_at.isoformat(),
            "resolved_at": c.resolved_at.isoformat() if c.resolved_at else "",
        })
    df = pd.DataFrame(rows)
    return df.to_csv(index=False)
