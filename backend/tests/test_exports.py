from fastapi.testclient import TestClient
from backend.app.core.config import settings


def test_export_students_csv(client: TestClient):
    # Register a student
    client.post(
        f"{settings.API_V1_STR}/students",
        json={
            "full_name": "Export Test Student",
            "mobile_number": "9811122233",
            "email": "export.student@example.com"
        }
    )

    resp = client.get(f"{settings.API_V1_STR}/students/export")
    assert resp.status_code == 200
    assert resp.headers["content-type"].startswith("text/csv")
    assert "Student Code,Full Name,Mobile" in resp.text
    assert "Export Test Student" in resp.text
    assert "9811122233" in resp.text


def test_export_revenue_csv(client: TestClient):
    resp = client.get(f"{settings.API_V1_STR}/reports/revenue/export")
    assert resp.status_code == 200
    assert resp.headers["content-type"].startswith("text/csv")
    assert "Receipt Number,Payment ID,Date,Amount,Payment Method,Status" in resp.text
