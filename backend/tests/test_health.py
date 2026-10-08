import pytest
from fastapi.testclient import TestClient
from fastapi import APIRouter
from backend.app.core.exceptions import NotFoundException, ConflictException, ValidationException


def test_root_endpoint(client: TestClient):
    """Verifies the root welcome endpoint returns 200 OK and valid metadata."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "online"
    assert "version" in data
    assert data["documentation"] == "/docs"


def test_health_liveness_endpoint(client: TestClient):
    """Verifies the /api/v1/health liveness probe."""
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "timestamp" in data
    assert data["version"] == "1.0.0"


def test_custom_exception_mapping(client: TestClient):
    """
    Verifies that domain exceptions are intercepted by global handlers
    and formatted with machine-readable codes and structured payloads.
    """
    from backend.app.main import app

    # Create temporary test router to trigger domain exceptions
    test_router = APIRouter(prefix="/test-exceptions")

    @test_router.get("/not-found")
    def raise_not_found():
        raise NotFoundException("Student STU-999 not found", code="STUDENT_NOT_FOUND")

    @test_router.get("/conflict")
    def raise_conflict():
        raise ConflictException("Seat 25 is already booked", code="SEAT_ALREADY_BOOKED")

    app.include_router(test_router)

    # 1. Test 404 NotFoundException
    res_404 = client.get("/test-exceptions/not-found")
    assert res_404.status_code == 404
    body_404 = res_404.json()
    assert body_404["error"]["code"] == "STUDENT_NOT_FOUND"
    assert body_404["error"]["message"] == "Student STU-999 not found"
    assert "timestamp" in body_404["error"]

    # 2. Test 409 ConflictException
    res_409 = client.get("/test-exceptions/conflict")
    assert res_409.status_code == 409
    body_409 = res_409.json()
    assert body_409["error"]["code"] == "SEAT_ALREADY_BOOKED"
    assert body_409["error"]["message"] == "Seat 25 is already booked"
