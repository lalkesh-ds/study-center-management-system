from datetime import date, datetime
from decimal import Decimal
from typing import Optional, List
from uuid import UUID
from pydantic import BaseModel, Field


class CustomerDashboardStats(BaseModel):
    has_active_membership: bool
    active_membership_id: Optional[UUID] = None
    seat_number: Optional[int] = None
    shift_name: Optional[str] = None
    membership_status: Optional[str] = None
    days_remaining: Optional[int] = None
    total_fee: Optional[Decimal] = None
    total_paid: Optional[Decimal] = None
    due_amount: Optional[Decimal] = None
    is_checked_in: bool = False
    current_check_in_time: Optional[datetime] = None


class CustomerProfileResponse(BaseModel):
    id: UUID  # User ID
    student_id: Optional[UUID] = None
    username: str
    email: str
    mobile: Optional[str] = None
    full_name: str
    role: str
    student_code: Optional[str] = None
    id_proof_type: Optional[str] = None
    id_proof_number: Optional[str] = None
    emergency_contact: Optional[str] = None
    address: Optional[str] = None
    created_at: datetime
