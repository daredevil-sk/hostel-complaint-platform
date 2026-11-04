"""
Login and registration pages.
"""

import streamlit as st
from src.utils.auth import login, register, is_logged_in
from src.db.models import UserRole
from src.components.ui import page_header, back_button


def render_login():
    if is_logged_in():
        st.session_state["page"] = "home"
        st.rerun()

    back_button("Home", "home", "login_back")
    page_header("Sign In", "Welcome back")

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
    if st.button("Create a student account", use_container_width=True, key="btn_create_student_acc"):
        st.session_state["page"] = "register"
        st.rerun()


def render_register():
    if is_logged_in():
        st.session_state["page"] = "home"
        st.rerun()

    back_button("Sign In", "login", "reg_back")
    page_header("Create Account", "Join as a student")
    st.info("Student accounts can be created here. Caretaker and admin accounts are created by the administrator.")

    with st.form("register_form"):
        display_name = st.text_input("Full name / Display name *")
        email = st.text_input("Email address *")
        password = st.text_input("Password *", type="password")
        password2 = st.text_input("Confirm password *", type="password")

        gender = st.selectbox("Gender *", ["Male", "Female"], key="reg_gender_select")

        if gender == "Male":
            hostel_choices = [
                {"hostel": "Kalam", "block": "Block A", "label": "Kalam - Block A"},
                {"hostel": "Kalam", "block": "Block B", "label": "Kalam - Block B"},
                {"hostel": "Kalam", "block": "Block C", "label": "Kalam - Block C"},
                {"hostel": "Kalam", "block": "Block D", "label": "Kalam - Block D"},
                {"hostel": "CV Raman", "block": "", "label": "CV Raman (CVR)"},
                {"hostel": "Aryabhatta", "block": "Block A", "label": "Aryabhatta - Block A"},
                {"hostel": "Aryabhatta", "block": "Block B", "label": "Aryabhatta - Block B"},
                {"hostel": "Aryabhatta", "block": "Block D", "label": "Aryabhatta - Block D"},
            ]
        else:
            hostel_choices = [
                {"hostel": "Aryabhatta", "block": "Block C", "label": "Aryabhatta - Block C"},
                {"hostel": "Asima", "block": "", "label": "Asima"},
            ]

        labels = [c["label"] for c in hostel_choices]
        selected_label = st.selectbox("Which hostel are you allocated in? *", labels, key="reg_hostel_select")
        st.caption("Hostel allocation rules: Kalam A, B, C, D, CVR, Aryabhatta A, B, D for boys; Aryabhatta C, Asima for girls.")

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
            chosen = next((c for c in hostel_choices if c["label"] == selected_label), hostel_choices[0])
            ok, msg = register(
                email=email,
                display_name=display_name,
                password=password,
                role=UserRole.student,
                hostel=chosen["hostel"],
                gender=gender,
                block=chosen["block"],
            )
            if ok:
                st.success("Account created! You can now sign in.")
                st.session_state["page"] = "login"
                st.rerun()
            else:
                st.error(msg)
