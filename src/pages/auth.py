"""
Login and registration pages.
"""

import streamlit as st
from src.utils.auth import login, register, is_logged_in
from src.db.models import UserRole
from src.components.ui import page_header


def render_login():
    if is_logged_in():
        st.session_state["page"] = "home"
        st.rerun()

    page_header("🔑 Sign In", "Welcome back to Team R")

    with st.form("login_form"):
        email = st.text_input("Email address")
        password = st.text_input("Password", type="password")
        submitted = st.form_submit_button("Sign In", use_container_width=True, type="primary")

    if submitted:
        if not email or not password:
            st.error("Please enter your email and password.")
        else:
            ok, msg = login(email, password)
            if ok:
                st.success(msg)
                st.session_state["page"] = "home"
                st.rerun()
            else:
                st.error(msg)

    st.markdown("---")
    st.markdown("Don't have an account?")
    if st.button("📝 Create a student account"):
        st.session_state["page"] = "register"
        st.rerun()

    # Demo accounts hint
    with st.expander("🎭 Demo accounts (for presentation)"):
        st.markdown(
            """
            | Role | Email | Password |
            |------|-------|----------|
            | Student | student1@demo.teamr | demo1234 |
            | Student | student2@demo.teamr | demo1234 |
            | Caretaker | caretaker@demo.teamr | demo1234 |
            | Admin | admin@demo.teamr | demo1234 |

            > ⚠️ These are fictional demo accounts, not real IIT Patna staff.
            """
        )


def render_register():
    if is_logged_in():
        st.session_state["page"] = "home"
        st.rerun()

    page_header("📝 Create Account", "Join Team R as a student")
    st.info("ℹ️ Student accounts can be created here. Caretaker and admin accounts are created by the administrator.")

    with st.form("register_form"):
        display_name = st.text_input("Full name / Display name")
        email = st.text_input("Email address")
        password = st.text_input("Password", type="password")
        password2 = st.text_input("Confirm password", type="password")
        hostel = st.selectbox("Your hostel (optional)", ["", "Alaknanda", "Barak",
            "Brahmaputra", "Ganga", "Godavari", "Kaveri", "Mahanadi",
            "Narmada", "Saraswati", "Yamuna", "Other"])
        submitted = st.form_submit_button("Create Account", use_container_width=True,
                                          type="primary")

    if submitted:
        errors = []
        if not display_name.strip():
            errors.append("Display name is required.")
        if not email.strip():
            errors.append("Email is required.")
        if len(password) < 6:
            errors.append("Password must be at least 6 characters.")
        if password != password2:
            errors.append("Passwords do not match.")
        if errors:
            for e in errors:
                st.error(e)
        else:
            ok, msg = register(
                email=email,
                display_name=display_name,
                password=password,
                role=UserRole.student,
                hostel=hostel or None,
            )
            if ok:
                st.success("✅ Account created! You can now sign in.")
                st.session_state["page"] = "login"
                st.rerun()
            else:
                st.error(msg)

    st.markdown("---")
    if st.button("← Back to Sign In"):
        st.session_state["page"] = "login"
        st.rerun()
