from datetime import date
from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from backend.app.db.session import get_db
from backend.app.schemas.attendance import (
    AttendanceCheckInSchema,
    AttendanceCheckOutSchema,
    AttendanceResponseSchema,
)
from backend.app.services.attendance_service import attendance_service

router = APIRouter(prefix="/attendance", tags=["Attendance"])


def format_attendance_response(att) -> AttendanceResponseSchema:
    duration_hours = None
    if att.check_out and att.check_in:
        duration_hours = round((att.check_out - att.check_in).total_seconds() / 3600.0, 2)

    return AttendanceResponseSchema(
        id=att.id,
        student_id=att.student_id,
        student_name=att.student.full_name if att.student else None,
        membership_id=att.membership_id,
        seat_id=att.membership.seat_id if att.membership else None,
        attendance_date=att.attendance_date,
        check_in=att.check_in,
        check_out=att.check_out,
        status=att.status,
        source=att.source,
        duration_hours=duration_hours,
        notes=att.notes,
        created_at=att.created_at
    )


@router.post("/check-in", response_model=AttendanceResponseSchema, status_code=status.HTTP_201_CREATED)
def record_student_check_in(
    payload: AttendanceCheckInSchema,
    db: Session = Depends(get_db)
):
    """
    Records student physical arrival at desk.
    Verifies that the student holds an active membership for the current date.
    """
    att = attendance_service.record_check_in(db=db, payload=payload)
    return format_attendance_response(att)


@router.post("/{id}/check-out", response_model=AttendanceResponseSchema)
def record_student_check_out(
    id: UUID,
    payload: Optional[AttendanceCheckOutSchema] = None,
    db: Session = Depends(get_db)
):
    """
    Records student departure, calculates session duration, and completes the log.
    """
    if payload is None:
        payload = AttendanceCheckOutSchema()
    att = attendance_service.record_check_out(db=db, attendance_id=id, payload=payload)
    return format_attendance_response(att)


@router.get("/daily", response_model=List[AttendanceResponseSchema])
def list_daily_attendance(
    attendance_date: Optional[date] = Query(None, description="Target date (defaults to today)"),
    db: Session = Depends(get_db)
):
    """
    Returns daily attendance logs for front desk review.
    """
    logs = attendance_service.list_daily(db=db, attendance_date=attendance_date)
    return [format_attendance_response(att) for att in logs]
