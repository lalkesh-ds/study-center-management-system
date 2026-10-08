import streamlit as st
from datetime import date
import pandas as pd
from frontend.streamlit_app.api_client import APIClient

st.set_page_config(page_title="Seat Grid - Smart Library", page_icon="🪑", layout="wide")

if "api_client" not in st.session_state:
    st.session_state["api_client"] = APIClient()

api: APIClient = st.session_state["api_client"]
if st.session_state.get("token"):
    api.set_token(st.session_state["token"])

st.title("🪑 100-Seat Interactive Grid & Physical Layout")
st.caption("Live temporal allocation matrix across Morning, Afternoon, Evening, and Full Day")

# Top Controls
col_date, col_filter, col_search = st.columns([2, 2, 2])
with col_date:
    selected_date = st.date_input("Target Date", value=date.today())
with col_filter:
    shift_filter = st.selectbox(
        "Shift Perspective",
        ["ALL_SHIFTS", "MORNING (07-11)", "AFTERNOON (11-15)", "EVENING (15-23)", "FULL_DAY (07-23)"]
    )
with col_search:
    search_seat = st.number_input("Find Seat #", min_value=1, max_value=100, value=1, step=1)

# Fetch matrix from backend
try:
    with st.spinner("Fetching seat availability matrix..."):
        matrix = api.get_seat_availability(target_date=str(selected_date))
except Exception as e:
    st.error(f"Failed to fetch seat availability: {e}")
    st.stop()

# Helper to categorize seat state
def get_seat_summary(seat_data):
    if not seat_data.get("is_active", True):
        return "MAINTENANCE", "🔴 Maintenance"
    m = seat_data.get("morning_available", True)
    a = seat_data.get("afternoon_available", True)
    e = seat_data.get("evening_available", True)
    f = seat_data.get("full_day_available", True)

    if not f and (not m and not a and not e):
        return "FULL_DAY_OCCUPIED", "🟣 Full Day"
    if m and a and e:
        return "ALL_FREE", "🟢 Completely Free"
    return "PARTIAL", "🟡 Partially Booked"

# Summary metrics
total_seats = len(matrix)
free_count = sum(1 for s in matrix if s.get("is_active") and s.get("morning_available") and s.get("afternoon_available") and s.get("evening_available"))
maintenance_count = sum(1 for s in matrix if not s.get("is_active"))
partially_booked = sum(1 for s in matrix if s.get("is_active") and not (s.get("morning_available") and s.get("afternoon_available") and s.get("evening_available")))

c1, c2, c3, c4 = st.columns(4)
c1.metric("Total Physical Seats", total_seats)
c2.metric("Completely Available", free_count)
c3.metric("Partially / Fully Booked", partially_booked)
c4.metric("Under Maintenance", maintenance_count)

st.markdown("---")

# Quick Seat Inspector on Top
searched_seat_info = next((s for s in matrix if s["seat_number"] == search_seat), None)
if searched_seat_info:
    with st.expander(f"🔍 Seat #{search_seat} Detailed Schedule for {selected_date}", expanded=True):
        sc1, sc2, sc3 = st.columns(3)
        with sc1:
            st.markdown(f"**Seat Number**: `#{searched_seat_info['seat_number']}`")
            st.markdown(f"**Status**: {'🟢 Active' if searched_seat_info['is_active'] else '🔴 Maintenance'}")
            st.markdown(f"**Power Outlet**: {'⚡ Yes' if searched_seat_info.get('has_power_outlet') else 'No'}")
            st.markdown(f"**Locker**: {'🔐 Yes' if searched_seat_info.get('has_locker') else 'No'}")
        with sc2:
            st.markdown("#### Shift Status:")
            st.markdown(f"- **Morning (07-11)**: {'🟢 Free' if searched_seat_info['morning_available'] else f'🔴 Occupied by {searched_seat_info.get(\"morning_occupied_by\", \"Unknown\")}'}")
            st.markdown(f"- **Afternoon (11-15)**: {'🟢 Free' if searched_seat_info['afternoon_available'] else f'🔴 Occupied by {searched_seat_info.get(\"afternoon_occupied_by\", \"Unknown\")}'}")
            st.markdown(f"- **Evening (15-23)**: {'🟢 Free' if searched_seat_info['evening_available'] else f'🔴 Occupied by {searched_seat_info.get(\"evening_occupied_by\", \"Unknown\")}'}")
            st.markdown(f"- **Full Day (07-23)**: {'🟢 Free' if searched_seat_info['full_day_available'] else '🔴 Blocked'}")
        with sc3:
            st.markdown("#### Staff Actions:")
            if st.button(f"{'Disable (Mark Broken)' if searched_seat_info['is_active'] else 'Enable (Back to Service)'}", key=f"toggle_{search_seat}"):
                try:
                    api.toggle_seat_maintenance(searched_seat_info["seat_id"])
                    st.success(f"Seat #{search_seat} status toggled successfully!")
                    st.rerun()
                except Exception as ex:
                    st.error(f"Failed to toggle seat: {ex}")

# 10 x 10 Visual Layout Grid
st.markdown("### 🗺️ Physical Floor Map (100 Desks)")
st.caption("🟢 Completely Free | 🟡 Partially Booked | 🟣 Full Day Booked | 🔴 Maintenance")

# Render 10 rows of 10 seats
for row in range(10):
    cols = st.columns(10)
    for col in range(10):
        seat_num = row * 10 + col + 1
        s_data = next((s for s in matrix if s["seat_number"] == seat_num), None)
        if not s_data:
            cols[col].write(f"#{seat_num}")
            continue

        cat, label = get_seat_summary(s_data)

        # Apply Shift filter if selected
        if shift_filter.startswith("MORNING") and not s_data["morning_available"]:
            btn_label = f"#{seat_num} 🔴"
        elif shift_filter.startswith("AFTERNOON") and not s_data["afternoon_available"]:
            btn_label = f"#{seat_num} 🔴"
        elif shift_filter.startswith("EVENING") and not s_data["evening_available"]:
            btn_label = f"#{seat_num} 🔴"
        elif shift_filter.startswith("FULL_DAY") and not s_data["full_day_available"]:
            btn_label = f"#{seat_num} 🔴"
        elif cat == "MAINTENANCE":
            btn_label = f"#{seat_num} 🛠️"
        elif cat == "FULL_DAY_OCCUPIED":
            btn_label = f"#{seat_num} 🟣"
        elif cat == "PARTIAL":
            btn_label = f"#{seat_num} 🟡"
        else:
            btn_label = f"#{seat_num} 🟢"

        if cols[col].button(btn_label, key=f"grid_{seat_num}", use_container_width=True):
            st.session_state["selected_seat_quick"] = seat_num
            st.info(f"Seat #{seat_num}: Morning={'Free' if s_data['morning_available'] else 'Occupied'}, Afternoon={'Free' if s_data['afternoon_available'] else 'Occupied'}, Evening={'Free' if s_data['evening_available'] else 'Occupied'}")
