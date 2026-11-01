"""
Administrator dashboard — assignment, merge, priority, user management, audit.
"""

from __future__ import annotations

import streamlit as st
from src.db.database import get_db
from src.db.models import (
    Complaint, Profile, UserRole, ComplaintStatus, Priority, AuditLog,
)
from src.utils.auth import require_role, get_current_user, register
from src.utils.complaints import (
    list_complaints, assign_complaint, update_status, merge_complaints,
    get_seen_status, get_audit_logs, export_complaints_csv,
)
from src.components.ui import (
    empty_state, page_header, status_badge, priority_badge, fmt_dt, back_button,
)


def render():
    require_role(UserRole.admin)
    user = get_current_user()
    db = get_db()

    try:
        back_button("Home", "home", "admin_back")
        page_header("Admin Dashboard", "Manage complaints, users, and platform operations")

        tabs = st.tabs([
            "Overview", "All Complaints", "Assignments",
            "Merge Duplicates", "User Management", "Audit Log",
        ])

        with tabs[0]:
            _render_overview(db)

        with tabs[1]:
            _render_all_complaints(db, user)

        with tabs[2]:
            _render_assignments(db, user)

        with tabs[3]:
            _render_merges(db, user)

        with tabs[4]:
            _render_user_management(db, user)

        with tabs[5]:
            _render_audit_log(db)

    finally:
        db.close()


def _render_overview(db):
    from src.utils.complaints import get_analytics_data
    data = get_analytics_data(db)

    # Metrics row
    cols = st.columns(6)
    metric_items = [
        ("Total", data["total"], "#4F46E5"),
        ("Submitted", data["by_status"].get("Submitted", 0), "#64748B"),
        ("In Progress", data["by_status"].get("In Progress", 0), "#2563EB"),
        ("Resolved", data["by_status"].get("Resolved", 0), "#16A34A"),
        ("Reopened", data["by_status"].get("Reopened", 0), "#DC2626"),
        ("Closed", data["by_status"].get("Closed", 0), "#64748B"),
    ]
    for col, (label, value, color) in zip(cols, metric_items):
        with col:
            st.markdown(
                f"""<div style="text-align:center;padding:10px;background:#FFFFFF;
                               border:1px solid #E2E8F0;border-radius:8px;
                               border-top:3px solid {color};">
                  <div style="font-size:1.6rem;font-weight:700;color:{color};">{value}</div>
                  <div style="font-size:0.75rem;color:#64748B;">{label}</div>
                </div>""",
                unsafe_allow_html=True,
            )

    st.markdown("<br/>", unsafe_allow_html=True)

    # Avg response times
    def _hr(v):
        if v is None:
            return "—"
        if v < 1:
            return f"{v*60:.0f} min"
        return f"{v:.1f} h"

    t1, t2, t3 = st.columns(3)
    for col, label, val in [
        (t1, "Avg time to first seen", _hr(data["avg_seen_hours"])),
        (t2, "Avg time to acknowledgement", _hr(data["avg_ack_hours"])),
        (t3, "Avg resolution time", _hr(data["avg_resolution_hours"])),
    ]:
        with col:
            st.metric(label, val)

    st.markdown("---")

    # CSV export
    st.markdown("#### 📥 Export Data")
    if st.button("Export all complaints as CSV"):
        csv_str = export_complaints_csv(db)
        st.download_button(
            label="⬇️ Download CSV",
            data=csv_str,
            file_name="teamr_complaints_export.csv",
            mime="text/csv",
        )

    st.markdown("---")
    st.markdown("#### 🏆 Most Supported Issues")
    for c in data["top_voted"]:
        st.markdown(
            f"- **{c.complaint_number}** — {c.title} "
            f"({c.vote_count} supporters) [{c.status.value if c.status else ''}]"
        )


def _render_all_complaints(db, user):
    st.markdown("#### All Complaints")

    f1, f2, f3 = st.columns(3)
    with f1:
        filt_status = st.selectbox("Status", ["All"] + [s.value for s in ComplaintStatus],
                                   key="adm_filt_status")
    with f2:
        filt_priority = st.selectbox("Priority", ["All"] + [p.value for p in Priority],
                                     key="adm_filt_priority")
    with f3:
        filt_search = st.text_input("Search", key="adm_search")

    complaints, total = list_complaints(
        db,
        search=filt_search,
        status="" if filt_status == "All" else filt_status,
        priority="" if filt_priority == "All" else filt_priority,
        include_private=True,
        sort_by="newest",
        page=1,
        page_size=50,
    )
    st.markdown(f"**{total} complaints**")

    for c in complaints:
        is_seen, ack = get_seen_status(db, c.id)
        col1, col2, col3 = st.columns([4, 2, 1])
        with col1:
            st.markdown(
                f"**{c.complaint_number}** — {c.title}  \n"
                f"🏠 {c.hostel} | 📁 {c.category.value if c.category else ''} | "
                f"👥 {c.vote_count} supporters | 📅 {fmt_dt(c.created_at)}"
            )
        with col2:
            st.markdown(status_badge(c.status.value if c.status else "Submitted") + " " +
                        priority_badge(c.priority.value if c.priority else "Medium"),
                        unsafe_allow_html=True)
        with col3:
            if st.button("View", key=f"adm_view_{c.id}"):
                st.session_state["selected_complaint_id"] = c.id
                st.session_state["page"] = "complaint_detail"
                st.rerun()
        st.markdown("---")


