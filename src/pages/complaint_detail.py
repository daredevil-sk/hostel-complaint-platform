"""
Complaint detail page — full timeline, voting, comments, seen/ack status.
"""

from __future__ import annotations

from pathlib import Path
import streamlit as st
from src.db.database import get_db
from src.db.models import (
    ComplaintStatus, UserRole, ComplaintStatusHistory,
    ComplaintComment, CaretakerAcknowledgement,
)
from src.utils.auth import (
    get_current_user, is_logged_in, get_role,
    is_student, is_caretaker, is_admin,
)
from src.utils.complaints import (
    get_complaint_by_id, toggle_vote, has_voted, add_comment,
    get_seen_status, mark_seen, acknowledge_complaint, update_status,
    moderate_comment, ALLOWED_TRANSITIONS,
)
from src.components.ui import (
    status_badge, priority_badge, seen_badge, fmt_dt, page_header,
)
import os


def render():
    complaint_id = st.session_state.get("selected_complaint_id")
    if not complaint_id:
        st.error("No complaint selected.")
        if st.button("← Back to Board"):
            st.session_state["page"] = "board"
            st.rerun()
        return

    db = get_db()
    try:
        complaint = get_complaint_by_id(db, complaint_id)
        if not complaint:
            st.error("Complaint not found.")
            return

        # Redirect if merged
        if complaint.merged_into_id:
            st.warning(
                f"⚠️ This complaint has been merged. "
                f"Redirecting to the surviving complaint…"
            )
            st.session_state["selected_complaint_id"] = complaint.merged_into_id
            st.rerun()

        user = get_current_user()
        role = get_role()
        is_seen, ack = get_seen_status(db, complaint_id)

        # ─── Auto mark-seen for assigned caretaker ────────────────────────────
        if user and role in (UserRole.caretaker, UserRole.admin):
            if complaint.assigned_caretaker_id == user.id or role == UserRole.admin:
                if not is_seen or (ack and ack.caretaker_id == user.id and
                                   ack.first_seen_at is None):
                    mark_seen(db, complaint_id, user.id, role)
                    db.refresh(complaint)
                    is_seen, ack = get_seen_status(db, complaint_id)

        # ─── Header ───────────────────────────────────────────────────────────
        if st.button("← Back to Board"):
            st.session_state["page"] = "board"
            st.rerun()

        st.markdown(
            f"""
            <div style="padding:16px 0 8px 0;">
              <span style="font-size:0.8rem;color:#64748B;font-weight:500;">
                {complaint.complaint_number}</span>
              <h2 style="color:#1E293B;margin:4px 0;">{complaint.title}</h2>
              <div style="display:flex;flex-wrap:wrap;gap:8px;margin:8px 0;">
                {status_badge(complaint.status.value if complaint.status else "Submitted")}
                {priority_badge(complaint.priority.value if complaint.priority else "Medium")}
                {seen_badge(is_seen, ack and ack.acknowledged_at is not None)}
              </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        # ─── Details ──────────────────────────────────────────────────────────
        col_info, col_actions = st.columns([3, 1])

        with col_info:
            st.markdown("#### 📄 Description")
            st.markdown(complaint.description)

            # Seen indicator (explicit, for students)
            st.markdown("#### 👁️ Caretaker Seen Status")
            if is_seen and ack:
                caretaker_name = (ack.caretaker.display_name
                                  if ack.caretaker else "Caretaker")
                st.markdown(
                    f"""
                    <div style="background:#EFF6FF;border:1px solid #BFDBFE;
                                border-radius:8px;padding:12px 16px;">
                      <strong style="color:#1D4ED8;">👁️ Seen by caretaker</strong><br/>
                      <span style="color:#1E40AF;font-size:0.88rem;">
                        {caretaker_name} first opened this complaint on<br/>
                        <strong>{fmt_dt(ack.first_seen_at)}</strong>
                        {' (Acknowledged: ' + fmt_dt(ack.acknowledged_at) + ')' if ack.acknowledged_at else ''}
                      </span>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
                if ack.work_notes:
                    st.info(f"🔧 Work notes: {ack.work_notes}")
                if ack.estimated_completion:
                    st.info(f"📅 Estimated completion: {fmt_dt(ack.estimated_completion)}")
            else:
                st.markdown(
                    """
                    <div style="background:#FFF1F2;border:1px solid #FECDD3;
                                border-radius:8px;padding:12px 16px;">
                      <strong style="color:#BE123C;">👁️ Not yet seen by caretaker</strong><br/>
                      <span style="color:#9F1239;font-size:0.88rem;">
                        No caretaker has opened this complaint yet.
                      </span>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

            # Photos
            if complaint.attachments:
                st.markdown("#### 📷 Photos")
                photo_cols = st.columns(min(3, len(complaint.attachments)))
                for i, att in enumerate(complaint.attachments):
                    if att.attachment_type == "complaint_photo":
                        p = Path(att.storage_path)
                        if p.exists():
                            with photo_cols[i % 3]:
                                st.image(str(p), caption=att.filename, use_column_width=True)

        with col_info:
            st.markdown("---")
            st.markdown("#### 📍 Location")
            st.markdown(
                f"""
                <table style="font-size:0.88rem;color:#334155;">
                  <tr><td><strong>Hostel</strong></td><td>{complaint.hostel}</td></tr>
                  {'<tr><td><strong>Block</strong></td><td>' + complaint.block + '</td></tr>' if complaint.block else ''}
                  {'<tr><td><strong>Floor</strong></td><td>' + complaint.floor + '</td></tr>' if complaint.floor else ''}
                  {'<tr><td><strong>Location</strong></td><td>' + complaint.location_detail + '</td></tr>' if complaint.location_detail else ''}
                  <tr><td><strong>Category</strong></td>
                    <td>{complaint.category.value if complaint.category else ''}</td></tr>
                  <tr><td><strong>Submitted</strong></td>
                    <td>{fmt_dt(complaint.created_at)}</td></tr>
                  <tr><td><strong>Last updated</strong></td>
                    <td>{fmt_dt(complaint.updated_at)}</td></tr>
                </table>
                """,
                unsafe_allow_html=True,
            )

        with col_actions:
            # Vote
            st.markdown("#### 👥 Support")
            st.markdown(
                f"""
                <div style="text-align:center;background:#F8FAFC;border:1px solid #E2E8F0;
                            border-radius:12px;padding:16px 8px;">
                  <div style="font-size:2rem;font-weight:700;color:#4F46E5;">
                    {complaint.vote_count}</div>
                  <div style="font-size:0.82rem;color:#64748B;">supporters</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
            if is_logged_in() and is_student():
                voted = has_voted(db, complaint_id, user.id)
                btn_label = "✅ Remove support" if voted else "👍 Add support"
                if st.button(btn_label, use_container_width=True, type="primary"):
                    added, msg, new_count = toggle_vote(db, complaint_id, user.id)
                    st.success(msg)
                    st.rerun()

            # Caretaker actions
            if is_logged_in() and role in (UserRole.caretaker, UserRole.admin):
                st.markdown("#### 🔧 Caretaker Actions")

                if not is_seen or (ack and ack.caretaker_id == user.id
                                   and ack.first_seen_at is None):
                    if st.button("👁️ Mark as Seen", use_container_width=True):
                        ok, msg = mark_seen(db, complaint_id, user.id, role)
                        if ok:
                            st.success(msg)
                        else:
                            st.error(msg)
                        st.rerun()

                if not (ack and ack.caretaker_id == user.id
                        and ack.acknowledged_at is not None):
                    with st.expander("✅ Acknowledge complaint"):
                        work_notes = st.text_area("Work notes", key="ack_notes")
                        est = st.date_input("Estimated completion", key="ack_est",
                                            value=None)
                        from datetime import datetime
                        est_dt = datetime.combine(est,
                                                  datetime.min.time()) if est else None
                        if st.button("Acknowledge", use_container_width=True,
                                     type="primary"):
                            ok, msg = acknowledge_complaint(
                                db, complaint_id, user.id, role,
                                work_notes=work_notes, estimated_completion=est_dt)
                            if ok:
                                st.success(msg)
                            else:
                                st.error(msg)
                            st.rerun()

                # Status update
                st.markdown("#### 📊 Update Status")
                current = complaint.status
                allowed = ALLOWED_TRANSITIONS.get(current, [])
                if allowed:
                    new_status = st.selectbox(
                        "New status",
                        [s.value for s in allowed],
                        key="caretaker_status",
                    )
                    status_notes = st.text_input("Notes", key="caretaker_notes")
                    if st.button("Update Status", use_container_width=True):
                        ok, msg = update_status(
                            db, complaint_id, new_status,
                            actor_id=user.id, actor_role=role, notes=status_notes)
                        if ok:
                            st.success(msg)
                        else:
                            st.error(msg)
                        st.rerun()
                else:
                    st.info("No further status transitions available.")

            # Student reopen / confirm resolved
            if (is_logged_in() and is_student() and
                    complaint.submitter_id == user.id and
                    complaint.status == ComplaintStatus.resolved):
                st.markdown("#### 🔄 Resolution")
                if not complaint.student_confirmed_resolved:
                    col_conf, col_reopen = st.columns(2)
                    with col_conf:
                        if st.button("✅ Confirm Resolved", use_container_width=True,
                                     type="primary"):
                            db.refresh(complaint)
                            complaint.student_confirmed_resolved = True
                            db.commit()
                            st.success("Thank you for confirming the resolution!")
                            st.rerun()
                    with col_reopen:
                        if st.button("🔄 Reopen", use_container_width=True):
                            reopen_reason = st.text_input(
                                "Reason for reopening", key="reopen_reason")
                            if reopen_reason:
                                ok, msg = update_status(
                                    db, complaint_id, "Reopened",
                                    actor_id=user.id,
                                    actor_role=role,
                                    notes=reopen_reason)
                                if ok:
                                    st.success(msg)
                                else:
                                    st.error(msg)
                                st.rerun()

        # ─── Status Timeline ──────────────────────────────────────────────────
        st.markdown("---")
        st.markdown("#### 🕐 Activity Timeline")
        history = (
            db.query(ComplaintStatusHistory)
            .filter_by(complaint_id=complaint_id)
            .order_by(ComplaintStatusHistory.created_at)
            .all()
        )
        if not history:
            st.info("No status history yet.")
        else:
            for h in history:
                actor_name = h.actor.display_name if h.actor else "System"
                arrow = f"{h.old_status} → " if h.old_status else ""
                st.markdown(
                    f"""
                    <div style="display:flex;gap:12px;align-items:flex-start;
                                margin-bottom:10px;padding:10px;
                                background:#F8FAFC;border-radius:8px;
                                border-left:3px solid #4F46E5;">
                      <div style="flex-shrink:0;font-size:0.75rem;color:#64748B;
                                  min-width:130px;">{fmt_dt(h.created_at)}</div>
                      <div>
                        <span style="font-weight:600;color:#1E293B;">
                          {arrow}<strong>{h.new_status}</strong></span><br/>
                        <span style="font-size:0.82rem;color:#64748B;">
                          by {actor_name}</span>
                        {('<br/><span style="font-size:0.82rem;color:#475569;">' + h.notes + '</span>') if h.notes else ''}
                      </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

        # ─── Comments ─────────────────────────────────────────────────────────
        st.markdown("---")
        st.markdown("#### 💬 Discussion")

        comments = (
            db.query(ComplaintComment)
            .filter_by(complaint_id=complaint_id)
            .order_by(ComplaintComment.created_at)
            .all()
        )
        if not comments:
            st.info("No comments yet. Be the first to comment.")
        else:
            for cm in comments:
                if cm.is_moderated and not is_admin():
                    continue
                author_name = cm.author.display_name if cm.author else "Unknown"
                author_role = cm.author.role.value.upper() if cm.author else ""
                border_color = "#4F46E5" if cm.is_official else "#E2E8F0"
                bg_color = "#EEF2FF" if cm.is_official else "#FFFFFF"
                official_label = (
                    '<span style="background:#4F46E5;color:#FFF;padding:1px 7px;'
                    'border-radius:8px;font-size:0.72rem;margin-left:6px;">'
                    'Official Update</span>'
                ) if cm.is_official else ""
                moderated_label = (
                    '<span style="background:#FEF2F2;color:#DC2626;padding:1px 7px;'
                    'border-radius:8px;font-size:0.72rem;margin-left:6px;">'
                    '[Moderated]</span>'
                ) if cm.is_moderated else ""

                st.markdown(
                    f"""
                    <div style="border:1px solid {border_color};background:{bg_color};
                                border-radius:8px;padding:12px 16px;margin-bottom:8px;">
                      <div style="display:flex;justify-content:space-between;
                                  align-items:center;margin-bottom:6px;">
                        <span style="font-weight:600;color:#1E293B;font-size:0.88rem;">
                          {author_name}
                          <span style="background:#F1F5F9;color:#64748B;padding:1px 6px;
                                       border-radius:6px;font-size:0.7rem;margin-left:4px;">
                            {author_role}</span>
                          {official_label}{moderated_label}
                        </span>
                        <span style="font-size:0.75rem;color:#94A3B8;">
                          {fmt_dt(cm.created_at)}</span>
                      </div>
                      <div style="color:#334155;font-size:0.9rem;">
                        {'<em style="color:#94A3B8;">[This comment has been moderated.]</em>' if cm.is_moderated else cm.content}
                      </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

                # Admin moderate button
                if is_admin() and not cm.is_moderated:
                    if st.button(f"🚫 Moderate", key=f"mod_{cm.id}"):
                        ok, msg = moderate_comment(db, cm.id, user.id)
                        if ok:
                            st.success(msg)
                        else:
                            st.error(msg)
                        st.rerun()

        # Add comment
        if is_logged_in():
            is_official = role in (UserRole.caretaker, UserRole.admin)
            with st.form(f"comment_form_{complaint_id}"):
                label = "Add an official update" if is_official else "Add a comment"
                content = st.text_area(label, placeholder="Type your comment…", height=80)
                posted = st.form_submit_button(
                    "Post official update" if is_official else "Post comment",
                    use_container_width=True,
                )
            if posted:
                if content.strip():
                    ok, msg = add_comment(db, complaint_id, user.id,
                                          content, is_official=is_official)
                    if ok:
                        st.success(msg)
                    else:
                        st.error(msg)
                    st.rerun()
                else:
                    st.warning("Please enter a comment.")

        # ─── Resolution photos ────────────────────────────────────────────────
        res_photos = [a for a in complaint.attachments
                      if a.attachment_type == "resolution_photo"]
        if res_photos:
            st.markdown("---")
            st.markdown("#### 📷 Resolution Evidence")
            rcols = st.columns(min(3, len(res_photos)))
            for i, att in enumerate(res_photos):
                p = Path(att.storage_path)
                if p.exists():
                    with rcols[i % 3]:
                        st.image(str(p), caption=att.filename, use_column_width=True)

        # Upload resolution photo (caretaker/admin)
        if is_logged_in() and role in (UserRole.caretaker, UserRole.admin):
            if complaint.status in (ComplaintStatus.in_progress, ComplaintStatus.resolved):
                with st.expander("📷 Upload resolution photo"):
                    res_file = st.file_uploader("Resolution photo",
                                                type=["jpg", "jpeg", "png", "webp"])
                    if res_file and st.button("Upload"):
                        from src.utils.complaints import save_attachment
                        ok, msg = save_attachment(
                            db, complaint_id=complaint_id, uploader_id=user.id,
                            file_bytes=res_file.read(), filename=res_file.name,
                            mime_type=res_file.type, attachment_type="resolution_photo")
                        if ok:
                            st.success("Photo uploaded.")
                        else:
                            st.error(msg)
                        st.rerun()

    finally:
        db.close()
