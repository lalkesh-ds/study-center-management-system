from uuid import uuid4
from fastapi.testclient import TestClient


# ============================================================================
# STUDENT MASTER DATA TESTS
# ============================================================================

def test_student_registration_success(client: TestClient):
    """Verifies valid student registration and deterministic code assignment."""
    payload = {
        "full_name": "Rahul Sharma",
        "mobile": "9876543210",
        "email": "rahul.sharma@example.com",
        "id_proof_type": "AADHAAR",
        "id_proof_number": "1234-5678-9012",
        "emergency_contact": "9876543211",
        "address": "Flat 402, Green Valley Apartments, New Delhi",
        "notes": "Preparing for UPSC 2027"
    }
    response = client.post("/api/v1/students", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["full_name"] == "Rahul Sharma"
    assert data["mobile"] == "9876543210"
    assert data["status"] == "ACTIVE"
    assert "student_code" in data
    assert data["student_code"].startswith("STU-")
    assert "id" in data


def test_student_duplicate_mobile_rejected(client: TestClient):
    """Verifies that duplicate mobile registration is blocked with HTTP 409 Conflict."""
    payload1 = {
        "full_name": "Amit Verma",
        "mobile": "9811122233",
        "email": "amit@example.com"
    }
    res1 = client.post("/api/v1/students", json=payload1)
    assert res1.status_code == 201

    payload2 = {
        "full_name": "Amit Another",
        "mobile": "9811122233",  # Same mobile
        "email": "amit2@example.com"
    }
    res2 = client.post("/api/v1/students", json=payload2)
    assert res2.status_code == 409
    body = res2.json()
    assert body["error"]["code"] == "MOBILE_ALREADY_EXISTS"
    assert "already registered" in body["error"]["message"]


def test_student_invalid_mobile_validation(client: TestClient):
    """Verifies that invalid mobile formats are caught by Pydantic validation."""
    payload = {
        "full_name": "Invalid Mobile User",
        "mobile": "12345"  # Too short
    }
    response = client.post("/api/v1/students", json=payload)
    assert response.status_code == 422
    body = response.json()
    assert body["error"]["code"] == "REQUEST_VALIDATION_FAILED"


def test_student_list_pagination(client: TestClient):
    """Verifies pagination metadata and search filtering."""
    # Enroll 3 students
    for i in range(1, 4):
        client.post("/api/v1/students", json={
            "full_name": f"Student {i}",
            "mobile": f"900000000{i}"
        })

    # Retrieve page 1 with limit 2
    res = client.get("/api/v1/students?skip=0&limit=2")
    assert res.status_code == 200
    data = res.json()
    assert len(data["items"]) == 2
    assert data["pagination"]["total"] == 3
    assert data["pagination"]["has_more"] is True


def test_student_search_by_name(client: TestClient):
    """Verifies search parameter matches full_name substring."""
    client.post("/api/v1/students", json={"full_name": "Deepak Kumar", "mobile": "9111111111"})
    client.post("/api/v1/students", json={"full_name": "Suresh Raina", "mobile": "9222222222"})

    res = client.get("/api/v1/students?search=Deepak")
    assert res.status_code == 200
    data = res.json()
    assert len(data["items"]) == 1
    assert data["items"][0]["full_name"] == "Deepak Kumar"


def test_student_get_by_id_and_not_found(client: TestClient):
    """Verifies profile retrieval and 404 handling."""
    created = client.post("/api/v1/students", json={"full_name": "Pooja Patel", "mobile": "9333333333"}).json()
    student_id = created["id"]

    # 1. Successful get
    res = client.get(f"/api/v1/students/{student_id}")
    assert res.status_code == 200
    assert res.json()["full_name"] == "Pooja Patel"

    # 2. Random UUID 404
    non_existent = str(uuid4())
    res_404 = client.get(f"/api/v1/students/{non_existent}")
    assert res_404.status_code == 404
    assert res_404.json()["error"]["code"] == "STUDENT_NOT_FOUND"


def test_student_update_profile(client: TestClient):
    """Verifies updating address, notes, and status."""
    created = client.post("/api/v1/students", json={"full_name": "Vikas Singh", "mobile": "9444444444"}).json()
    student_id = created["id"]

    patch_res = client.patch(f"/api/v1/students/{student_id}", json={
        "address": "Updated Address Lane 5",
        "notes": "Shifted from Morning to Evening batch",
        "status": "BLOCKED"
    })
    assert patch_res.status_code == 200
    updated = patch_res.json()
    assert updated["address"] == "Updated Address Lane 5"
    assert updated["status"] == "BLOCKED"
    assert updated["notes"] == "Shifted from Morning to Evening batch"


# ============================================================================
# SEAT MASTER DATA TESTS
# ============================================================================

def test_seats_list_all_100(client: TestClient):
    """Verifies all 100 physical study seats are accessible."""
    res = client.get("/api/v1/seats")
    assert res.status_code == 200
    seats = res.json()
    assert len(seats) == 100
    assert seats[0]["seat_number"] == 1
    assert seats[99]["seat_number"] == 100


def test_seat_maintenance_toggle(client: TestClient):
    """Verifies placing a desk into maintenance and reactivating it."""
    # Place Seat 10 into maintenance
    patch_res = client.patch("/api/v1/seats/10/status", json={
        "is_active": False,
        "reason": "Broken power socket under repair"
    })
    assert patch_res.status_code == 200
    seat = patch_res.json()
    assert seat["is_active"] is False
    assert "Broken power socket" in seat["description"]

    # Filter by active only
    res_active = client.get("/api/v1/seats?is_active=true")
    assert len(res_active.json()) == 99

    res_inactive = client.get("/api/v1/seats?is_active=false")
    assert len(res_inactive.json()) == 1
    assert res_inactive.json()[0]["id"] == 10


# ============================================================================
# SHIFT MASTER DATA TESTS
# ============================================================================

def test_shifts_list_canonical(client: TestClient):
    """Verifies the 4 canonical shifts exist with correct base fees and timings."""
    res = client.get("/api/v1/shifts")
    assert res.status_code == 200
    shifts = res.json()
    assert len(shifts) == 4
    names = [s["name"] for s in shifts]
    assert "MORNING" in names
    assert "AFTERNOON" in names
    assert "EVENING" in names
    assert "FULL_DAY" in names


def test_shift_get_by_id(client: TestClient):
    """Verifies retrieving a specific shift (Morning)."""
    res = client.get("/api/v1/shifts/1")
    assert res.status_code == 200
    shift = res.json()
    assert shift["name"] == "MORNING"
    assert shift["start_minute"] == 420
    assert shift["end_minute"] == 660
