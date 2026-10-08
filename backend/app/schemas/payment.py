from datetime import datetime
from decimal import Decimal
from typing import Optional
from uuid import UUID
from pydantic import BaseModel, Field


class PaymentCreateSchema(BaseModel):
    """Payload to record an installment fee payment."""
    membership_id: UUID = Field(..., description="Target membership ID")
    amount: Decimal = Field(..., gt=0, description="Payment amount (must be positive)")
    payment_method: str = Field(..., pattern="^(CASH|UPI|CARD|NET_BANKING)$", description="Method of payment")
    transaction_ref: Optional[str] = Field(None, max_length=100, description="UPI UTR number / Bank reference")
    notes: Optional[str] = Field(None, description="Optional payment notes")


class PaymentVoidSchema(BaseModel):
    """Payload to void an erroneous payment entry."""
    void_reason: str = Field(..., min_length=5, max_length=255, description="Mandatory reason for voiding")


class PaymentResponseSchema(BaseModel):
    """Payment ledger record response."""
    id: UUID
    receipt_number: str
    membership_id: UUID
    student_id: UUID
    amount: Decimal
    payment_method: str
    transaction_ref: Optional[str] = None
    status: str
    voided_at: Optional[datetime] = None
    void_reason: Optional[str] = None
    notes: Optional[str] = None
    created_at: datetime

    model_config = {"from_attributes": True}
