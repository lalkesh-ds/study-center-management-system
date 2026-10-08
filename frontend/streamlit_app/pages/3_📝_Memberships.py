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
from decimal import Decimal
import pandas as pd

try:
    from frontend.streamlit_app.api_client import APIClient
except ImportError:
    from api_client import APIClient

st.set_page_config(page_title="Memberships - Smart Library", page_icon="📝", layout="wide")

if "api_client" not in st.session_state:
    st.session_state["api_client"] = APIClient()

api: APIClient = st.session_state["api_client"]
if st.session_state.get("token"):
    api.set_token(st.session_state["token"])

st.title("📝 Membership Admissions, Renewals & Lifecycle")
st.caption("Deterministic seat allocation, automated conflict prevention, renewals, and cancellations")

tabs = st.tabs(["➕ New Student Admission", "🔄 Subscription Renewals", "❌ Cancellations", "📋 All Memberships"])

# Load master shifts and active seats
try:
    shifts = api.get_shifts()
    shift_map = {s["name"]: s for s in shifts}
except Exception as e:
    st.error(f"Failed to fetch shifts: {e}")
    shifts = []
    shift_map = {}

# -----------------------------------------------------------------------------
# TAB 1: New Admission Booking
# -----------------------------------------------------------------------------
with tabs[0]:
    st.subheader("➕ New Desk Admission")

    # Fetch students for dropdown
    students = []
    try:
        students = api.get_students(limit=200)
        if isinstance(students, dict):
            students = students.get("items", [])
    except Exception:
        pass

    if not students:
        st.warning("No students registered yet. Please register a student first in the Students page.")
    else:
        student_choices = {
            f"{s['full_name']} ({s.get('mobile_number') or s.get('mobile', 'No Mobile')})": s["id"]
            for s in students
        }
        
        col1, col2 = st.columns(2)
        with col1:
            sel_student_label = st.selectbox("Select Student *", list(student_choices.keys()), key="admit_student")
            student_id = student_choices[sel_student_label]
            
            seat_number = st.number_input("Physical Seat Number (1-100) *", min_value=1, max_value=100, value=1, step=1)
            
            shift_names = list(shift_map.keys()) if shift_map else ["MORNING", "AFTERNOON", "EVENING", "FULL_DAY"]
            selected_shift_name = st.selectbox("Select Shift *", shift_names, key="admit_shift")
            selected_shift = shift_map.get(selected_shift_name, {})
            shift_id = selected_shift.get("id", 1)
            base_fee = float(selected_shift.get("base_fee", 800.0))

        with col2:
            today = date.today()
            start_date = st.date_input("Start Date *", value=today, key="admit_start")
            # Default to 30 days
            default_end = start_date + timedelta(days=29)
            end_date = st.date_input("End Date (Inclusive) *", value=default_end, key="admit_end")
            
            discount = st.number_input("Discount Amount (₹)", min_value=0.0, max_value=float(base_fee), value=0.0, step=50.0)
            final_fee = max(0.0, base_fee - discount)
            st.info(f"💰 **Base Fee**: ₹{base_fee:.2f} | **Discount**: ₹{discount:.2f} | **Final Payable**: ₹{final_fee:.2f}")

        st.markdown("---")
        st.subheader("💳 Initial Payment Collection (Optional)")
        pay_col1, pay_col2, pay_col3 = st.columns(3)
        with pay_col1:
            collect_payment = st.checkbox("Collect payment at admission time", value=True)
            payment_amount = st.number_input("Amount Collected (₹)", min_value=0.0, max_value=float(final_fee), value=float(final_fee) if collect_payment else 0.0, step=50.0)
        with pay_col2:
            pay_method = st.selectbox("Payment Method", ["CASH", "UPI", "CARD", "NET_BANKING"])
        with pay_col3:
            txn_ref = st.text_input("Transaction / UPI Reference (Optional)", placeholder="e.g. UPI/123456789")

        if st.button("🚀 Confirm and Book Desk Allocation", type="primary", width="stretch"):
            if start_date > end_date:
                st.error("Start Date cannot be after End Date.")
            else:
                payload = {
                    "student_id": student_id,
                    "seat_id": int(seat_number),
                    "shift_id": shift_id,
                    "start_date": str(start_date),
                    "end_date": str(end_date),
                    "discount_amount": discount,
                    "initial_payment_amount": payment_amount if (collect_payment and payment_amount > 0) else None,
                    "initial_payment_method": pay_method if (collect_payment and payment_amount > 0) else None,
                    "initial_payment_ref": txn_ref if (collect_payment and payment_amount > 0 and txn_ref) else None
                }

                try:
                    res = api.create_membership(payload)
                    st.success(f"🎉 Admission successfully created! Membership ID: `{res['id']}` for Seat #{seat_number} ({selected_shift_name})")
                except Exception as ex:
                    st.error(f"❌ Booking Rejected: {ex}")

