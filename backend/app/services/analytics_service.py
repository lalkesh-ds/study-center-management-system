from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
from typing import List, Optional
import uuid
from sqlalchemy import select, func, and_, or_, cast, Date
from sqlalchemy.orm import Session, joinedload

from backend.app.models.seat import Seat
from backend.app.models.shift import Shift
from backend.app.models.membership import Membership
from backend.app.models.payment import Payment
from backend.app.repositories.membership_repository import membership_repository
from backend.app.schemas.dashboard import (
    DashboardSummarySchema,
    MembershipExpirySchema,
    RevenueReportSchema,
)


class AnalyticsService:
    """
    Domain service for real-time operational capacity metrics,
    financial collections, and reporting.
    """

    @classmethod
    def get_dashboard_summary(
        cls,
        db: Session,
        target_date: Optional[date] = None,
        owner_id: Optional[uuid.UUID] = None
    ) -> DashboardSummarySchema:
        """
        Computes the three core capacity metrics (Physical Utilization, Slot Occupancy,
        and Time-Weighted Occupancy) along with enrollment and financial KPIs.
        """
        today = target_date or date.today()

        # 1. Fetch active memberships covering target date
        active_conditions = [
            Membership.status == "ACTIVE",
            Membership.start_date <= today,
            Membership.end_date >= today
        ]
        if owner_id:
            active_conditions.append(Membership.created_by == owner_id)

        active_stmt = (
            select(Membership)
            .options(joinedload(Membership.shift))
            .where(and_(*active_conditions))
        )
        active_mems = list(db.scalars(active_stmt).all())

        # Metric A: Physical Seat Utilization (Chairs with >= 1 student)
        occupied_seats = set(m.seat_id for m in active_mems)
        occupied_seats_count = len(occupied_seats)
        physical_rate = round((occupied_seats_count / 100.0) * 100.0, 2)

        # Metric B: Slot-Capacity Occupancy (Out of 300 shift-slots)
        # Full Day = 3 slots, Morning/Afternoon/Evening = 1 slot
        booked_slots = sum(3 if m.shift_id == 4 or (m.shift and m.shift.name == "FULL_DAY") else 1 for m in active_mems)
        slot_rate = round((booked_slots / 300.0) * 100.0, 2)

        # Metric C: Time-Weighted Occupancy (Out of 1,600 daily seat-hours)
        booked_hours = sum((m.end_minute - m.start_minute) / 60.0 for m in active_mems)
        seat_hour_rate = round((booked_hours / 1600.0) * 100.0, 2)

        # Enrollment Counts
        active_students = len(set(m.student_id for m in active_mems))

        # Expiring Soon (Within 3 days)
        expiring_threshold = today + timedelta(days=3)
        expiring_count = sum(1 for m in active_mems if today <= m.end_date <= expiring_threshold)

        # Expired in last 7 days without renewal
        past_week = today - timedelta(days=7)
        expired_conditions = [
            Membership.status == "ACTIVE",
            Membership.end_date < today,
            Membership.end_date >= past_week
        ]
        if owner_id:
            expired_conditions.append(Membership.created_by == owner_id)

        expired_stmt = select(func.count()).select_from(Membership).where(and_(*expired_conditions))
        expired_count = db.scalar(expired_stmt) or 0

        # Daily Realized Revenue (Payments completed today)
        today_start = datetime.combine(today, datetime.min.time())
        today_end = datetime.combine(today, datetime.max.time())
        daily_rev_conditions = [
            Payment.status == "COMPLETED",
            Payment.created_at >= today_start,
            Payment.created_at <= today_end
        ]
        if owner_id:
            daily_rev_conditions.append(
                or_(
                    Payment.received_by == owner_id,
                    Payment.membership.has(Membership.created_by == owner_id)
                )
            )

        daily_rev_stmt = select(func.coalesce(func.sum(Payment.amount), Decimal("0.00"))).where(
            and_(*daily_rev_conditions)
        )
        daily_revenue = Decimal(str(db.scalar(daily_rev_stmt) or Decimal("0.00")))

        # Total Outstanding Dues across today's active memberships
        total_dues = Decimal("0.00")
        for m in active_mems:
            _, due, _ = membership_repository.get_financial_summary(db, m.id, m.final_fee)
            total_dues += due

        return DashboardSummarySchema(
            target_date=today,
            total_physical_seats=100,
            occupied_physical_seats=occupied_seats_count,
            physical_utilization_rate=physical_rate,
            total_slot_capacity=300,
            booked_shift_slots=booked_slots,
            slot_occupancy_rate=slot_rate,
            total_seat_hours_capacity=1600,
            booked_seat_hours=round(booked_hours, 2),
            seat_hour_occupancy_rate=seat_hour_rate,
            active_students_count=active_students,
            expiring_soon_count=expiring_count,
            expired_unrenewed_count=expired_count,
            daily_revenue=daily_revenue,
            total_outstanding_dues=total_dues
        )

    @classmethod
    def get_expiring_queue(
        cls,
        db: Session,
        days_threshold: int = 3,
        reference_date: Optional[date] = None,
        owner_id: Optional[uuid.UUID] = None
    ) -> List[MembershipExpirySchema]:
        """
        Returns actionable list of memberships expiring within N days.
        """
        today = reference_date or date.today()
        threshold_date = today + timedelta(days=days_threshold)

        conditions = [
            Membership.status == "ACTIVE",
            Membership.end_date >= today,
            Membership.end_date <= threshold_date
        ]
        if owner_id:
            conditions.append(Membership.created_by == owner_id)

        stmt = (
            select(Membership)
            .options(
                joinedload(Membership.student),
                joinedload(Membership.seat),
                joinedload(Membership.shift)
            )
            .where(and_(*conditions))
            .order_by(Membership.end_date.asc())
        )
        mems = list(db.scalars(stmt).all())

        results = []
        for m in mems:
            days_left = (m.end_date - today).days
            _, due, _ = membership_repository.get_financial_summary(db, m.id, m.final_fee)
            results.append(MembershipExpirySchema(
                membership_id=m.id,
                student_id=m.student_id,
                student_name=m.student.full_name if m.student else "Unknown",
                student_mobile=m.student.mobile if m.student else "",
                seat_number=m.seat.seat_number if m.seat else m.seat_id,
                shift_name=m.shift.name if m.shift else "Unknown",
                start_date=m.start_date,
                end_date=m.end_date,
                days_remaining=days_left,
                due_amount=due
            ))

        return results

    @classmethod
    def get_revenue_report(
        cls,
        db: Session,
        start_date: date,
        end_date: date,
        owner_id: Optional[uuid.UUID] = None
    ) -> RevenueReportSchema:
        """
        Computes revenue aggregated by payment method for a date span.
        Uses datetime bounds for 100% compatibility across PostgreSQL and SQLite.
        """
        start_dt = datetime.combine(start_date, datetime.min.time())
        end_dt = datetime.combine(end_date, datetime.max.time())

        conditions = [
            Payment.status == "COMPLETED",
            Payment.created_at >= start_dt,
            Payment.created_at <= end_dt
        ]
        if owner_id:
            conditions.append(
                or_(
                    Payment.received_by == owner_id,
                    Payment.membership.has(Membership.created_by == owner_id)
                )
            )

        base_stmt = select(Payment).where(and_(*conditions))
        payments = list(db.scalars(base_stmt).all())

        total = Decimal("0.00")
        cash = Decimal("0.00")
        upi = Decimal("0.00")
        card = Decimal("0.00")
        net = Decimal("0.00")

        for p in payments:
            amt = Decimal(str(p.amount))
            total += amt
            if p.payment_method == "CASH":
                cash += amt
            elif p.payment_method == "UPI":
                upi += amt
            elif p.payment_method == "CARD":
                card += amt
            elif p.payment_method == "NET_BANKING":
                net += amt

        return RevenueReportSchema(
            start_date=start_date,
            end_date=end_date,
            total_revenue=total,
            transaction_count=len(payments),
            cash_total=cash,
            upi_total=upi,
            card_total=card,
            net_banking_total=net
        )


analytics_service = AnalyticsService()
