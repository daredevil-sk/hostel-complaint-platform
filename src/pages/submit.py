"""
Complaint submission form.
"""

from __future__ import annotations

import streamlit as st
from src.db.database import get_db
from src.db.models import Category, Priority, UserRole
from src.utils.auth import require_login, get_current_user, get_role
from src.utils.complaints import create_complaint, save_attachment
from src.components.ui import page_header, back_button

HOSTELS = ["Aryabhatta", "Asima", "Kalam", "CV Raman", "Other"]


def render():
    require_login()
    role = get_role()
    if role not in (UserRole.student, UserRole.admin):
        st.error("Only students and administrators can submit complaints.")
        return

    back_button("Back", "home", "submit_back")
    page_header("Submit a Complaint",
                "Report a hostel issue. Your complaint ID will be generated automatically.")

    # Guard against double-submission
    if "last_submission_id" not in st.session_state:
        st.session_state["last_submission_id"] = None

    # If already submitted, show success & redirect button immediately
    if st.session_state.get("submission_success"):
        complaint_num = st.session_state["last_submission_id"]
        st.success(
            f"Complaint submitted successfully!\n\n"
            f"Your complaint ID is: **`{complaint_num}`**\n\n"
            f"Save this ID to track your complaint."
        )
        col1, col2 = st.columns(2)
        with col1:
            if st.button("View on Complaint Board", use_container_width=True, type="primary"):
                st.session_state["submission_success"] = False
                st.session_state["page"] = "board"
                st.rerun()
        with col2:
            if st.button("Submit Another", use_container_width=True):
                st.session_state["submission_success"] = False
                st.rerun()
        return

    user = get_current_user()

    with st.form("submit_complaint_form", clear_on_submit=False):
        st.markdown("### Complaint Details")

        title = st.text_input("Complaint title *",
                              placeholder="e.g. Water cooler not working in Block B")
        category = st.selectbox("Category *",
                                [c.value for c in Category])

        st.markdown("### Location")
        st.caption("Hostels: Asima (Girls) | Aryabhatta (Block C: Girls; Blocks A, B, D: Boys) | Kalam (Blocks A-D: Boys) | CV Raman (Boys)")
        c1, c2 = st.columns(2)
        with c1:
            hostel = st.selectbox("Hostel *", HOSTELS)
        with c2:
            block = st.text_input("Block / Building", placeholder="e.g. Block A, B, C, D")

        c3, c4 = st.columns(2)
        with c3:
            floor = st.text_input("Floor", placeholder="e.g. Ground, 1st, 2nd")
        with c4:
            location_detail = st.text_input("Specific location",
                                            placeholder="e.g. Near washroom 204")

        st.markdown("### Description")
        description = st.text_area(
            "Detailed description *",
            placeholder="Describe the issue clearly. When did it start? How severe is it?",
            height=140,
        )

        st.markdown("### Photo Evidence (optional)")
        uploaded_files = st.file_uploader(
            "Upload photos (JPEG, PNG, WebP — max 5 MB each)",
            type=["jpg", "jpeg", "png", "webp", "gif"],
            accept_multiple_files=True,
        )

        st.markdown("### Options")
        is_anonymous = st.checkbox(
            "Submit anonymously",
            value=False,
            help="Your name will not be shown publicly. Your account is still linked internally for tracking purposes.",
        )

        if role == UserRole.admin:
            priority = st.selectbox("Priority", [p.value for p in Priority])
            is_public = st.checkbox("Make publicly visible", value=True)
        else:
            priority = "Medium"
            is_public = True

        st.markdown("---")
        submitted = st.form_submit_button("Submit Complaint",
                                          use_container_width=True, type="primary")

    if submitted:
        errors = []
        if not title.strip():
            errors.append("Complaint title is required.")
        if not description.strip():
            errors.append("Description is required.")
        if errors:
            for e in errors:
                st.error(e)
            return

        db = get_db()
        try:
            ok, result, complaint = create_complaint(
                db,
                title=title,
                description=description,
                category=category,
                hostel=hostel,
                block=block,
                floor=floor,
                location_detail=location_detail,
                submitter_id=user.id,
                priority=priority if role == UserRole.admin else "Medium",
                is_public=is_public if role == UserRole.admin else True,
                is_demo=False,
                is_anonymous=is_anonymous,
            )

            if not ok:
                st.error(f"Submission failed: {result}")
                return

            # Save attachments
            attachment_errors = []
            if uploaded_files and complaint:
                for uploaded in uploaded_files:
                    file_bytes = uploaded.read()
                    mime = uploaded.type or "image/jpeg"
                    att_ok, att_msg = save_attachment(
                        db,
                        complaint_id=complaint.id,
                        uploader_id=user.id,
                        file_bytes=file_bytes,
                        filename=uploaded.name,
                        mime_type=mime,
                        attachment_type="complaint_photo",
                    )
                    if not att_ok:
                        attachment_errors.append(att_msg)

            st.session_state["last_submission_id"] = result
            st.session_state["submission_success"] = True

            if attachment_errors:
                st.warning("Some photos could not be saved: " +
                           "; ".join(attachment_errors))

            st.rerun()

        finally:
            db.close()
