from datetime import date, datetime
from typing import Optional
from uuid import UUID
from pydantic import BaseModel, Field


class AttendanceCheckInSchema(BaseModel):
    """Payload to record student arrival check-in."""
    student_id: Optional[UUID] = Field(None, description="Student ID (if known)")
    membership_id: Optional[UUID] = Field(None, description="Direct Membership ID (if known)")
    source: str = Field(default="MANUAL_STAFF", pattern="^(MANUAL_STAFF|KIOSK|BIOMETRIC_SYNC)$")
    notes: Optional[str] = Field(None, description="Optional desk notes")


class AttendanceCheckOutSchema(BaseModel):
    """Payload to record student departure check-out."""
    check_out_time: Optional[datetime] = Field(None, description="Departure time (defaults to current time)")


class AttendanceResponseSchema(BaseModel):
    """Attendance log representation."""
    id: UUID
    student_id: UUID
    student_name: Optional[str] = None
    membership_id: UUID
    seat_id: Optional[int] = None
    attendance_date: date
    check_in: datetime
    check_out: Optional[datetime] = None
    status: str
    source: str
    duration_hours: Optional[float] = None
    notes: Optional[str] = None
    created_at: datetime

    model_config = {"from_attributes": True}
