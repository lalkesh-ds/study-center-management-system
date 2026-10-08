from datetime import date
from decimal import Decimal
from uuid import uuid4
from fastapi.testclient import TestClient


def create_mock_student(client: TestClient, name="Test Rahul", mobile="9876000001") -> str:
    res = client.post("/api/v1/students", json={
        "full_name": name,
        "mobile": mobile,
        "email": f"user{mobile}@example.com"
    })
    assert res.status_code == 201
    return res.json()["id"]


def test_membership_admission_success_no_payment(client: TestClient):
    """Verifies atomic admission without initial payment."""
    student_id = create_mock_student(client, "Arun Kumar", "9812345678")

    payload = {
        "student_id": student_id,
        "seat_id": 15,
        "shift_id": 1,  # MORNING
        "start_date": "2026-10-01",
        "end_date": "2026-10-31",
        "discount_amount": 100.00
    }
    res = client.post("/api/v1/memberships", json=payload)
    assert res.status_code == 201
    data = res.json()
    assert data["student_id"] == student_id
    assert data["seat_id"] == 15
    assert data["shift_name"] == "MORNING"
    assert Decimal(str(data["base_fee"])) == Decimal("800.00")
    assert Decimal(str(data["discount_amount"])) == Decimal("100.00")
    assert Decimal(str(data["final_fee"])) == Decimal("700.00")
    assert data["status"] == "ACTIVE"


def test_membership_admission_with_initial_payment(client: TestClient):
    """Verifies atomic admission with upfront fee collection creates payment ledger record."""
    student_id = create_mock_student(client, "Kavita Roy", "9812345679")

    payload = {
        "student_id": student_id,
        "seat_id": 20,
        "shift_id": 2,  # AFTERNOON (base 800)
        "start_date": "2026-10-01",
        "end_date": "2026-10-31",
        "discount_amount": 0.00,
        "initial_payment_amount": 500.00,
        "initial_payment_method": "UPI",
        "initial_payment_ref": "UPI-UTR-99887766"
    }
    res = client.post("/api/v1/memberships", json=payload)
    assert res.status_code == 201
    mem_id = res.json()["id"]

    # Check detail endpoint for ledger balances
    detail_res = client.get(f"/api/v1/memberships/{mem_id}")
    assert detail_res.status_code == 200
    detail = detail_res.json()
    assert Decimal(str(detail["total_paid"])) == Decimal("500.00")
    assert Decimal(str(detail["due_amount"])) == Decimal("300.00")
    assert detail["payment_status"] == "PARTIAL"


def test_membership_seat_conflict_rejected(client: TestClient):
    """TC-004: Booking the same seat for the same shift on overlapping dates must be rejected with 409."""
    student1 = create_mock_student(client, "Student 1", "9812345681")
    student2 = create_mock_student(client, "Student 2", "9812345682")

    # Student 1 books Seat 30 Morning
    res1 = client.post("/api/v1/memberships", json={
        "student_id": student1,
        "seat_id": 30,
        "shift_id": 1,
        "start_date": "2026-10-01",
        "end_date": "2026-10-31"
    })
    assert res1.status_code == 201

    # Student 2 tries to book Seat 30 Morning
    res2 = client.post("/api/v1/memberships", json={
        "student_id": student2,
        "seat_id": 30,
        "shift_id": 1,
        "start_date": "2026-10-15",
        "end_date": "2026-11-15"
    })
    assert res2.status_code == 409
    body = res2.json()
    assert body["error"]["code"] == "SEAT_ALREADY_BOOKED"


def test_membership_student_collision_rejected(client: TestClient):
    """TC-008: A student cannot hold 2 different seats for the same shift simultaneously."""
    student = create_mock_student(client, "Double Booker", "9812345683")

    # Book Seat 35 Morning
    client.post("/api/v1/memberships", json={
        "student_id": student,
        "seat_id": 35,
        "shift_id": 1,
        "start_date": "2026-10-01",
        "end_date": "2026-10-31"
    })

    # Try to book Seat 36 Morning for same student
    res = client.post("/api/v1/memberships", json={
        "student_id": student,
        "seat_id": 36,
        "shift_id": 1,
        "start_date": "2026-10-01",
        "end_date": "2026-10-31"
    })
    assert res.status_code == 409
    assert res.json()["error"]["code"] == "STUDENT_TIME_COLLISION"


def test_membership_inactive_seat_rejected(client: TestClient):
    """Booking an inactive/maintenance seat must be rejected with 400."""
    student = create_mock_student(client, "User Broken Desk", "9812345684")

    # Put Seat 5 into maintenance
    client.patch("/api/v1/seats/5/status", json={"is_active": False, "reason": "Under repair"})

    res = client.post("/api/v1/memberships", json={
        "student_id": student,
        "seat_id": 5,
        "shift_id": 1,
        "start_date": "2026-10-01",
        "end_date": "2026-10-31"
    })
    assert res.status_code == 400
    assert res.json()["error"]["code"] == "SEAT_INACTIVE"


def test_membership_invalid_discount_rejected(client: TestClient):
    """Discount higher than base fee must be rejected with 400."""
    student = create_mock_student(client, "User High Discount", "9812345685")

    res = client.post("/api/v1/memberships", json={
        "student_id": student,
        "seat_id": 12,
        "shift_id": 1,  # Base fee is 800
        "start_date": "2026-10-01",
        "end_date": "2026-10-31",
        "discount_amount": 950.00
    })
    assert res.status_code == 400
    assert res.json()["error"]["code"] == "INVALID_DISCOUNT"


