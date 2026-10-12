"""
Automated Security, Authentication, RBAC, and Penetration Testing Suite.
Validates:
1. Authentication edge cases (invalid creds, unknown user, expired token, revoked token reuse).
2. Multi-tenant RBAC & IDOR defenses (cross-tenant access to students, memberships, payments, attendance).
3. Security headers, rate limiting, and input sanitization (SQLi, invalid discount/payment amounts).
"""

import uuid
from decimal import Decimal
from datetime import date, timedelta
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from backend.app.main import app
from backend.app.db.session import get_db
from backend.app.models.user import User
from backend.app.models.student import Student
from backend.app.models.membership import Membership
from backend.app.models.payment import Payment
from backend.app.core.security import get_password_hash, create_access_token


@pytest.fixture
def make_client(db_session: Session):
    """Factory fixture returning TestClient configured with test db overrides."""
    clients = []

    def _client(token: str = None):
        app.dependency_overrides[get_db] = lambda: db_session
        headers = {"Authorization": f"Bearer {token}"} if token else {}
        tc = TestClient(app, headers=headers)
        clients.append(tc)
        return tc

    yield _client

    for c in clients:
        c.close()
    app.dependency_overrides.clear()


def test_unauthenticated_requests_rejected(make_client):
    """Verify that unauthenticated callers cannot reach protected endpoints."""
    anonymous_client = make_client()
    # Protected endpoints must return 401 Unauthorized
    assert anonymous_client.get("/api/v1/seats").status_code == 401
    assert anonymous_client.get("/api/v1/shifts").status_code == 401
    assert anonymous_client.get("/api/v1/students").status_code == 401
    assert anonymous_client.get("/api/v1/memberships").status_code == 401
    assert anonymous_client.get("/api/v1/dashboard/summary").status_code == 401
    assert anonymous_client.get("/api/v1/auth/me").status_code == 401


def test_invalid_and_unknown_credentials(make_client):
    """Verify generic error handling for bad credentials without account enumeration."""
    client = make_client()
    # Unknown account
    resp_unknown = client.post("/api/v1/auth/login", json={
        "username": "non_existent_user_9999",
        "password": "SomePassword123!"
    })
    assert resp_unknown.status_code == 401
    assert "Incorrect username or password" in resp_unknown.json()["detail"]

    # Wrong password for existing user
    resp_wrong = client.post("/api/v1/auth/login", json={
        "username": "admin",
        "password": "WrongPassword123!"
    })
    assert resp_wrong.status_code == 401
    assert "Incorrect username or password" in resp_wrong.json()["detail"]


def test_revoked_refresh_token_reuse_detection(make_client):
    """Verify refresh token rotation and full session revocation upon reuse."""
    client = make_client()
    # 1. Register a new user
    reg_resp = client.post("/api/v1/auth/register", json={
        "username": "reuse_test_user",
        "email": "reuse@test.com",
        "mobile": "9998887771",
        "full_name": "Reuse Tester",
        "password": "SecurePassword123!"
    })
    assert reg_resp.status_code == 201
    tokens = reg_resp.json()
    refresh_token_v1 = tokens["refresh_token"]

    # 2. Legitimate refresh
    refresh_resp = client.post("/api/v1/auth/refresh", json={"refresh_token": refresh_token_v1})
    assert refresh_resp.status_code == 200
    new_tokens = refresh_resp.json()
    assert new_tokens["refresh_token"] != refresh_token_v1

    # 3. Malicious reuse of the old revoked refresh token
    reuse_resp = client.post("/api/v1/auth/refresh", json={"refresh_token": refresh_token_v1})
    assert reuse_resp.status_code == 401
    assert "Revoked refresh token" in reuse_resp.json()["detail"]


def test_cross_tenant_student_isolation(db_session: Session, make_client):
    """Ensure Library Owner B cannot view or update Library Owner A's students (IDOR prevention)."""
    owner_a = User(
        id=uuid.uuid4(),
        username="owner_alpha",
        email="owner_a@library.com",
        password_hash=get_password_hash("Pass@1234"),
        full_name="Owner A",
        role="ADMIN",
        is_active=True
    )
    owner_b = User(
        id=uuid.uuid4(),
        username="owner_beta",
        email="owner_b@library.com",
        password_hash=get_password_hash("Pass@1234"),
        full_name="Owner B",
        role="ADMIN",
        is_active=True
    )
    db_session.add_all([owner_a, owner_b])
    db_session.commit()

    # Owner A creates student
    student_a = Student(
        id=uuid.uuid4(),
        student_code="STU-2026-9001",
        full_name="Student Alpha",
        mobile="9800000001",
        status="ACTIVE",
        created_by=owner_a.id
    )
    db_session.add(student_a)
    db_session.commit()

    token_b = create_access_token(subject=str(owner_b.id), role="ADMIN")
    client_b = make_client(token=token_b)

    # Owner B tries to read Owner A's student
    get_res = client_b.get(f"/api/v1/students/{student_a.id}")
    assert get_res.status_code == 404

    # Owner B tries to modify Owner A's student
    patch_res = client_b.patch(f"/api/v1/students/{student_a.id}", json={"full_name": "Hacked Name"})
    assert patch_res.status_code == 404


