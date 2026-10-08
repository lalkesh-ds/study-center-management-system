from datetime import date, timedelta
from fastapi.testclient import TestClient


def create_active_student_and_membership(client: TestClient, seat_id=60):
    today = date.today()
    start = today - timedelta(days=5)
    end = today + timedelta(days=25)

    res_stu = client.post("/api/v1/students", json={
        "full_name": f"Attendance User {seat_id}",
        "mobile": f"98880000{seat_id:02d}",
        "email": f"attuser{seat_id}@example.com"
    })
    student_id = res_stu.json()["id"]

    res_mem = client.post("/api/v1/memberships", json={
        "student_id": student_id,
        "seat_id": seat_id,
        "shift_id": 1,
        "start_date": str(start),
        "end_date": str(end),
        "discount_amount": 0.00
    })
    mem_id = res_mem.json()["id"]
    return student_id, mem_id


def test_check_in_active_membership_success(client: TestClient):
    """Verifies that an enrolled student with an active subscription can check in."""
    student_id, mem_id = create_active_student_and_membership(client, seat_id=61)

    res = client.post("/api/v1/attendance/check-in", json={
        "student_id": student_id,
        "source": "MANUAL_STAFF",
        "notes": "Entered front door"
    })
    assert res.status_code == 201
    data = res.json()
    assert data["status"] == "PRESENT"
    assert data["student_id"] == student_id
    assert data["membership_id"] == mem_id
    assert "check_in" in data


def test_check_in_no_active_membership_rejected(client: TestClient):
    """Verifies that check-in is blocked if the student has no active subscription for today."""
    # Student with expired subscription (last month)
    res_stu = client.post("/api/v1/students", json={
        "full_name": "Expired Student",
        "mobile": "9888000099",
        "email": "expired@example.com"
    })
    student_id = res_stu.json()["id"]

    past_start = date.today() - timedelta(days=60)
    past_end = date.today() - timedelta(days=30)
    client.post("/api/v1/memberships", json={
        "student_id": student_id,
        "seat_id": 62,
        "shift_id": 1,
        "start_date": str(past_start),
        "end_date": str(past_end)
    })

    # Attempt check in today -> 400 NO_ACTIVE_MEMBERSHIP_TODAY
    res = client.post("/api/v1/attendance/check-in", json={"student_id": student_id})
    assert res.status_code == 400
    assert res.json()["error"]["code"] == "NO_ACTIVE_MEMBERSHIP_TODAY"


def test_check_in_duplicate_rejected(client: TestClient):
    """Verifies that check-in cannot be recorded twice for the same student shift on the same day."""
    student_id, mem_id = create_active_student_and_membership(client, seat_id=63)

    # 1. First check-in -> Success
    res1 = client.post("/api/v1/attendance/check-in", json={"student_id": student_id})
    assert res1.status_code == 201

    # 2. Second check-in -> 409 ALREADY_CHECKED_IN
    res2 = client.post("/api/v1/attendance/check-in", json={"student_id": student_id})
    assert res2.status_code == 409
    assert res2.json()["error"]["code"] == "ALREADY_CHECKED_IN"


def test_check_out_workflow(client: TestClient):
    """Verifies completing check-out and calculating study duration."""
    student_id, mem_id = create_active_student_and_membership(client, seat_id=64)

    # Check-in
    att_id = client.post("/api/v1/attendance/check-in", json={"student_id": student_id}).json()["id"]

    # Check-out
    res_out = client.post(f"/api/v1/attendance/{att_id}/check-out", json={})
    assert res_out.status_code == 200
    data = res_out.json()
    assert data["check_out"] is not None

    # Duplicate check-out -> 400 ALREADY_CHECKED_OUT
    res_dup = client.post(f"/api/v1/attendance/{att_id}/check-out", json={})
    assert res_dup.status_code == 400
    assert res_dup.json()["error"]["code"] == "ALREADY_CHECKED_OUT"


def test_list_daily_attendance(client: TestClient):
    """Verifies listing today's attendance logs."""
    student_id, mem_id = create_active_student_and_membership(client, seat_id=65)
    client.post("/api/v1/attendance/check-in", json={"student_id": student_id})

    res = client.get("/api/v1/attendance/daily")
    assert res.status_code == 200
    logs = res.json()
    assert len(logs) >= 1
    assert any(l["student_id"] == student_id for l in logs)
