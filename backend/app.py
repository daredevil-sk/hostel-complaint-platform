"""
Hostel Grievance & Accountability Platform — FastAPI Backend.
Reuses existing SQLAlchemy models and business logic from src.
"""

from __future__ import annotations

import os
import sys
import secrets
from datetime import datetime, timezone, timedelta
from typing import Optional, List
from pathlib import Path

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from fastapi import FastAPI, Depends, HTTPException, status, Header, UploadFile, File, Form, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, PlainTextResponse, JSONResponse
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session

from src.db.database import get_db, init_db
from src.db.models import Profile, Complaint, ComplaintStatus, UserRole, Priority, Category, ComplaintVote
from src.utils.auth import hash_password, verify_password
from src.utils.complaints import (
    create_complaint, list_complaints, get_complaint_by_id, delete_complaint,
    toggle_vote, has_voted, add_comment, moderate_comment, mark_seen,
    acknowledge_complaint, update_status, assign_complaint, merge_complaints,
    save_attachment, get_seen_status, get_notifications, mark_notifications_read,
    get_audit_logs, get_analytics_data, export_complaints_csv, ALLOWED_TRANSITIONS,
)

# Initialize database
init_db()

app = FastAPI(
    title="Hostel Grievance Platform API",
    description="REST API for IIT Patna Hostel Grievance & Accountability Platform",
    version="2.0.0",
)

# Enable CORS for local dev
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─── In-Memory Session Token Storage ─────────────────────────────────────────
# Maps token -> user_id
SESSIONS: dict[str, str] = {}


def get_current_user_optional(authorization: Optional[str] = Header(None), db: Session = Depends(get_db)) -> Optional[Profile]:
    if not authorization:
        return None
    token = authorization.replace("Bearer ", "").strip()
    user_id = SESSIONS.get(token)
    if not user_id:
        return None
    user = db.query(Profile).filter(Profile.id == user_id, Profile.is_active == True).first()
    return user


def get_current_user(authorization: Optional[str] = Header(None), db: Session = Depends(get_db)) -> Profile:
    user = get_current_user_optional(authorization, db)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required. Please sign in.",
        )
    return user


def require_role(*roles: UserRole):
    def role_checker(user: Profile = Depends(get_current_user)):
        if user.role not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied. Requires one of roles: {[r.value for r in roles]}",
            )
        return user
    return role_checker


# ─── IST Helper ─────────────────────────────────────────────────────────────
_IST = timedelta(hours=5, minutes=30)

def fmt_ist(dt: Optional[datetime]) -> Optional[str]:
    if dt is None:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    ist_dt = dt.astimezone(timezone(_IST))
    return ist_dt.strftime("%d %b %Y, %I:%M %p IST")


# ─── Pydantic Schemas ─────────────────────────────────────────────────────────

class LoginRequest(BaseModel):
    email: str
    password: str

class RegisterRequest(BaseModel):
    display_name: str
    email: str
    password: str
    hostel: Optional[str] = None

class UserResponse(BaseModel):
    id: str
    email: str
    display_name: str
    role: str
    hostel: Optional[str] = None

class CommentRequest(BaseModel):
    content: str
    is_official: bool = False

class AcknowledgeRequest(BaseModel):
    work_notes: Optional[str] = ""
    estimated_completion: Optional[str] = None  # ISO format string

class StatusUpdateRequest(BaseModel):
    new_status: str
    notes: Optional[str] = ""

class AssignRequest(BaseModel):
    caretaker_id: Optional[str] = None
    department: Optional[str] = None
    priority: Optional[str] = None
    notes: Optional[str] = ""

class MergeRequest(BaseModel):
    original_id: str
    surviving_id: str
    reason: Optional[str] = ""

class CreateUserRequest(BaseModel):
    display_name: str
    email: str
    password: str
    role: str
    hostel: Optional[str] = None


