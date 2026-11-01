"""
Home / landing page.
"""

import streamlit as st
from src.components.ui import page_header
from src.utils.auth import is_logged_in, get_role
from src.db.models import UserRole


def render():
    # Hero section
    st.markdown(
        """
        <div style="text-align:center;padding:40px 20px 28px 20px;">
          <h1 style="color:#E2E8F0;font-size:2rem;margin-bottom:8px;font-weight:700;">
            Hostel Grievance Platform</h1>
          <p style="color:#818CF8;font-size:1.05rem;font-weight:600;margin-bottom:16px;">
            IIT Patna — Transparent. Accountable. Community-driven.</p>
          <div style="background:#1E293B;border-left:4px solid #4F46E5;
                      border-radius:8px;padding:14px 22px;max-width:560px;
                      margin:0 auto 24px auto;text-align:left;">
            <p style="font-size:1rem;font-style:italic;color:#CBD5E1;margin:0;">
              "One complaint gets ignored. A hundred can't be."</p>
          </div>
          <p style="color:#94A3B8;font-size:0.93rem;max-width:560px;margin:0 auto 32px auto;">
            Submit hostel issues, gather community support, and hold caretakers
            publicly accountable — all in one place.
          </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # CTA buttons — primary actions
    if not is_logged_in():
        c1, c2, c3 = st.columns([1, 2, 1])
        with c2:
            if st.button("Sign In", use_container_width=True, type="primary"):
                st.session_state["page"] = "login"
                st.rerun()
            st.markdown("<div style='height:6px'></div>", unsafe_allow_html=True)
            if st.button("Create Account", use_container_width=True):
                st.session_state["page"] = "register"
                st.rerun()
            st.markdown("<div style='height:6px'></div>", unsafe_allow_html=True)
            if st.button("Browse Public Board", use_container_width=True):
                st.session_state["page"] = "board"
                st.rerun()
    else:
        role = get_role()
        c1, c2, c3 = st.columns([1, 2, 1])
        with c2:
            if st.button("View Complaint Board", use_container_width=True, type="primary"):
                st.session_state["page"] = "board"
                st.rerun()
            st.markdown("<div style='height:6px'></div>", unsafe_allow_html=True)
            if role == UserRole.student:
                if st.button("Submit a Complaint", use_container_width=True):
                    st.session_state["page"] = "submit"
                    st.rerun()
                st.markdown("<div style='height:6px'></div>", unsafe_allow_html=True)
                if st.button("My Complaints", use_container_width=True):
                    st.session_state["page"] = "my_complaints"
                    st.rerun()
            elif role == UserRole.caretaker:
                if st.button("My Dashboard", use_container_width=True):
                    st.session_state["page"] = "caretaker_dashboard"
                    st.rerun()
            elif role == UserRole.admin:
                if st.button("Admin Dashboard", use_container_width=True):
                    st.session_state["page"] = "admin_dashboard"
                    st.rerun()

    st.markdown("<br/>", unsafe_allow_html=True)

    # Feature cards — each is a clickable button
    st.markdown(
        """
        <h3 style="color:#CBD5E1;text-align:center;margin-bottom:16px;
                   font-size:1.1rem;font-weight:600;">What you can do</h3>
        """,
        unsafe_allow_html=True,
    )
    cols = st.columns(3)
    features = [
        ("Report Issues", "Submit complaints with photos and location details. Get a unique complaint ID instantly.", "submit" if is_logged_in() else "login"),
        ("Community Support", "See how many students share your problem. Add your support to existing complaints.", "board"),
        ("Transparent Tracking", "Every complaint has a visible timeline — submitted, seen, acknowledged, resolved.", "board"),
    ]
    for col, (title, desc, target) in zip(cols, features):
        with col:
            st.markdown(
                f"""
                <div style="text-align:center;padding:18px 14px;border:1px solid #334155;
                            border-radius:12px;background:#1E293B;
                            box-shadow:0 2px 8px rgba(0,0,0,0.3);height:100%;
                            margin-bottom:8px;">
                  <h3 style="color:#E2E8F0;font-size:0.95rem;margin-bottom:8px;">{title}</h3>
                  <p style="color:#64748B;font-size:0.82rem;margin:0;">{desc}</p>
                </div>
                """,
                unsafe_allow_html=True,
            )
            if st.button(f"Go to {title}", key=f"feat_{title}", use_container_width=True):
                st.session_state["page"] = target
                st.rerun()

    # How it works
    st.markdown("---")
    st.markdown(
        """
        <h3 style="color:#CBD5E1;text-align:center;margin-bottom:16px;font-size:1.1rem;">
          How it works</h3>
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
                        background:#1E293B;border-radius:8px;border:1px solid #334155;">
              <span style="background:#4F46E5;color:#FFF;border-radius:50%;
                           width:26px;height:26px;display:flex;align-items:center;
                           justify-content:center;font-size:0.82rem;font-weight:700;
                           flex-shrink:0;">{num}</span>
              <span style="color:#CBD5E1;font-size:0.88rem;">{desc}</span>
            </div>
            """,
            unsafe_allow_html=True,
        )