def test_membership_overpayment_rejected(client: TestClient):
    """Initial payment exceeding final fee must be rejected with 400."""
    student = create_mock_student(client, "User Overpay", "9812345686")

    res = client.post("/api/v1/memberships", json={
        "student_id": student,
        "seat_id": 14,
        "shift_id": 1,  # Base fee 800
        "start_date": "2026-10-01",
        "end_date": "2026-10-31",
        "initial_payment_amount": 1200.00,
        "initial_payment_method": "CASH"
    })
    assert res.status_code == 400
    assert res.json()["error"]["code"] == "OVERPAYMENT"


def test_membership_list_and_pagination(client: TestClient):
    """Verifies listing and pagination for memberships."""
    student = create_mock_student(client, "User Multi List", "9812345687")
    client.post("/api/v1/memberships", json={
        "student_id": student,
        "seat_id": 70,
        "shift_id": 1,
        "start_date": "2026-10-01",
        "end_date": "2026-10-31"
    })

    res = client.get("/api/v1/memberships?seat_id=70")
    assert res.status_code == 200
    data = res.json()
    assert len(data["items"]) == 1
    assert data["items"][0]["seat_id"] == 70


def test_membership_renewal_same_seat_success(client: TestClient):
    """Verifies renewal creates new row, links renewed_from_id, and keeps old row intact."""
    student = create_mock_student(client, "Renewal Student", "9812345688")

    # Cycle 1: Oct 1 - Oct 31
    res1 = client.post("/api/v1/memberships", json={
        "student_id": student,
        "seat_id": 45,
        "shift_id": 1,
        "start_date": "2026-10-01",
        "end_date": "2026-10-31"
    })
    assert res1.status_code == 201
    old_id = res1.json()["id"]

    # Cycle 2 Renewal: Nov 1 - Nov 30
    res2 = client.post(f"/api/v1/memberships/{old_id}/renew", json={
        "start_date": "2026-11-01",
        "end_date": "2026-11-30"
    })
    assert res2.status_code == 201
    renewed = res2.json()
    assert renewed["renewed_from_id"] == old_id
    assert renewed["seat_id"] == 45
    assert renewed["shift_id"] == 1
    assert renewed["start_date"] == "2026-11-01"

    # Old membership still exists and active
    old_check = client.get(f"/api/v1/memberships/{old_id}")
    assert old_check.status_code == 200
    assert old_check.json()["status"] == "ACTIVE"


def test_membership_renewal_seat_change_success(client: TestClient):
    """Verifies renewing with seat migration to an available desk."""
    student = create_mock_student(client, "Seat Change User", "9812345689")

    res1 = client.post("/api/v1/memberships", json={
        "student_id": student,
        "seat_id": 46,
        "shift_id": 1,
        "start_date": "2026-10-01",
        "end_date": "2026-10-31"
    })
    old_id = res1.json()["id"]

    # Renew onto Seat 47
    res2 = client.post(f"/api/v1/memberships/{old_id}/renew", json={
        "start_date": "2026-11-01",
        "end_date": "2026-11-30",
        "target_seat_id": 47
    })
    assert res2.status_code == 201
    assert res2.json()["seat_id"] == 47


def test_membership_cancellation_and_immediate_seat_release(client: TestClient):
    """Verifies cancellation releases the seat immediately for another booking."""
    student1 = create_mock_student(client, "Canceller Student", "9812345690")
    student2 = create_mock_student(client, "New Booker", "9812345691")

    # Student 1 books Seat 55
    res1 = client.post("/api/v1/memberships", json={
        "student_id": student1,
        "seat_id": 55,
        "shift_id": 1,
        "start_date": "2026-10-01",
        "end_date": "2026-10-31"
    })
    mem_id = res1.json()["id"]

    # Student 1 cancels
    cancel_res = client.post(f"/api/v1/memberships/{mem_id}/cancel", json={
        "cancel_reason": "Relocating to another city for college"
    })
    assert cancel_res.status_code == 200
    assert cancel_res.json()["status"] == "CANCELLED"
    assert cancel_res.json()["derived_status"] == "CANCELLED"

    # Student 2 can now immediately book Seat 55 for same slot!
    res2 = client.post("/api/v1/memberships", json={
        "student_id": student2,
        "seat_id": 55,
        "shift_id": 1,
        "start_date": "2026-10-01",
        "end_date": "2026-10-31"
    })
    assert res2.status_code == 201
    assert res2.json()["seat_id"] == 55


def test_cannot_renew_cancelled_membership(client: TestClient):
    """Verifies that cancelled memberships cannot be renewed."""
    student = create_mock_student(client, "User Cancel Renew", "9812345692")

    mem_id = client.post("/api/v1/memberships", json={
        "student_id": student,
        "seat_id": 58,
        "shift_id": 1,
        "start_date": "2026-10-01",
        "end_date": "2026-10-31"
    }).json()["id"]

    # Cancel
    client.post(f"/api/v1/memberships/{mem_id}/cancel", json={"cancel_reason": "Personal reasons"})

    # Try renew -> 400 CANNOT_RENEW_CANCELLED
    renew_res = client.post(f"/api/v1/memberships/{mem_id}/renew", json={
        "start_date": "2026-11-01",
        "end_date": "2026-11-30"
    })
    assert renew_res.status_code == 400
    assert renew_res.json()["error"]["code"] == "CANNOT_RENEW_CANCELLED"
