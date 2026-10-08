"""
Database Connection & Schema Verification Utility
Usage: python scripts/verify_cloud_db.py
Tests database connectivity, btree_gist extension status, and table health.
"""
import sys
from sqlalchemy import create_engine, text
from backend.app.core.config import settings


def verify_database():
    print("=" * 70)
    print("  SMART LIBRARY SYSTEM - DATABASE HEALTH & SCHEMA DIAGNOSTIC")
    print("=" * 70)
    print(f"Connecting to: {settings.DATABASE_URL.split('@')[-1] if '@' in settings.DATABASE_URL else settings.DATABASE_URL}")

    try:
        engine = create_engine(settings.DATABASE_URL)
        with engine.connect() as conn:
            # 1. Engine & Version
            version = conn.execute(text("SELECT version();")).scalar()
            print("\n[1/5] Connection Successful!")
            print(f"  -> PostgreSQL Version: {version[:55]}...")

            # 2. btree_gist Extension
            ext = conn.execute(
                text("SELECT extname, extversion FROM pg_extension WHERE extname = 'btree_gist';")
            ).first()
            if ext:
                print(f"\n[2/5] btree_gist Extension: INSTALLED (v{ext[1]})")
            else:
                print("\n[2/5] btree_gist Extension: NOT FOUND! (Required for GiST exclusions)")

            # 3. Tables Check
            tables = [
                "seats", "shifts", "students", "memberships", "payments",
                "attendance", "users", "audit_logs"
            ]
            print("\n[3/5] Verifying Core Database Tables:")
            for t in tables:
                exists = conn.execute(
                    text("SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = :t)"),
                    {"t": t}
                ).scalar()
                if exists:
                    count = conn.execute(text(f"SELECT COUNT(*) FROM {t}")).scalar()
                    print(f"  -> {t:<15} : EXISTS ({count} records)")
                else:
                    print(f"  -> {t:<15} : MISSING (Run 'python -m alembic upgrade head')")

            # 4. GiST Exclusion Constraints
            print("\n[4/5] Checking Multidimensional GiST Exclusion Constraints:")
            constraints = conn.execute(
                text("""
                    SELECT conname FROM pg_constraint 
                    WHERE conname IN ('exclude_seat_time_conflict', 'exclude_student_time_conflict')
                """)
            ).scalars().all()
            for c in ['exclude_seat_time_conflict', 'exclude_student_time_conflict']:
                if c in constraints:
                    print(f"  -> {c:<32} : ACTIVE")
                else:
                    print(f"  -> {c:<32} : NOT FOUND")

            # 5. Expanded View
            print("\n[5/5] Checking Dynamic Status View:")
            view_exists = conn.execute(
                text("SELECT EXISTS (SELECT FROM information_schema.views WHERE table_name = 'v_memberships_expanded')")
            ).scalar()
            if view_exists:
                print("  -> v_memberships_expanded       : ACTIVE")
            else:
                print("  -> v_memberships_expanded       : NOT FOUND")

        print("\n" + "=" * 70)
        print("  DATABASE HEALTH DIAGNOSTIC COMPLETED.")
        print("=" * 70)
        return True

    except Exception as e:
        print(f"\n[ERROR] Connection or query failed: {e}")
        return False


if __name__ == "__main__":
    success = verify_database()
    sys.exit(0 if success else 1)