# -----------------------------------------------------------------------------
# TAB 2: Renewals
# -----------------------------------------------------------------------------
with tabs[1]:
    st.subheader("🔄 Subscription Renewal Desk")
    st.caption("Extends student tenure with full historical audit lineage preservation")

    try:
        active_memberships = api.get_memberships(status="ACTIVE", limit=100)
        if isinstance(active_memberships, dict):
            active_memberships = active_memberships.get("items", [])
    except Exception:
        active_memberships = []

    if not active_memberships:
        st.info("No active memberships available for renewal.")
    else:
        mem_choices = {
            f"Seat #{m.get('seat_number', m.get('seat_id'))} - {m.get('student_name', 'Student')} ({m.get('shift_name', 'Shift')} | Ends {m.get('end_date')} )": m
            for m in active_memberships
        }
        selected_mem_key = st.selectbox("Select Active Subscription to Renew", list(mem_choices.keys()))
        target_mem = mem_choices[selected_mem_key]

        # Pre-populate renewal defaults
        curr_end = date.fromisoformat(target_mem["end_date"])
        renew_start_default = curr_end + timedelta(days=1)
        renew_end_default = renew_start_default + timedelta(days=29)

        rc1, rc2 = st.columns(2)
        with rc1:
            renew_start = st.date_input("Renewal Start Date", value=renew_start_default, key="renew_start")
            renew_end = st.date_input("Renewal End Date (Inclusive)", value=renew_end_default, key="renew_end")
            retain_seat = st.checkbox("Retain Same Seat", value=True)
            if retain_seat:
                renew_seat_id = target_mem["seat_id"]
                st.write(f"Assigned Seat: **#{target_mem['seat_number']}**")
            else:
                renew_seat_id = st.number_input("Migrate to New Seat #", min_value=1, max_value=100, value=target_mem["seat_number"], step=1)

        with rc2:
            retain_shift = st.checkbox("Retain Same Shift", value=True)
            if retain_shift:
                renew_shift_id = target_mem["shift_id"]
                st.write(f"Assigned Shift: **{target_mem['shift_name']}**")
            else:
                renew_shift_name = st.selectbox("Select New Shift", list(shift_map.keys()), key="renew_new_shift")
                renew_shift_id = shift_map[renew_shift_name]["id"]

            renew_discount = st.number_input("Renewal Discount (₹)", min_value=0.0, value=0.0, step=50.0)

        # Initial renewal payment
        r_pay1, r_pay2 = st.columns(2)
        with r_pay1:
            r_pay_amount = st.number_input("Initial Renewal Payment (₹)", min_value=0.0, value=0.0, step=100.0)
        with r_pay2:
            r_pay_method = st.selectbox("Renewal Payment Method", ["CASH", "UPI", "CARD", "NET_BANKING"], key="r_pay_meth")

        if st.button("🔄 Execute Subscription Renewal", type="primary", width="stretch"):
            renewal_payload = {
                "start_date": str(renew_start),
                "end_date": str(renew_end),
                "target_seat_id": int(renew_seat_id) if not retain_seat else None,
                "target_shift_id": int(renew_shift_id) if not retain_shift else None,
                "discount_amount": renew_discount,
                "initial_payment_amount": r_pay_amount if r_pay_amount > 0 else None,
                "initial_payment_method": r_pay_method if r_pay_amount > 0 else None
            }
            try:
                renewed = api.renew_membership(target_mem["id"], renewal_payload)
                st.success(f"🎉 Membership renewed successfully! New Subscription ID: `{renewed['id']}` (Valid {renewed['start_date']} to {renewed['end_date']})")
            except Exception as e:
                st.error(f"Renewal Failed: {e}")

