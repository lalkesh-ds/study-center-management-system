import sys
from pathlib import Path

# Add project root to sys.path to enable absolute imports
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# Add app directory to sys.path for direct imports
APP_DIR = Path(__file__).resolve().parent
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

import streamlit as st
from datetime import date

try:
    from frontend.streamlit_app.api_client import APIClient
except ImportError:
    from api_client import APIClient

# Streamlit Page Setup
st.set_page_config(
    page_title="Smart Library & Study Center",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Initialize Session State
if "api_client" not in st.session_state:
    st.session_state["api_client"] = APIClient()

if "token" not in st.session_state:
    st.session_state["token"] = None

if "user" not in st.session_state:
    st.session_state["user"] = None

api: APIClient = st.session_state["api_client"]
if st.session_state["token"]:
    api.set_token(st.session_state["token"])


# -----------------------------------------------------------------------------
# Authentication Guard / Login Screen
# -----------------------------------------------------------------------------
def render_login_view():
    st.title("📚 Smart Library & Study Center")
    st.markdown("### Front-Desk Management Portal (100 Physical Seats)")
    st.markdown("---")

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.subheader("🔐 Staff & Administrator Sign-In")
        with st.form("login_form", clear_on_submit=False):
            username = st.text_input("Username", value="admin")
            password = st.text_input("Password", type="password", value="Admin@Library2026!")
            submit = st.form_submit_button("Sign In to Terminal", use_container_width=True)

            if submit:
                try:
                    res = api.login(username=username, password=password)
                    st.session_state["token"] = res["access_token"]
                    st.session_state["user"] = res["user"]
                    api.set_token(res["access_token"])
                    st.success("Authentication successful! Loading front-desk...")
                    st.rerun()
                except Exception as e:
                    st.error(f"Authentication Failed: {str(e)}")

        st.info("💡 **Default Credentials**: Username `admin` | Password `Admin@Library2026!`")


# -----------------------------------------------------------------------------
# Main Portal Landing View
# -----------------------------------------------------------------------------
def render_main_view():
    user = st.session_state["user"]

    # Sidebar Profile & Logout
    st.sidebar.markdown(f"### 👤 Logged In: **{user['full_name']}**")
    st.sidebar.markdown(f"**Role**: `{user['role']}` | **User**: `{user['username']}`")
    if st.sidebar.button("🚪 Logout", use_container_width=True):
        st.session_state["token"] = None
        st.session_state["user"] = None
        api.set_token(None)
        st.rerun()

    st.sidebar.markdown("---")
    st.sidebar.markdown("### 📌 Facility Specifications")
    st.sidebar.markdown("- **Physical Desks**: 100 Seats (1 to 100)")
    st.sidebar.markdown("- **Daily Shifts**: 4 Canonical Shifts")
    st.sidebar.markdown("- **Hours**: 07:00 AM – 11:00 PM")

    # Header
    st.title("📚 Smart Library & Study Center Portal")
    st.caption("Central Operations & Space Allocation System • Desk 1 to 100")
    st.markdown("---")

    # Quick Status Metrics
    try:
        summary = api.get_dashboard_summary(target_date=str(date.today()))
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Active Subscriptions", summary.get("active_memberships_today", 0))
        m2.metric("Physical Desks Occupied", f"{summary.get('occupied_seats_count', 0)} / 100")
        m3.metric("Shift-Slot Occupancy", f"{summary.get('slot_occupancy_percentage', 0.0):.1f}%", help="Out of 300 daily slots")
        m4.metric("Seat-Hour Occupancy", f"{summary.get('seat_hour_occupancy_percentage', 0.0):.1f}%", help="Out of 1,600 daily facility hours")
    except Exception as e:
        st.warning(f"Could not load live KPI summary: {e}")

    st.markdown("---")
    st.subheader("⚡ Front-Desk Module Navigation")

    c1, c2, c3 = st.columns(3)
    with c1:
        st.info("### 🪑 1. Seat Grid\nLive visual matrix of all 100 seats across Morning, Afternoon, Evening, and Full Day.")
    with c2:
        st.success("### 👨‍🎓 2. Students\nDirectory of registered aspirants, contact details, ID verification, and membership history.")
    with c3:
        st.warning("### 📝 3. Memberships\nNew student admissions, deterministic conflict-free booking, renewals, and cancellations.")

    c4, c5, c6 = st.columns(3)
    with c4:
        st.error("### 💳 4. Cashier Payments\nMulti-installment collections, due balance tracking, payment receipts, and void auditing.")
    with c5:
        st.info("### ⏱️ 5. Attendance\nFront-desk rapid check-in / check-out terminal, time studied, and daily roster.")
    with c6:
        st.success("### 📊 6. Analytics Dashboard\nReal-time occupancy charts, revenue breakdown, and expiring membership renewal queue.")


if not st.session_state["user"]:
    render_login_view()
else:
    render_main_view()