def _render_assignments(db, user):
    st.markdown("#### Assign Complaints to Caretakers")

    # Get unassigned / re-assignable complaints
    complaints, _ = list_complaints(
        db, include_private=True, sort_by="priority", page=1, page_size=100)
    caretakers = db.query(Profile).filter_by(role=UserRole.caretaker, is_active=True).all()

    if not caretakers:
        st.warning("No active caretakers found. Add caretakers in User Management.")
        return

    caretaker_opts = {f"{ct.display_name} ({ct.email})": ct.id for ct in caretakers}

    for c in complaints:
        if c.status in (ComplaintStatus.resolved, ComplaintStatus.closed):
            continue
        with st.expander(f"{c.complaint_number} — {c.title} [{c.status.value if c.status else ''}]"):
            current_ct = c.assigned_caretaker.display_name if c.assigned_caretaker else "Unassigned"
            st.markdown(f"**Current:** {current_ct}")

            a1, a2, a3 = st.columns(3)
            with a1:
                sel_ct = st.selectbox("Assign to caretaker",
                                      list(caretaker_opts.keys()),
                                      key=f"assign_ct_{c.id}")
            with a2:
                sel_dept = st.text_input("Or department",
                                         key=f"assign_dept_{c.id}",
                                         placeholder="e.g. Maintenance Wing")
            with a3:
                sel_prio = st.selectbox("Priority",
                                        [p.value for p in Priority],
                                        index=[p.value for p in Priority].index(
                                            c.priority.value if c.priority else "Medium"),
                                        key=f"assign_prio_{c.id}")

            assign_notes = st.text_input("Notes", key=f"assign_notes_{c.id}")

            if st.button("Assign", key=f"do_assign_{c.id}", type="primary"):
                ct_id = caretaker_opts[sel_ct]
                ok, msg = assign_complaint(
                    db, c.id,
                    assigning_admin_id=user.id,
                    caretaker_id=ct_id,
                    department=sel_dept or None,
                    priority=sel_prio,
                    notes=assign_notes,
                )
                if ok:
                    st.success(msg)
                else:
                    st.error(msg)
                st.rerun()


def _render_merges(db, user):
    st.markdown("#### Merge Duplicate Complaints")
    st.info(
        "Merging transfers votes (without double-counting) and closes the original. "
        "The history of both complaints is preserved."
    )

    all_complaints, _ = list_complaints(db, include_private=True, page=1, page_size=200,
                                         exclude_merged=True)
    opts = {f"{c.complaint_number} — {c.title}": c.id for c in all_complaints}

    c1, c2 = st.columns(2)
    with c1:
        orig_label = st.selectbox("Duplicate (to be merged)", list(opts.keys()),
                                  key="merge_orig")
    with c2:
        surv_label = st.selectbox("Surviving complaint (keep this one)", list(opts.keys()),
                                  key="merge_surv")

    reason = st.text_area("Reason for merge", key="merge_reason")

    if st.button("Merge complaints", type="primary"):
        orig_id = opts[orig_label]
        surv_id = opts[surv_label]
        if orig_id == surv_id:
            st.error("Select two different complaints.")
        else:
            ok, msg = merge_complaints(db, orig_id, surv_id, user.id, reason)
            if ok:
                st.success(msg)
            else:
                st.error(msg)
            st.rerun()


def _render_user_management(db, user):
    st.markdown("#### Registered Users")

    users = db.query(Profile).order_by(Profile.created_at.desc()).all()
    for u in users:
        c1, c2, c3 = st.columns([3, 1, 1])
        with c1:
            st.markdown(f"**{u.display_name}** — {u.email}")
        with c2:
            st.markdown(f"`{u.role.value}`")
        with c3:
            status_label = "Active" if u.is_active else "Inactive"
            if u.id != user.id:
                if st.button(
                    "Deactivate" if u.is_active else "Activate",
                    key=f"toggle_{u.id}",
                ):
                    u.is_active = not u.is_active
                    db.commit()
                    st.rerun()
        st.markdown("---")

    st.markdown("#### ➕ Add Caretaker / Admin Account")
    with st.form("add_user_form"):
        new_name = st.text_input("Display name")
        new_email = st.text_input("Email")
        new_pass = st.text_input("Temporary password", type="password")
        new_role = st.selectbox("Role", ["caretaker", "admin"])
        add_submitted = st.form_submit_button("Create Account")

    if add_submitted:
        if not new_name or not new_email or not new_pass:
            st.error("All fields are required.")
        else:
            ok, msg = register(
                email=new_email,
                display_name=new_name,
                password=new_pass,
                role=UserRole(new_role),
            )
            if ok:
                st.success(f"Account created: {new_email}")
                st.rerun()
            else:
                st.error(msg)


def _render_audit_log(db):
    st.markdown("#### Audit Log")
    logs = get_audit_logs(db, limit=100)
    if not logs:
        empty_state("No audit events recorded yet.", "📜")
        return

    for log in logs:
        actor_name = log.actor.display_name if log.actor else "System"
        st.markdown(
            f"""
            <div style="display:flex;gap:12px;padding:8px 12px;
                        border-bottom:1px solid #F1F5F9;font-size:0.84rem;">
              <span style="color:#94A3B8;min-width:130px;">{fmt_dt(log.created_at)}</span>
              <span style="color:#4F46E5;font-weight:600;min-width:120px;">{log.action}</span>
              <span style="color:#64748B;">{actor_name}</span>
              <span style="color:#94A3B8;">{log.entity_type}:{log.entity_id or ''}</span>
            </div>
            """,
            unsafe_allow_html=True,
        )
