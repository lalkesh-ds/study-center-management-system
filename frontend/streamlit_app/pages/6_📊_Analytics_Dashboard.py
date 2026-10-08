import sys
from pathlib import Path

# Add project root and streamlit_app directory to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

APP_DIR = Path(__file__).resolve().parent.parent
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

import streamlit as st
from datetime import date, timedelta
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

try:
    from frontend.streamlit_app.api_client import APIClient
except ImportError:
    from api_client import APIClient

st.set_page_config(page_title="Executive Analytics - Smart Library", page_icon="📊", layout="wide")

if "api_client" not in st.session_state:
    st.session_state["api_client"] = APIClient()

api: APIClient = st.session_state["api_client"]
if st.session_state.get("token"):
    api.set_token(st.session_state["token"])

st.title("📊 Executive Analytics & Capacity KPI Dashboard")
st.caption("Multidimensional space utilization, renewal pipeline alerts, and financial intelligence")

tabs = st.tabs(["📈 Capacity & Utilization KPIs", "⏳ Renewal Action Queue", "💵 Financial Revenue Reports"])

# -----------------------------------------------------------------------------
# TAB 1: Capacity & Utilization KPIs
# -----------------------------------------------------------------------------
with tabs[0]:
    st.subheader("📈 Real-Time Desk Capacity Analytics")
    kpi_date = st.date_input("Target Date for Capacity Audit", value=date.today(), key="kpi_date")

    try:
        summary = api.get_dashboard_summary(target_date=str(kpi_date))
        
        # 3 Primary KPI Cards
        kc1, kc2, kc3, kc4 = st.columns(4)
        kc1.metric(
            "Physical Seat Utilization",
            f"{summary.get('physical_utilization_percentage', 0.0):.1f}%",
            f"{summary.get('occupied_seats_count', 0)} / 100 Desks",
            help="Desks with at least one active allocation today"
        )
        kc2.metric(
            "Slot-Capacity Occupancy",
            f"{summary.get('slot_occupancy_percentage', 0.0):.1f}%",
            f"{summary.get('consumed_slots', 0)} / 300 Slots",
            help="Standardized 300 shift-slots capacity (Full Day = 3 slots)"
        )
        kc3.metric(
            "Seat-Hour Occupancy",
            f"{summary.get('seat_hour_occupancy_percentage', 0.0):.1f}%",
            f"{summary.get('consumed_seat_hours', 0):.0f} / 1,600 Hrs",
            help="Time-weighted facility capacity out of 1,600 daily seat-hours"
        )
        kc4.metric(
            "Total Active Subscriptions",
            summary.get("active_memberships_today", 0),
            f"{summary.get('empty_seats_count', 0)} Entirely Free Desks"
        )

        st.markdown("---")

        # Visual Plotly Charts
        chart_col1, chart_col2 = st.columns(2)
        with chart_col1:
            st.markdown("#### Shift Distribution Breakdown")
            shift_counts = summary.get("shift_breakdown", {})
            if shift_counts and any(v > 0 for v in shift_counts.values()):
                df_shift = pd.DataFrame({
                    "Shift": list(shift_counts.keys()),
                    "Count": list(shift_counts.values())
                })
                fig_pie = px.pie(
                    df_shift,
                    values="Count",
                    names="Shift",
                    hole=0.45,
                    color_discrete_sequence=px.colors.qualitative.Prism
                )
                fig_pie.update_layout(margin=dict(t=10, b=10, l=10, r=10))
                st.plotly_chart(fig_pie, use_container_width=True)
            else:
                st.info("No active subscriptions logged for this date.")

        with chart_col2:
            st.markdown("#### Facility Capacity Utilization Comparison")
            metrics = ["Physical Desks", "Slot-Capacity", "Seat-Hours"]
            values = [
                summary.get("physical_utilization_percentage", 0.0),
                summary.get("slot_occupancy_percentage", 0.0),
                summary.get("seat_hour_occupancy_percentage", 0.0)
            ]
            fig_bar = go.Figure(go.Bar(
                x=metrics,
                y=values,
                marker_color=["#2b5c8f", "#17a2b8", "#28a745"],
                text=[f"{v:.1f}%" for v in values],
                textposition="auto"
            ))
            fig_bar.update_layout(
                yaxis=dict(range=[0, 100], title="Occupancy Percentage (%)"),
                margin=dict(t=10, b=10, l=10, r=10)
            )
            st.plotly_chart(fig_bar, use_container_width=True)

    except Exception as e:
        st.error(f"Failed to fetch summary: {e}")

