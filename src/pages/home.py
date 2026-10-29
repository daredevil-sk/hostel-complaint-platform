"""
Home / landing page.
"""

import streamlit as st
from src.components.ui import demo_banner, page_header
from src.utils.auth import is_logged_in, get_role
from src.db.models import UserRole
import os


def render():
    if os.getenv("DEMO_MODE", "true").lower() == "true":
        demo_banner()

    # Hero section
    st.markdown(
        """
        <div style="text-align:center;padding:40px 20px 24px 20px;">
          <div style="font-size:3rem;margin-bottom:8px;">🏛️</div>
          <h1 style="color:#1E293B;font-size:2.2rem;margin-bottom:8px;">Team R</h1>
          <p style="color:#4F46E5;font-size:1.2rem;font-weight:600;margin-bottom:16px;">
            Hostel Grievance &amp; Accountability Platform</p>
          <div style="background:#EEF2FF;border-left:4px solid #4F46E5;
                      border-radius:8px;padding:16px 24px;max-width:600px;
                      margin:0 auto 24px auto;text-align:left;">
            <p style="font-size:1.1rem;font-style:italic;color:#1E293B;margin:0;">
              "One complaint gets ignored. A hundred can't be."</p>
          </div>
          <p style="color:#64748B;font-size:0.95rem;max-width:580px;margin:0 auto 32px auto;">
            This platform consolidates recurring hostel issues — water shortages, broken
            fixtures, hygiene problems — into a single transparent system. Students add
            community support to issues that matter, and caretakers are publicly accountable
            for every response.
          </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Feature cards
    cols = st.columns(3)
    features = [
        ("📢", "Report Issues", "Submit complaints with photos and location details. Get a unique complaint ID instantly."),
        ("👥", "Community Support", "See how many students share your problem. Add your support to existing complaints."),
        ("📊", "Transparent Tracking", "Every complaint has a visible timeline — submitted, seen, acknowledged, resolved."),
    ]
    for col, (emoji, title, desc) in zip(cols, features):
        with col:
            st.markdown(
                f"""
                <div style="text-align:center;padding:20px;border:1px solid #E2E8F0;
                            border-radius:12px;background:#FFFFFF;
                            box-shadow:0 1px 3px rgba(0,0,0,0.06);height:100%;">
                  <div style="font-size:2rem;margin-bottom:8px;">{emoji}</div>
                  <h3 style="color:#1E293B;font-size:1rem;margin-bottom:8px;">{title}</h3>
                  <p style="color:#64748B;font-size:0.85rem;margin:0;">{desc}</p>
                </div>
                """,
                unsafe_allow_html=True,
            )

    st.markdown("<br/>", unsafe_allow_html=True)

    # CTA buttons
    if not is_logged_in():
        c1, c2, c3 = st.columns([1, 2, 1])
        with c2:
            if st.button("🔑 Sign In", use_container_width=True, type="primary"):
                st.session_state["page"] = "login"
                st.rerun()
            if st.button("📝 Create Account", use_container_width=True):
                st.session_state["page"] = "register"
                st.rerun()
            if st.button("📋 Browse Public Board", use_container_width=True):
                st.session_state["page"] = "board"
                st.rerun()
    else:
        role = get_role()
        c1, c2, c3 = st.columns([1, 2, 1])
        with c2:
            if st.button("📋 View Complaint Board", use_container_width=True, type="primary"):
                st.session_state["page"] = "board"
                st.rerun()
            if role == UserRole.student:
                if st.button("➕ Submit a Complaint", use_container_width=True):
                    st.session_state["page"] = "submit"
                    st.rerun()
            elif role == UserRole.caretaker:
                if st.button("📊 My Dashboard", use_container_width=True):
                    st.session_state["page"] = "caretaker_dashboard"
                    st.rerun()
            elif role == UserRole.admin:
                if st.button("📊 Admin Dashboard", use_container_width=True):
                    st.session_state["page"] = "admin_dashboard"
                    st.rerun()

    # How it works
    st.markdown("---")
    st.markdown(
        """
        <h3 style="color:#1E293B;text-align:center;margin-bottom:20px;">How it works</h3>
        """,
        unsafe_allow_html=True,
    )
    steps = [
        ("1", "Student submits a complaint with photo and location"),
        ("2", "Other students see it and add their support"),
        ("3", "Caretaker is assigned and marks it as seen"),
        ("4", "Progress is tracked: Acknowledged → In Progress → Resolved"),
        ("5", "Student confirms resolution or reopens if needed"),
    ]
    for num, desc in steps:
        st.markdown(
            f"""
            <div style="display:flex;align-items:center;gap:12px;
                        padding:10px 16px;margin-bottom:8px;
                        background:#F8FAFC;border-radius:8px;">
              <span style="background:#4F46E5;color:#FFF;border-radius:50%;
                           width:28px;height:28px;display:flex;align-items:center;
                           justify-content:center;font-size:0.85rem;font-weight:700;
                           flex-shrink:0;">{num}</span>
              <span style="color:#334155;font-size:0.9rem;">{desc}</span>
            </div>
            """,
            unsafe_allow_html=True,
        )
