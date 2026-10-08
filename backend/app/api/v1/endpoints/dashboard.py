from datetime import date
from typing import List, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from backend.app.core.exceptions import ValidationException
from backend.app.db.session import get_db
from backend.app.schemas.dashboard import (
    DashboardSummarySchema,
    MembershipExpirySchema,
    RevenueReportSchema,
)
from backend.app.services.analytics_service import analytics_service

router = APIRouter(tags=["Dashboard & Reports"])


@router.get("/dashboard/summary", response_model=DashboardSummarySchema)
def get_dashboard_summary(
    target_date: Optional[date] = Query(None, description="Target evaluation date (defaults to today)"),
    db: Session = Depends(get_db)
):
    """
    Returns real-time capacity and revenue KPIs for the study center:
    - Physical Seat Utilization (% of 100 chairs)
    - Slot-Capacity Occupancy Rate (% of 300 daily slots)
    - Time-Weighted Capacity Occupancy Rate (% of 1,600 daily seat-hours)
    - Active students, expiring subscriptions, and financial dues.
    """
    return analytics_service.get_dashboard_summary(db=db, target_date=target_date)


@router.get("/reports/expiring", response_model=List[MembershipExpirySchema])
def get_expiring_memberships_report(
    days_threshold: int = Query(3, ge=1, le=30, description="Alert horizon in days (default 3)"),
    db: Session = Depends(get_db)
):
    """
    Returns the operational action queue of memberships expiring soon.
    """
    return analytics_service.get_expiring_queue(db=db, days_threshold=days_threshold)


from datetime import date, timedelta

@router.get("/reports/revenue", response_model=RevenueReportSchema)
def get_revenue_collection_report(
    start_date: Optional[date] = Query(None, description="Start date (defaults to 30 days ago)"),
    end_date: Optional[date] = Query(None, description="End date (defaults to today)"),
    db: Session = Depends(get_db)
):
    """
    Returns financial collections broken down by payment method (CASH, UPI, CARD, NET_BANKING).
    """
    if end_date is None:
        end_date = date.today()
    if start_date is None:
        start_date = end_date - timedelta(days=30)

    if start_date > end_date:
        raise ValidationException("Start date cannot be after end date.", code="INVALID_DATE_RANGE")

    return analytics_service.get_revenue_report(db=db, start_date=start_date, end_date=end_date)
