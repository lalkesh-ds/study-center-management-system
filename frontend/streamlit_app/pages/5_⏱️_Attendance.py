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
            if isinstance(candidates, dict):
                candidates = candidates.get("items", [])
            if candidates:
                found_student = candidates[0]
                mems = api.get_memberships(student_id=found_student["id"], status="ACTIVE")
                if isinstance(mems, dict):
                    mems = mems.get("items", [])
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
            mobile_num = found_student.get("mobile_number") or found_student.get("mobile", "—")
            st.markdown(f"📱 **Mobile**: `{mobile_num}`")

            if not target_membership:
                st.error("❌ No Active Subscription for Today. Student cannot check in.")
            else:
                seat_num_disp = target_membership.get("seat_number", target_membership.get("seat_id", "—"))
                st.success(f"✅ Active Subscription Found: **Seat #{seat_num_disp}** ({target_membership.get('shift_name', 'Shift')})")
                st.caption(f"Valid: {target_membership['start_date']} to {target_membership['end_date']}")

                # Check if already checked in today
                daily_records = api.get_daily_attendance(attendance_date=str(date.today()))
                if isinstance(daily_records, dict):
                    daily_records = daily_records.get("items", [])
                existing_record = next((r for r in daily_records if r["student_id"] == found_student["id"]), None)

                if not existing_record:
                    if st.button("🟢 CHECK-IN STUDENT NOW", type="primary", width="stretch"):
                        try:
                            res = api.check_in({
                                "student_id": found_student["id"],
                                "membership_id": target_membership["id"],
                                "source": "MANUAL_STAFF"
                            })
                            st.success(f"Student checked in at {res['check_in'][:19].replace('T', ' ')}! Assigned Desk: #{seat_num_disp}")
                            st.rerun()
                        except Exception as ex:
                            st.error(f"Check-in rejected: {ex}")
                else:
                    st.info(f"Entry timestamp: `{existing_record['check_in'][:19].replace('T', ' ')}` | Status: `{existing_record['status']}`")
                    hours_val = existing_record.get('duration_hours') if existing_record.get('duration_hours') is not None else existing_record.get('hours_studied', 'N/A')
                    if existing_record["status"] == "PRESENT":
                        if st.button("🔴 CHECK-OUT STUDENT (Mark Departure)", type="secondary", width="stretch"):
                            try:
                                res = api.check_out(existing_record["id"])
                                studied_hrs = res.get('duration_hours') if res.get('duration_hours') is not None else res.get('hours_studied', 'N/A')
                                st.success(f"Student checked out! Total hours studied: {studied_hrs} hrs.")
                                st.rerun()
                            except Exception as ex:
                                st.error(f"Check-out failed: {ex}")
                    else:
                        st.success(f"Student has already completed their study session today ({hours_val} hours).")
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
        if isinstance(roster, dict):
            roster = roster.get("items", [])
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
                dur = r.get("duration_hours") if r.get("duration_hours") is not None else r.get("hours_studied")
                table_rows.append({
                    "Student Name": r.get("student_name", "—"),
                    "Seat": f"#{r.get('seat_number') or r.get('seat_id', '—')}",
                    "Shift": r.get("shift_name", "—"),
                    "Check-In Time": r["check_in"][11:19] if r.get("check_in") else "—",
                    "Check-Out Time": r["check_out"][11:19] if r.get("check_out") else "—",
                    "Status": "🟢 IN FACILITY" if r["status"] == "PRESENT" else "⚪ DEPARTED",
                    "Hours Studied": f"{dur} hrs" if dur is not None else "In Progress"
                })
            df = pd.DataFrame(table_rows)
            st.dataframe(df, width="stretch")

    except Exception as e:
        st.error(f"Failed to fetch attendance roster: {e}")
