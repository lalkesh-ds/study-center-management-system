from datetime import date
from decimal import Decimal
from typing import List, Optional
from uuid import UUID
from pydantic import BaseModel


class DashboardSummarySchema(BaseModel):
    """Real-time operational KPIs resolving the 100-seat multiplexing capacity."""
    target_date: date
    total_physical_seats: int = 100
    occupied_physical_seats: int
    physical_utilization_rate: float

    # Shift-Slot Occupancy (Out of 300 Daily Slots)
    total_slot_capacity: int = 300
    booked_shift_slots: int
    slot_occupancy_rate: float

    # Time-Weighted Occupancy (Out of 1,600 Daily Seat-Hours)
    total_seat_hours_capacity: int = 1600
    booked_seat_hours: float
    seat_hour_occupancy_rate: float

    # Enrollment & Revenue KPIs
    active_students_count: int
    expiring_soon_count: int
    expired_unrenewed_count: int
    daily_revenue: Decimal
    total_outstanding_dues: Decimal


class MembershipExpirySchema(BaseModel):
    """Item in the expiring subscription action queue."""
    membership_id: UUID
    student_id: UUID
    student_name: str
    student_mobile: str
    seat_number: int
    shift_name: str
    start_date: date
    end_date: date
    days_remaining: int
    due_amount: Decimal


class RevenueReportSchema(BaseModel):
    """Financial revenue collection summary."""
    start_date: date
    end_date: date
    total_revenue: Decimal
    transaction_count: int
    cash_total: Decimal
    upi_total: Decimal
    card_total: Decimal
    net_banking_total: Decimal
