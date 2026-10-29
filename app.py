"""
Team R — Hostel Grievance & Accountability Platform
Main Streamlit application entry point.

Run with:
    streamlit run app.py
"""

import os
import sys

# Ensure project root is in the Python path when running from any directory
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import streamlit as st

# Safe environment loading (works with or without python-dotenv)
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    from src.utils.env_loader import load_env
    load_env()

# ─── Page config (must be first Streamlit call) ───────────────────────────────
st.set_page_config(
    page_title="Team R — Hostel Grievance Platform",
    page_icon="🏛️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─── Initialise database ──────────────────────────────────────────────────────
from src.db.database import init_db
init_db()

# ─── Global CSS ───────────────────────────────────────────────────────────────
st.markdown(
    """
    <style>
    /* Remove Streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}

    /* Typography */
    html, body, [class*="css"] {
        font-family: 'Inter', 'Segoe UI', system-ui, sans-serif;
    }

    /* Form inputs */
    .stTextInput > div > div > input,
    .stTextArea > div > div > textarea,
    .stSelectbox > div > div > div {
        border-radius: 8px !important;
    }

    /* Buttons */
    .stButton > button {
        border-radius: 8px !important;
        font-weight: 500 !important;
    }

    /* Sidebar */
    section[data-testid="stSidebar"] {
        background: #F8FAFC;
        border-right: 1px solid #E2E8F0;
    }

    /* Expanders */
    details > summary {
        border-radius: 8px !important;
    }

    /* Remove padding in mobile */
    .block-container {
        padding-top: 1rem !important;
        padding-bottom: 2rem !important;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# ─── Session state initialisation ────────────────────────────────────────────
if "page" not in st.session_state:
    st.session_state["page"] = "home"
if "current_user" not in st.session_state:
    st.session_state["current_user"] = None

# ─── Navigation ───────────────────────────────────────────────────────────────
from src.components.ui import sidebar_nav

current_page = st.session_state.get("page", "home")
sidebar_nav(current_page)

# ─── Route to page ────────────────────────────────────────────────────────────
if current_page == "home":
    from src.pages import home
    home.render()

elif current_page == "login":
    from src.pages.auth import render_login
    render_login()

elif current_page == "register":
    from src.pages.auth import render_register
    render_register()

elif current_page == "board":
    from src.pages import board
    board.render()

elif current_page == "submit":
    from src.pages import submit
    submit.render()

elif current_page == "complaint_detail":
    from src.pages import complaint_detail
    complaint_detail.render()

elif current_page == "my_complaints":
    from src.pages import my_complaints
    my_complaints.render()

elif current_page == "caretaker_dashboard":
    from src.pages import caretaker_dashboard
    caretaker_dashboard.render()

elif current_page == "admin_dashboard":
    from src.pages import admin_dashboard
    admin_dashboard.render()

elif current_page == "analytics":
    from src.pages import analytics
    analytics.render()

elif current_page == "notifications":
    # Inline notifications page (simple)
    from src.utils.auth import require_login, get_current_user
    from src.utils.complaints import get_notifications, mark_notifications_read
    from src.db.database import get_db
    from src.components.ui import page_header, empty_state, fmt_dt

    require_login()
    user = get_current_user()
    db = get_db()
    try:
        page_header("🔔 Notifications")
        notifs = get_notifications(db, user.id, limit=50)
        if notifs:
            if st.button("✅ Mark all as read"):
                mark_notifications_read(db, user.id)
                st.rerun()
        if not notifs:
            empty_state("No notifications.", "🔔")
        else:
            for n in notifs:
                bg = "#F8FAFC" if n.is_read else "#EEF2FF"
                st.markdown(
                    f"""<div style="background:{bg};border:1px solid #E2E8F0;
                                    border-radius:8px;padding:10px 14px;margin-bottom:6px;">
                      <div style="font-size:0.8rem;color:#94A3B8;">{fmt_dt(n.created_at)}</div>
                      <div>{n.message}</div>
                    </div>""",
                    unsafe_allow_html=True,
                )
                if n.complaint_id:
                    if st.button("View →", key=f"notif_{n.id}"):
                        st.session_state["selected_complaint_id"] = n.complaint_id
                        st.session_state["page"] = "complaint_detail"
                        st.rerun()
    finally:
        db.close()

else:
    st.error(f"Unknown page: {current_page}")
    if st.button("← Go Home"):
        st.session_state["page"] = "home"
        st.rerun()
