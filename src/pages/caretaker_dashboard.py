"""
Caretaker dashboard — assigned complaints, seen/ack workflow, status updates.
"""

from __future__ import annotations

from datetime import datetime
import streamlit as st
from src.db.database import get_db
from src.db.models import (
    Complaint, ComplaintStatus, UserRole, CaretakerAcknowledgement,
)
from src.utils.auth import require_role, get_current_user
from src.utils.complaints import (
    list_complaints, get_seen_status, mark_seen, acknowledge_complaint,
    update_status, get_notifications, ALLOWED_TRANSITIONS,
)
from src.components.ui import (
    complaint_card, empty_state, page_header, status_badge, priority_badge,
    seen_badge, fmt_dt, back_button,
)


def render():
    require_role(UserRole.caretaker, UserRole.admin)
    user = get_current_user()
    role = user.role
    db = get_db()

    try:
        back_button("Home", "home", "ct_back")
        page_header("Caretaker Dashboard", f"Welcome, {user.display_name}")

        # Stats
        assigned, _ = list_complaints(db, assigned_caretaker_id=user.id,
                                       include_private=True, page=1, page_size=500)
        total_assigned = len(assigned)
        new_unseen = sum(1 for c in assigned
                         if not get_seen_status(db, c.id)[0])
        acknowledged_count = sum(
            1 for c in assigned
            if c.status == ComplaintStatus.acknowledged
        )
        in_progress_count = sum(
            1 for c in assigned
            if c.status == ComplaintStatus.in_progress
        )
        overdue_count = sum(
            1 for c in assigned
            if (c.status in (ComplaintStatus.assigned, ComplaintStatus.in_progress) and
                c.created_at and (datetime.utcnow() - c.created_at).days > 3)
        )

        m1, m2, m3, m4, m5 = st.columns(5)
        for col, label, value, color in [
            (m1, "Assigned", total_assigned, "#818CF8"),
            (m2, "New / Unseen", new_unseen, "#F87171"),
            (m3, "Acknowledged", acknowledged_count, "#FBBF24"),
            (m4, "In Progress", in_progress_count, "#60A5FA"),
            (m5, "Overdue (>3d)", overdue_count, "#C084FC"),
        ]:
            with col:
                st.markdown(
                    f"""
                    <div style="text-align:center;padding:14px 8px;background:#1E293B;
                                border:1px solid #334155;border-radius:10px;
                                border-top:3px solid {color};margin-bottom:12px;">
                      <div style="font-size:1.8rem;font-weight:700;color:{color};">
                        {value}</div>
                      <div style="font-size:0.78rem;color:#64748B;">{label}</div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

        st.markdown("<br/>", unsafe_allow_html=True)

        # Tabs
        tab_unseen, tab_assigned, tab_inprog, tab_all = st.tabs([
            "Unseen", "Assigned", "In Progress", "All"])

        def _render_complaint_list(complaints_list):
            if not complaints_list:
                empty_state("No complaints in this category.")
                return
            for c in complaints_list:
                is_seen, ack = get_seen_status(db, c.id)
                _caretaker_complaint_row(db, c, is_seen, ack, user, role)

        with tab_unseen:
            unseen = [c for c in assigned if not get_seen_status(db, c.id)[0]]
            _render_complaint_list(unseen)

        with tab_assigned:
            _render_complaint_list(
                [c for c in assigned if c.status in (
                    ComplaintStatus.submitted, ComplaintStatus.acknowledged,
                    ComplaintStatus.assigned)])

        with tab_inprog:
            _render_complaint_list(
                [c for c in assigned if c.status == ComplaintStatus.in_progress])

        with tab_all:
            _render_complaint_list(assigned)

    finally:
        db.close()


def _caretaker_complaint_row(db, complaint, is_seen, ack, user, role):
    """Render a single complaint row with inline caretaker actions."""
    unseen_label = " [UNSEEN]" if not is_seen else ""
    with st.expander(
        f"{complaint.complaint_number} — {complaint.title} "
        f"[{complaint.status.value if complaint.status else ''}]"
        f"{unseen_label}"
    ):
        c_left, c_right = st.columns([3, 1])
        with c_left:
            st.markdown(f"**{complaint.title}**")
            st.markdown(f"Location: {complaint.hostel} {complaint.block or ''} {complaint.floor or ''}")
            st.markdown(f"Category: {complaint.category.value if complaint.category else ''}")
            st.markdown(f"Submitted: {fmt_dt(complaint.created_at)}")
            st.markdown(f"Supporters: {complaint.vote_count}")
            if complaint.description:
                st.markdown(complaint.description[:300] +
                            ("..." if len(complaint.description) > 300 else ""))

        with c_right:
            st.markdown(seen_badge(is_seen, ack and ack.acknowledged_at is not None),
                        unsafe_allow_html=True)

            # Mark seen
            if not is_seen:
                if st.button("Mark as Seen", key=f"ct_seen_{complaint.id}",
                             use_container_width=True, type="primary"):
                    ok, msg = mark_seen(db, complaint.id, user.id, role)
                    if ok:
                        st.success(msg)
                    else:
                        st.error(msg)
                    st.rerun()

            # Acknowledge
            if not (ack and ack.caretaker_id == user.id and ack.acknowledged_at):
                with st.popover("Acknowledge"):
                    notes = st.text_area("Work notes", key=f"ct_ack_notes_{complaint.id}")
                    if st.button("Confirm Acknowledgement",
                                 key=f"ct_ack_{complaint.id}", type="primary"):
                        ok, msg = acknowledge_complaint(
                            db, complaint.id, user.id, role, work_notes=notes)
                        if ok:
                            st.success(msg)
                        else:
                            st.error(msg)
                        st.rerun()

            # Status update
            allowed = ALLOWED_TRANSITIONS.get(complaint.status, [])
            if allowed:
                new_s = st.selectbox("New status",
                                     [s.value for s in allowed],
                                     key=f"ct_stat_{complaint.id}")
                s_notes = st.text_input("Notes", key=f"ct_snotes_{complaint.id}")
                if st.button("Update Status", key=f"ct_upd_{complaint.id}",
                             use_container_width=True):
                    ok, msg = update_status(db, complaint.id, new_s,
                                            actor_id=user.id, actor_role=role,
                                            notes=s_notes)
                    if ok:
                        st.success(msg)
                    else:
                        st.error(msg)
                    st.rerun()

        if st.button("View full details", key=f"ct_det_{complaint.id}",
                     use_container_width=True, type="primary"):
            st.session_state["selected_complaint_id"] = complaint.id
            st.session_state["page"] = "complaint_detail"
            st.rerun()