# ─── Auth Endpoints ──────────────────────────────────────────────────────────

@app.post("/api/auth/login")
def api_login(req: LoginRequest, db: Session = Depends(get_db)):
    email = req.email.strip().lower()
    user = db.query(Profile).filter(Profile.email == email).first()
    if not user or not verify_password(req.password, user.password_hash):
        raise HTTPException(status_code=400, detail="Invalid email or password.")
    if not user.is_active:
        raise HTTPException(status_code=403, detail="Account is deactivated.")

    token = secrets.token_hex(32)
    SESSIONS[token] = user.id

    return {
        "token": token,
        "user": {
            "id": user.id,
            "email": user.email,
            "display_name": user.display_name,
            "role": user.role.value,
            "hostel": user.hostel,
        }
    }


@app.post("/api/auth/register")
def api_register(req: RegisterRequest, db: Session = Depends(get_db)):
    email = req.email.strip().lower()
    if not email:
        raise HTTPException(status_code=400, detail="Email is required.")
    if not req.display_name.strip():
        raise HTTPException(status_code=400, detail="Display name is required.")
    if len(req.password) < 6:
        raise HTTPException(status_code=400, detail="Password must be at least 6 characters.")

    existing = db.query(Profile).filter(Profile.email == email).first()
    if existing:
        raise HTTPException(status_code=400, detail="An account with this email already exists.")

    hashed = hash_password(req.password)
    user = Profile(
        email=email,
        display_name=req.display_name.strip(),
        password_hash=hashed,
        role=UserRole.student,
        hostel=req.hostel or None,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    token = secrets.token_hex(32)
    SESSIONS[token] = user.id

    return {
        "token": token,
        "user": {
            "id": user.id,
            "email": user.email,
            "display_name": user.display_name,
            "role": user.role.value,
            "hostel": user.hostel,
        }
    }


@app.get("/api/auth/me")
def api_me(user: Profile = Depends(get_current_user)):
    return {
        "id": user.id,
        "email": user.email,
        "display_name": user.display_name,
        "role": user.role.value,
        "hostel": user.hostel,
    }


@app.post("/api/auth/logout")
def api_logout(authorization: Optional[str] = Header(None)):
    if authorization:
        token = authorization.replace("Bearer ", "").strip()
        SESSIONS.pop(token, None)
    return {"message": "Logged out successfully."}


@app.get("/api/auth/demo-accounts")
def api_demo_accounts():
    return [
        {"role": "Student (Girls)", "hostel": "Asima", "email": "student1@demo.teamr", "password": "demo1234"},
        {"role": "Student (Girls)", "hostel": "Aryabhatta C", "email": "student2@demo.teamr", "password": "demo1234"},
        {"role": "Student (Boys)", "hostel": "Kalam", "email": "student3@demo.teamr", "password": "demo1234"},
        {"role": "Student (Boys)", "hostel": "CV Raman", "email": "student4@demo.teamr", "password": "demo1234"},
        {"role": "Caretaker", "hostel": "Campus", "email": "caretaker@demo.teamr", "password": "demo1234"},
        {"role": "Administrator", "hostel": "Admin", "email": "admin@demo.teamr", "password": "demo1234"},
    ]


# ─── Complaints List & Detail Endpoints ──────────────────────────────────────

@app.get("/api/complaints")
def api_list_complaints(
    search: str = "",
    category: str = "",
    hostel: str = "",
    block: str = "",
    status: str = "",
    priority: str = "",
    sort_by: str = "newest",
    page: int = 1,
    page_size: int = 10,
    user: Optional[Profile] = Depends(get_current_user_optional),
    db: Session = Depends(get_db),
):
    complaints, total = list_complaints(
        db,
        search=search,
        category=category,
        hostel=hostel,
        block=block,
        status=status,
        priority=priority,
        sort_by=sort_by,
        page=page,
        page_size=page_size,
        include_private=False,
    )

    total_pages = max(1, (total + page_size - 1) // page_size)

    items = []
    for c in complaints:
        is_seen, ack = get_seen_status(db, c.id)
        voted = False
        if user and user.role == UserRole.student:
            voted = has_voted(db, c.id, user.id)

        items.append({
            "id": c.id,
            "complaint_number": c.complaint_number,
            "title": c.title,
            "category": c.category.value if c.category else "Other",
            "hostel": c.hostel,
            "block": c.block or "",
            "floor": c.floor or "",
            "location_detail": c.location_detail or "",
            "status": c.status.value if c.status else "Submitted",
            "priority": c.priority.value if c.priority else "Medium",
            "vote_count": c.vote_count,
            "is_anonymous": getattr(c, "is_anonymous", False),
            "is_seen": is_seen,
            "is_acknowledged": bool(ack and ack.acknowledged_at),
            "created_at": fmt_ist(c.created_at),
            "updated_at": fmt_ist(c.updated_at),
            "voted": voted,
        })

    return {
        "complaints": items,
        "total": total,
        "page": page,
        "total_pages": total_pages,
    }


@app.get("/api/complaints/{complaint_id}")
def api_get_complaint(
    complaint_id: str,
    user: Optional[Profile] = Depends(get_current_user_optional),
    db: Session = Depends(get_db),
):
    complaint = get_complaint_by_id(db, complaint_id)
    if not complaint:
        raise HTTPException(status_code=404, detail="Complaint not found.")

    if complaint.merged_into_id:
        return {"merged": True, "surviving_id": complaint.merged_into_id}

    is_seen, ack = get_seen_status(db, complaint.id)

    # Auto-mark seen if assigned caretaker/admin opens it
    if user and user.role in (UserRole.caretaker, UserRole.admin):
        if complaint.assigned_caretaker_id == user.id or user.role == UserRole.admin:
            if not is_seen or (ack and ack.caretaker_id == user.id and ack.first_seen_at is None):
                mark_seen(db, complaint.id, user.id, user.role)
                db.refresh(complaint)
                is_seen, ack = get_seen_status(db, complaint.id)

    # Attachments
    photos = []
    res_photos = []
    for att in complaint.attachments:
        info = {
            "id": att.id,
            "filename": att.filename,
            "url": f"/uploads/{complaint.id}/{Path(att.storage_path).name}",
            "type": att.attachment_type,
        }
        if att.attachment_type == "resolution_photo":
            res_photos.append(info)
        else:
            photos.append(info)

    # History timeline
    timeline = []
    for h in complaint.status_history:
        actor_name = h.actor.display_name if h.actor else "System"
        timeline.append({
            "id": h.id,
            "old_status": h.old_status,
            "new_status": h.new_status,
            "actor": actor_name,
            "notes": h.notes,
            "created_at": fmt_ist(h.created_at),
        })

    # Comments
    comments_list = []
    for cm in complaint.comments:
        if cm.is_moderated and (not user or user.role != UserRole.admin):
            continue
        author_name = cm.author.display_name if cm.author else "Unknown"
        author_role = cm.author.role.value if cm.author else "student"
        comments_list.append({
            "id": cm.id,
            "author_name": author_name,
            "author_role": author_role,
            "content": "[This comment has been moderated.]" if cm.is_moderated else cm.content,
            "is_official": cm.is_official,
            "is_moderated": cm.is_moderated,
            "created_at": fmt_ist(cm.created_at),
        })

    voted = False
    if user and user.role == UserRole.student:
        voted = has_voted(db, complaint.id, user.id)

    submitter_display = "Anonymous" if getattr(complaint, "is_anonymous", False) else (
        complaint.submitter.display_name if complaint.submitter else "Unknown"
    )

    allowed_transitions = [s.value for s in ALLOWED_TRANSITIONS.get(complaint.status, [])]

    return {
        "id": complaint.id,
        "complaint_number": complaint.complaint_number,
        "title": complaint.title,
        "description": complaint.description,
        "category": complaint.category.value if complaint.category else "Other",
        "hostel": complaint.hostel,
        "block": complaint.block or "",
        "floor": complaint.floor or "",
        "location_detail": complaint.location_detail or "",
        "status": complaint.status.value if complaint.status else "Submitted",
        "priority": complaint.priority.value if complaint.priority else "Medium",
        "vote_count": complaint.vote_count,
        "is_anonymous": getattr(complaint, "is_anonymous", False),
        "submitter_name": submitter_display,
        "submitter_id": complaint.submitter_id,
        "created_at": fmt_ist(complaint.created_at),
        "updated_at": fmt_ist(complaint.updated_at),
        "resolved_at": fmt_ist(complaint.resolved_at),
        "student_confirmed_resolved": complaint.student_confirmed_resolved,
        "voted": voted,
        "is_seen": is_seen,
        "first_seen_at": fmt_ist(ack.first_seen_at) if ack and ack.first_seen_at else None,
        "acknowledged_at": fmt_ist(ack.acknowledged_at) if ack and ack.acknowledged_at else None,
        "caretaker_name": ack.caretaker.display_name if ack and ack.caretaker else None,
        "work_notes": ack.work_notes if ack else None,
        "estimated_completion": fmt_ist(ack.estimated_completion) if ack and ack.estimated_completion else None,
        "photos": photos,
        "resolution_photos": res_photos,
        "timeline": timeline,
        "comments": comments_list,
        "allowed_transitions": allowed_transitions,
    }


# ─── Create & Delete Complaints ──────────────────────────────────────────────

@app.post("/api/complaints")
async def api_create_complaint(
    title: str = Form(...),
    description: str = Form(...),
    category: str = Form(...),
    hostel: str = Form(...),
    block: Optional[str] = Form(""),
    floor: Optional[str] = Form(""),
    location_detail: Optional[str] = Form(""),
    is_anonymous: bool = Form(False),
    priority: Optional[str] = Form("Medium"),
    is_public: bool = Form(True),
    photos: List[UploadFile] = File(None),
    user: Profile = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if user.role not in (UserRole.student, UserRole.admin):
        raise HTTPException(status_code=403, detail="Only students and admins can submit complaints.")

    ok, result, complaint = create_complaint(
        db,
        title=title,
        description=description,
        category=category,
        hostel=hostel,
        block=block or "",
        floor=floor or "",
        location_detail=location_detail or "",
        submitter_id=user.id,
        priority=priority if user.role == UserRole.admin else "Medium",
        is_public=is_public if user.role == UserRole.admin else True,
        is_anonymous=is_anonymous,
    )

    if not ok:
        raise HTTPException(status_code=400, detail=result)

    # Save attachments
    if photos and complaint:
        for p in photos:
            if p.filename:
                file_bytes = await p.read()
                mime = p.content_type or "image/jpeg"
                save_attachment(
                    db,
                    complaint_id=complaint.id,
                    uploader_id=user.id,
                    file_bytes=file_bytes,
                    filename=p.filename,
                    mime_type=mime,
                    attachment_type="complaint_photo",
                )

    return {
        "success": True,
        "complaint_id": complaint.id,
        "complaint_number": result,
        "message": f"Complaint {result} submitted successfully.",
    }


@app.delete("/api/complaints/{complaint_id}")
def api_delete_complaint(
    complaint_id: str,
    user: Profile = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    ok, msg = delete_complaint(db, complaint_id, user.id, user.role)
    if not ok:
        raise HTTPException(status_code=400, detail=msg)
    return {"success": True, "message": msg}


# ─── Actions: Vote, Comment, Seen, Acknowledge, Status ───────────────────────

@app.post("/api/complaints/{complaint_id}/vote")
def api_toggle_vote(
    complaint_id: str,
    user: Profile = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if user.role != UserRole.student:
        raise HTTPException(status_code=403, detail="Only students can support complaints.")
    added, msg, new_count = toggle_vote(db, complaint_id, user.id)
    return {"voted": added, "message": msg, "vote_count": new_count}


@app.post("/api/complaints/{complaint_id}/comments")
def api_add_comment(
    complaint_id: str,
    req: CommentRequest,
    user: Profile = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    is_official = req.is_official and (user.role in (UserRole.caretaker, UserRole.admin))
    ok, msg = add_comment(db, complaint_id, user.id, req.content, is_official=is_official)
    if not ok:
        raise HTTPException(status_code=400, detail=msg)
    return {"success": True, "message": msg}


@app.post("/api/comments/{comment_id}/moderate")
def api_moderate_comment(
    comment_id: str,
    user: Profile = Depends(require_role(UserRole.admin)),
    db: Session = Depends(get_db),
):
    ok, msg = moderate_comment(db, comment_id, user.id)
    if not ok:
        raise HTTPException(status_code=400, detail=msg)
    return {"success": True, "message": msg}


@app.post("/api/complaints/{complaint_id}/seen")
def api_mark_seen(
    complaint_id: str,
    user: Profile = Depends(require_role(UserRole.caretaker, UserRole.admin)),
    db: Session = Depends(get_db),
):
    ok, msg = mark_seen(db, complaint_id, user.id, user.role)
    if not ok:
        raise HTTPException(status_code=400, detail=msg)
    return {"success": True, "message": msg}


@app.post("/api/complaints/{complaint_id}/acknowledge")
def api_acknowledge(
    complaint_id: str,
    req: AcknowledgeRequest,
    user: Profile = Depends(require_role(UserRole.caretaker, UserRole.admin)),
    db: Session = Depends(get_db),
):
    est_dt = None
    if req.estimated_completion:
        try:
            est_dt = datetime.fromisoformat(req.estimated_completion.replace("Z", ""))
        except Exception:
            pass

    ok, msg = acknowledge_complaint(
        db, complaint_id, user.id, user.role,
        work_notes=req.work_notes or "",
        estimated_completion=est_dt,
    )
    if not ok:
        raise HTTPException(status_code=400, detail=msg)
    return {"success": True, "message": msg}


@app.post("/api/complaints/{complaint_id}/status")
def api_update_status(
    complaint_id: str,
    req: StatusUpdateRequest,
    user: Profile = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    ok, msg = update_status(
        db, complaint_id, req.new_status,
        actor_id=user.id, actor_role=user.role, notes=req.notes or "",
    )
    if not ok:
        raise HTTPException(status_code=400, detail=msg)
    return {"success": True, "message": msg}


@app.post("/api/complaints/{complaint_id}/confirm-resolved")
def api_confirm_resolved(
    complaint_id: str,
    user: Profile = Depends(require_role(UserRole.student)),
    db: Session = Depends(get_db),
):
    complaint = get_complaint_by_id(db, complaint_id)
    if not complaint:
        raise HTTPException(status_code=404, detail="Complaint not found.")
    if complaint.submitter_id != user.id:
        raise HTTPException(status_code=403, detail="Only the submitter can confirm resolution.")
    if complaint.status != ComplaintStatus.resolved:
        raise HTTPException(status_code=400, detail="Complaint is not marked as resolved.")

    complaint.student_confirmed_resolved = True
    db.commit()
    return {"success": True, "message": "Resolution confirmed. Thank you!"}


@app.post("/api/complaints/{complaint_id}/upload-photo")
async def api_upload_photo(
    complaint_id: str,
    file: UploadFile = File(...),
    photo_type: str = Form("resolution_photo"),
    user: Profile = Depends(require_role(UserRole.caretaker, UserRole.admin)),
    db: Session = Depends(get_db),
):
    file_bytes = await file.read()
    ok, msg = save_attachment(
        db,
        complaint_id=complaint_id,
        uploader_id=user.id,
        file_bytes=file_bytes,
        filename=file.filename,
        mime_type=file.content_type or "image/jpeg",
        attachment_type=photo_type,
    )
    if not ok:
        raise HTTPException(status_code=400, detail=msg)
    return {"success": True, "message": "Photo uploaded successfully."}


# ─── Student Dashboards & Notifications ──────────────────────────────────────

@app.get("/api/my-complaints")
def api_my_complaints(
    user: Profile = Depends(require_role(UserRole.student)),
    db: Session = Depends(get_db),
):
    # Mine
    mine, total_mine = list_complaints(db, submitter_id=user.id, include_private=True, page=1, page_size=50)
    my_items = []
    for c in mine:
        is_seen, ack = get_seen_status(db, c.id)
        my_items.append({
            "id": c.id,
            "complaint_number": c.complaint_number,
            "title": c.title,
            "category": c.category.value if c.category else "Other",
            "hostel": c.hostel,
            "block": c.block or "",
            "status": c.status.value if c.status else "Submitted",
            "priority": c.priority.value if c.priority else "Medium",
            "vote_count": c.vote_count,
            "is_seen": is_seen,
            "is_acknowledged": bool(ack and ack.acknowledged_at),
            "created_at": fmt_ist(c.created_at),
            "updated_at": fmt_ist(c.updated_at),
        })

    # Supported
    voted_ids = [v.complaint_id for v in db.query(ComplaintVote).filter_by(student_id=user.id).all()]
    supported = (
        db.query(Complaint)
        .filter(Complaint.id.in_(voted_ids))
        .order_by(Complaint.updated_at.desc())
        .all()
    ) if voted_ids else []

    voted_items = []
    for c in supported:
        is_seen, ack = get_seen_status(db, c.id)
        voted_items.append({
            "id": c.id,
            "complaint_number": c.complaint_number,
            "title": c.title,
            "category": c.category.value if c.category else "Other",
            "hostel": c.hostel,
            "block": c.block or "",
            "status": c.status.value if c.status else "Submitted",
            "priority": c.priority.value if c.priority else "Medium",
            "vote_count": c.vote_count,
            "is_seen": is_seen,
            "is_acknowledged": bool(ack and ack.acknowledged_at),
            "created_at": fmt_ist(c.created_at),
            "updated_at": fmt_ist(c.updated_at),
        })

    return {"my_submissions": my_items, "supported_complaints": voted_items}


@app.get("/api/notifications")
def api_get_notifications(
    user: Profile = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    notifs = get_notifications(db, user.id, limit=40)
    items = []
    unread_count = 0
    for n in notifs:
        if not n.is_read:
            unread_count += 1
        items.append({
            "id": n.id,
            "message": n.message,
            "complaint_id": n.complaint_id,
            "is_read": n.is_read,
            "created_at": fmt_ist(n.created_at),
        })
    return {"notifications": items, "unread_count": unread_count}


@app.post("/api/notifications/read-all")
def api_mark_notifications_read(
    user: Profile = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    mark_notifications_read(db, user.id)
    return {"success": True, "message": "All notifications marked as read."}


# ─── Caretaker Dashboard ─────────────────────────────────────────────────────

@app.get("/api/caretaker/dashboard")
def api_caretaker_dashboard(
    user: Profile = Depends(require_role(UserRole.caretaker, UserRole.admin)),
    db: Session = Depends(get_db),
):
    assigned, _ = list_complaints(db, assigned_caretaker_id=user.id, include_private=True, page=1, page_size=500)
    total_assigned = len(assigned)
    new_unseen = sum(1 for c in assigned if not get_seen_status(db, c.id)[0])
    acknowledged = sum(1 for c in assigned if c.status == ComplaintStatus.acknowledged)
    in_progress = sum(1 for c in assigned if c.status == ComplaintStatus.in_progress)
    now = datetime.utcnow()
    overdue = sum(
        1 for c in assigned
        if (c.status in (ComplaintStatus.assigned, ComplaintStatus.in_progress) and
            c.created_at and (now - c.created_at).days > 3)
    )

    def _format_list(comps):
        out = []
        for c in comps:
            is_seen, ack = get_seen_status(db, c.id)
            out.append({
                "id": c.id,
                "complaint_number": c.complaint_number,
                "title": c.title,
                "category": c.category.value if c.category else "Other",
                "hostel": c.hostel,
                "block": c.block or "",
                "status": c.status.value if c.status else "Submitted",
                "priority": c.priority.value if c.priority else "Medium",
                "vote_count": c.vote_count,
                "is_seen": is_seen,
                "is_acknowledged": bool(ack and ack.acknowledged_at),
                "work_notes": ack.work_notes if ack else "",
                "created_at": fmt_ist(c.created_at),
            })
        return out

    unseen_list = [c for c in assigned if not get_seen_status(db, c.id)[0]]
    assigned_list = [c for c in assigned if c.status in (ComplaintStatus.submitted, ComplaintStatus.acknowledged, ComplaintStatus.assigned)]
    in_progress_list = [c for c in assigned if c.status == ComplaintStatus.in_progress]

    return {
        "metrics": {
            "total_assigned": total_assigned,
            "new_unseen": new_unseen,
            "acknowledged": acknowledged,
            "in_progress": in_progress,
            "overdue": overdue,
        },
        "unseen": _format_list(unseen_list),
        "assigned": _format_list(assigned_list),
        "in_progress": _format_list(in_progress_list),
        "all": _format_list(assigned),
    }


# ─── Admin Endpoints ─────────────────────────────────────────────────────────

@app.get("/api/admin/overview")
def api_admin_overview(
    user: Profile = Depends(require_role(UserRole.admin)),
    db: Session = Depends(get_db),
):
    total = db.query(Complaint).filter(Complaint.merged_into_id == None).count()
    unassigned = db.query(Complaint).filter(Complaint.merged_into_id == None, Complaint.assigned_caretaker_id == None).count()
    unseen = sum(1 for c in db.query(Complaint).filter(Complaint.merged_into_id == None).all() if not get_seen_status(db, c.id)[0])
    users_count = db.query(Profile).count()

    return {
        "total_complaints": total,
        "unassigned_complaints": unassigned,
        "unseen_complaints": unseen,
        "total_users": users_count,
    }


@app.get("/api/admin/caretakers")
def api_admin_caretakers(
    user: Profile = Depends(require_role(UserRole.admin)),
    db: Session = Depends(get_db),
):
    caretakers = db.query(Profile).filter(Profile.role == UserRole.caretaker, Profile.is_active == True).all()
    return [{"id": c.id, "display_name": c.display_name, "email": c.email} for c in caretakers]


@app.post("/api/admin/assign")
def api_admin_assign(
    req: AssignRequest,
    complaint_id: str = Query(...),
    user: Profile = Depends(require_role(UserRole.admin)),
    db: Session = Depends(get_db),
):
    ok, msg = assign_complaint(
        db, complaint_id, user.id,
        caretaker_id=req.caretaker_id,
        department=req.department,
        priority=req.priority,
        notes=req.notes or "",
    )
    if not ok:
        raise HTTPException(status_code=400, detail=msg)
    return {"success": True, "message": msg}


@app.post("/api/admin/merge")
def api_admin_merge(
    req: MergeRequest,
    user: Profile = Depends(require_role(UserRole.admin)),
    db: Session = Depends(get_db),
):
    ok, msg = merge_complaints(
        db, req.original_id, req.surviving_id, user.id, reason=req.reason or "",
    )
    if not ok:
        raise HTTPException(status_code=400, detail=msg)
    return {"success": True, "message": msg}


@app.get("/api/admin/users")
def api_admin_users(
    user: Profile = Depends(require_role(UserRole.admin)),
    db: Session = Depends(get_db),
):
    users = db.query(Profile).order_by(Profile.created_at.desc()).all()
    return [
        {
            "id": u.id,
            "display_name": u.display_name,
            "email": u.email,
            "role": u.role.value,
            "hostel": u.hostel,
            "is_active": u.is_active,
            "created_at": fmt_ist(u.created_at),
        }
        for u in users
    ]


@app.post("/api/admin/users")
def api_admin_create_user(
    req: CreateUserRequest,
    user: Profile = Depends(require_role(UserRole.admin)),
    db: Session = Depends(get_db),
):
    email = req.email.strip().lower()
    existing = db.query(Profile).filter(Profile.email == email).first()
    if existing:
        raise HTTPException(status_code=400, detail="User with this email already exists.")

    try:
        role_enum = UserRole(req.role)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid role. Choices: {[r.value for r in UserRole]}")

    hashed = hash_password(req.password)
    new_user = Profile(
        email=email,
        display_name=req.display_name.strip(),
        password_hash=hashed,
        role=role_enum,
        hostel=req.hostel or None,
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return {"success": True, "message": f"Created user {new_user.display_name} ({new_user.role.value})."}


@app.get("/api/admin/audit-logs")
def api_admin_audit_logs(
    user: Profile = Depends(require_role(UserRole.admin)),
    db: Session = Depends(get_db),
):
    logs = get_audit_logs(db, limit=50)
    items = []
    for l in logs:
        actor_name = l.actor.display_name if l.actor else "System"
        items.append({
            "id": l.id,
            "actor": actor_name,
            "action": l.action,
            "entity_type": l.entity_type,
            "entity_id": l.entity_id,
            "created_at": fmt_ist(l.created_at),
        })
    return items


# ─── Analytics & CSV Export ──────────────────────────────────────────────────

@app.get("/api/analytics")
def api_analytics(
    user: Profile = Depends(require_role(UserRole.admin)),
    db: Session = Depends(get_db),
):
    data = get_analytics_data(db)
    top_voted = []
    for c in data.get("top_voted", []):
        top_voted.append({
            "id": c.id,
            "complaint_number": c.complaint_number,
            "title": c.title,
            "vote_count": c.vote_count,
            "hostel": c.hostel,
            "category": c.category.value if c.category else "Other",
        })
    data["top_voted"] = top_voted
    return data


@app.get("/api/analytics/export")
def api_export_csv(
    user: Profile = Depends(require_role(UserRole.admin)),
    db: Session = Depends(get_db),
):
    csv_str = export_complaints_csv(db)
    return PlainTextResponse(
        content=csv_str,
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=hostel_complaints_export.csv"},
    )


# ─── Static Files & Frontend Serving ─────────────────────────────────────────

# Mount upload directory
UPLOAD_DIR = PROJECT_ROOT / os.getenv("UPLOAD_DIR", "uploads")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=str(UPLOAD_DIR)), name="uploads")

# Frontend directory
FRONTEND_DIR = PROJECT_ROOT / "frontend"
FRONTEND_DIR.mkdir(parents=True, exist_ok=True)
app.mount("/static", StaticFiles(directory=str(FRONTEND_DIR)), name="frontend_static")

@app.get("/{full_path:path}")
def serve_spa(full_path: str):
    # Check if a specific file exists in frontend
    file_path = FRONTEND_DIR / full_path
    if full_path and file_path.exists() and file_path.is_file():
        return FileResponse(file_path)
    # Default to index.html for client-side routing
    index_file = FRONTEND_DIR / "index.html"
    if index_file.exists():
        return FileResponse(index_file)
    return {"message": "Hostel Grievance Platform API is running. Visit /docs for Swagger API."}
