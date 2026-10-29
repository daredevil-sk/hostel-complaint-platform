"""
Reusable UI components.
"""

from __future__ import annotations
import streamlit as st
from datetime import datetime
from src.db.models import Complaint, ComplaintStatus, Priority, UserRole


# ─── Status badge colours ────────────────────────────────────────────────────

STATUS_COLORS = {
    "Submitted":    ("#EEF2FF", "#4F46E5"),
    "Acknowledged": ("#FFF7ED", "#EA580C"),
    "Assigned":     ("#F0FDF4", "#16A34A"),
    "In Progress":  ("#FFFBEB", "#D97706"),
    "Resolved":     ("#F0FDF4", "#15803D"),
    "Reopened":     ("#FFF1F2", "#E11D48"),
    "Closed":       ("#F1F5F9", "#64748B"),
}

PRIORITY_COLORS = {
    "Low":    ("#F0FDF4", "#16A34A"),
    "Medium": ("#FFFBEB", "#D97706"),
    "High":   ("#FFF7ED", "#EA580C"),
    "Urgent": ("#FFF1F2", "#E11D48"),
}

PRIORITY_EMOJI = {
    "Low": "🟢", "Medium": "🟡", "High": "🟠", "Urgent": "🔴",
}

STATUS_EMOJI = {
    "Submitted": "📥",
    "Acknowledged": "✅",
    "Assigned": "👷",
    "In Progress": "🔧",
    "Resolved": "✔️",
    "Reopened": "🔄",
    "Closed": "🔒",
}


def status_badge(status: str) -> str:
    bg, fg = STATUS_COLORS.get(status, ("#F1F5F9", "#334155"))
    emoji = STATUS_EMOJI.get(status, "")
    return (
        f'<span style="background:{bg};color:{fg};padding:3px 10px;'
        f'border-radius:12px;font-size:0.78rem;font-weight:600;">'
        f'{emoji} {status}</span>'
    )


def priority_badge(priority: str) -> str:
    bg, fg = PRIORITY_COLORS.get(priority, ("#F1F5F9", "#334155"))
    emoji = PRIORITY_EMOJI.get(priority, "")
    return (
        f'<span style="background:{bg};color:{fg};padding:3px 10px;'
        f'border-radius:12px;font-size:0.78rem;font-weight:600;">'
        f'{emoji} {priority}</span>'
    )


def seen_badge(is_seen: bool, acknowledged: bool = False) -> str:
    if acknowledged:
        return (
            '<span style="background:#F0FDF4;color:#15803D;padding:3px 10px;'
            'border-radius:12px;font-size:0.78rem;font-weight:600;">👁️ Acknowledged</span>'
        )
    if is_seen:
        return (
            '<span style="background:#EFF6FF;color:#1D4ED8;padding:3px 10px;'
            'border-radius:12px;font-size:0.78rem;font-weight:600;">👁️ Seen by caretaker</span>'
        )
    return (
        '<span style="background:#FFF1F2;color:#BE123C;padding:3px 10px;'
        'border-radius:12px;font-size:0.78rem;font-weight:600;">👁️ Not yet seen</span>'
    )


def fmt_dt(dt: datetime | None, default: str = "—") -> str:
    if dt is None:
        return default
    return dt.strftime("%d %b %Y, %I:%M %p")


