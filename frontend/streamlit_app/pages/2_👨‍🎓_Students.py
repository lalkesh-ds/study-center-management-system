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
import pandas as pd

try:
    from frontend.streamlit_app.api_client import APIClient
except ImportError:
    from api_client import APIClient

st.set_page_config(page_title="Students Directory - Smart Library", page_icon="👨‍🎓", layout="wide")

if "api_client" not in st.session_state:
    st.session_state["api_client"] = APIClient()

api: APIClient = st.session_state["api_client"]
if st.session_state.get("token"):
    api.set_token(st.session_state["token"])

st.title("👨‍🎓 Students Directory & Admission Profiles")
st.caption("Manage registered aspirants, ID records, contact verification, and membership records")

tabs = st.tabs(["📋 Student Directory", "➕ Register New Student", "🔍 Student Profile & History"])

# -----------------------------------------------------------------------------
# TAB 1: Student Directory
# -----------------------------------------------------------------------------
with tabs[0]:
    c_search, c_limit = st.columns([3, 1])
    with c_search:
        search_query = st.text_input("🔍 Search Students (by Name or Mobile)", placeholder="e.g. Rahul or 9876543210")
    with c_limit:
        limit = st.selectbox("Show rows", [20, 50, 100], index=1)

    try:
        students = api.get_students(search=search_query if search_query else None, limit=limit)
        if isinstance(students, dict):
            students = students.get("items", [])
        if not students:
            st.info("No student records found matching search criteria.")
        else:
            table_data = []
            for s in students:
                mobile = s.get("mobile_number") or s.get("mobile") or "—"
                table_data.append({
                    "Student ID": str(s["id"])[:8] + "...",
                    "Full Name": s["full_name"],
                    "Mobile Number": mobile,
                    "Email": s.get("email") or "—",
                    "Status": "🟢 Active" if s.get("is_active", True) else "🔴 Inactive",
                    "Registered On": str(s.get("created_at", ""))[:10],
                    "_id": s["id"]
                })
            df = pd.DataFrame(table_data)
            st.dataframe(df[["Full Name", "Mobile Number", "Email", "Status", "Registered On"]], width="stretch")

    except Exception as e:
        st.error(f"Failed to fetch students: {e}")

# -----------------------------------------------------------------------------
# TAB 2: Register New Student
# -----------------------------------------------------------------------------
with tabs[1]:
    st.subheader("➕ Aspirant Registration Form")
    with st.form("new_student_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            full_name = st.text_input("Full Name *", placeholder="e.g. Rahul Sharma")
            mobile_number = st.text_input("Mobile Number (10 Digits) *", placeholder="e.g. 9876543210", max_chars=10)
            email = st.text_input("Email Address (Optional)", placeholder="e.g. rahul@example.com")
        with col2:
            id_proof_type = st.selectbox("ID Proof Type", ["Aadhaar Card", "PAN Card", "Driving License", "College ID", "Passport"])
            id_proof_number = st.text_input("ID Proof Number (Optional)", placeholder="e.g. 1234-5678-9012")
            address = st.text_area("Residential Address (Optional)", placeholder="Street, City, Pincode")

        submitted = st.form_submit_button("Register Student", width="stretch")
        if submitted:
            if not full_name or not mobile_number:
                st.error("Please fill in both Full Name and Mobile Number.")
            elif len(mobile_number) != 10 or not mobile_number.isdigit():
                st.error("Mobile Number must be exactly 10 digits.")
            else:
                payload = {
                    "full_name": full_name.strip(),
                    "mobile_number": mobile_number.strip(),
                    "email": email.strip() if email else None,
                    "id_proof_type": id_proof_type,
                    "id_proof_number": id_proof_number.strip() if id_proof_number else None,
                    "address": address.strip() if address else None,
                    "is_active": True
                }
                try:
                    res = api.create_student(payload)
                    st.success(f"Student **{res['full_name']}** successfully registered! ID: `{res['id']}`")
                except Exception as ex:
                    st.error(f"Registration failed: {ex}")

# -----------------------------------------------------------------------------
# TAB 3: Student Profile & History
# -----------------------------------------------------------------------------
with tabs[2]:
    st.subheader("🔍 Student Profile Lookup")
    all_students = []
    try:
        all_students = api.get_students(limit=100)
        if isinstance(all_students, dict):
            all_students = all_students.get("items", [])
    except Exception:
        pass

    if not all_students:
        st.warning("No students available to select.")
    else:
        student_options = {
            f"{s['full_name']} ({s.get('mobile_number') or s.get('mobile', 'No Mobile')})": s["id"]
            for s in all_students
        }
        selected_label = st.selectbox("Select Student", list(student_options.keys()))
        selected_student_id = student_options[selected_label]

        try:
            student_profile = api.get_student(selected_student_id)
            sp1, sp2 = st.columns(2)
            with sp1:
                st.markdown(f"### {student_profile['full_name']}")
                mobile_disp = student_profile.get('mobile_number') or student_profile.get('mobile', '—')
                st.markdown(f"📱 **Mobile**: `{mobile_disp}`")
                st.markdown(f"✉️ **Email**: `{student_profile.get('email') or 'Not Provided'}`")
                st.markdown(f"🆔 **ID Document**: {student_profile.get('id_proof_type') or 'N/A'} - `{student_profile.get('id_proof_number') or 'N/A'}`")
                st.markdown(f"🏠 **Address**: {student_profile.get('address') or 'N/A'}")
            
            with sp2:
                # Memberships for this student
                memberships = api.get_memberships(student_id=selected_student_id)
                if isinstance(memberships, dict):
                    memberships = memberships.get("items", [])
                st.markdown(f"### 📋 Membership Subscriptions ({len(memberships)})")
                if not memberships:
                    st.info("No memberships booked for this student yet.")
                else:
                    for m in memberships:
                        status_color = "🟢" if m["status"] == "ACTIVE" else "🔴"
                        paid_disp = m.get('total_paid', m.get('paid_amount', 0))
                        due_disp = m.get('due_amount', 0)
                        st.markdown(
                            f"- {status_color} **Seat #{m['seat_number']}** ({m['shift_name']}) | "
                            f"{m['start_date']} to {m['end_date']} | "
                            f"Fee: ₹{m['final_fee']} (Paid: ₹{paid_disp}, Due: ₹{due_disp})"
                        )
        except Exception as err:
            st.error(f"Error fetching profile: {err}")
