import os
import sys
from datetime import date
from decimal import Decimal
from uuid import uuid4
from sqlalchemy import text
from psycopg.errors import ExclusionViolation

# Ensure backend root is on sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.app.core.config import settings
from backend.app.db.session import SessionLocal


def test_gist_exclusion_constraints():
    """
    Verifies that the PostgreSQL GiST multidimensional exclusion constraint
    strictly enforces the physical and temporal allocation invariants.
    """
    db = SessionLocal()
    print("=" * 70)
    print("TESTING POSTGRESQL GIST MULTIDIMENSIONAL EXCLUSION CONSTRAINTS")
    print("=" * 70)

    try:
        # Check connection
        res = db.execute(text("SELECT version();")).scalar()
        print(f"Connected to: {res[:45]}...")

        # Setup isolated mock student
        mock_student_id = str(uuid4())
        mock_student_code = f"TEST-{uuid4().hex[:6].upper()}"
        mock_mobile = f"99{uuid4().int % 100000000:08d}"

        db.execute(
            text("""
                INSERT INTO students (id, student_code, full_name, mobile, status)
                VALUES (:id, :code, 'Mock Test Student', :mobile, 'ACTIVE')
            """),
            {"id": mock_student_id, "code": mock_student_code, "mobile": mock_mobile}
        )

        test_seat_id = 99  # Use Seat 99 for isolated test
        start_date = date(2026, 11, 1)
        end_date = date(2026, 11, 30)

        # -----------------------------------------------------------------
        # TEST 1: Insert Morning Shift (07:00 - 11:00) -> [420, 660)
        # -----------------------------------------------------------------
        m1_id = str(uuid4())
        print("\n[TEST 1] Inserting Morning shift on Seat 99 (07:00 - 11:00)...")
        db.execute(
            text("""
                INSERT INTO memberships (
                    id, student_id, seat_id, shift_id, start_date, end_date,
                    start_minute, end_minute, base_fee, discount_amount, final_fee, status
                ) VALUES (
                    :id, :student_id, :seat_id, 1, :start_date, :end_date,
                    420, 660, 800.00, 0.00, 800.00, 'ACTIVE'
                )
            """),
            {"id": m1_id, "student_id": mock_student_id, "seat_id": test_seat_id, "start_date": start_date, "end_date": end_date}
        )
        db.commit()
        print("  -> SUCCESS: Morning shift booked.")

        # -----------------------------------------------------------------
        # TEST 2: Insert Afternoon Shift (11:00 - 15:00) -> [660, 900)
        # Boundary touching: Morning ends at 660, Afternoon starts at 660.
        # MUST SUCCEED (Zero overlap in half-open intervals).
        # -----------------------------------------------------------------
        m2_id = str(uuid4())
        print("\n[TEST 2] Inserting Afternoon shift on Seat 99 (11:00 - 15:00) on same dates...")
        db.execute(
            text("""
                INSERT INTO memberships (
                    id, student_id, seat_id, shift_id, start_date, end_date,
                    start_minute, end_minute, base_fee, discount_amount, final_fee, status
                ) VALUES (
                    :id, :student_id, :seat_id, 2, :start_date, :end_date,
                    660, 900, 800.00, 0.00, 800.00, 'ACTIVE'
                )
            """),
            {"id": m2_id, "student_id": mock_student_id, "seat_id": test_seat_id, "start_date": start_date, "end_date": end_date}
        )
        db.commit()
        print("  -> SUCCESS: Touching boundary handover cleanly accepted without collision!")

        # -----------------------------------------------------------------
        # TEST 3: Attempt to insert overlapping Shift on Seat 99 (e.g. 09:00 - 13:00)
        # MUST BE REJECTED by exclude_seat_time_conflict
        # -----------------------------------------------------------------
        print("\n[TEST 3] Attempting overlapping shift (09:00 - 13:00) on Seat 99...")
        m3_id = str(uuid4())
        try:
            db.execute(
                text("""
                    INSERT INTO memberships (
                        id, student_id, seat_id, shift_id, start_date, end_date,
                        start_minute, end_minute, base_fee, discount_amount, final_fee, status
                    ) VALUES (
                        :id, :student_id, :seat_id, 1, :start_date, :end_date,
                        540, 780, 800.00, 0.00, 800.00, 'ACTIVE'
                    )
                """),
                {"id": m3_id, "student_id": mock_student_id, "seat_id": test_seat_id, "start_date": start_date, "end_date": end_date}
            )
            db.commit()
            raise AssertionError("CRITICAL FAILURE: Overlapping shift was erroneously permitted!")
        except Exception as e:
            db.rollback()
            if "exclude_seat_time_conflict" in str(e) or "exclusion constraint" in str(e):
                print(f"  -> SUCCESS: PostgreSQL GiST constraint correctly aborted double-booking!\n     ({e.args[0][:80]}...)")
            else:
                raise e

        # -----------------------------------------------------------------
        # TEST 4: Attempt to insert Full Day Shift (07:00 - 23:00) on Seat 99
        # MUST BE REJECTED by exclude_seat_time_conflict
        # -----------------------------------------------------------------
        print("\n[TEST 4] Attempting Full Day shift (07:00 - 23:00) on Seat 99...")
        m4_id = str(uuid4())
        try:
            db.execute(
                text("""
                    INSERT INTO memberships (
                        id, student_id, seat_id, shift_id, start_date, end_date,
                        start_minute, end_minute, base_fee, discount_amount, final_fee, status
                    ) VALUES (
                        :id, :student_id, :seat_id, 4, :start_date, :end_date,
                        420, 1380, 2200.00, 0.00, 2200.00, 'ACTIVE'
                    )
                """),
                {"id": m4_id, "student_id": mock_student_id, "seat_id": test_seat_id, "start_date": start_date, "end_date": end_date}
            )
            db.commit()
            raise AssertionError("CRITICAL FAILURE: Full Day shift was erroneously permitted on occupied seat!")
        except Exception as e:
            db.rollback()
            if "exclude_seat_time_conflict" in str(e) or "exclusion constraint" in str(e):
                print(f"  -> SUCCESS: PostgreSQL GiST constraint correctly blocked Full Day collision!")
            else:
                raise e

        # Cleanup test records
        print("\nCleaning up test artifacts...")
        db.execute(text("DELETE FROM memberships WHERE student_id = :id"), {"id": mock_student_id})
        db.execute(text("DELETE FROM students WHERE id = :id"), {"id": mock_student_id})
        db.commit()
        print("Test artifacts cleaned up successfully.")

        print("\n" + "=" * 70)
        print("ALL DATABASE CONSTRAINT TESTS PASSED PERFECTLY!")
        print("=" * 70)

    except Exception as e:
        db.rollback()
        print(f"\n[ERROR] Constraint verification failed: {e}")
        raise e
    finally:
        db.close()


if __name__ == "__main__":
    test_gist_exclusion_constraints()