# -----------------------------------------------------------------------------
# TAB 2: Renewal Action Queue
# -----------------------------------------------------------------------------
with tabs[1]:
    st.subheader("⏳ Expiring Membership Action Queue")
    st.caption("Aspirants reaching subscription expiry; requires front-desk renewal outreach")

    threshold = st.slider("Expiry Horizon (Days from Today)", min_value=1, max_value=14, value=3)

    try:
        expiring = api.get_expiring_memberships(threshold_days=threshold)
        if not expiring:
            st.success(f"🎉 No subscriptions expiring within the next {threshold} days!")
        else:
            st.warning(f"⚠️ {len(expiring)} students are due for renewal within {threshold} days.")
            q_rows = []
            for item in expiring:
                q_rows.append({
                    "Days Left": f"🔴 {item['days_remaining']} days" if item['days_remaining'] <= 1 else f"🟡 {item['days_remaining']} days",
                    "Student Name": item["student_name"],
                    "Mobile": item["student_mobile"],
                    "Seat": f"#{item['seat_number']}",
                    "Shift": item["shift_name"],
                    "End Date": item["end_date"],
                    "Due Balance": f"₹{item['due_amount']}"
                })
            st.dataframe(pd.DataFrame(q_rows), use_container_width=True)
    except Exception as e:
        st.error(f"Error fetching expiring queue: {e}")

# -----------------------------------------------------------------------------
# TAB 3: Financial Revenue Reports
# -----------------------------------------------------------------------------
with tabs[2]:
    st.subheader("💵 Financial Collections & Revenue Ledger")
    
    rev_c1, rev_c2 = st.columns(2)
    with rev_c1:
        rev_start = st.date_input("From Date", value=date.today() - timedelta(days=30), key="rev_start")
    with rev_c2:
        rev_end = st.date_input("To Date", value=date.today(), key="rev_end")

    try:
        report = api.get_revenue_report(start_date=str(rev_start), end_date=str(rev_end))
        
        rc1, rc2, rc3 = st.columns(3)
        rc1.metric("Total Net Collections", f"₹{report.get('total_collections', 0.0):,.2f}")
        rc2.metric("Total Transactions", report.get("transaction_count", 0))
        rc3.metric("Voided Transactions", report.get("voided_count", 0))

        st.markdown("---")

        by_method = report.get("by_payment_method", {})
        if by_method:
            b_col1, b_col2 = st.columns([1, 1])
            with b_col1:
                st.markdown("#### Collections by Payment Method")
                df_meth = pd.DataFrame({
                    "Method": list(by_method.keys()),
                    "Revenue (₹)": list(by_method.values())
                })
                fig_m = px.bar(
                    df_meth,
                    x="Method",
                    y="Revenue (₹)",
                    color="Method",
                    text="Revenue (₹)"
                )
                fig_m.update_traces(texttemplate='₹%{text:.2f}', textposition='outside')
                st.plotly_chart(fig_m, use_container_width=True)

            with b_col2:
                st.markdown("#### Payment Channel Share")
                fig_p = px.pie(df_meth, values="Revenue (₹)", names="Method", hole=0.4)
                st.plotly_chart(fig_p, use_container_width=True)

    except Exception as e:
        st.error(f"Failed to fetch revenue report: {e}")
