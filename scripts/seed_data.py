import os
import sys
from decimal import Decimal
from datetime import time
import bcrypt
from sqlalchemy import text

# Ensure backend root is on sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.app.core.config import settings
from backend.app.db.session import SessionLocal


def seed_database():
    """
    Seeds initial reference data:
    1. 100 Physical Seats (Numbered 1 to 100)
    2. 4 Canonical Shifts (Morning, Afternoon, Evening, Full Day)
    3. Initial Administrator Account
    """
    db = SessionLocal()
    print("=" * 70)
    print("SMART LIBRARY & STUDY CENTER - INITIAL DATA SEEDING")
    print("=" * 70)
    print(f"Connecting to database: {settings.DATABASE_URL.split('@')[-1] if '@' in settings.DATABASE_URL else 'localhost'}")

    try:
        # 1. Seed Seats (1 to 100)
        print("\n[1/3] Checking physical seats inventory (1 - 100)...")
        existing_seats = db.execute(text("SELECT COUNT(*) FROM seats")).scalar()
        if existing_seats == 0:
            print("  -> Seeding 100 physical study desks...")
            for seat_num in range(1, 101):
                # Standard amenities: All desks have power outlets; every 5th desk has locker
                has_locker = (seat_num % 5 == 0)
                description = f"Desk #{seat_num} - Standard Quiet Zone"
                if has_locker:
                    description += " with Dedicated Locker"
                db.execute(
                    text("""
                        INSERT INTO seats (id, seat_number, is_active, has_power_outlet, has_locker, description)
                        VALUES (:id, :num, TRUE, TRUE, :locker, :desc)
                    """),
                    {"id": seat_num, "num": seat_num, "locker": has_locker, "desc": description}
                )
            db.commit()
            print("  -> 100 seats created successfully.")
        else:
            print(f"  -> Seats already exist ({existing_seats} seats found). Skipping.")

        # 2. Seed Shifts
        print("\n[2/3] Checking canonical shifts...")
        shifts_config = [
            {
                "name": "MORNING",
                "start_time": time(7, 0, 0),
                "end_time": time(11, 0, 0),
                "start_minute": 420,
                "end_minute": 660,
                "base_fee": Decimal("800.00")
            },
            {
                "name": "AFTERNOON",
                "start_time": time(11, 0, 0),
                "end_time": time(15, 0, 0),
                "start_minute": 660,
                "end_minute": 900,
                "base_fee": Decimal("800.00")
            },
            {
                "name": "EVENING",
                "start_time": time(15, 0, 0),
                "end_time": time(23, 0, 0),
                "start_minute": 900,
                "end_minute": 1380,
                "base_fee": Decimal("1200.00")
            },
            {
                "name": "FULL_DAY",
                "start_time": time(7, 0, 0),
                "end_time": time(23, 0, 0),
                "start_minute": 420,
                "end_minute": 1380,
                "base_fee": Decimal("2200.00")
            }
        ]

        for s in shifts_config:
            existing_shift = db.execute(
                text("SELECT id FROM shifts WHERE name = :name"),
                {"name": s["name"]}
            ).first()

            if not existing_shift:
                db.execute(
                    text("""
                        INSERT INTO shifts (name, start_time, end_time, start_minute, end_minute, base_fee, is_active)
                        VALUES (:name, :start_time, :end_time, :start_min, :end_min, :fee, TRUE)
                    """),
                    {
                        "name": s["name"],
                        "start_time": s["start_time"],
                        "end_time": s["end_time"],
                        "start_min": s["start_minute"],
                        "end_min": s["end_minute"],
                        "fee": s["base_fee"]
                    }
                )
                print(f"  -> Created shift: {s['name']} ({s['start_time']} - {s['end_time']}, Fee: Rs.{s['base_fee']})")
            else:
                print(f"  -> Shift {s['name']} already exists.")
        db.commit()

        # 3. Seed Initial Administrator Account
        print("\n[3/3] Checking initial administrator account...")
        admin_user = db.execute(
            text("SELECT id FROM users WHERE username = :username"),
            {"username": settings.INITIAL_ADMIN_USERNAME}
        ).first()

        if not admin_user:
            # Hash password with bcrypt
            pwd_bytes = settings.INITIAL_ADMIN_PASSWORD.encode("utf-8")
            hashed_pwd = bcrypt.hashpw(pwd_bytes, bcrypt.gensalt()).decode("utf-8")

            db.execute(
                text("""
                    INSERT INTO users (username, email, password_hash, full_name, role, is_active)
                    VALUES (:username, :email, :pwd_hash, :name, 'ADMIN', TRUE)
                """),
                {
                    "username": settings.INITIAL_ADMIN_USERNAME,
                    "email": settings.INITIAL_ADMIN_EMAIL,
                    "pwd_hash": hashed_pwd,
                    "name": settings.INITIAL_ADMIN_FULL_NAME
                }
            )
            db.commit()
            print(f"  -> Created Admin: '{settings.INITIAL_ADMIN_USERNAME}' ({settings.INITIAL_ADMIN_EMAIL})")
        else:
            print(f"  -> Admin user '{settings.INITIAL_ADMIN_USERNAME}' already exists.")

        print("\n" + "=" * 70)
        print("SEEDING COMPLETED SUCCESSFULLY!")
        print("=" * 70)

    except Exception as e:
        db.rollback()
        print(f"\n[ERROR] Seeding failed: {e}")
        raise e
    finally:
        db.close()


if __name__ == "__main__":
    seed_database()
