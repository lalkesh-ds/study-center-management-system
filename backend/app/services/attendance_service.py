import uuid
from datetime import date, datetime, timezone
from typing import List, Optional, Tuple
from uuid import UUID
from sqlalchemy import select, and_
from sqlalchemy.orm import Session, joinedload

from backend.app.core.exceptions import (
    NotFoundException, ConflictException, ValidationException
)
from backend.app.models.membership import Membership
from backend.app.models.attendance import Attendance
from backend.app.schemas.attendance import AttendanceCheckInSchema, AttendanceCheckOutSchema


class AttendanceService:
    """
    Domain service governing daily student attendance, verification against
    active membership contracts, and study duration tracking.
    """

    @classmethod
    def record_check_in(
        cls,
        db: Session,
        payload: AttendanceCheckInSchema,
        marked_by_user_id: Optional[UUID] = None,
        target_date: Optional[date] = None
    ) -> Attendance:
        """
        Validates membership eligibility and records student arrival.
        """
        today = target_date or date.today()

        # Step 1: Resolve Membership
        membership = None
        if payload.membership_id:
            membership = db.get(Membership, payload.membership_id)
            if not membership or membership.status != "ACTIVE":
                raise ValidationException("Specified membership is invalid or inactive.", code="INVALID_MEMBERSHIP")
            if not (membership.start_date <= today <= membership.end_date):
                raise ValidationException("Membership is not valid for today's date.", code="NO_ACTIVE_MEMBERSHIP_TODAY")
        elif payload.student_id:
            stmt = select(Membership).where(
                and_(
                    Membership.student_id == payload.student_id,
                    Membership.status == "ACTIVE",
                    Membership.start_date <= today,
                    Membership.end_date >= today
                )
            )
            membership = db.scalars(stmt).first()
            if not membership:
                raise ValidationException("No active membership found for this student on current date.", code="NO_ACTIVE_MEMBERSHIP_TODAY")
        else:
            raise ValidationException("Either student_id or membership_id must be provided for check-in.", code="MISSING_IDENTIFIER")

        # Step 2: Prevent duplicate daily check-in
        existing_stmt = select(Attendance).where(
            and_(
                Attendance.membership_id == membership.id,
                Attendance.attendance_date == today
            )
        )
        existing = db.scalars(existing_stmt).first()
        if existing:
            raise ConflictException(
                f"Student is already checked in for today's shift (Checked in at {existing.check_in.strftime('%H:%M:%S')}).",
                code="ALREADY_CHECKED_IN"
            )

        # Step 3: Record Attendance
        attendance = Attendance(
            id=uuid.uuid4(),
            student_id=membership.student_id,
            membership_id=membership.id,
            attendance_date=today,
            check_in=datetime.now(timezone.utc),
            status="PRESENT",
            source=payload.source,
            marked_by=marked_by_user_id,
            notes=payload.notes
        )

        db.add(attendance)
        db.commit()
        db.refresh(attendance)
        return attendance

    @classmethod
    def record_check_out(
        cls,
        db: Session,
        attendance_id: UUID,
        payload: AttendanceCheckOutSchema,
        owner_id: Optional[UUID] = None
    ) -> Attendance:
        """
        Records student departure and marks session completion.
        """
        attendance = db.get(Attendance, attendance_id)
        if not attendance:
            raise NotFoundException(f"Attendance log with ID '{attendance_id}' was not found.", code="ATTENDANCE_NOT_FOUND")

        # Tenant isolation
        if owner_id and attendance.membership and attendance.membership.created_by and attendance.membership.created_by != owner_id:
            raise NotFoundException(f"Attendance log with ID '{attendance_id}' was not found.", code="ATTENDANCE_NOT_FOUND")

        if attendance.check_out is not None:
            raise ValidationException("Student has already completed check-out for this session.", code="ALREADY_CHECKED_OUT")

        check_out_time = payload.check_out_time or datetime.now(timezone.utc)

        # Normalize timezone awareness between check_in and check_out
        check_in_dt = attendance.check_in
        if check_in_dt.tzinfo is not None and check_out_time.tzinfo is None:
            check_out_time = check_out_time.replace(tzinfo=timezone.utc)
        elif check_in_dt.tzinfo is None and check_out_time.tzinfo is not None:
            check_out_time = check_out_time.replace(tzinfo=None)

        if check_out_time < check_in_dt:
            raise ValidationException("Check-out time cannot precede check-in time.", code="INVALID_CHECKOUT_TIME")

        attendance.check_out = check_out_time

        # Calculate session duration
        duration = check_out_time - check_in_dt
        hours = duration.total_seconds() / 3600.0
        if hours < 2.0:
            attendance.status = "HALF_DAY"

        db.commit()
        db.refresh(attendance)
        return attendance

    @classmethod
    def list_daily(
        cls,
        db: Session,
        attendance_date: Optional[date] = None,
        owner_id: Optional[UUID] = None
    ) -> List[Attendance]:
        """Lists daily attendance logs with eager-loaded student and membership relations."""
        target = attendance_date or date.today()
        stmt = (
            select(Attendance)
            .options(
                joinedload(Attendance.student),
                joinedload(Attendance.membership)
            )
            .where(Attendance.attendance_date == target)
        )
        if owner_id:
            stmt = stmt.where(Attendance.membership.has(Membership.created_by == owner_id))

        stmt = stmt.order_by(Attendance.check_in.desc())
        return list(db.scalars(stmt).all())


attendance_service = AttendanceService()
