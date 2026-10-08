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
from datetime import datetime
import pandas as pd

try:
    from frontend.streamlit_app.api_client import APIClient
except ImportError:
    from api_client import APIClient

st.set_page_config(page_title="Cashier & Payments - Smart Library", page_icon="💳", layout="wide")

if "api_client" not in st.session_state:
    st.session_state["api_client"] = APIClient()

api: APIClient = st.session_state["api_client"]
if st.session_state.get("token"):
    api.set_token(st.session_state["token"])

st.title("💳 Cashier Terminal & Financial Ledger")
st.caption("Collect dues installments, generate formal receipts, and manage immutable ledger entries")

tabs = st.tabs(["💰 Collect Installment / Dues", "🧾 Payment Receipts & Ledger", "🚫 Void Payment (Admin Only)"])

# -----------------------------------------------------------------------------
# TAB 1: Collect Installment / Dues
# -----------------------------------------------------------------------------
with tabs[0]:
    st.subheader("💰 Outstanding Dues Collection")

    # Fetch memberships with due_amount > 0
    try:
        active_mems = api.get_memberships(status="ACTIVE", limit=200)
        due_mems = [m for m in active_mems if float(m["due_amount"]) > 0]
    except Exception as e:
        due_mems = []
        st.error(f"Error fetching dues: {e}")

    if not due_mems:
        st.success("🎉 All active student subscriptions are fully paid up! Zero outstanding dues.")
    else:
        st.warning(f"⚠️ {len(due_mems)} student subscriptions currently have pending fee balances.")
        
        due_choices = {
            f"{m['student_name']} | Seat #{m['seat_number']} ({m['shift_name']}) | Due: ₹{m['due_amount']}": m
            for m in due_mems
        }
        selected_due_key = st.selectbox("Select Student Account", list(due_choices.keys()))
        target_due_mem = due_choices[selected_due_key]

        dc1, dc2 = st.columns(2)
        with dc1:
            st.markdown(f"### Student: **{target_due_mem['student_name']}**")
            st.markdown(f"- **Seat**: `#{target_due_mem['seat_number']}` ({target_due_mem['shift_name']})")
            st.markdown(f"- **Total Fee**: ₹{target_due_mem['final_fee']}")
            st.markdown(f"- **Already Paid**: ₹{target_due_mem['paid_amount']}")
            st.markdown(f"- **Pending Due**: :red[**₹{target_due_mem['due_amount']}**]")

        with dc2:
            st.markdown("### Record Installment")
            with st.form("collect_due_form", clear_on_submit=True):
                max_due = float(target_due_mem['due_amount'])
                pay_amount = st.number_input("Payment Amount (₹) *", min_value=1.0, max_value=max_due, value=max_due, step=50.0)
                pay_method = st.selectbox("Payment Method *", ["CASH", "UPI", "CARD", "NET_BANKING"])
                txn_ref = st.text_input("Transaction / UPI Reference", placeholder="e.g. UPI-REF-99210")
                notes = st.text_input("Internal Remarks", placeholder="e.g. Second installment paid in cash")

                submit_pay = st.form_submit_button("💳 Process Payment & Issue Receipt", type="primary", use_container_width=True)
                if submit_pay:
                    payload = {
                        "membership_id": target_due_mem["id"],
                        "student_id": target_due_mem["student_id"],
                        "amount": pay_amount,
                        "payment_method": pay_method,
                        "transaction_ref": txn_ref if txn_ref else None,
                        "notes": notes if notes else None
                    }
                    try:
                        res = api.create_payment(payload)
                        st.success(f"Payment recorded! Receipt Number: `{res['receipt_number']}`")
                        st.session_state["last_receipt"] = res
                        st.session_state["last_receipt_mem"] = target_due_mem
                    except Exception as ex:
                        st.error(f"Payment failed: {ex}")

    # Display receipt if just created
    if "last_receipt" in st.session_state:
        r = st.session_state["last_receipt"]
        m = st.session_state["last_receipt_mem"]
        st.markdown("---")
        with st.container():
            st.success("### 🧾 Official Fee Receipt")
            rc1, rc2 = st.columns(2)
            with rc1:
                st.markdown(f"**Receipt No**: `{r['receipt_number']}`")
                st.markdown(f"**Date**: {r['created_at'][:19].replace('T', ' ')}")
                st.markdown(f"**Student**: {m['student_name']}")
                st.markdown(f"**Seat Number**: #{m['seat_number']} ({m['shift_name']})")
            with rc2:
                st.markdown(f"**Amount Paid**: ₹{r['amount']}")
                st.markdown(f"**Payment Method**: {r['payment_method']}")
                st.markdown(f"**Status**: `COMPLETED`")
                st.markdown(f"**Remaining Due**: ₹{float(m['due_amount']) - float(r['amount']):.2f}")