# -----------------------------------------------------------------------------
# TAB 3: Cancellations
# -----------------------------------------------------------------------------
with tabs[2]:
    st.subheader("❌ Early Subscription Cancellation")
    st.caption("Releases seat inventory immediately to the availability pool while preserving accounting ledger")

    try:
        active_list = api.get_memberships(status="ACTIVE", limit=100)
        if isinstance(active_list, dict):
            active_list = active_list.get("items", [])
    except Exception:
        active_list = []

    if not active_list:
        st.info("No active memberships to cancel.")
    else:
        cancel_choices = {
            f"Seat #{m.get('seat_number', m.get('seat_id'))} - {m.get('student_name', 'Student')} ({m.get('shift_name', 'Shift')} | {m.get('start_date')} to {m.get('end_date')})": m
            for m in active_list
        }
        sel_cancel_key = st.selectbox("Select Subscription to Terminate", list(cancel_choices.keys()))
        cancel_target = cancel_choices[sel_cancel_key]

        cancel_reason = st.text_input("Mandatory Reason for Cancellation *", placeholder="e.g. Relocating, Exam completed, Medical reasons")
        if st.button("⚠️ Confirm and Terminate Subscription", type="secondary", width="stretch"):
            if not cancel_reason.strip():
                st.error("Please enter a valid cancellation reason.")
            else:
                try:
                    c_res = api.cancel_membership(cancel_target["id"], {"cancel_reason": cancel_reason.strip()})
                    st.success(f"Subscription for Seat #{cancel_target['seat_number']} successfully cancelled. Desk inventory is now freed!")
                except Exception as ex:
                    st.error(f"Cancellation failed: {ex}")

# -----------------------------------------------------------------------------
# TAB 4: All Memberships Table
# -----------------------------------------------------------------------------
with tabs[3]:
    st.subheader("📋 Master Subscriptions Table")
    status_filter = st.selectbox("Filter Status", ["ALL", "ACTIVE", "CANCELLED"])
    try:
        all_mems = api.get_memberships(
            status=status_filter if status_filter != "ALL" else None,
            limit=100
        )
        if isinstance(all_mems, dict):
            all_mems = all_mems.get("items", [])
        if not all_mems:
            st.info("No memberships match the criteria.")
        else:
            table_rows = []
            for m in all_mems:
                table_rows.append({
                    "Seat": f"#{m.get('seat_number', m.get('seat_id', '—'))}",
                    "Student": m.get("student_name", "—"),
                    "Shift": m.get("shift_name", "—"),
                    "Start Date": m.get("start_date", "—"),
                    "End Date": m.get("end_date", "—"),
                    "Status": m.get("status", "—"),
                    "Final Fee": f"₹{m.get('final_fee', 0)}",
                    "Paid": f"₹{m.get('total_paid', m.get('paid_amount', 0))}",
                    "Due": f"₹{m.get('due_amount', 0)}",
                    "Payment State": m.get("payment_status", "—"),
                })
            df = pd.DataFrame(table_rows)
            st.dataframe(df, width="stretch")
    except Exception as e:
        st.error(f"Failed to load memberships: {e}")
