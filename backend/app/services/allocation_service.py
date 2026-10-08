from datetime import date
from typing import Dict, List, Optional, Tuple
from uuid import UUID
from sqlalchemy import select, and_
from sqlalchemy.orm import Session

from backend.app.core.config import settings
from backend.app.models.seat import Seat
from backend.app.models.shift import Shift
from backend.app.models.membership import Membership


class AllocationService:
    """
    Core Domain Seat Allocation Engine.
    Enforces physical desk constraints, half-open interval checks,
    and multi-tier collision detection.
    """

    @staticmethod
    def check_seat_availability(
        db: Session,
        seat_id: int,
        start_date: date,
        end_date: date,
        start_minute: int,
        end_minute: int,
        exclude_membership_id: Optional[UUID] = None
    ) -> Tuple[bool, Optional[Membership]]:
        """
        Evaluates whether a physical seat is free from active collisions.
        Returns:
            (True, None) if free and active.
            (False, None) if seat is inactive/under maintenance.
            (False, conflicting_membership) if blocked by an active membership.
        """
        # 1. Verify seat physical status
        seat = db.get(Seat, seat_id)
        if not seat or not seat.is_active:
            return False, None

        # 2. Check for overlapping active memberships
        # Mathematical Condition:
        #   status = 'ACTIVE'
        #   AND m.start_date <= end_date AND m.end_date >= start_date (Inclusive Date Overlap)
        #   AND m.start_minute < end_minute AND m.end_minute > start_minute (Half-Open Time Overlap)
        stmt = select(Membership).where(
            and_(
                Membership.seat_id == seat_id,
                Membership.status == "ACTIVE",
                Membership.start_date <= end_date,
                Membership.end_date >= start_date,
                Membership.start_minute < end_minute,
                Membership.end_minute > start_minute
            )
        )

        if exclude_membership_id:
            stmt = stmt.where(Membership.id != exclude_membership_id)

        conflicting_membership = db.scalars(stmt).first()
        if conflicting_membership:
            return False, conflicting_membership

        return True, None

    @staticmethod
    def check_student_time_conflict(
        db: Session,
        student_id: UUID,
        start_date: date,
        end_date: date,
        start_minute: int,
        end_minute: int,
        exclude_membership_id: Optional[UUID] = None
    ) -> Tuple[bool, Optional[Membership]]:
        """
        Verifies that a student does not hold simultaneous overlapping shifts.
        If ALLOW_MULTI_SHIFT_PER_STUDENT is True, disjoint time slots are allowed.
        If False, any active membership in the date range causes a collision.
        """
        stmt = select(Membership).where(
            and_(
                Membership.student_id == student_id,
                Membership.status == "ACTIVE",
                Membership.start_date <= end_date,
                Membership.end_date >= start_date
            )
        )

        if settings.ALLOW_MULTI_SHIFT_PER_STUDENT:
            # Overlap only occurs if the time intervals also intersect
            stmt = stmt.where(
                and_(
                    Membership.start_minute < end_minute,
                    Membership.end_minute > start_minute
                )
            )

        if exclude_membership_id:
            stmt = stmt.where(Membership.id != exclude_membership_id)

        collision = db.scalars(stmt).first()
        if collision:
            return False, collision

        return True, None

    @staticmethod
    def get_seat_availability_matrix(
        db: Session,
        start_date: date,
        end_date: date,
        shift_id: int
    ) -> Dict:
        """
        Generates real-time availability status for all 100 physical seats
        for a given target date range and shift.
        """
        shift = db.get(Shift, shift_id)
        if not shift:
            return {"error": "Shift not found"}

        # Query all active seats
        seats = list(db.scalars(select(Seat).order_by(Seat.seat_number.asc())).all())

        # Query all conflicting memberships for this shift window
        overlapping_stmt = select(Membership).where(
            and_(
                Membership.status == "ACTIVE",
                Membership.start_date <= end_date,
                Membership.end_date >= start_date,
                Membership.start_minute < shift.end_minute,
                Membership.end_minute > shift.start_minute
            )
        )
        overlapping_memberships = {m.seat_id: m for m in db.scalars(overlapping_stmt).all()}

        seat_matrix = []
        available_count = 0
        occupied_count = 0
        maintenance_count = 0

        for seat in seats:
            if not seat.is_active:
                status_str = "MAINTENANCE"
                maintenance_count += 1
                occupant_info = None
            elif seat.id in overlapping_memberships:
                status_str = "OCCUPIED"
                occupied_count += 1
                occ = overlapping_memberships[seat.id]
                occupant_info = {
                    "student_id": str(occ.student_id),
                    "membership_id": str(occ.id),
                    "shift_name": occ.shift.name if occ.shift else None
                }
            else:
                status_str = "AVAILABLE"
                available_count += 1
                occupant_info = None

            seat_matrix.append({
                "seat_id": seat.id,
                "seat_number": seat.seat_number,
                "status": status_str,
                "has_power_outlet": seat.has_power_outlet,
                "has_locker": seat.has_locker,
                "occupant": occupant_info
            })

        return {
            "shift_id": shift.id,
            "shift_name": shift.name,
            "start_date": str(start_date),
            "end_date": str(end_date),
            "total_seats": len(seats),
            "available_count": available_count,
            "occupied_count": occupied_count,
            "maintenance_count": maintenance_count,
            "seats": seat_matrix
        }


allocation_service = AllocationService()
