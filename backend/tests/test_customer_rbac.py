import uuid
import pytest
from datetime import date, timedelta
from decimal import Decimal
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from backend.app.core.config import settings
from backend.app.core.security import create_access_token, get_password_hash
from backend.app.models.user import User
from backend.app.models.student import Student
from backend.app.models.membership import Membership
from backend.app.models.payment import Payment


@pytest.fixture
def unauthenticated_client(db_session: Session) -> TestClient:
    """FastAPI TestClient with NO authorization headers."""
    from backend.app.main import app
    from backend.app.db.session import get_db

    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
def registered_owner(unauthenticated_client: TestClient):
    """Registers a fresh library owner and returns auth credentials, token, and user data."""
    payload = {
        "username": "owner_alice",
        "email": "alice@ownerlibrary.com",
        "mobile": "9876500001",
        "full_name": "Alice Library Owner",
        "password": "OwnerSecurePass123!"
    }
    res = unauthenticated_client.post(f"{settings.API_V1_STR}/auth/register", json=payload)
    assert res.status_code == 201
    data = res.json()
    return {
        "token": data["access_token"],
        "refresh_token": data["refresh_token"],
        "user": data["user"],
        "password": "OwnerSecurePass123!"
    }


# ============================================================================
# 1. LIBRARY OWNER REGISTRATION & SECURITY TESTS
# ============================================================================

def test_library_owner_registration_creates_admin_role(unauthenticated_client: TestClient, db_session: Session):
    """
    Test 1: Public registration creates a Library Owner account with ADMIN privileges.
    """
    payload = {
        "username": "owner_bob",
        "email": "bob@boblibrary.com",
        "mobile": "9876500002",
        "full_name": "Bob Library Admin",
        "password": "BobSecurePassword123!"
    }
    res = unauthenticated_client.post(f"{settings.API_V1_STR}/auth/register", json=payload)
    assert res.status_code == 201
    data = res.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["user"]["role"] == "ADMIN"
    assert data["user"]["email"] == "bob@boblibrary.com"


def test_registration_duplicate_email_or_username_rejected(unauthenticated_client: TestClient):
    """
    Test 2: Reject registration with 409 if email or username is already taken.
    """
    payload1 = {
        "username": "unique_owner",
        "email": "unique@library.com",
        "mobile": "9876500004",
        "full_name": "Unique Owner",
        "password": "Password123!"
    }
    res1 = unauthenticated_client.post(f"{settings.API_V1_STR}/auth/register", json=payload1)
    assert res1.status_code == 201

    # Duplicate username
    payload2 = {
        "username": "unique_owner",
        "email": "another@library.com",
        "mobile": "9876500005",
        "full_name": "Duplicate Owner",
        "password": "Password123!"
    }
    res2 = unauthenticated_client.post(f"{settings.API_V1_STR}/auth/register", json=payload2)
    assert res2.status_code == 409


def test_registration_password_length_validation(unauthenticated_client: TestClient):
    """
    Test 3: Passwords under 8 chars or over 72 bytes are rejected with 422.
    """
    # Too short
    res_short = unauthenticated_client.post(
        f"{settings.API_V1_STR}/auth/register",
        json={"username": "shorty", "email": "short@lib.com", "mobile": "9876500006", "full_name": "Short", "password": "123"}
    )
    assert res_short.status_code == 422

    # Too long (Bcrypt 72-byte max limit)
    res_long = unauthenticated_client.post(
        f"{settings.API_V1_STR}/auth/register",
        json={"username": "longy", "email": "long@lib.com", "mobile": "9876500007", "full_name": "Long", "password": "A" * 75}
    )
    assert res_long.status_code == 422


# ============================================================================
# 2. MULTI-TENANT ISOLATION TESTS (STUDENTS, MEMBERSHIPS, DASHBOARD)
# ============================================================================