def complaint_card(c: Complaint, is_seen: bool = False,
                   ack=None, show_details_button: bool = True):
    """Render a compact complaint card."""
    status_str = c.status.value if c.status else "Submitted"
    priority_str = c.priority.value if c.priority else "Medium"
    cat_str = c.category.value if c.category else "Other"

    with st.container():
        st.markdown(
            f"""
            <div style="border:1px solid #E2E8F0;border-radius:12px;padding:16px 20px;
                        margin-bottom:12px;background:#FFFFFF;
                        box-shadow:0 1px 3px rgba(0,0,0,0.06);">
              <div style="display:flex;justify-content:space-between;align-items:flex-start;
                          flex-wrap:wrap;gap:8px;">
                <div>
                  <span style="font-size:0.75rem;color:#64748B;font-weight:500;">
                    {c.complaint_number}</span>
                  <h4 style="margin:4px 0 8px 0;color:#1E293B;font-size:1rem;">
                    {c.title}</h4>
                  <div style="display:flex;flex-wrap:wrap;gap:6px;margin-bottom:8px;">
                    {status_badge(status_str)}
                    {priority_badge(priority_str)}
                    {seen_badge(is_seen, ack and ack.acknowledged_at is not None)}
                  </div>
                </div>
                <div style="text-align:right;font-size:0.78rem;color:#64748B;">
                  <div>🏠 {c.hostel} {('• ' + c.block) if c.block else ''}</div>
                  <div>📁 {cat_str}</div>
                  <div>🗓️ {fmt_dt(c.created_at)}</div>
                </div>
              </div>
              <div style="display:flex;align-items:center;gap:12px;
                          font-size:0.82rem;color:#64748B;margin-top:4px;">
                <span>👥 {c.vote_count} supporter{'s' if c.vote_count != 1 else ''}</span>
                <span>🕐 Updated {fmt_dt(c.updated_at)}</span>
              </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        if show_details_button:
            if st.button(f"View details →", key=f"view_{c.id}"):
                st.session_state["selected_complaint_id"] = c.id
                st.session_state["page"] = "complaint_detail"
                st.rerun()


def demo_banner():
    st.markdown(
        """
        <div style="background:#FFFBEB;border:1px solid #F59E0B;border-radius:8px;
                    padding:10px 16px;margin-bottom:16px;font-size:0.88rem;color:#92400E;">
          ⚠️ <strong>Demo Mode:</strong> This environment uses sample data for demonstration
          purposes. All users, complaints, and interactions shown are fictional.
        </div>
        """,
        unsafe_allow_html=True,
    )


def page_header(title: str, subtitle: str = ""):
    st.markdown(
        f"""
        <div style="padding:8px 0 20px 0;">
          <h1 style="color:#1E293B;margin-bottom:4px;">{title}</h1>
          {f'<p style="color:#64748B;font-size:1rem;margin:0;">{subtitle}</p>' if subtitle else ''}
        </div>
        """,
        unsafe_allow_html=True,
    )


def empty_state(message: str = "No complaints found.", emoji: str = "🔍"):
    st.markdown(
        f"""
        <div style="text-align:center;padding:48px 20px;color:#94A3B8;">
          <div style="font-size:3rem;">{emoji}</div>
          <p style="font-size:1rem;margin-top:12px;">{message}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def sidebar_nav(current_page: str):
    """Render sidebar navigation."""
    from src.utils.auth import get_current_user, is_logged_in, logout, get_role
    from src.db.database import get_db
    from src.utils.complaints import get_notifications

    user = get_current_user()

    with st.sidebar:
        st.markdown(
            """
            <div style="text-align:center;padding:16px 0 8px 0;">
              <div style="font-size:1.8rem;">🏛️</div>
              <div style="font-weight:700;color:#1E293B;font-size:1.1rem;">Team R</div>
              <div style="font-size:0.72rem;color:#64748B;">
                Hostel Grievance & Accountability Platform</div>
              <div style="font-size:0.65rem;color:#94A3B8;margin-top:2px;">IIT Patna</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.markdown("---")

        if is_logged_in():
            role = get_role()
            db = get_db()
            try:
                notifs = get_notifications(db, user.id, unread_only=True, limit=5)
                unread_count = len(notifs)
            except Exception:
                unread_count = 0
            finally:
                db.close()

            notif_badge = f" 🔔{unread_count}" if unread_count > 0 else ""
            st.markdown(
                f"""<div style="font-size:0.82rem;color:#64748B;padding:4px 0;">
                  Signed in as <strong>{user.display_name}</strong>
                  <br/><span style="background:#EEF2FF;color:#4F46E5;padding:2px 8px;
                  border-radius:8px;font-size:0.7rem;">{role.value.upper()}</span>
                </div>""",
                unsafe_allow_html=True,
            )
            st.markdown("---")

            nav_items = [
                ("🏠", "Home", "home"),
                ("📋", f"Complaint Board{notif_badge}", "board"),
            ]

            if role == UserRole.student:
                nav_items += [
                    ("➕", "Submit Complaint", "submit"),
                    ("📁", "My Complaints", "my_complaints"),
                    ("🔔", f"Notifications{notif_badge}", "notifications"),
                ]
            elif role == UserRole.caretaker:
                nav_items += [
                    ("📊", "My Dashboard", "caretaker_dashboard"),
                    ("🔔", f"Notifications{notif_badge}", "notifications"),
                ]
            elif role == UserRole.admin:
                nav_items += [
                    ("📊", "Admin Dashboard", "admin_dashboard"),
                    ("➕", "Submit Complaint", "submit"),
                    ("📈", "Analytics", "analytics"),
                    ("🔔", f"Notifications{notif_badge}", "notifications"),
                ]

            for emoji, label, page_key in nav_items:
                is_active = current_page == page_key
                btn_style = (
                    "background:#EEF2FF;color:#4F46E5;font-weight:600;"
                    if is_active else ""
                )
                if st.button(f"{emoji} {label}", key=f"nav_{page_key}",
                             use_container_width=True):
                    st.session_state["page"] = page_key
                    st.rerun()

            st.markdown("---")
            if st.button("🚪 Sign Out", use_container_width=True):
                logout()
                st.session_state["page"] = "home"
                st.rerun()
        else:
            if st.button("🔑 Sign In", use_container_width=True):
                st.session_state["page"] = "login"
                st.rerun()
            if st.button("📝 Register", use_container_width=True):
                st.session_state["page"] = "register"
                st.rerun()

        # Always show board
        st.markdown("---")
        if st.button("📋 Public Board", use_container_width=True):
            st.session_state["page"] = "board"
            st.rerun()

        import os
        if os.getenv("DEMO_MODE", "true").lower() == "true":
            st.markdown(
                '<div style="font-size:0.7rem;color:#94A3B8;text-align:center;'
                'padding-top:8px;">⚠️ Demo Environment</div>',
                unsafe_allow_html=True,
            )
