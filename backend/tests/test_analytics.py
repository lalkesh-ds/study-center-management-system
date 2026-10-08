from datetime import date, timedelta
from decimal import Decimal
from fastapi.testclient import TestClient


def test_dashboard_summary_capacity_formulas(client: TestClient):
    """
    Verifies that the 3 capacity formulas execute with precision:
    - Physical Utilization: chairs / 100
    - Slot Occupancy: slots / 300 (Full Day counts as 3 slots, Morning as 1)
    - Time-Weighted: hours / 1600 (Full Day = 16h, Morning = 4h)
    """
    today = date.today()
    start = today - timedelta(days=2)
    end = today + timedelta(days=20)

    # Student 1: Seat 1 Morning (4 hours, 1 slot)
    s1 = client.post("/api/v1/students", json={"full_name": "KPI User 1", "mobile": "9866000001", "email": "kpi1@example.com"}).json()["id"]
    client.post("/api/v1/memberships", json={
        "student_id": s1,
        "seat_id": 1,
        "shift_id": 1,  # MORNING (4h, 1 slot)
        "start_date": str(start),
        "end_date": str(end)
    })

    # Student 2: Seat 2 Full Day (16 hours, 3 slots)
    s2 = client.post("/api/v1/students", json={"full_name": "KPI User 2", "mobile": "9866000002", "email": "kpi2@example.com"}).json()["id"]
    client.post("/api/v1/memberships", json={
        "student_id": s2,
        "seat_id": 2,
        "shift_id": 4,  # FULL_DAY (16h, 3 slots)
        "start_date": str(start),
        "end_date": str(end)
    })

    res = client.get(f"/api/v1/dashboard/summary?target_date={today}")
    assert res.status_code == 200
    kpis = res.json()

    assert kpis["occupied_physical_seats"] == 2
    assert kpis["physical_utilization_rate"] == 2.0

    # 1 slot (Morning) + 3 slots (Full Day) = 4 slots
    assert kpis["booked_shift_slots"] == 4
    assert kpis["slot_occupancy_rate"] == round((4 / 300.0) * 100, 2)

    # 4 hours (Morning) + 16 hours (Full Day) = 20 seat-hours
    assert kpis["booked_seat_hours"] == 20.0
    assert kpis["seat_hour_occupancy_rate"] == round((20 / 1600.0) * 100, 2)

    assert kpis["active_students_count"] == 2


def test_expiring_memberships_queue(client: TestClient):
    """Verifies that memberships ending within threshold appear in the action queue."""
    today = date.today()
    s = client.post("/api/v1/students", json={"full_name": "Expiring Student", "mobile": "9866000003", "email": "exp@example.com"}).json()["id"]

    # Ending in 2 days
    client.post("/api/v1/memberships", json={
        "student_id": s,
        "seat_id": 80,
        "shift_id": 1,
        "start_date": str(today - timedelta(days=25)),
        "end_date": str(today + timedelta(days=2))
    })

    res = client.get("/api/v1/reports/expiring?days_threshold=3")
    assert res.status_code == 200
    queue = res.json()
    assert len(queue) >= 1
    target = next((item for item in queue if item["student_id"] == s), None)
    assert target is not None
    assert target["days_remaining"] == 2
    assert target["seat_number"] == 80


def test_revenue_collection_report(client: TestClient):
    """Verifies payment method revenue aggregation."""
    today = date.today()
    s = client.post("/api/v1/students", json={"full_name": "Revenue Student", "mobile": "9866000004", "email": "rev@example.com"}).json()["id"]
    m = client.post("/api/v1/memberships", json={
        "student_id": s,
        "seat_id": 85,
        "shift_id": 1,
        "start_date": str(today),
        "end_date": str(today + timedelta(days=30))
    }).json()["id"]

    # Record 1 Cash payment of 300 and 1 UPI payment of 400
    client.post("/api/v1/payments", json={"membership_id": m, "amount": 300.00, "payment_method": "CASH"})
    client.post("/api/v1/payments", json={"membership_id": m, "amount": 400.00, "payment_method": "UPI"})

    res = client.get(f"/api/v1/reports/revenue?start_date={today}&end_date={today}")
    assert res.status_code == 200
    report = res.json()
    assert Decimal(str(report["total_revenue"])) == Decimal("700.00")
    assert Decimal(str(report["cash_total"])) == Decimal("300.00")
    assert Decimal(str(report["upi_total"])) == Decimal("400.00")
    assert report["transaction_count"] == 2
