"""
Hostel Grievance & Accountability Platform
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
    page_title="Hostel Grievance Platform",
    page_icon="H",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─── Initialise database ──────────────────────────────────────────────────────
from src.db.database import init_db
init_db()

# ─── Global CSS (dark mode) ───────────────────────────────────────────────────
st.markdown(
    """
    <style>
    /* Remove Streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}

    /* Dark mode base */
    :root {
        --bg-primary: #0F172A;
        --bg-secondary: #1E293B;
        --bg-card: #1E293B;
        --bg-card-hover: #243147;
        --border: #334155;
        --text-primary: #E2E8F0;
        --text-secondary: #94A3B8;
        --text-muted: #64748B;
        --accent: #818CF8;
        --accent-dark: #6366F1;
        --success: #34D399;
        --warning: #FBBF24;
        --danger: #F87171;
    }

    /* Typography */
    html, body, [class*="css"] {
        font-family: 'Inter', 'Segoe UI', system-ui, sans-serif;
    }

    /* Main background */
    .stApp {
        background-color: #0F172A !important;
    }

    /* Main content area */
    .block-container {
        padding-top: 1.5rem !important;
        padding-bottom: 2rem !important;
        max-width: 1100px;
    }

    /* Sidebar */
    section[data-testid="stSidebar"] {
        background: #1E293B !important;
        border-right: 1px solid #334155 !important;
    }
    section[data-testid="stSidebar"] * {
        color: #CBD5E1 !important;
    }

    /* Buttons */
    .stButton > button {
        border-radius: 8px !important;
        font-weight: 500 !important;
        border: 1px solid #334155 !important;
        background: #1E293B !important;
        color: #E2E8F0 !important;
        transition: all 0.2s ease !important;
        width: 100%;
    }
    .stButton > button:hover {
        background: #243147 !important;
        border-color: #818CF8 !important;
        color: #818CF8 !important;
    }
    .stButton > button[kind="primary"] {
        background: #4F46E5 !important;
        border-color: #4F46E5 !important;
        color: #FFFFFF !important;
    }
    .stButton > button[kind="primary"]:hover {
        background: #4338CA !important;
        border-color: #4338CA !important;
        color: #FFFFFF !important;
    }

    /* Form inputs */
    .stTextInput > div > div > input,
    .stTextArea > div > div > textarea,
    .stSelectbox > div > div > div {
        border-radius: 8px !important;
        background: #0F172A !important;
        border: 1px solid #334155 !important;
        color: #E2E8F0 !important;
    }
    .stTextInput > div > div > input:focus,
    .stTextArea > div > div > textarea:focus {
        border-color: #818CF8 !important;
        box-shadow: 0 0 0 2px rgba(129,140,248,0.2) !important;
    }

    /* Expanders */
    details > summary {
        border-radius: 8px !important;
        background: #1E293B !important;
        color: #E2E8F0 !important;
    }
    details {
        background: #1E293B !important;
        border: 1px solid #334155 !important;
        border-radius: 8px !important;
    }

    /* Tabs */
    .stTabs [data-baseweb="tab-list"] {
        background: #1E293B !important;
        border-radius: 8px !important;
        padding: 4px !important;
    }
    .stTabs [data-baseweb="tab"] {
        border-radius: 6px !important;
        color: #94A3B8 !important;
        font-weight: 500 !important;
    }
    .stTabs [aria-selected="true"] {
        background: #4F46E5 !important;
        color: #FFFFFF !important;
    }

    /* Info / success / error / warning boxes */
    .stAlert {
        border-radius: 8px !important;
    }

    /* Metrics */
    [data-testid="stMetricValue"] {
        color: #818CF8 !important;
    }

    /* Divider */
    hr {
        border-color: #334155 !important;
    }

    /* Tables */
    table {
        color: #CBD5E1 !important;
    }

    /* Mobile: auto-close sidebar when nav item clicked */
    @media (max-width: 768px) {
        section[data-testid="stSidebar"] {
            z-index: 999 !important;
        }
    }

    /* Scrollbar */
    ::-webkit-scrollbar { width: 6px; }
    ::-webkit-scrollbar-track { background: #0F172A; }
    ::-webkit-scrollbar-thumb { background: #334155; border-radius: 3px; }
    ::-webkit-scrollbar-thumb:hover { background: #475569; }

    /* File uploader */
    [data-testid="stFileUploader"] {
        background: #1E293B !important;
        border: 1px dashed #334155 !important;
        border-radius: 8px !important;
    }

    /* Popover */
    [data-testid="stPopover"] {
        background: #1E293B !important;
        border: 1px solid #334155 !important;
    }

    /* Dataframe */
    [data-testid="stDataFrame"] {
        background: #1E293B !important;
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
    from src.utils.auth import require_login, get_current_user
    from src.utils.complaints import get_notifications, mark_notifications_read
    from src.db.database import get_db
    from src.components.ui import page_header, empty_state, fmt_dt

    require_login()
    user = get_current_user()
    db = get_db()
    try:
        col_back, col_title = st.columns([1, 5])
        with col_back:
            if st.button("Back", key="notif_back"):
                st.session_state["page"] = "home"
                st.rerun()
        page_header("Notifications")
        notifs = get_notifications(db, user.id, limit=50)
        if notifs:
            if st.button("Mark all as read"):
                mark_notifications_read(db, user.id)
                st.rerun()
        if not notifs:
            empty_state("No notifications.", "")
        else:
            for n in notifs:
                bg = "#1E293B" if n.is_read else "#1e2d4a"
                border = "#334155" if n.is_read else "#4F46E5"
                st.markdown(
                    f"""<div style="background:{bg};border:1px solid {border};
                                    border-radius:8px;padding:10px 14px;margin-bottom:6px;">
                      <div style="font-size:0.8rem;color:#94A3B8;">{fmt_dt(n.created_at)}</div>
                      <div style="color:#E2E8F0;">{n.message}</div>
                    </div>""",
                    unsafe_allow_html=True,
                )
                if n.complaint_id:
                    if st.button("View complaint", key=f"notif_{n.id}"):
                        st.session_state["selected_complaint_id"] = n.complaint_id
                        st.session_state["page"] = "complaint_detail"
                        st.rerun()
    finally:
        db.close()

else:
    st.error(f"Unknown page: {current_page}")
    if st.button("Go Home"):
        st.session_state["page"] = "home"
        st.rerun()
