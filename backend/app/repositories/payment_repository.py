from datetime import datetime
from typing import List, Optional
from uuid import UUID
from sqlalchemy import select, func
from sqlalchemy.orm import Session

from backend.app.models.payment import Payment
from backend.app.repositories.base import BaseRepository


class PaymentRepository(BaseRepository[Payment]):
    """
    Data Access Layer for Payments Ledger.
    """
    def __init__(self):
        super().__init__(Payment)

    def generate_receipt_number(self, db: Session) -> str:
        """Generates receipt sequence: RCP-YYYYMMDD-XXXX."""
        today_str = datetime.now().strftime("%Y%m%d")
        prefix = f"RCP-{today_str}-"
        stmt = select(func.count()).select_from(Payment).where(Payment.receipt_number.like(f"{prefix}%"))
        count = db.scalar(stmt) or 0
        return f"{prefix}{count + 1:04d}"

    def list_by_membership(self, db: Session, membership_id: UUID) -> List[Payment]:
        """Lists all payment ledger rows for a specific membership."""
        stmt = (
            select(Payment)
            .where(Payment.membership_id == membership_id)
            .order_by(Payment.created_at.asc())
        )
        return list(db.scalars(stmt).all())

    def list_by_student(self, db: Session, student_id: UUID, skip: int = 0, limit: int = 50) -> List[Payment]:
        """Lists all historical payments across memberships for a student."""
        stmt = (
            select(Payment)
            .where(Payment.student_id == student_id)
            .order_by(Payment.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        return list(db.scalars(stmt).all())


payment_repository = PaymentRepository()
