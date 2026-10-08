import uuid
from datetime import date, datetime, timezone, timedelta
from decimal import Decimal
from typing import Optional
from sqlalchemy import (
    Integer, String, Numeric, Date, DateTime, Enum, ForeignKey, Text
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.app.db.base import Base


class Membership(Base):
    """
    Membership subscription contracts.
    Represents the lease of a Seat for a Shift over an inclusive Date Range.
    """
    __tablename__ = "memberships"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    student_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("students.id", ondelete="RESTRICT"),
        nullable=False,
        index=True
    )
    seat_id: Mapped[int] = mapped_column(
        ForeignKey("seats.id", ondelete="RESTRICT"),
        nullable=False,
        index=True
    )
    shift_id: Mapped[int] = mapped_column(
        ForeignKey("shifts.id", ondelete="RESTRICT"),
        nullable=False
    )

    # Inclusive calendar dates
    start_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    end_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)

    # Canonical half-open time bounds in minutes from midnight [start_minute, end_minute)
    start_minute: Mapped[int] = mapped_column(Integer, nullable=False)
    end_minute: Mapped[int] = mapped_column(Integer, nullable=False)

    # Financial contract
    base_fee: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    discount_amount: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=Decimal("0.00"), nullable=False)
    final_fee: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)

    # Persisted Lifecycle state (Only ACTIVE and CANCELLED)
    status: Mapped[str] = mapped_column(
        Enum("ACTIVE", "CANCELLED", name="membership_status_enum"),
        default="ACTIVE",
        index=True,
        nullable=False
    )

    # Cancellation metadata
    cancelled_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    cancelled_by: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    cancel_reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Renewal chain link
    renewed_from_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        ForeignKey("memberships.id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )

    created_by: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False
    )

    # Relationships
    student = relationship("Student", backref="memberships")
    seat = relationship("Seat", backref="memberships")
    shift = relationship("Shift", backref="memberships")
    renewed_from = relationship("Membership", remote_side=[id], backref="renewals")

    def get_derived_status(self, target_date: Optional[date] = None, alert_threshold_days: int = 3) -> str:
        """
        Dynamically derives user-facing status based on current calendar date.
        Prevents stale-state bugs.
        """
        if self.status == "CANCELLED":
            return "CANCELLED"

        today = target_date or date.today()
        if today < self.start_date:
            return "UPCOMING"
        elif today > self.end_date:
            return "EXPIRED"
        elif today >= (self.end_date - timedelta(days=alert_threshold_days)) and today <= self.end_date:
            return "EXPIRING_SOON"
        else:
            return "ACTIVE"
