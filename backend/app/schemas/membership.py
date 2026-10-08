from datetime import date, datetime
from decimal import Decimal
from typing import Optional
from uuid import UUID
from pydantic import BaseModel, Field, model_validator


class MembershipCreateSchema(BaseModel):
    """Payload to create a new membership allocation (Admission)."""
    student_id: UUID = Field(..., description="Target student identifier")
    seat_id: int = Field(..., ge=1, le=100, description="Target physical seat number (1-100)")
    shift_id: int = Field(..., ge=1, le=4, description="Operating shift identifier (1-4)")
    start_date: date = Field(..., description="Membership start date (inclusive)")
    end_date: date = Field(..., description="Membership end date (inclusive)")
    discount_amount: Decimal = Field(default=Decimal("0.00"), ge=0, description="Approved discount amount")
    
    # Optional upfront fee collection during admission
    initial_payment_amount: Optional[Decimal] = Field(None, ge=0, description="Upfront payment collected")
    initial_payment_method: Optional[str] = Field(None, pattern="^(CASH|UPI|CARD|NET_BANKING)$", description="Payment method")
    initial_payment_ref: Optional[str] = Field(None, max_length=100, description="Transaction reference / UTR")

    @model_validator(mode="after")
    def validate_dates(self):
        if self.start_date > self.end_date:
            raise ValueError("Membership start_date must not be after end_date.")
        if self.initial_payment_amount and self.initial_payment_amount > 0 and not self.initial_payment_method:
            raise ValueError("initial_payment_method is required when initial_payment_amount is provided.")
        return self


class MembershipRenewSchema(BaseModel):
    """Payload to extend an existing subscription with lineage preservation."""
    start_date: date = Field(..., description="Start date of renewal period")
    end_date: date = Field(..., description="End date of renewal period")
    target_seat_id: Optional[int] = Field(None, ge=1, le=100, description="Optional new seat (retains previous if omitted)")
    target_shift_id: Optional[int] = Field(None, ge=1, le=4, description="Optional new shift (retains previous if omitted)")
    discount_amount: Decimal = Field(default=Decimal("0.00"), ge=0, description="Discount amount for renewal cycle")
    initial_payment_amount: Optional[Decimal] = Field(None, ge=0)
    initial_payment_method: Optional[str] = Field(None, pattern="^(CASH|UPI|CARD|NET_BANKING)$")
    initial_payment_ref: Optional[str] = None

    @model_validator(mode="after")
    def validate_dates(self):
        if self.start_date > self.end_date:
            raise ValueError("Renewal start_date must not be after end_date.")
        if self.initial_payment_amount and self.initial_payment_amount > 0 and not self.initial_payment_method:
            raise ValueError("initial_payment_method is required when initial_payment_amount is provided.")
        return self


class MembershipCancelSchema(BaseModel):
    """Payload to cancel an active membership."""
    cancel_reason: str = Field(..., min_length=5, max_length=255, description="Mandatory cancellation reason")



from pydantic import computed_field

class MembershipResponseSchema(BaseModel):
    """Public membership response representation."""
    id: UUID
    student_id: UUID
    student_name: Optional[str] = None
    seat_id: int
    seat_number: Optional[int] = None
    shift_id: int
    shift_name: Optional[str] = None
    start_date: date
    end_date: date
    start_minute: int
    end_minute: int
    base_fee: Decimal
    discount_amount: Decimal
    final_fee: Decimal
    status: str
    derived_status: str
    renewed_from_id: Optional[UUID] = None
    total_paid: Decimal = Decimal("0.00")
    due_amount: Decimal = Decimal("0.00")
    payment_status: str = "PENDING"
    created_at: datetime

    model_config = {"from_attributes": True}

    @computed_field
    def paid_amount(self) -> Decimal:
        return self.total_paid


class MembershipDetailSchema(MembershipResponseSchema):
    """Detailed membership view with ledger and audit metrics."""
    cancelled_at: Optional[datetime] = None
    cancel_reason: Optional[str] = None