# -----------------------------------------------------------------------------
# TAB 2: Payment Receipts & Ledger
# -----------------------------------------------------------------------------
with tabs[1]:
    st.subheader("🧾 Historical Financial Ledger")
    
    # Pick a membership to view payments
    try:
        all_memberships = api.get_memberships(limit=100)
    except Exception:
        all_memberships = []

    if not all_memberships:
        st.info("No memberships found.")
    else:
        m_map = {f"Seat #{m['seat_number']} - {m['student_name']} ({m['shift_name']})": m for m in all_memberships}
        sel_m_key = st.selectbox("Inspect Ledger for Membership", list(m_map.keys()), key="ledger_select")
        chosen_m = m_map[sel_m_key]

        try:
            payments = api.get_membership_payments(chosen_m["id"])
            if not payments:
                st.info("No payment records for this subscription yet.")
            else:
                p_rows = []
                for p in payments:
                    p_rows.append({
                        "Receipt #": p["receipt_number"],
                        "Amount": f"₹{p['amount']}",
                        "Method": p["payment_method"],
                        "Status": "🟢 COMPLETED" if p["status"] == "COMPLETED" else "🔴 VOIDED",
                        "Txn Ref": p.get("transaction_ref") or "—",
                        "Date": p["created_at"][:19].replace("T", " "),
                        "Void Reason": p.get("void_reason") or "—"
                    })
                st.dataframe(pd.DataFrame(p_rows), use_container_width=True)
        except Exception as e:
            st.error(f"Error loading payments: {e}")

# -----------------------------------------------------------------------------
# TAB 3: Void Payment (Admin Only)
# -----------------------------------------------------------------------------
with tabs[2]:
    st.subheader("🚫 Void Payment Entry")
    st.caption("Administrative protection: Marks a transaction VOIDED and immediately restores student's due balance.")

    user = st.session_state.get("user")
    if not user or user.get("role") != "ADMIN":
        st.warning("🔒 Administrative Privileges Required. Only users with role `ADMIN` may void payment records.")
    else:
        receipt_lookup = st.text_input("Enter Receipt Number to Void", placeholder="e.g. REC-20261008-ABCD12")
        void_reason = st.text_input("Mandatory Void Reason *", placeholder="e.g. Staff double-entry typo, incorrect payment method")

        if st.button("Confirm Void Transaction", type="secondary"):
            if not receipt_lookup.strip() or not void_reason.strip():
                st.error("Please enter both Receipt Number and Void Reason.")
            else:
                # Find payment by receipt number
                found_payment = None
                try:
                    for m in all_memberships:
                        plist = api.get_membership_payments(m["id"])
                        for p in plist:
                            if p["receipt_number"].strip() == receipt_lookup.strip():
                                found_payment = p
                                break
                        if found_payment:
                            break
                    
                    if not found_payment:
                        st.error(f"Receipt '{receipt_lookup}' not found.")
                    else:
                        api.void_payment(found_payment["id"], {"void_reason": void_reason.strip()})
                        st.success(f"Payment `{receipt_lookup}` successfully VOIDED. Dues balance has been restored.")
                except Exception as ex:
                    st.error(f"Void failed: {ex}")
