from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class SeatResponseSchema(BaseModel):
    """Desk inventory entity schema."""
    id: int
    seat_number: int
    is_active: bool
    has_power_outlet: bool
    has_locker: bool
    description: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class SeatStatusUpdateSchema(BaseModel):
    """Payload to toggle seat operational / maintenance status."""
    is_active: bool = Field(..., description="True for active, False for maintenance/disabled")
    reason: Optional[str] = Field(None, max_length=255, description="Reason for status change")
