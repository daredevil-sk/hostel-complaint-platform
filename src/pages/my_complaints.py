"""
Student dashboard — my complaints, my votes, notifications.
"""

from __future__ import annotations

import streamlit as st
from src.db.database import get_db
from src.db.models import ComplaintVote, UserRole
from src.utils.auth import require_role, get_current_user
from src.utils.complaints import (
    list_complaints, get_seen_status, get_notifications, mark_notifications_read,
)
from src.components.ui import (
    complaint_card, empty_state, page_header, status_badge, fmt_dt,
)


def render():
    require_role(UserRole.student)
    user = get_current_user()
    db = get_db()
    try:
        page_header("📁 My Complaints", f"Your submissions and supported issues, {user.display_name}")

        tab_mine, tab_voted, tab_notifs = st.tabs(
            ["📋 My Submissions", "👍 Complaints I Support", "🔔 Notifications"])

        with tab_mine:
            complaints, total = list_complaints(
                db, submitter_id=user.id, include_private=True, sort_by="newest",
                page=1, page_size=50)
            if not complaints:
                empty_state("You haven't submitted any complaints yet.", "📭")
            else:
                st.markdown(f"**{total} complaint{'s' if total != 1 else ''}**")
                for c in complaints:
                    is_seen, ack = get_seen_status(db, c.id)
                    complaint_card(c, is_seen=is_seen, ack=ack)

        with tab_voted:
            voted_ids = [v.complaint_id for v in
                         db.query(ComplaintVote).filter_by(student_id=user.id).all()]
            if not voted_ids:
                empty_state("You haven't supported any complaints yet.", "👍")
            else:
                from src.db.models import Complaint
                voted_complaints = (
                    db.query(Complaint)
                    .filter(Complaint.id.in_(voted_ids))
                    .order_by(Complaint.updated_at.desc())
                    .all()
                )
                st.markdown(f"**{len(voted_complaints)} complaint{'s' if len(voted_complaints) != 1 else ''}**")
                for c in voted_complaints:
                    is_seen, ack = get_seen_status(db, c.id)
                    complaint_card(c, is_seen=is_seen, ack=ack)

        with tab_notifs:
            notifs = get_notifications(db, user.id, limit=30)
            if notifs:
                if st.button("✅ Mark all as read"):
                    mark_notifications_read(db, user.id)
                    st.rerun()
            if not notifs:
                empty_state("No notifications.", "🔔")
            else:
                for n in notifs:
                    bg = "#F8FAFC" if n.is_read else "#EEF2FF"
                    border = "#E2E8F0" if n.is_read else "#A5B4FC"
                    st.markdown(
                        f"""
                        <div style="background:{bg};border:1px solid {border};
                                    border-radius:8px;padding:10px 14px;margin-bottom:6px;">
                          <div style="font-size:0.82rem;color:#64748B;">{fmt_dt(n.created_at)}</div>
                          <div style="color:#1E293B;font-size:0.9rem;">{n.message}</div>
                          {'<span style="font-size:0.72rem;color:#4F46E5;">NEW</span>' if not n.is_read else ''}
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )
                    if n.complaint_id:
                        if st.button(f"View complaint →", key=f"notif_view_{n.id}"):
                            st.session_state["selected_complaint_id"] = n.complaint_id
                            st.session_state["page"] = "complaint_detail"
                            st.rerun()
    finally:
        db.close()
