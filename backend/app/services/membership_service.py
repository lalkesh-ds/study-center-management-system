import uuid
from datetime import datetime, date, timezone
from decimal import Decimal
from typing import Optional
from uuid import UUID
from sqlalchemy import select, func
from sqlalchemy.orm import Session

from backend.app.core.exceptions import (
    NotFoundException, ConflictException, ValidationException
)
from backend.app.models.student import Student
from backend.app.models.seat import Seat
from backend.app.models.shift import Shift
from backend.app.models.membership import Membership
from backend.app.models.payment import Payment
from backend.app.schemas.membership import MembershipCreateSchema, MembershipRenewSchema
from backend.app.services.allocation_service import allocation_service


class MembershipService:
    """
    Domain service orchestrating atomic admissions, renewals, and cancellations.
    """

    @staticmethod
    def generate_receipt_number(db: Session) -> str:
        """Generates sequential receipt number: RCP-YYYYMMDD-XXXX."""
        today_str = datetime.now().strftime("%Y%m%d")
        prefix = f"RCP-{today_str}-"
        stmt = select(func.count()).select_from(Payment).where(Payment.receipt_number.like(f"{prefix}%"))
        count = db.scalar(stmt) or 0
        return f"{prefix}{count + 1:04d}"

    @classmethod
    def create_admission_atomic(
        cls,
        db: Session,
        payload: MembershipCreateSchema,
        creator_user_id: Optional[UUID] = None
    ) -> Membership:
        """
        Executes atomic student admission with pessimistic seat row-locking.
        Guarantees zero double-booking even under concurrent staff booking requests.
        """
        # Step 1: Verify Student exists and is not blocked
        student = db.get(Student, payload.student_id)
        if not student:
            raise NotFoundException(f"Student with ID '{payload.student_id}' does not exist.", code="STUDENT_NOT_FOUND")
        if student.status == "BLOCKED":
            raise ValidationException(f"Student '{student.full_name}' is currently BLOCKED from admissions.", code="STUDENT_BLOCKED")

        # Step 2: Pessimistic Row Lock on Seat
        # SELECT id FROM seats WHERE id = :seat_id FOR UPDATE;
        stmt_seat = select(Seat).where(Seat.id == payload.seat_id).with_for_update()
        seat = db.scalars(stmt_seat).first()
        if not seat:
            raise NotFoundException(f"Seat #{payload.seat_id} does not exist.", code="SEAT_NOT_FOUND")
        if not seat.is_active:
            raise ValidationException(f"Seat #{payload.seat_id} is currently disabled/under maintenance.", code="SEAT_INACTIVE")

        # Step 3: Fetch Shift Details
        shift = db.get(Shift, payload.shift_id)
        if not shift or not shift.is_active:
            raise NotFoundException(f"Shift with ID {payload.shift_id} is invalid or inactive.", code="SHIFT_NOT_FOUND")

        # Step 4: Seat Availability Check
        is_seat_free, seat_conflict = allocation_service.check_seat_availability(
            db=db,
            seat_id=payload.seat_id,
            start_date=payload.start_date,
            end_date=payload.end_date,
            start_minute=shift.start_minute,
            end_minute=shift.end_minute
        )
        if not is_seat_free:
            raise ConflictException(
                f"Seat #{payload.seat_id} is already occupied for the requested slot ({shift.name}) between {payload.start_date} and {payload.end_date}.",
                code="SEAT_ALREADY_BOOKED"
            )

        # Step 5: Student Simultaneous Collision Check
        is_student_free, student_conflict = allocation_service.check_student_time_conflict(
            db=db,
            student_id=payload.student_id,
            start_date=payload.start_date,
            end_date=payload.end_date,
            start_minute=shift.start_minute,
            end_minute=shift.end_minute
        )
        if not is_student_free:
            raise ConflictException(
                f"Student '{student.full_name}' already holds an active booking (Seat #{student_conflict.seat_id}) during these hours.",
                code="STUDENT_TIME_COLLISION"
            )

        # Step 6: Fee Calculation
        if payload.discount_amount > shift.base_fee:
            raise ValidationException("Discount amount cannot exceed the shift base fee.", code="INVALID_DISCOUNT")
        final_fee = shift.base_fee - payload.discount_amount

        # Step 7: Create Membership Entity
        membership = Membership(
            id=uuid.uuid4(),
            student_id=payload.student_id,
            seat_id=payload.seat_id,
            shift_id=payload.shift_id,
            start_date=payload.start_date,
            end_date=payload.end_date,
            start_minute=shift.start_minute,
            end_minute=shift.end_minute,
            base_fee=shift.base_fee,
            discount_amount=payload.discount_amount,
            final_fee=final_fee,
            status="ACTIVE",
            created_by=creator_user_id
        )
        db.add(membership)
        db.flush()

        # Step 8: Handle Initial Payment if provided
        if payload.initial_payment_amount and payload.initial_payment_amount > Decimal("0.00"):
            if payload.initial_payment_amount > final_fee:
                raise ValidationException("Initial payment amount cannot exceed total membership fee.", code="OVERPAYMENT")

            payment = Payment(
                id=uuid.uuid4(),
                receipt_number=cls.generate_receipt_number(db),
                membership_id=membership.id,
                student_id=payload.student_id,
                amount=payload.initial_payment_amount,
                payment_method=payload.initial_payment_method,
                transaction_ref=payload.initial_payment_ref,
                status="COMPLETED",
                received_by=creator_user_id
            )
            db.add(payment)

        db.commit()
        db.refresh(membership)
        return membership

    @classmethod
    def renew_membership_atomic(
        cls,
        db: Session,
        old_membership_id: UUID,
        payload: "MembershipRenewSchema",
        creator_user_id: Optional[UUID] = None
    ) -> Membership:
        """
        Extends subscription by instantiating a new membership linked to the prior row.
        Preserves complete historical audit trail and allows seat/shift migration.
        """
        old_membership = db.get(Membership, old_membership_id)
        if not old_membership:
            raise NotFoundException(f"Prior membership with ID '{old_membership_id}' does not exist.", code="MEMBERSHIP_NOT_FOUND")

        if old_membership.status == "CANCELLED":
            raise ValidationException("Cancelled memberships cannot be renewed. Create a new admission instead.", code="CANNOT_RENEW_CANCELLED")

        # Determine target seat and shift
        seat_id = payload.target_seat_id if payload.target_seat_id is not None else old_membership.seat_id
        shift_id = payload.target_shift_id if payload.target_shift_id is not None else old_membership.shift_id

        # Instantiate admission payload
        admission_payload = MembershipCreateSchema(
            student_id=old_membership.student_id,
            seat_id=seat_id,
            shift_id=shift_id,
            start_date=payload.start_date,
            end_date=payload.end_date,
            discount_amount=payload.discount_amount,
            initial_payment_amount=payload.initial_payment_amount,
            initial_payment_method=payload.initial_payment_method,
            initial_payment_ref=payload.initial_payment_ref
        )

        new_membership = cls.create_admission_atomic(
            db=db,
            payload=admission_payload,
            creator_user_id=creator_user_id
        )

        # Establish lineage link
        new_membership.renewed_from_id = old_membership.id
        db.commit()
        db.refresh(new_membership)
        return new_membership

    @classmethod
    def cancel_membership_atomic(
        cls,
        db: Session,
        membership_id: UUID,
        cancel_reason: str,
        canceller_user_id: Optional[UUID] = None
    ) -> Membership:
        """
        Cancels an active membership, instantly freeing seat inventory for subsequent bookings.
        Financial records remain intact on the payment ledger.
        """
        membership = db.get(Membership, membership_id)
        if not membership:
            raise NotFoundException(f"Membership with ID '{membership_id}' was not found.", code="MEMBERSHIP_NOT_FOUND")

        if membership.status == "CANCELLED":
            raise ValidationException("This membership has already been cancelled.", code="ALREADY_CANCELLED")

        membership.status = "CANCELLED"
        membership.cancelled_at = datetime.now(timezone.utc)
        membership.cancel_reason = cancel_reason
        membership.cancelled_by = canceller_user_id

        db.commit()
        db.refresh(membership)
        return membership



membership_service = MembershipService()
