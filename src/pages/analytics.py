"""
Analytics dashboard — charts from real database records.
"""

from __future__ import annotations

import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from src.db.database import get_db
from src.db.models import Complaint, ComplaintStatus, UserRole
from src.utils.auth import require_role
from src.utils.complaints import get_analytics_data
from src.components.ui import page_header


def render():
    require_role(UserRole.admin)
    db = get_db()
    try:
        page_header("📈 Analytics", "Metrics computed from live database records")
        data = get_analytics_data(db)

        if data["total"] == 0:
            st.info("No complaint data yet. Submit some complaints first.")
            return

        # ─── Row 1: Status and category breakdown ─────────────────────────────
        c1, c2 = st.columns(2)

        with c1:
            st.markdown("#### Complaints by Status")
            status_data = {k: v for k, v in data["by_status"].items() if v > 0}
            if status_data:
                fig = px.pie(
                    values=list(status_data.values()),
                    names=list(status_data.keys()),
                    color_discrete_sequence=px.colors.qualitative.Set2,
                )
                fig.update_layout(margin=dict(t=0, b=0, l=0, r=0), height=280)
                st.plotly_chart(fig, use_container_width=True)

        with c2:
            st.markdown("#### Complaints by Category")
            cat_data = {str(k): v for k, v in data["by_category"].items() if v > 0}
            if cat_data:
                fig2 = px.bar(
                    x=list(cat_data.values()),
                    y=list(cat_data.keys()),
                    orientation="h",
                    color=list(cat_data.values()),
                    color_continuous_scale="Viridis",
                )
                fig2.update_layout(margin=dict(t=0, b=0, l=0, r=0), height=280,
                                   coloraxis_showscale=False)
                st.plotly_chart(fig2, use_container_width=True)

        # ─── Row 2: Hostel breakdown + priority ───────────────────────────────
        c3, c4 = st.columns(2)

        with c3:
            st.markdown("#### Complaints by Hostel")
            hostel_data = {str(k): v for k, v in data["by_hostel"].items() if v > 0}
            if hostel_data:
                fig3 = px.bar(
                    x=list(hostel_data.keys()),
                    y=list(hostel_data.values()),
                    color=list(hostel_data.values()),
                    color_continuous_scale="Blues",
                )
                fig3.update_layout(margin=dict(t=0, b=0, l=0, r=0), height=260,
                                   coloraxis_showscale=False)
                st.plotly_chart(fig3, use_container_width=True)

        with c4:
            st.markdown("#### Complaints by Priority")
            prio_data = {str(k): v for k, v in data["by_priority"].items() if v > 0}
            if prio_data:
                colors_map = {"Low": "#16A34A", "Medium": "#D97706",
                              "High": "#EA580C", "Urgent": "#DC2626"}
                fig4 = px.bar(
                    x=list(prio_data.keys()),
                    y=list(prio_data.values()),
                    color=list(prio_data.keys()),
                    color_discrete_map=colors_map,
                )
                fig4.update_layout(margin=dict(t=0, b=0, l=0, r=0), height=260,
                                   showlegend=False)
                st.plotly_chart(fig4, use_container_width=True)

        # ─── Row 3: Trend over time ───────────────────────────────────────────
        st.markdown("---")
        st.markdown("#### Complaint Volume Over Time")
        complaints_all = (
            db.query(Complaint)
            .filter(Complaint.merged_into_id == None)
            .order_by(Complaint.created_at)
            .all()
        )
        if complaints_all:
            df = pd.DataFrame([
                {"date": c.created_at.date() if c.created_at else None,
                 "category": c.category.value if c.category else "Other"}
                for c in complaints_all
                if c.created_at
            ])
            if not df.empty:
                df_daily = df.groupby("date").size().reset_index(name="count")
                fig5 = px.line(df_daily, x="date", y="count",
                               title="Daily new complaints",
                               markers=True)
                fig5.update_layout(margin=dict(t=30, b=0), height=260)
                st.plotly_chart(fig5, use_container_width=True)

        # ─── Row 4: Key metrics table ─────────────────────────────────────────
        st.markdown("---")
        st.markdown("#### Response Time Metrics")
        st.markdown(
            """
            > **Metric definitions:**
            > - **Avg time to first seen**: Time from submission to the first caretaker mark-seen. Calculated only for complaints with a recorded seen timestamp.
            > - **Avg time to acknowledgement**: Time from submission to explicit caretaker acknowledgement. Only complaints with an `acknowledged_at` timestamp are included.
            > - **Avg resolution time**: Time from submission to resolution. Only resolved complaints are included. Unresolved complaints are excluded from this calculation (not treated as 0).
            """
        )

        def _fmt(v, suffix="h"):
            if v is None:
                return "— (no data)"
            if suffix == "h" and v < 1:
                return f"{v * 60:.1f} min"
            return f"{v:.1f} {suffix}"

        metrics_df = pd.DataFrame([
            {"Metric": "Avg time to first seen",
             "Value": _fmt(data["avg_seen_hours"])},
            {"Metric": "Avg time to acknowledgement",
             "Value": _fmt(data["avg_ack_hours"])},
            {"Metric": "Avg resolution time",
             "Value": _fmt(data["avg_resolution_hours"])},
            {"Metric": "Total complaints",
             "Value": str(data["total"])},
            {"Metric": "Resolved",
             "Value": str(data["by_status"].get("Resolved", 0))},
            {"Metric": "Reopened",
             "Value": str(data["by_status"].get("Reopened", 0))},
        ])
        st.dataframe(metrics_df, hide_index=True, use_container_width=True)

        # ─── Top voted ────────────────────────────────────────────────────────
        if data["top_voted"]:
            st.markdown("---")
            st.markdown("#### 🏆 Most Supported Issues")
            for c in data["top_voted"]:
                st.markdown(
                    f"- **{c.complaint_number}** — {c.title} "
                    f"| {c.vote_count} supporters | "
                    f"{c.status.value if c.status else ''}"
                )

    finally:
        db.close()
