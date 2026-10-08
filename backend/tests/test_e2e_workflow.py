from datetime import date, timedelta
from fastapi.testclient import TestClient
from backend.app.core.config import settings


def test_complete_end_to_end_operational_lifecycle(client: TestClient):
    """
    Simulates a full real-world business day at the Smart Study Center:
    1. Staff authentication via JWT.
    2. Student onboarding / KYC registration.
    3. Seat allocation with conflict checks and partial payment.
    4. Front-desk biometric/web kiosk Check-In and Check-Out.
    5. Balance installment clearance via cashier terminal.
    6. Subscription renewal with seat/shift retention.
    7. Executive capacity & financial reporting audit.
    """
    # -------------------------------------------------------------------------
    # STEP 1: Staff Authentication
    # -------------------------------------------------------------------------
    auth_resp = client.post(
        f"{settings.API_V1_STR}/auth/login",
        json={
            "username": settings.INITIAL_ADMIN_USERNAME,
            "password": settings.INITIAL_ADMIN_PASSWORD
        }
    )
    assert auth_resp.status_code == 200, f"Login failed: {auth_resp.text}"
    token = auth_resp.json()["access_token"]
    auth_headers = {"Authorization": f"Bearer {token}"}

    # -------------------------------------------------------------------------
    # STEP 2: Student Registration
    # -------------------------------------------------------------------------
    student_payload = {
        "full_name": "Pooja Patel",
        "mobile_number": "9123456789",
        "email": "pooja.patel@example.com",
        "id_proof_type": "Aadhaar Card",
        "id_proof_number": "9988-7766-5544",
        "address": "42 Civil Lines, North Zone",
        "is_active": True
    }
    student_resp = client.post(f"{settings.API_V1_STR}/students", json=student_payload)
    assert student_resp.status_code == 201
    student_data = student_resp.json()
    student_id = student_data["id"]

    # -------------------------------------------------------------------------
    # STEP 3: Admission Booking (Seat 15, Morning Shift, Partial Payment)
    # -------------------------------------------------------------------------
    start_d = date.today()
    end_d = start_d + timedelta(days=29)

    admission_payload = {
        "student_id": student_id,
        "seat_id": 15,
        "shift_id": 1,  # MORNING (07:00 - 11:00, Rs. 800)
        "start_date": str(start_d),
        "end_date": str(end_d),
        "discount_amount": 50.0,  # Rs. 750 net fee
        "initial_payment_amount": 400.0,      # Partial payment
        "initial_payment_method": "UPI",
        "initial_payment_ref": "UPI/TXN/990011"
    }
    adm_resp = client.post(f"{settings.API_V1_STR}/memberships", json=admission_payload)
    assert adm_resp.status_code == 201
    mem_data = adm_resp.json()
    membership_id = mem_data["id"]
    assert float(mem_data["final_fee"]) == 750.0
    assert float(mem_data["paid_amount"]) == 400.0
    assert float(mem_data["due_amount"]) == 350.0
    assert mem_data["payment_status"] == "PARTIAL"

    # Verify conflict: Another student CANNOT book Seat 15 in the morning
    collision_payload = {
        "student_id": student_id,  # or another student
        "seat_id": 15,
        "shift_id": 1,  # MORNING
        "start_date": str(start_d),
        "end_date": str(end_d),
        "discount_amount": 0.0
    }
    collision_resp = client.post(f"{settings.API_V1_STR}/memberships", json=collision_payload)
    assert collision_resp.status_code == 409  # Conflict properly rejected!

    # -------------------------------------------------------------------------
    # STEP 4: Front-Desk Attendance Check-In & Check-Out
    # -------------------------------------------------------------------------
    check_in_resp = client.post(
        f"{settings.API_V1_STR}/attendance/check-in",
        json={
            "student_id": student_id,
            "membership_id": membership_id,
            "source": "MANUAL_STAFF"
        }
    )
    assert check_in_resp.status_code == 201
    attendance_record = check_in_resp.json()
    attendance_id = attendance_record["id"]
    assert attendance_record["status"] == "PRESENT"

    # Check-out student
    check_out_resp = client.post(f"{settings.API_V1_STR}/attendance/{attendance_id}/check-out")
    assert check_out_resp.status_code == 200
    assert check_out_resp.json()["check_out"] is not None
    assert check_out_resp.json()["status"] in ["HALF_DAY", "PRESENT"]

    # -------------------------------------------------------------------------
    # STEP 5: Cashier Balance Clearance
    # -------------------------------------------------------------------------
    pay_resp = client.post(
        f"{settings.API_V1_STR}/payments",
        json={
            "membership_id": membership_id,
            "student_id": student_id,
            "amount": 350.0,
            "payment_method": "CASH",
            "notes": "Cleared remaining due balance"
        }
    )
    assert pay_resp.status_code == 201
    receipt = pay_resp.json()
    assert receipt["status"] == "COMPLETED"
    assert "RCP-" in receipt["receipt_number"]

    # Verify membership is now marked PAID
    updated_mem = client.get(f"{settings.API_V1_STR}/memberships/{membership_id}").json()
    assert float(updated_mem["due_amount"]) == 0.0
    assert updated_mem["payment_status"] == "PAID"

    # -------------------------------------------------------------------------
    # STEP 6: Subscription Renewal
    # -------------------------------------------------------------------------
    renew_start = end_d + timedelta(days=1)
    renew_end = renew_start + timedelta(days=29)

    renew_resp = client.post(
        f"{settings.API_V1_STR}/memberships/{membership_id}/renew",
        json={
            "start_date": str(renew_start),
            "end_date": str(renew_end),
            "target_shift_id": 2,  # Migrate to AFTERNOON shift
            "discount_amount": 0.0,
            "initial_payment_amount": 800.0,
            "initial_payment_method": "CARD"
        }
    )
    assert renew_resp.status_code == 201
    renewed_mem = renew_resp.json()
    assert renewed_mem["renewed_from_id"] == membership_id
    assert renewed_mem["shift_name"] == "AFTERNOON"

    # -------------------------------------------------------------------------
    # STEP 7: Analytics & Capacity Audit
    # -------------------------------------------------------------------------
    dash_resp = client.get(f"{settings.API_V1_STR}/dashboard/summary?target_date={str(start_d)}")
    assert dash_resp.status_code == 200
    kpis = dash_resp.json()
    assert kpis["occupied_physical_seats"] >= 1
    assert kpis["slot_occupancy_rate"] > 0

    rev_resp = client.get(f"{settings.API_V1_STR}/reports/revenue")
    assert rev_resp.status_code == 200
    rev_data = rev_resp.json()
    assert float(rev_data["total_revenue"]) >= 1550.0  # 400 + 350 + 800
