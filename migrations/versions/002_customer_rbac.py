"""Add customer role, student linkage, and refresh tokens table

Revision ID: 002_customer_rbac
Revises: 001_initial_schema
Create Date: 2026-10-10 18:30:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '002_customer_rbac'
down_revision: Union[str, None] = '001_initial_schema'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    is_postgres = bind.dialect.name == "postgresql"

    # 1. Update user_role_enum to include 'CUSTOMER' if PostgreSQL
    if is_postgres:
        op.execute("ALTER TYPE user_role_enum ADD VALUE IF NOT EXISTS 'CUSTOMER';")
        # Add columns to users table
        op.execute("""
            ALTER TABLE users ADD COLUMN IF NOT EXISTS mobile VARCHAR(15) NULL UNIQUE;
            ALTER TABLE users ADD COLUMN IF NOT EXISTS student_id UUID NULL UNIQUE REFERENCES students(id) ON DELETE SET NULL;
            CREATE INDEX IF NOT EXISTS idx_users_mobile ON users(mobile);
            CREATE INDEX IF NOT EXISTS idx_users_student_id ON users(student_id);
        """)
        # Create refresh_tokens table
        op.execute("""
            CREATE TABLE IF NOT EXISTS refresh_tokens (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                token_hash VARCHAR(64) NOT NULL UNIQUE,
                expires_at TIMESTAMPTZ NOT NULL,
                is_revoked BOOLEAN NOT NULL DEFAULT FALSE,
                revoked_at TIMESTAMPTZ NULL,
                created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
                user_agent VARCHAR(255) NULL,
                ip_address VARCHAR(45) NULL
            );
            CREATE INDEX IF NOT EXISTS idx_refresh_tokens_user_id ON refresh_tokens(user_id);
            CREATE INDEX IF NOT EXISTS idx_refresh_tokens_token_hash ON refresh_tokens(token_hash);
        """)
    else:
        # SQLite fallback for migrations in dev/test
        with op.batch_alter_table("users") as batch_op:
            batch_op.add_column(sa.Column("mobile", sa.String(15), nullable=True, unique=True))
            batch_op.add_column(sa.Column("student_id", sa.Uuid(), nullable=True))
            batch_op.create_foreign_key("fk_users_student_id", "students", ["student_id"], ["id"], ondelete="SET NULL")
            batch_op.create_unique_constraint("uq_users_student_id", ["student_id"])

        op.create_table(
            "refresh_tokens",
            sa.Column("id", sa.Uuid(), primary_key=True),
            sa.Column("user_id", sa.Uuid(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True),
            sa.Column("token_hash", sa.String(64), nullable=False, unique=True, index=True),
            sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("is_revoked", sa.Boolean(), default=False, nullable=False),
            sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("user_agent", sa.String(255), nullable=True),
            sa.Column("ip_address", sa.String(45), nullable=True),
        )


def downgrade() -> None:
    bind = op.get_bind()
    is_postgres = bind.dialect.name == "postgresql"

    if is_postgres:
        op.execute("DROP TABLE IF EXISTS refresh_tokens;")
        op.execute("ALTER TABLE users DROP COLUMN IF EXISTS student_id;")
        op.execute("ALTER TABLE users DROP COLUMN IF EXISTS mobile;")
    else:
        op.drop_table("refresh_tokens")
        with op.batch_alter_table("users") as batch_op:
            batch_op.drop_column("student_id")
            batch_op.drop_column("mobile")
