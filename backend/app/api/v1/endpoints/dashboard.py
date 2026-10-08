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


import csv
import io
from fastapi.responses import StreamingResponse
from backend.app.models.payment import Payment

@router.get("/reports/revenue/export")
def export_revenue_csv(
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    db: Session = Depends(get_db)
):
    """
    Exports payment transaction records as a downloadable CSV file.
    """
    if end_date is None:
        end_date = date.today()
    if start_date is None:
        start_date = end_date - timedelta(days=30)

    from datetime import datetime, time
    from sqlalchemy import select
    start_dt = datetime.combine(start_date, time.min)
    end_dt = datetime.combine(end_date, time.max)

    stmt = select(Payment).where(Payment.created_at >= start_dt, Payment.created_at <= end_dt).order_by(Payment.created_at.desc())
    payments = db.execute(stmt).scalars().all()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["Receipt Number", "Payment ID", "Date", "Amount", "Payment Method", "Status", "Transaction Ref", "Void Reason"])

    for p in payments:
        writer.writerow([
            p.receipt_number,
            str(p.id),
            p.created_at.strftime("%Y-%m-%d %H:%M:%S") if p.created_at else "",
            f"{p.amount:.2f}",
            p.payment_method,
            p.status,
            p.transaction_ref or "",
            p.void_reason or ""
        ])

    output.seek(0)
    filename = f"revenue_report_{start_date}_to_{end_date}.csv"
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )
