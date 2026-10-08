import pytest
from fastapi.testclient import TestClient
from backend.app.core.config import settings
from backend.app.models.user import User
from backend.app.core.security import get_password_hash


def test_auth_login_success(client: TestClient, db_session):
    # Ensure admin user is seeded or exists
    admin = db_session.query(User).filter(User.username == settings.INITIAL_ADMIN_USERNAME).first()
    if not admin:
        admin = User(
            username=settings.INITIAL_ADMIN_USERNAME,
            email=settings.INITIAL_ADMIN_EMAIL,
            password_hash=get_password_hash(settings.INITIAL_ADMIN_PASSWORD),
            full_name=settings.INITIAL_ADMIN_FULL_NAME,
            role="ADMIN",
            is_active=True
        )
        db_session.add(admin)
        db_session.commit()

    response = client.post(
        f"{settings.API_V1_STR}/auth/login",
        json={
            "username": settings.INITIAL_ADMIN_USERNAME,
            "password": settings.INITIAL_ADMIN_PASSWORD
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert data["user"]["username"] == settings.INITIAL_ADMIN_USERNAME
    assert data["user"]["role"] == "ADMIN"


def test_auth_login_invalid_password(client: TestClient):
    response = client.post(
        f"{settings.API_V1_STR}/auth/login",
        json={
            "username": settings.INITIAL_ADMIN_USERNAME,
            "password": "WrongPassword123!"
        }
    )
    assert response.status_code == 401
    assert "Incorrect username or password" in response.json()["detail"]


def test_auth_get_me_profile(client: TestClient):
    # 1. Login
    login_resp = client.post(
        f"{settings.API_V1_STR}/auth/login",
        json={
            "username": settings.INITIAL_ADMIN_USERNAME,
            "password": settings.INITIAL_ADMIN_PASSWORD
        }
    )
    token = login_resp.json()["access_token"]

    # 2. Get profile with Bearer token
    headers = {"Authorization": f"Bearer {token}"}
    me_resp = client.get(f"{settings.API_V1_STR}/auth/me", headers=headers)
    assert me_resp.status_code == 200
    assert me_resp.json()["username"] == settings.INITIAL_ADMIN_USERNAME
    assert me_resp.json()["role"] == "ADMIN"


def test_auth_create_staff_user_by_admin(client: TestClient):
    login_resp = client.post(
        f"{settings.API_V1_STR}/auth/login",
        json={
            "username": settings.INITIAL_ADMIN_USERNAME,
            "password": settings.INITIAL_ADMIN_PASSWORD
        }
    )
    token = login_resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    create_resp = client.post(
        f"{settings.API_V1_STR}/auth/users",
        headers=headers,
        json={
            "username": "frontdesk_staff_1",
            "email": "staff1@smartlibrary.com",
            "password": "StaffSecretPassword123!",
            "full_name": "Front Desk Operator",
            "role": "STAFF",
            "is_active": True
        }
    )
    assert create_resp.status_code == 201
    data = create_resp.json()
    assert data["username"] == "frontdesk_staff_1"
    assert data["role"] == "STAFF"

    # Now verify the newly created staff can log in
    staff_login = client.post(
        f"{settings.API_V1_STR}/auth/login",
        json={
            "username": "frontdesk_staff_1",
            "password": "StaffSecretPassword123!"
        }
    )
    assert staff_login.status_code == 200
    staff_token = staff_login.json()["access_token"]

    # And verify staff CANNOT create other users (RBAC check)
    staff_headers = {"Authorization": f"Bearer {staff_token}"}
    unauthorized_create = client.post(
        f"{settings.API_V1_STR}/auth/users",
        headers=staff_headers,
        json={
            "username": "illegal_user",
            "email": "illegal@smartlibrary.com",
            "password": "IllegalPassword123!",
            "full_name": "Illegal User",
            "role": "STAFF"
        }
    )
    assert unauthorized_create.status_code == 403
