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
from datetime import date, datetime
import pandas as pd

try:
    from frontend.streamlit_app.api_client import APIClient
except ImportError:
    from api_client import APIClient

st.set_page_config(page_title="Attendance - Smart Library", page_icon="⏱️", layout="wide")

if "api_client" not in st.session_state:
    st.session_state["api_client"] = APIClient()

api: APIClient = st.session_state["api_client"]
if st.session_state.get("token"):
    api.set_token(st.session_state["token"])

st.title("⏱️ Front-Desk Attendance & Study Session Terminal")
st.caption("Verify shift access windows, record physical entry/exit, and audit study session hours")

tabs = st.tabs(["🚀 Rapid Check-In / Check-Out", "📅 Daily Attendance Roster"])

# -----------------------------------------------------------------------------
# TAB 1: Rapid Check-In / Check-Out Terminal
# -----------------------------------------------------------------------------
with tabs[0]:
    st.subheader("🚀 Student Access Terminal")
    
    col_input, col_action = st.columns([2, 3])
    
    with col_input:
        mobile_or_name = st.text_input("Enter Student Mobile # or Search Name", placeholder="e.g. 9876543210")
        search_clicked = st.button("🔍 Search Aspirant")

    # Locate student & active membership
    found_student = None
    target_membership = None

    if mobile_or_name.strip():
        try:
            candidates = api.get_students(search=mobile_or_name.strip(), limit=5)
            if candidates:
                found_student = candidates[0]
                mems = api.get_memberships(student_id=found_student["id"], status="ACTIVE")
                today_str = str(date.today())
                for m in mems:
                    if m["start_date"] <= today_str <= m["end_date"]:
                        target_membership = m
                        break
        except Exception as e:
            st.error(f"Search failed: {e}")

    with col_action:
        if found_student:
            st.markdown(f"### Student: **{found_student['full_name']}**")
            st.markdown(f"📱 **Mobile**: `{found_student['mobile_number']}`")

            if not target_membership:
                st.error("❌ No Active Subscription for Today. Student cannot check in.")
            else:
                st.success(f"✅ Active Subscription Found: **Seat #{target_membership['seat_number']}** ({target_membership['shift_name']})")
                st.caption(f"Valid: {target_membership['start_date']} to {target_membership['end_date']}")

                # Check if already checked in today
                daily_records = api.get_daily_attendance(attendance_date=str(date.today()))
                existing_record = next((r for r in daily_records if r["student_id"] == found_student["id"]), None)

                if not existing_record:
                    if st.button("🟢 CHECK-IN STUDENT NOW", type="primary", use_container_width=True):
                        try:
                            res = api.check_in({
                                "student_id": found_student["id"],
                                "membership_id": target_membership["id"],
                                "source": "MANUAL_STAFF"
                            })
                            st.success(f"Student checked in at {res['check_in'][:19].replace('T', ' ')}! Assigned Desk: #{target_membership['seat_number']}")
                            st.rerun()
                        except Exception as ex:
                            st.error(f"Check-in rejected: {ex}")
                else:
                    st.info(f"Entry timestamp: `{existing_record['check_in'][:19].replace('T', ' ')}` | Status: `{existing_record['status']}`")
                    if existing_record["status"] == "PRESENT":
                        if st.button("🔴 CHECK-OUT STUDENT (Mark Departure)", type="secondary", use_container_width=True):
                            try:
                                res = api.check_out(existing_record["id"])
                                st.success(f"Student checked out! Total hours studied: {res.get('hours_studied', 'N/A')} hrs.")
                                st.rerun()
                            except Exception as ex:
                                st.error(f"Check-out failed: {ex}")
                    else:
                        st.success(f"Student has already completed their study session today ({existing_record.get('hours_studied', 'N/A')} hours).")
        elif mobile_or_name.strip() and not found_student:
            st.warning("No student matched the search criteria.")

# -----------------------------------------------------------------------------
# TAB 2: Daily Attendance Roster
# -----------------------------------------------------------------------------
with tabs[1]:
    st.subheader("📅 Daily Attendance Roster")
    selected_roster_date = st.date_input("Select Date", value=date.today(), key="roster_date")

    try:
        roster = api.get_daily_attendance(attendance_date=str(selected_roster_date))
        if not roster:
            st.info(f"No attendance records logged for {selected_roster_date}.")
        else:
            total_present = sum(1 for r in roster if r["status"] == "PRESENT")
            total_completed = sum(1 for r in roster if r["status"] == "CHECKED_OUT")

            m1, m2, m3 = st.columns(3)
            m1.metric("Total Check-Ins", len(roster))
            m2.metric("Currently in Facility", total_present)
            m3.metric("Departed / Completed", total_completed)

            table_rows = []
            for r in roster:
                table_rows.append({
                    "Student Name": r.get("student_name", "—"),
                    "Seat": f"#{r.get('seat_number', '—')}",
                    "Shift": r.get("shift_name", "—"),
                    "Check-In Time": r["check_in"][11:19] if r.get("check_in") else "—",
                    "Check-Out Time": r["check_out"][11:19] if r.get("check_out") else "—",
                    "Status": "🟢 IN FACILITY" if r["status"] == "PRESENT" else "⚪ DEPARTED",
                    "Hours Studied": f"{r['hours_studied']} hrs" if r.get("hours_studied") is not None else "In Progress"
                })
            df = pd.DataFrame(table_rows)
            st.dataframe(df, use_container_width=True)

    except Exception as e:
        st.error(f"Failed to fetch attendance roster: {e}")
