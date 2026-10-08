from datetime import date, datetime
from decimal import Decimal
from typing import List, Optional, Tuple
from uuid import UUID
from sqlalchemy import select, func, and_
from sqlalchemy.orm import Session, joinedload

from backend.app.models.membership import Membership
from backend.app.models.payment import Payment
from backend.app.repositories.base import BaseRepository


class MembershipRepository(BaseRepository[Membership]):
    """
    Data Access Layer for Memberships.
    """
    def __init__(self):
        super().__init__(Membership)

    def get_with_relations(self, db: Session, membership_id: UUID) -> Optional[Membership]:
        """Loads membership with student, seat, and shift joined."""
        stmt = (
            select(Membership)
            .options(
                joinedload(Membership.student),
                joinedload(Membership.seat),
                joinedload(Membership.shift)
            )
            .where(Membership.id == membership_id)
        )
        return db.scalars(stmt).first()

    def search_and_paginate(
        self,
        db: Session,
        student_id: Optional[UUID] = None,
        seat_id: Optional[int] = None,
        shift_id: Optional[int] = None,
        status: Optional[str] = None,
        target_date: Optional[date] = None,
        skip: int = 0,
        limit: int = 50
    ) -> Tuple[List[Membership], int]:
        """
        Lists memberships with optional filters and eager-loaded relations.
        """
        query = select(Membership).options(
            joinedload(Membership.student),
            joinedload(Membership.seat),
            joinedload(Membership.shift)
        )
        count_query = select(func.count()).select_from(Membership)

        filters = []
        if student_id:
            filters.append(Membership.student_id == student_id)
        if seat_id:
            filters.append(Membership.seat_id == seat_id)
        if shift_id:
            filters.append(Membership.shift_id == shift_id)
        if status:
            filters.append(Membership.status == status)
        if target_date:
            filters.append(and_(
                Membership.start_date <= target_date,
                Membership.end_date >= target_date
            ))

        if filters:
            query = query.where(and_(*filters))
            count_query = count_query.where(and_(*filters))

        total = db.scalar(count_query) or 0
        items = list(db.scalars(query.order_by(Membership.created_at.desc()).offset(skip).limit(limit)).all())
        return items, total

    def get_financial_summary(self, db: Session, membership_id: UUID, final_fee: Decimal) -> Tuple[Decimal, Decimal, str]:
        """
        Aggregates completed payments to calculate:
        (total_paid, due_amount, payment_status)
        """
        stmt = select(func.coalesce(func.sum(Payment.amount), Decimal("0.00"))).where(
            and_(
                Payment.membership_id == membership_id,
                Payment.status == "COMPLETED"
            )
        )
        total_paid = Decimal(str(db.scalar(stmt) or Decimal("0.00")))
        due_amount = max(Decimal("0.00"), final_fee - total_paid)

        if total_paid == Decimal("0.00"):
            pay_status = "PENDING"
        elif total_paid < final_fee:
            pay_status = "PARTIAL"
        else:
            pay_status = "PAID"

        return total_paid, due_amount, pay_status


membership_repository = MembershipRepository()
