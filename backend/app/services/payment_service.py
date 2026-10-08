import uuid
from datetime import datetime, timezone, timedelta
from decimal import Decimal
from typing import Optional
from uuid import UUID
from sqlalchemy.orm import Session

from backend.app.core.exceptions import (
    NotFoundException, ValidationException
)
from backend.app.models.membership import Membership
from backend.app.models.payment import Payment
from backend.app.repositories.membership_repository import membership_repository
from backend.app.repositories.payment_repository import payment_repository
from backend.app.schemas.payment import PaymentCreateSchema


class PaymentService:
    """
    Domain service governing ledger entries, receipts, balance reconciliation,
    and payment voiding.
    """

    @classmethod
    def record_payment(
        cls,
        db: Session,
        payload: PaymentCreateSchema,
        received_by_user_id: Optional[UUID] = None
    ) -> Payment:
        """
        Records a fee payment installment against an active membership.
        Enforces that payments cannot exceed outstanding dues.
        """
        # Step 1: Verify Membership
        membership = db.get(Membership, payload.membership_id)
        if not membership:
            raise NotFoundException(f"Membership with ID '{payload.membership_id}' was not found.", code="MEMBERSHIP_NOT_FOUND")

        if membership.status == "CANCELLED":
            raise ValidationException("Cannot process payments on a cancelled membership.", code="CANNOT_PAY_CANCELLED")

        # Step 2: Calculate Outstanding Due
        _, due_amount, _ = membership_repository.get_financial_summary(
            db, membership.id, membership.final_fee
        )

        if payload.amount > due_amount:
            raise ValidationException(
                f"Payment amount of Rs.{payload.amount} exceeds outstanding balance of Rs.{due_amount}.",
                code="PAYMENT_EXCEEDS_DUE"
            )

        # Step 3: Record Immutable Ledger Row
        receipt_number = payment_repository.generate_receipt_number(db)
        payment = Payment(
            id=uuid.uuid4(),
            receipt_number=receipt_number,
            membership_id=membership.id,
            student_id=membership.student_id,
            amount=payload.amount,
            payment_method=payload.payment_method,
            transaction_ref=payload.transaction_ref,
            status="COMPLETED",
            notes=payload.notes,
            received_by=received_by_user_id
        )

        db.add(payment)
        db.commit()
        db.refresh(payment)
        return payment

    @classmethod
    def void_payment(
        cls,
        db: Session,
        payment_id: UUID,
        void_reason: str,
        voided_by_user_id: Optional[UUID] = None
    ) -> Payment:
        """
        Voids an erroneous payment entry.
        Restores outstanding debt on the student profile without deleting historical records.
        """
        payment = db.get(Payment, payment_id)
        if not payment:
            raise NotFoundException(f"Payment with ID '{payment_id}' was not found.", code="PAYMENT_NOT_FOUND")

        if payment.status == "VOIDED":
            raise ValidationException("This payment has already been marked VOIDED.", code="ALREADY_VOIDED")

        # Invariant: Must have non-empty void reason
        if not void_reason or len(void_reason.strip()) < 5:
            raise ValidationException("A detailed void reason (minimum 5 characters) is required.", code="INVALID_VOID_REASON")

        # Apply voiding
        payment.status = "VOIDED"
        payment.voided_at = datetime.now(timezone.utc)
        payment.void_reason = void_reason.strip()
        payment.voided_by = voided_by_user_id

        db.commit()
        db.refresh(payment)
        return payment


payment_service = PaymentService()
