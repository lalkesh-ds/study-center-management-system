import uuid
from datetime import date, datetime, timezone
from typing import Optional
from sqlalchemy import (
    Date, DateTime, Enum, ForeignKey, Text, UniqueConstraint
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.app.db.base import Base


class Attendance(Base):
    """
    Daily physical attendance logs.
    Linked to Student and Membership.
    """
    __tablename__ = "attendance"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    student_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("students.id", ondelete="RESTRICT"),
        nullable=False,
        index=True
    )
    membership_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("memberships.id", ondelete="RESTRICT"),
        nullable=False,
        index=True
    )
    attendance_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)

    check_in: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    check_out: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    status: Mapped[str] = mapped_column(
        Enum("PRESENT", "ABSENT", "HALF_DAY", name="attendance_status_enum"),
        default="PRESENT",
        nullable=False
    )
    source: Mapped[str] = mapped_column(
        Enum("MANUAL_STAFF", "KIOSK", "BIOMETRIC_SYNC", name="attendance_source_enum"),
        default="MANUAL_STAFF",
        nullable=False
    )

    marked_by: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )

    # Invariant: exactly one attendance entry per membership per day
    __table_args__ = (
        UniqueConstraint("membership_id", "attendance_date", name="uq_membership_daily_attendance"),
    )

    # Relationships
    student = relationship("Student", backref="attendance_logs")
    membership = relationship("Membership", backref="attendance_logs")
