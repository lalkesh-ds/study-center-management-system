from datetime import time
from decimal import Decimal
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool

from backend.app.main import app
from backend.app.db.base import Base
from backend.app.db.session import get_db
from backend.app.models.seat import Seat
from backend.app.models.shift import Shift


@pytest.fixture(scope="session")
def test_db_engine():
    """
    Creates an isolated SQLite in-memory database engine for automated testing.
    StaticPool ensures the in-memory database persists across connections during tests.
    """
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    return engine


@pytest.fixture(scope="function")
def db_session(test_db_engine) -> Session:
    """
    Yields an isolated database session for a test function with clean rollback/re-creation.
    """
    Base.metadata.drop_all(test_db_engine)
    Base.metadata.create_all(test_db_engine)

    SessionTesting = sessionmaker(autocommit=False, autoflush=False, bind=test_db_engine)
    db = SessionTesting()

    # Pre-seed 100 seats and 4 canonical shifts for test scenarios
    for num in range(1, 101):
        db.add(Seat(
            id=num,
            seat_number=num,
            is_active=True,
            has_power_outlet=True,
            has_locker=(num % 5 == 0),
            description=f"Seat #{num}"
        ))

    shifts = [
        Shift(id=1, name="MORNING", start_time=time(7, 0), end_time=time(11, 0), start_minute=420, end_minute=660, base_fee=Decimal("800.00"), is_active=True),
        Shift(id=2, name="AFTERNOON", start_time=time(11, 0), end_time=time(15, 0), start_minute=660, end_minute=900, base_fee=Decimal("800.00"), is_active=True),
        Shift(id=3, name="EVENING", start_time=time(15, 0), end_time=time(23, 0), start_minute=900, end_minute=1380, base_fee=Decimal("1200.00"), is_active=True),
        Shift(id=4, name="FULL_DAY", start_time=time(7, 0), end_time=time(23, 0), start_minute=420, end_minute=1380, base_fee=Decimal("2200.00"), is_active=True),
    ]
    for s in shifts:
        db.add(s)

    # Pre-seed default admin user for authentication tests
    from backend.app.models.user import User
    from backend.app.core.security import get_password_hash
    from backend.app.core.config import settings

    admin = User(
        username=settings.INITIAL_ADMIN_USERNAME,
        email=settings.INITIAL_ADMIN_EMAIL,
        password_hash=get_password_hash(settings.INITIAL_ADMIN_PASSWORD),
        full_name=settings.INITIAL_ADMIN_FULL_NAME,
        role="ADMIN",
        is_active=True
    )
    db.add(admin)

    db.commit()

    try:
        yield db
    finally:
        db.close()


@pytest.fixture(scope="function")
def client(db_session: Session) -> TestClient:
    """
    FastAPI TestClient with dependency override pointing to isolated test DB.
    """
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()
