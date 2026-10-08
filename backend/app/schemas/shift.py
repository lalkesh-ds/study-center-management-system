from datetime import time, datetime
from decimal import Decimal
from pydantic import BaseModel


class ShiftResponseSchema(BaseModel):
    """Canonical operating shift response schema."""
    id: int
    name: str
    start_time: time
    end_time: time
    start_minute: int
    end_minute: int
    base_fee: Decimal
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}
