import uuid
from datetime import date, time
from decimal import Decimal
from sqlalchemy.orm import Session
from fastapi.testclient import TestClient

from backend.app.models.student import Student
from backend.app.models.membership import Membership
from backend.app.services.allocation_service import allocation_service
from backend.app.utils.time_ranges import intervals_overlap, date_ranges_overlap


# ============================================================================
# PURE MATHEMATICAL TIME & DATE RANGE TESTS
# ============================================================================

def test_interval_overlap_math():
    """Validates mathematical rules for half-open intervals [S, E)."""
    # 1. Non-overlapping touching boundaries (7-11 and 11-15) -> [420, 660) and [660, 900)
    assert intervals_overlap(420, 660, 660, 900) is False
    assert intervals_overlap(660, 900, 420, 660) is False

    # 2. Non-overlapping separated (7-11 and 15-23) -> [420, 660) and [900, 1380)
    assert intervals_overlap(420, 660, 900, 1380) is False

    # 3. Partial overlap (7-11 and 9-13) -> [420, 660) and [540, 780)
    assert intervals_overlap(420, 660, 540, 780) is True

    # 4. Full Day engulfing Morning (7-23 and 7-11) -> [420, 1380) and [420, 660)
    assert intervals_overlap(420, 1380, 420, 660) is True

    # 5. Full Day engulfing Evening (7-23 and 15-23) -> [420, 1380) and [900, 1380)
    assert intervals_overlap(420, 1380, 900, 1380) is True


def test_date_range_overlap_math():
    """Validates inclusive calendar date overlap math [D1_start, D1_end]."""
    # Consecutive months (Oct 1-31 and Nov 1-30) -> NO overlap
    assert date_ranges_overlap(date(2026, 10, 1), date(2026, 10, 31), date(2026, 11, 1), date(2026, 11, 30)) is False

    # Same month overlap (Oct 1-31 and Oct 15-Nov 15) -> Overlap
    assert date_ranges_overlap(date(2026, 10, 1), date(2026, 10, 31), date(2026, 10, 15), date(2026, 11, 15)) is True


# ============================================================================
# SEAT & STUDENT DOMAIN CONFLICT ENGINE TESTS
# ============================================================================

def test_seat_consecutive_shifts_allowed(db_session: Session):
    """
    TC-001 & TC-003: Seat 25 leased for Morning (07-11).
    Afternoon shift (11-15) on same seat and same dates MUST be ALLOWED.
    """
    student1 = Student(
        id=uuid.uuid4(),
        student_code="STU-001",
        full_name="Student One",
        mobile="9800000001",
        status="ACTIVE"
    )
    db_session.add(student1)

    m1 = Membership(
        id=uuid.uuid4(),
        student_id=student1.id,
        seat_id=25,
        shift_id=1,  # MORNING
        start_date=date(2026, 10, 1),
        end_date=date(2026, 10, 31),
        start_minute=420,
        end_minute=660,
        base_fee=Decimal("800.00"),
        discount_amount=Decimal("0.00"),
        final_fee=Decimal("800.00"),
        status="ACTIVE"
    )
    db_session.add(m1)
    db_session.commit()

    # Query Seat 25 for Afternoon (11-15) -> start_min=660, end_min=900
    is_free, conflict = allocation_service.check_seat_availability(
        db=db_session,
        seat_id=25,
        start_date=date(2026, 10, 1),
        end_date=date(2026, 10, 31),
        start_minute=660,
        end_minute=900
    )
    assert is_free is True
    assert conflict is None


def test_seat_partial_overlap_rejected(db_session: Session):
    """
    TC-004: Seat 25 occupied Morning (07-11).
    Custom shift (09-13) overlaps [540, 780) with [420, 660) -> MUST BE REJECTED.
    """
    student1 = Student(id=uuid.uuid4(), student_code="STU-002", full_name="Student Two", mobile="9800000002", status="ACTIVE")
    db_session.add(student1)
    m1 = Membership(
        id=uuid.uuid4(),
        student_id=student1.id,
        seat_id=25,
        shift_id=1,
        start_date=date(2026, 10, 1),
        end_date=date(2026, 10, 31),
        start_minute=420,
        end_minute=660,
        base_fee=Decimal("800.00"),
        discount_amount=Decimal("0.00"),
        final_fee=Decimal("800.00"),
        status="ACTIVE"
    )
    db_session.add(m1)
    db_session.commit()

    is_free, conflict = allocation_service.check_seat_availability(
        db=db_session,
        seat_id=25,
        start_date=date(2026, 10, 1),
        end_date=date(2026, 10, 31),
        start_minute=540,
        end_minute=780
    )
    assert is_free is False
    assert conflict is not None
    assert conflict.id == m1.id


def test_seat_full_day_blocks_all_shifts(db_session: Session):
    """
    TC-005 & TC-006: Seat 25 occupied Full Day (07-23).
    Morning, Afternoon, and Evening shifts on Seat 25 MUST BE REJECTED.
    """
    student = Student(id=uuid.uuid4(), student_code="STU-003", full_name="Student Three", mobile="9800000003", status="ACTIVE")
    db_session.add(student)
    m_full = Membership(
        id=uuid.uuid4(),
        student_id=student.id,
        seat_id=25,
        shift_id=4,  # FULL_DAY
        start_date=date(2026, 10, 1),
        end_date=date(2026, 10, 31),
        start_minute=420,
        end_minute=1380,
        base_fee=Decimal("2200.00"),
        discount_amount=Decimal("0.00"),
        final_fee=Decimal("2200.00"),
        status="ACTIVE"
    )
    db_session.add(m_full)
    db_session.commit()

    # 1. Morning (07-11)
    free_m, _ = allocation_service.check_seat_availability(db_session, 25, date(2026, 10, 1), date(2026, 10, 31), 420, 660)
    assert free_m is False

    # 2. Afternoon (11-15)
    free_a, _ = allocation_service.check_seat_availability(db_session, 25, date(2026, 10, 1), date(2026, 10, 31), 660, 900)
    assert free_a is False

    # 3. Evening (15-23)
    free_e, _ = allocation_service.check_seat_availability(db_session, 25, date(2026, 10, 1), date(2026, 10, 31), 900, 1380)
    assert free_e is False


