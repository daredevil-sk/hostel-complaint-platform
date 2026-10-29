"""
Public complaint board — searchable, filterable list of complaints.
"""

from __future__ import annotations

import streamlit as st
from src.db.database import get_db
from src.db.models import Category, ComplaintStatus, Priority, UserRole
from src.utils.complaints import list_complaints, get_seen_status
from src.utils.auth import is_logged_in, get_current_user, get_role
from src.components.ui import (
    complaint_card, empty_state, page_header, demo_banner, status_badge,
    priority_badge, seen_badge, fmt_dt,
)
import os

HOSTELS = ["", "Aryabhatta", "Asima", "Kalam", "CV Raman", "Other"]

PAGE_SIZE = 10


def render():
    if os.getenv("DEMO_MODE", "true").lower() == "true":
        demo_banner()

    page_header("📋 Complaint Board",
                "Browse and support hostel grievances raised by the community.")

    # ─── Filters ──────────────────────────────────────────────────────────────
    with st.expander("🔍 Search & Filters", expanded=True):
        c1, c2 = st.columns([3, 1])
        with c1:
            search = st.text_input("Search by title, description, or complaint ID",
                                   placeholder="e.g. water cooler, TR-2026-0003…")
        with c2:
            sort_by = st.selectbox("Sort by", ["newest", "oldest", "most_supported", "priority"],
                                   format_func=lambda x: {
                                       "newest": "🕐 Newest first",
                                       "oldest": "🕐 Oldest first",
                                       "most_supported": "👥 Most supported",
                                       "priority": "🔴 Priority",
                                   }[x])

        f1, f2, f3, f4, f5 = st.columns(5)
        with f1:
            sel_category = st.selectbox("Category", ["All"] +
                                        [c.value for c in Category])
        with f2:
            sel_hostel = st.selectbox("Hostel", ["All"] + HOSTELS[1:])
        with f3:
            sel_status = st.selectbox("Status", ["All"] +
                                      [s.value for s in ComplaintStatus])
        with f4:
            sel_priority = st.selectbox("Priority", ["All"] +
                                        [p.value for p in Priority])
        with f5:
            sel_block = st.text_input("Block", placeholder="e.g. A, B…")

    # ─── Pagination ────────────────────────────────────────────────────────────
    if "board_page" not in st.session_state:
        st.session_state["board_page"] = 1

    db = get_db()
    try:
        complaints, total = list_complaints(
            db,
            search=search,
            category="" if sel_category == "All" else sel_category,
            hostel="" if sel_hostel == "All" else sel_hostel,
            block=sel_block.strip(),
            status="" if sel_status == "All" else sel_status,
            priority="" if sel_priority == "All" else sel_priority,
            sort_by=sort_by,
            page=st.session_state["board_page"],
            page_size=PAGE_SIZE,
            include_private=False,
        )

        total_pages = max(1, (total + PAGE_SIZE - 1) // PAGE_SIZE)

        # Stats bar
        st.markdown(
            f"""
            <div style="display:flex;gap:20px;padding:12px 0;color:#64748B;font-size:0.85rem;">
              <span>📊 <strong>{total}</strong> complaint{'s' if total != 1 else ''} found</span>
              <span>📄 Page {st.session_state['board_page']} of {total_pages}</span>
            </div>
            """,
            unsafe_allow_html=True,
        )

        if not complaints:
            empty_state("No complaints match your filters.", "🔍")
        else:
            for c in complaints:
                is_seen, ack = get_seen_status(db, c.id)
                complaint_card(c, is_seen=is_seen, ack=ack)

        # Pagination controls
        pc1, pc2, pc3 = st.columns([1, 2, 1])
        with pc1:
            if st.session_state["board_page"] > 1:
                if st.button("← Previous"):
                    st.session_state["board_page"] -= 1
                    st.rerun()
        with pc3:
            if st.session_state["board_page"] < total_pages:
                if st.button("Next →"):
                    st.session_state["board_page"] += 1
                    st.rerun()

    finally:
        db.close()

    # ─── CTA ──────────────────────────────────────────────────────────────────
    st.markdown("---")
    if is_logged_in() and get_role() in (UserRole.student, UserRole.admin):
        if st.button("➕ Submit a new complaint", type="primary"):
            st.session_state["page"] = "submit"
            st.rerun()
    elif not is_logged_in():
        st.info("🔑 Sign in to submit complaints, add your support, or comment on issues.")
        if st.button("Sign In"):
            st.session_state["page"] = "login"
            st.rerun()
