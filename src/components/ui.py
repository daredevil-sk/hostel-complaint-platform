"""
Reusable UI components — dark mode edition.
"""

from __future__ import annotations
import streamlit as st
from datetime import datetime, timezone, timedelta
from src.db.models import Complaint, ComplaintStatus, Priority, UserRole

# IST offset
_IST = timedelta(hours=5, minutes=30)


# ─── Status / Priority colours (dark-mode friendly) ─────────────────────────

STATUS_COLORS = {
    "Submitted":    ("#1e2d4a", "#818CF8"),
    "Acknowledged": ("#2a1f0e", "#FBBF24"),
    "Assigned":     ("#0d2218", "#34D399"),
    "In Progress":  ("#1e2510", "#86EFAC"),
    "Resolved":     ("#0d2218", "#34D399"),
    "Reopened":     ("#2a0f1a", "#F87171"),
    "Closed":       ("#1a1f2e", "#64748B"),
}

PRIORITY_COLORS = {
    "Low":    ("#0d2218", "#34D399"),
    "Medium": ("#2a1f0e", "#FBBF24"),
    "High":   ("#2a1500", "#FB923C"),
    "Urgent": ("#2a0f1a", "#F87171"),
}


def status_badge(status: str) -> str:
    bg, fg = STATUS_COLORS.get(status, ("#1a1f2e", "#94A3B8"))
    return (
        f'<span style="background:{bg};color:{fg};padding:3px 10px;'
        f'border-radius:12px;font-size:0.78rem;font-weight:600;'
        f'border:1px solid {fg}40;">'
        f'{status}</span>'
    )


def priority_badge(priority: str) -> str:
    bg, fg = PRIORITY_COLORS.get(priority, ("#1a1f2e", "#94A3B8"))
    return (
        f'<span style="background:{bg};color:{fg};padding:3px 10px;'
        f'border-radius:12px;font-size:0.78rem;font-weight:600;'
        f'border:1px solid {fg}40;">'
        f'{priority}</span>'
    )


def seen_badge(is_seen: bool, acknowledged: bool = False) -> str:
    if acknowledged:
        return (
            '<span style="background:#0d2218;color:#34D399;padding:3px 10px;'
            'border-radius:12px;font-size:0.78rem;font-weight:600;'
            'border:1px solid #34D39940;">Acknowledged</span>'
        )
    if is_seen:
        return (
            '<span style="background:#1e2d4a;color:#818CF8;padding:3px 10px;'
            'border-radius:12px;font-size:0.78rem;font-weight:600;'
            'border:1px solid #818CF840;">Seen by caretaker</span>'
        )
    return (
        '<span style="background:#2a0f1a;color:#F87171;padding:3px 10px;'
        'border-radius:12px;font-size:0.78rem;font-weight:600;'
        'border:1px solid #F8717140;">Not yet seen</span>'
    )


def fmt_dt(dt: datetime | None, default: str = "—") -> str:
    """Format datetime in IST (UTC+5:30)."""
    if dt is None:
        return default
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    ist_dt = dt.astimezone(timezone(_IST))
    return ist_dt.strftime("%d %b %Y, %I:%M %p IST")