def test_multi_tenant_student_isolation(unauthenticated_client: TestClient):
    """
    Test 4: When Owner A and Owner B enroll students, each owner only sees their own students.
    Owner B cannot access or view Owner A's students.
    """
    # 1. Register Owner A
    res_a = unauthenticated_client.post(f"{settings.API_V1_STR}/auth/register", json={
        "username": "owner_a", "email": "ownera@library.com", "mobile": "9811111111", "full_name": "Owner A", "password": "OwnerPass123!"
    })
    token_a = res_a.json()["access_token"]

    # 2. Register Owner B
    res_b = unauthenticated_client.post(f"{settings.API_V1_STR}/auth/register", json={
        "username": "owner_b", "email": "ownerb@library.com", "mobile": "9822222222", "full_name": "Owner B", "password": "OwnerPass123!"
    })
    token_b = res_b.json()["access_token"]

    # 3. Owner A registers a student
    headers_a = {"Authorization": f"Bearer {token_a}"}
    stu_res_a = unauthenticated_client.post(f"{settings.API_V1_STR}/students", headers=headers_a, json={
        "full_name": "Student Belonging to A",
        "mobile": "9111111111"
    })
    assert stu_res_a.status_code == 201
    student_a_id = stu_res_a.json()["id"]

    # 4. Owner B registers a student
    headers_b = {"Authorization": f"Bearer {token_b}"}
    stu_res_b = unauthenticated_client.post(f"{settings.API_V1_STR}/students", headers=headers_b, json={
        "full_name": "Student Belonging to B",
        "mobile": "9222222222"
    })
    assert stu_res_b.status_code == 201
    student_b_id = stu_res_b.json()["id"]

    # 5. Owner A lists students -> Should ONLY see Student A
    list_a = unauthenticated_client.get(f"{settings.API_V1_STR}/students", headers=headers_a)
    assert list_a.status_code == 200
    items_a = list_a.json()["items"]
    assert len(items_a) == 1
    assert items_a[0]["id"] == student_a_id
    assert items_a[0]["full_name"] == "Student Belonging to A"

    # 6. Owner B lists students -> Should ONLY see Student B
    list_b = unauthenticated_client.get(f"{settings.API_V1_STR}/students", headers=headers_b)
    assert list_b.status_code == 200
    items_b = list_b.json()["items"]
    assert len(items_b) == 1
    assert items_b[0]["id"] == student_b_id
    assert items_b[0]["full_name"] == "Student Belonging to B"

    # 7. Owner B tries to access Student A by UUID directly -> Returns 404 (IDOR prevented)
    idor_res = unauthenticated_client.get(f"{settings.API_V1_STR}/students/{student_a_id}", headers=headers_b)
    assert idor_res.status_code == 404


def test_new_owner_dashboard_starts_clean(unauthenticated_client: TestClient):
    """
    Test 5: A brand new library owner starts with 0 active students and 0 outstanding dues.
    They do not see old records from other libraries.
    """
    res = unauthenticated_client.post(f"{settings.API_V1_STR}/auth/register", json={
        "username": "fresh_owner", "email": "fresh@library.com", "mobile": "9833333333", "full_name": "Fresh Owner", "password": "FreshPass123!"
    })
    token = res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    dash_res = unauthenticated_client.get(f"{settings.API_V1_STR}/dashboard/summary", headers=headers)
    assert dash_res.status_code == 200
    data = dash_res.json()
    assert data["active_students_count"] == 0
    assert Decimal(str(data["total_outstanding_dues"])) == Decimal("0.00")
    assert data["occupied_physical_seats"] == 0


# ============================================================================
# 3. REFRESH TOKEN ROTATION & LOGOUT SECURITY
# ============================================================================

def test_refresh_token_rotation_flow(unauthenticated_client: TestClient, registered_owner):
    """
    Test 6: Refresh token rotation issues a new token pair and revokes old refresh token.
    """
    refresh_token = registered_owner["refresh_token"]
    res = unauthenticated_client.post(
        f"{settings.API_V1_STR}/auth/refresh",
        json={"refresh_token": refresh_token}
    )
    assert res.status_code == 200
    new_data = res.json()
    assert "access_token" in new_data
    assert "refresh_token" in new_data
    assert new_data["refresh_token"] != refresh_token

    # Re-using old refresh token must be rejected (Security Reuse Detection)
    reuse_res = unauthenticated_client.post(
        f"{settings.API_V1_STR}/auth/refresh",
        json={"refresh_token": refresh_token}
    )
    assert reuse_res.status_code in (401, 403)


def test_logout_revokes_refresh_token(unauthenticated_client: TestClient, registered_owner):
    """
    Test 7: Logout invalidates the refresh token session immediately.
    """
    token = registered_owner["token"]
    refresh_token = registered_owner["refresh_token"]

    # Logout
    logout_res = unauthenticated_client.post(
        f"{settings.API_V1_STR}/auth/logout",
        headers={"Authorization": f"Bearer {token}"},
        json={"refresh_token": refresh_token}
    )
    assert logout_res.status_code == 200

    # Attempting to refresh with the revoked token must fail
    res = unauthenticated_client.post(
        f"{settings.API_V1_STR}/auth/refresh",
        json={"refresh_token": refresh_token}
    )
    assert res.status_code in (401, 403)