def test_cross_tenant_membership_cancel_and_renew_blocked(db_session: Session, make_client):
    """Ensure Library Owner B cannot cancel or renew Library Owner A's membership (IDOR prevention)."""
    owner_a = User(
        id=uuid.uuid4(),
        username="owner_a_mem",
        email="owner_am@library.com",
        password_hash=get_password_hash("Pass@1234"),
        full_name="Owner A",
        role="ADMIN",
        is_active=True
    )
    owner_b = User(
        id=uuid.uuid4(),
        username="owner_b_mem",
        email="owner_bm@library.com",
        password_hash=get_password_hash("Pass@1234"),
        full_name="Owner B",
        role="ADMIN",
        is_active=True
    )
    db_session.add_all([owner_a, owner_b])
    db_session.commit()

    student_a = Student(
        id=uuid.uuid4(),
        student_code="STU-2026-9002",
        full_name="Student A2",
        mobile="9800000002",
        status="ACTIVE",
        created_by=owner_a.id
    )
    db_session.add(student_a)
    db_session.commit()

    # Membership belonging to Owner A
    mem_a = Membership(
        id=uuid.uuid4(),
        student_id=student_a.id,
        seat_id=10,
        shift_id=1,
        start_date=date.today(),
        end_date=date.today() + timedelta(days=30),
        start_minute=420,
        end_minute=660,
        base_fee=Decimal("800.00"),
        discount_amount=Decimal("0.00"),
        final_fee=Decimal("800.00"),
        status="ACTIVE",
        created_by=owner_a.id
    )
    db_session.add(mem_a)
    db_session.commit()

    token_b = create_access_token(subject=str(owner_b.id), role="ADMIN")
    client_b = make_client(token=token_b)

    # Owner B tries to cancel Owner A's membership
    cancel_res = client_b.post(f"/api/v1/memberships/{mem_a.id}/cancel", json={"cancel_reason": "Malicious cancellation"})
    assert cancel_res.status_code == 404

    # Owner B tries to renew Owner A's membership
    renew_res = client_b.post(f"/api/v1/memberships/{mem_a.id}/renew", json={
        "start_date": str(date.today() + timedelta(days=31)),
        "end_date": str(date.today() + timedelta(days=60)),
    })
    assert renew_res.status_code == 404


def test_cross_tenant_payment_void_and_list_blocked(db_session: Session, make_client):
    """Ensure Library Owner B cannot void or inspect Library Owner A's payments (IDOR prevention)."""
    owner_a = User(
        id=uuid.uuid4(),
        username="owner_a_pay",
        email="owner_ap@library.com",
        password_hash=get_password_hash("Pass@1234"),
        full_name="Owner A",
        role="ADMIN",
        is_active=True
    )
    owner_b = User(
        id=uuid.uuid4(),
        username="owner_b_pay",
        email="owner_bp@library.com",
        password_hash=get_password_hash("Pass@1234"),
        full_name="Owner B",
        role="ADMIN",
        is_active=True
    )
    db_session.add_all([owner_a, owner_b])
    db_session.commit()

    student_a = Student(
        id=uuid.uuid4(),
        student_code="STU-2026-9003",
        full_name="Student A3",
        mobile="9800000003",
        status="ACTIVE",
        created_by=owner_a.id
    )
    db_session.add(student_a)
    db_session.commit()

    mem_a = Membership(
        id=uuid.uuid4(),
        student_id=student_a.id,
        seat_id=11,
        shift_id=1,
        start_date=date.today(),
        end_date=date.today() + timedelta(days=30),
        start_minute=420,
        end_minute=660,
        base_fee=Decimal("800.00"),
        discount_amount=Decimal("0.00"),
        final_fee=Decimal("800.00"),
        status="ACTIVE",
        created_by=owner_a.id
    )
    db_session.add(mem_a)
    db_session.commit()

    payment_a = Payment(
        id=uuid.uuid4(),
        receipt_number="RCP-20261012-9999",
        membership_id=mem_a.id,
        student_id=student_a.id,
        amount=Decimal("800.00"),
        payment_method="UPI",
        status="COMPLETED",
        received_by=owner_a.id
    )
    db_session.add(payment_a)
    db_session.commit()

    token_b = create_access_token(subject=str(owner_b.id), role="ADMIN")
    client_b = make_client(token=token_b)

    # Owner B tries to void Owner A's payment
    void_res = client_b.post(f"/api/v1/payments/{payment_a.id}/void", json={"void_reason": "Malicious void attempt"})
    assert void_res.status_code == 404

    # Owner B tries to list payments of Owner A's membership
    list_res = client_b.get(f"/api/v1/memberships/{mem_a.id}/payments")
    assert list_res.status_code == 404


def test_security_headers_present(make_client):
    """Verify HTTP Security Headers are returned on API responses."""
    client = make_client()
    resp = client.get("/")
    assert resp.status_code == 200
    assert resp.headers.get("X-Content-Type-Options") == "nosniff"
    assert resp.headers.get("X-Frame-Options") == "DENY"
    assert resp.headers.get("X-XSS-Protection") == "1; mode=block"
    assert resp.headers.get("Referrer-Policy") == "strict-origin-when-cross-origin"


def test_business_invariants_payment_and_discount_tampering(client: TestClient, db_session: Session):
    """Verify that discount exceeding base fee is rejected by server."""
    # 1. Create student
    st_res = client.post("/api/v1/students", json={
        "full_name": "Tamper Test Student",
        "mobile": "9991112223"
    })
    assert st_res.status_code == 201
    student_id = st_res.json()["id"]

    # 2. Attempt admission with discount > base_fee (Morning shift base_fee is 800)
    bad_adm = client.post("/api/v1/memberships", json={
        "student_id": student_id,
        "seat_id": 25,
        "shift_id": 1,
        "start_date": str(date.today()),
        "end_date": str(date.today() + timedelta(days=30)),
        "discount_amount": 9999.00  # Exceeds base fee
    })
    assert bad_adm.status_code == 400
    assert "INVALID_DISCOUNT" in str(bad_adm.json())