def complaint_card(c: Complaint, is_seen: bool = False,
                   ack=None, show_details_button: bool = True):
    """Render a compact complaint card (dark mode)."""
    status_str = c.status.value if c.status else "Submitted"
    priority_str = c.priority.value if c.priority else "Medium"
    cat_str = c.category.value if c.category else "Other"
    anon = getattr(c, "is_anonymous", False)
    submitter_label = "Anonymous" if anon else ""

    with st.container():
        st.markdown(
            f"""
            <div style="border:1px solid #334155;border-radius:12px;padding:16px 20px;
                        margin-bottom:10px;background:#1E293B;
                        box-shadow:0 2px 8px rgba(0,0,0,0.3);">
              <div style="display:flex;justify-content:space-between;align-items:flex-start;
                          flex-wrap:wrap;gap:8px;">
                <div style="flex:1;min-width:0;">
                  <span style="font-size:0.73rem;color:#64748B;font-weight:500;
                               letter-spacing:0.05em;">{c.complaint_number}</span>
                  {"<span style='font-size:0.7rem;color:#FBBF24;margin-left:8px;'>Anonymous</span>" if anon else ""}
                  <h4 style="margin:4px 0 10px 0;color:#E2E8F0;font-size:0.97rem;
                             white-space:nowrap;overflow:hidden;text-overflow:ellipsis;">
                    {c.title}</h4>
                  <div style="display:flex;flex-wrap:wrap;gap:6px;margin-bottom:8px;">
                    {status_badge(status_str)}
                    {priority_badge(priority_str)}
                    {seen_badge(is_seen, ack and ack.acknowledged_at is not None)}
                  </div>
                </div>
                <div style="text-align:right;font-size:0.78rem;color:#64748B;
                            flex-shrink:0;padding-left:12px;">
                  <div>{c.hostel}{(' · ' + c.block) if c.block else ''}</div>
                  <div>{cat_str}</div>
                  <div>{fmt_dt(c.created_at)}</div>
                </div>
              </div>
              <div style="display:flex;align-items:center;gap:16px;
                          font-size:0.82rem;color:#64748B;margin-top:4px;
                          border-top:1px solid #334155;padding-top:8px;">
                <span>{c.vote_count} supporter{"s" if c.vote_count != 1 else ""}</span>
                <span>Updated {fmt_dt(c.updated_at)}</span>
              </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        if show_details_button:
            if st.button("View details", key=f"view_{c.id}",
                         use_container_width=True):
                st.session_state["selected_complaint_id"] = c.id
                st.session_state["page"] = "complaint_detail"
                st.rerun()


def page_header(title: str, subtitle: str = ""):
    st.markdown(
        f"""
        <div style="padding:4px 0 20px 0;">
          <h1 style="color:#E2E8F0;margin-bottom:4px;font-size:1.8rem;">{title}</h1>
          {f'<p style="color:#94A3B8;font-size:0.95rem;margin:0;">{subtitle}</p>' if subtitle else ''}
        </div>
        """,
        unsafe_allow_html=True,
    )


def empty_state(message: str = "No complaints found.", icon: str = ""):
    st.markdown(
        f"""
        <div style="text-align:center;padding:48px 20px;color:#475569;">
          {f'<div style="font-size:2.5rem;margin-bottom:12px;">{icon}</div>' if icon else ''}
          <p style="font-size:1rem;margin-top:8px;color:#64748B;">{message}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def back_button(label: str = "Back", target_page: str = "board", key: str = "back_btn"):
    """Render a consistent back button."""
    if st.button(f"← {label}", key=key):
        st.session_state["page"] = target_page
        st.rerun()


def sidebar_nav(current_page: str):
    """Render sidebar navigation (dark mode)."""
    from src.utils.auth import get_current_user, is_logged_in, logout, get_role
    from src.db.database import get_db
    from src.utils.complaints import get_notifications

    user = get_current_user()

    with st.sidebar:
        st.markdown(
            """
            <div style="text-align:center;padding:16px 0 8px 0;">
              <div style="font-weight:700;color:#E2E8F0;font-size:1.2rem;
                          letter-spacing:0.02em;">Hostel Grievances</div>
              <div style="font-size:0.72rem;color:#64748B;margin-top:2px;">IIT Patna</div>
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

            notif_badge = f" ({unread_count} new)" if unread_count > 0 else ""
            st.markdown(
                f"""<div style="font-size:0.82rem;color:#94A3B8;padding:4px 0;">
                  Signed in as <strong style="color:#CBD5E1;">{user.display_name}</strong>
                  <br/><span style="background:#312e81;color:#A5B4FC;padding:2px 8px;
                  border-radius:8px;font-size:0.7rem;">{role.value.upper()}</span>
                </div>""",
                unsafe_allow_html=True,
            )
            st.markdown("---")

            nav_items = [
                ("Home", "home"),
                (f"Complaint Board", "board"),
            ]

            if role == UserRole.student:
                nav_items += [
                    ("Submit Complaint", "submit"),
                    ("My Complaints", "my_complaints"),
                    (f"Notifications{notif_badge}", "notifications"),
                ]
            elif role == UserRole.caretaker:
                nav_items += [
                    ("My Dashboard", "caretaker_dashboard"),
                    (f"Notifications{notif_badge}", "notifications"),
                ]
            elif role == UserRole.admin:
                nav_items += [
                    ("Admin Dashboard", "admin_dashboard"),
                    ("Submit Complaint", "submit"),
                    ("Analytics", "analytics"),
                    (f"Notifications{notif_badge}", "notifications"),
                ]

            for label, page_key in nav_items:
                is_active = current_page == page_key
                btn_type = "primary" if is_active else "secondary"
                if st.button(label, key=f"nav_{page_key}",
                             use_container_width=True,
                             type="primary" if is_active else "secondary"):
                    st.session_state["page"] = page_key
                    # On mobile, collapse sidebar by setting state
                    st.session_state["_sidebar_collapsed"] = True
                    st.rerun()

            st.markdown("---")
            if st.button("Sign Out", use_container_width=True):
                logout()
                st.session_state["page"] = "home"
                st.rerun()
        else:
            if st.button("Sign In", use_container_width=True, type="primary"):
                st.session_state["page"] = "login"
                st.rerun()
            if st.button("Create Account", use_container_width=True):
                st.session_state["page"] = "register"
                st.rerun()

        # Always show public board
        st.markdown("---")
        if st.button("Public Board", use_container_width=True):
            st.session_state["page"] = "board"
            st.rerun()


# Legacy alias kept for backward compat
def demo_banner():
    """No-op: demo banners removed per user feedback."""
    pass
