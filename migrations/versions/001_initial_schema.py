"""Initial database schema with GiST multidimensional exclusion constraints and operational views

Revision ID: 001_initial_schema
Revises: 
Create Date: 2026-10-06 17:30:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '001_initial_schema'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Enable Required PostgreSQL Extensions
    op.execute('CREATE EXTENSION IF NOT EXISTS "btree_gist";')
    op.execute('CREATE EXTENSION IF NOT EXISTS "uuid-ossp";')

    # 2. Create Domain Enums
    op.execute("CREATE TYPE user_role_enum AS ENUM ('ADMIN', 'STAFF');")
    op.execute("CREATE TYPE student_status_enum AS ENUM ('ACTIVE', 'INACTIVE', 'BLOCKED');")
    op.execute("CREATE TYPE membership_status_enum AS ENUM ('ACTIVE', 'CANCELLED');")
    op.execute("CREATE TYPE payment_method_enum AS ENUM ('CASH', 'UPI', 'CARD', 'NET_BANKING');")
    op.execute("CREATE TYPE payment_status_enum AS ENUM ('COMPLETED', 'VOIDED');")
    op.execute("CREATE TYPE attendance_status_enum AS ENUM ('PRESENT', 'ABSENT', 'HALF_DAY');")
    op.execute("CREATE TYPE attendance_source_enum AS ENUM ('MANUAL_STAFF', 'KIOSK', 'BIOMETRIC_SYNC');")

    # 3. Table: users
    op.execute("""
    CREATE TABLE users (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        username VARCHAR(50) NOT NULL UNIQUE,
        email VARCHAR(255) NOT NULL UNIQUE,
        password_hash VARCHAR(255) NOT NULL,
        full_name VARCHAR(100) NOT NULL,
        role user_role_enum NOT NULL DEFAULT 'STAFF',
        is_active BOOLEAN NOT NULL DEFAULT TRUE,
        created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
    );
    CREATE INDEX idx_users_username ON users(username);
    CREATE INDEX idx_users_email ON users(email);
    """)

    # 4. Table: students
    op.execute("""
    CREATE TABLE students (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        student_code VARCHAR(20) NOT NULL UNIQUE,
        full_name VARCHAR(100) NOT NULL,
        mobile VARCHAR(15) NOT NULL UNIQUE,
        email VARCHAR(255) NULL,
        id_proof_type VARCHAR(50) NULL,
        id_proof_number VARCHAR(100) NULL,
        emergency_contact VARCHAR(15) NULL,
        address TEXT NULL,
        status student_status_enum NOT NULL DEFAULT 'ACTIVE',
        notes TEXT NULL,
        created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
    );
    CREATE INDEX idx_students_mobile ON students(mobile);
    CREATE INDEX idx_students_status ON students(status);
    CREATE INDEX idx_students_full_name ON students(full_name);
    """)

    # 5. Table: seats (1 to 100)
    op.execute("""
    CREATE TABLE seats (
        id INT PRIMARY KEY,
        seat_number INT NOT NULL UNIQUE CHECK (seat_number >= 1 AND seat_number <= 100),
        is_active BOOLEAN NOT NULL DEFAULT TRUE,
        has_power_outlet BOOLEAN NOT NULL DEFAULT TRUE,
        has_locker BOOLEAN NOT NULL DEFAULT FALSE,
        description VARCHAR(255) NULL,
        created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
    );
    CREATE INDEX idx_seats_is_active ON seats(is_active);
    """)

    # 6. Table: shifts
    op.execute("""
    CREATE TABLE shifts (
        id SERIAL PRIMARY KEY,
        name VARCHAR(50) NOT NULL UNIQUE,
        start_time TIME NOT NULL,
        end_time TIME NOT NULL,
        start_minute INT NOT NULL,
        end_minute INT NOT NULL,
        base_fee NUMERIC(10, 2) NOT NULL CHECK (base_fee >= 0),
        is_active BOOLEAN NOT NULL DEFAULT TRUE,
        created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
        CONSTRAINT chk_shift_time_order CHECK (start_time < end_time),
        CONSTRAINT chk_shift_minute_order CHECK (start_minute < end_minute AND start_minute >= 0 AND end_minute <= 1440)
    );
    """)

    # 7. Table: memberships (with Multidimensional GiST Exclusion Constraints)
    op.execute("""
    CREATE TABLE memberships (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        student_id UUID NOT NULL REFERENCES students(id) ON DELETE RESTRICT,
        seat_id INT NOT NULL REFERENCES seats(id) ON DELETE RESTRICT,
        shift_id INT NOT NULL REFERENCES shifts(id) ON DELETE RESTRICT,
        
        start_date DATE NOT NULL,
        end_date DATE NOT NULL,
        start_minute INT NOT NULL,
        end_minute INT NOT NULL,
        
        base_fee NUMERIC(10, 2) NOT NULL CHECK (base_fee >= 0),
        discount_amount NUMERIC(10, 2) NOT NULL DEFAULT 0.00 CHECK (discount_amount >= 0),
        final_fee NUMERIC(10, 2) NOT NULL CHECK (final_fee >= 0),
        
        status membership_status_enum NOT NULL DEFAULT 'ACTIVE',
        
        cancelled_at TIMESTAMPTZ NULL,
        cancelled_by UUID NULL REFERENCES users(id) ON DELETE SET NULL,
        cancel_reason TEXT NULL,
        
        renewed_from_id UUID NULL REFERENCES memberships(id) ON DELETE SET NULL,
        created_by UUID NULL REFERENCES users(id) ON DELETE SET NULL,
        created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
        
        CONSTRAINT chk_membership_date_order CHECK (start_date <= end_date),
        CONSTRAINT chk_membership_final_fee CHECK (final_fee = (base_fee - discount_amount)),
        CONSTRAINT chk_membership_cancelled_meta CHECK (
            (status = 'CANCELLED' AND cancelled_at IS NOT NULL AND cancel_reason IS NOT NULL)
            OR (status = 'ACTIVE' AND cancelled_at IS NULL AND cancel_reason IS NULL)
        ),
        
        -- Physical GiST Exclusion 1: Seat Time Conflict
        CONSTRAINT exclude_seat_time_conflict EXCLUDE USING gist (
            seat_id WITH =,
            daterange(start_date, end_date, '[]') WITH &&,
            int4range(start_minute, end_minute, '[)') WITH &&
        ) WHERE (status = 'ACTIVE'),
        
        -- Physical GiST Exclusion 2: Student Time Conflict
        CONSTRAINT exclude_student_time_conflict EXCLUDE USING gist (
            student_id WITH =,
            daterange(start_date, end_date, '[]') WITH &&,
            int4range(start_minute, end_minute, '[)') WITH &&
        ) WHERE (status = 'ACTIVE')
    );

    CREATE INDEX idx_memberships_student_id ON memberships(student_id);
    CREATE INDEX idx_memberships_seat_id ON memberships(seat_id);
    CREATE INDEX idx_memberships_dates ON memberships(start_date, end_date);
    CREATE INDEX idx_memberships_status ON memberships(status);
    CREATE INDEX idx_memberships_renewed_from ON memberships(renewed_from_id);
    """)

    # 8. Table: payments
    op.execute("""
    CREATE TABLE payments (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        receipt_number VARCHAR(30) NOT NULL UNIQUE,
        membership_id UUID NOT NULL REFERENCES memberships(id) ON DELETE RESTRICT,
        student_id UUID NOT NULL REFERENCES students(id) ON DELETE RESTRICT,
        
        amount NUMERIC(10, 2) NOT NULL CHECK (amount > 0),
        payment_method payment_method_enum NOT NULL,
        transaction_ref VARCHAR(100) NULL,
        status payment_status_enum NOT NULL DEFAULT 'COMPLETED',
        
        voided_at TIMESTAMPTZ NULL,
        voided_by UUID NULL REFERENCES users(id) ON DELETE SET NULL,
        void_reason TEXT NULL,
        
        notes TEXT NULL,
        received_by UUID NULL REFERENCES users(id) ON DELETE SET NULL,
        created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
        
        CONSTRAINT chk_payment_void_meta CHECK (
            (status = 'VOIDED' AND voided_at IS NOT NULL AND void_reason IS NOT NULL)
            OR (status = 'COMPLETED' AND voided_at IS NULL AND void_reason IS NULL)
        )
    );

    CREATE INDEX idx_payments_membership_id ON payments(membership_id);
    CREATE INDEX idx_payments_student_id ON payments(student_id);
    CREATE INDEX idx_payments_status ON payments(status);
    CREATE INDEX idx_payments_created_at ON payments(created_at);
    """)

    # 9. Table: attendance
    op.execute("""
    CREATE TABLE attendance (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        student_id UUID NOT NULL REFERENCES students(id) ON DELETE RESTRICT,
        membership_id UUID NOT NULL REFERENCES memberships(id) ON DELETE RESTRICT,
        attendance_date DATE NOT NULL,
        
        check_in TIMESTAMPTZ NOT NULL,
        check_out TIMESTAMPTZ NULL,
        status attendance_status_enum NOT NULL DEFAULT 'PRESENT',
        source attendance_source_enum NOT NULL DEFAULT 'MANUAL_STAFF',
        marked_by UUID NULL REFERENCES users(id) ON DELETE SET NULL,
        notes TEXT NULL,
        created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
        
        CONSTRAINT chk_attendance_times CHECK (check_out IS NULL OR check_out >= check_in),
        CONSTRAINT uq_membership_daily_attendance UNIQUE (membership_id, attendance_date)
    );

    CREATE INDEX idx_attendance_student_date ON attendance(student_id, attendance_date);
    CREATE INDEX idx_attendance_date ON attendance(attendance_date);
    """)

    # 10. Table: audit_logs
    op.execute("""
    CREATE TABLE audit_logs (
        id BIGSERIAL PRIMARY KEY,
        user_id UUID NULL REFERENCES users(id) ON DELETE SET NULL,
        action VARCHAR(50) NOT NULL,
        entity_name VARCHAR(50) NOT NULL,
        entity_id VARCHAR(50) NOT NULL,
        old_values JSONB NULL,
        new_values JSONB NULL,
        ip_address VARCHAR(45) NULL,
        created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
    );

    CREATE INDEX idx_audit_entity ON audit_logs(entity_name, entity_id);
    CREATE INDEX idx_audit_created_at ON audit_logs(created_at);
    """)

    # 11. Operational View: v_memberships_expanded
    op.execute("""
    CREATE OR REPLACE VIEW v_memberships_expanded AS
    SELECT 
        m.id,
        m.student_id,
        st.full_name AS student_name,
        st.mobile AS student_mobile,
        m.seat_id,
        s.seat_number,
        m.shift_id,
        sh.name AS shift_name,
        m.start_date,
        m.end_date,
        m.final_fee,
        m.status AS persisted_status,
        CASE 
            WHEN m.status = 'CANCELLED' THEN 'CANCELLED'
            WHEN CURRENT_DATE < m.start_date THEN 'UPCOMING'
            WHEN CURRENT_DATE > m.end_date THEN 'EXPIRED'
            WHEN CURRENT_DATE >= (m.end_date - INTERVAL '3 days') AND CURRENT_DATE <= m.end_date THEN 'EXPIRING_SOON'
            ELSE 'ACTIVE'
        END AS derived_status,
        COALESCE(SUM(p.amount) FILTER (WHERE p.status = 'COMPLETED'), 0.00) AS total_paid,
        m.final_fee - COALESCE(SUM(p.amount) FILTER (WHERE p.status = 'COMPLETED'), 0.00) AS due_amount,
        CASE 
            WHEN COALESCE(SUM(p.amount) FILTER (WHERE p.status = 'COMPLETED'), 0.00) = 0 THEN 'PENDING'
            WHEN COALESCE(SUM(p.amount) FILTER (WHERE p.status = 'COMPLETED'), 0.00) < m.final_fee THEN 'PARTIAL'
            ELSE 'PAID'
        END AS payment_status
    FROM memberships m
    JOIN students st ON m.student_id = st.id
    JOIN seats s ON m.seat_id = s.id
    JOIN shifts sh ON m.shift_id = sh.id
    LEFT JOIN payments p ON m.id = p.membership_id
    GROUP BY m.id, st.id, s.id, sh.id;
    """)


def downgrade() -> None:
    op.execute("DROP VIEW IF EXISTS v_memberships_expanded;")
    op.execute("DROP TABLE IF EXISTS audit_logs;")
    op.execute("DROP TABLE IF EXISTS attendance;")
    op.execute("DROP TABLE IF EXISTS payments;")
    op.execute("DROP TABLE IF EXISTS memberships;")
    op.execute("DROP TABLE IF EXISTS shifts;")
    op.execute("DROP TABLE IF EXISTS seats;")
    op.execute("DROP TABLE IF EXISTS students;")
    op.execute("DROP TABLE IF EXISTS users;")
    
    op.execute("DROP TYPE IF EXISTS attendance_source_enum;")
    op.execute("DROP TYPE IF EXISTS attendance_status_enum;")
    op.execute("DROP TYPE IF EXISTS payment_status_enum;")
    op.execute("DROP TYPE IF EXISTS payment_method_enum;")
    op.execute("DROP TYPE IF EXISTS membership_status_enum;")
    op.execute("DROP TYPE IF EXISTS student_status_enum;")
    op.execute("DROP TYPE IF EXISTS user_role_enum;")