def test_different_seats_same_shift_allowed(db_session: Session):
    """TC-007: Seat 25 occupied Morning. Seat 26 Morning MUST be ALLOWED."""
    student = Student(id=uuid.uuid4(), student_code="STU-004", full_name="Student Four", mobile="9800000004", status="ACTIVE")
    db_session.add(student)
    db_session.add(Membership(
        id=uuid.uuid4(),
        student_id=student.id,
        seat_id=25,
        shift_id=1,
        start_date=date(2026, 10, 1),
        end_date=date(2026, 10, 31),
        start_minute=420,
        end_minute=660,
        base_fee=Decimal("800.00"),
        discount_amount=Decimal("0.00"),
        final_fee=Decimal("800.00"),
        status="ACTIVE"
    ))
    db_session.commit()

    free_26, conflict = allocation_service.check_seat_availability(db_session, 26, date(2026, 10, 1), date(2026, 10, 31), 420, 660)
    assert free_26 is True
    assert conflict is None


def test_student_time_conflict_detection(db_session: Session):
    """
    TC-008 & TC-009:
    Same student cannot hold overlapping shifts on 2 different desks.
    Non-overlapping shifts for same student ARE ALLOWED.
    """
    student = Student(id=uuid.uuid4(), student_code="STU-005", full_name="Multi Shift Rahul", mobile="9800000005", status="ACTIVE")
    db_session.add(student)
    db_session.add(Membership(
        id=uuid.uuid4(),
        student_id=student.id,
        seat_id=10,
        shift_id=1,  # MORNING (07-11)
        start_date=date(2026, 10, 1),
        end_date=date(2026, 10, 31),
        start_minute=420,
        end_minute=660,
        base_fee=Decimal("800.00"),
        discount_amount=Decimal("0.00"),
        final_fee=Decimal("800.00"),
        status="ACTIVE"
    ))
    db_session.commit()

    # 1. Attempt same student on Seat 50 for MORNING (07-11) -> MUST COLLIDE
    can_book_morning, collision = allocation_service.check_student_time_conflict(
        db=db_session,
        student_id=student.id,
        start_date=date(2026, 10, 1),
        end_date=date(2026, 10, 31),
        start_minute=420,
        end_minute=660
    )
    assert can_book_morning is False
    assert collision is not None

    # 2. Attempt same student on Seat 50 for EVENING (15-23) -> MUST BE ALLOWED
    can_book_evening, col_evening = allocation_service.check_student_time_conflict(
        db=db_session,
        student_id=student.id,
        start_date=date(2026, 10, 1),
        end_date=date(2026, 10, 31),
        start_minute=900,
        end_minute=1380
    )
    assert can_book_evening is True
    assert col_evening is None


def test_cancelled_membership_frees_seat_immediately(db_session: Session):
    """TC-011: When membership is CANCELLED, seat is immediately free for re-allocation."""
    student = Student(id=uuid.uuid4(), student_code="STU-006", full_name="Student Cancel", mobile="9800000006", status="ACTIVE")
    db_session.add(student)
    m = Membership(
        id=uuid.uuid4(),
        student_id=student.id,
        seat_id=40,
        shift_id=1,
        start_date=date(2026, 10, 1),
        end_date=date(2026, 10, 31),
        start_minute=420,
        end_minute=660,
        base_fee=Decimal("800.00"),
        discount_amount=Decimal("0.00"),
        final_fee=Decimal("800.00"),
        status="CANCELLED"  # Prematurely cancelled
    )
    db_session.add(m)
    db_session.commit()

    is_free, conflict = allocation_service.check_seat_availability(
        db=db_session,
        seat_id=40,
        start_date=date(2026, 10, 1),
        end_date=date(2026, 10, 31),
        start_minute=420,
        end_minute=660
    )
    assert is_free is True
    assert conflict is None


def test_seat_availability_matrix_endpoint(client: TestClient, db_session: Session):
    """Verifies the GET /api/v1/seats/availability endpoint."""
    student = Student(id=uuid.uuid4(), student_code="STU-007", full_name="Matrix Student", mobile="9800000007", status="ACTIVE")
    db_session.add(student)
    # Book Seat 1 for Morning shift
    db_session.add(Membership(
        id=uuid.uuid4(),
        student_id=student.id,
        seat_id=1,
        shift_id=1,
        start_date=date(2026, 10, 1),
        end_date=date(2026, 10, 31),
        start_minute=420,
        end_minute=660,
        base_fee=Decimal("800.00"),
        discount_amount=Decimal("0.00"),
        final_fee=Decimal("800.00"),
        status="ACTIVE"
    ))
    db_session.commit()

    res = client.get("/api/v1/seats/availability?start_date=2026-10-01&end_date=2026-10-31&shift_id=1")
    assert res.status_code == 200
    data = res.json()
    assert data["shift_name"] == "MORNING"
    assert data["total_seats"] == 100
    assert data["occupied_count"] >= 1

    # Seat 1 should be OCCUPIED
    seat1 = next(s for s in data["seats"] if s["seat_id"] == 1)
    assert seat1["status"] == "OCCUPIED"

    # Seat 2 should be AVAILABLE
    seat2 = next(s for s in data["seats"] if s["seat_id"] == 2)
    assert seat2["status"] == "AVAILABLE"
