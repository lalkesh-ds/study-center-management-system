from typing import List
from uuid import UUID
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from backend.app.db.session import get_db
from backend.app.repositories.payment_repository import payment_repository
from backend.app.schemas.payment import (
    PaymentCreateSchema,
    PaymentVoidSchema,
    PaymentResponseSchema,
)
from backend.app.models.user import User
from backend.app.services.payment_service import payment_service
from backend.app.services.auth_service import require_staff_or_admin

router = APIRouter(
    tags=["Payments"],
    dependencies=[Depends(require_staff_or_admin)]
)


@router.post("/payments", response_model=PaymentResponseSchema, status_code=status.HTTP_201_CREATED)
def record_payment_installment(
    payload: PaymentCreateSchema,
    current_user: User = Depends(require_staff_or_admin),
    db: Session = Depends(get_db)
):
    """
    Records an installment payment towards a membership contract.
    Issues a verified receipt number and updates the live due balance.
    """
    return payment_service.record_payment(db=db, payload=payload, received_by_user_id=current_user.id)


from backend.app.core.exceptions import NotFoundException
from backend.app.models.membership import Membership

@router.post("/payments/{id}/void", response_model=PaymentResponseSchema)
def void_payment(
    id: UUID,
    payload: PaymentVoidSchema,
    current_user: User = Depends(require_staff_or_admin),
    db: Session = Depends(get_db)
):
    """
    Voids an erroneous payment record. Restores the due amount immediately.
    Permanent audit fields (voided_at, void_reason, voided_by) are preserved.
    """
    return payment_service.void_payment(
        db=db,
        payment_id=id,
        void_reason=payload.void_reason,
        voided_by_user_id=current_user.id
    )


@router.get("/memberships/{id}/payments", response_model=List[PaymentResponseSchema])
def list_membership_payments(
    id: UUID,
    current_user: User = Depends(require_staff_or_admin),
    db: Session = Depends(get_db)
):
    """
    Retrieves the complete immutable payment history for a specific membership.
    Enforces that the membership belongs to the authenticated library owner.
    """
    membership = db.get(Membership, id)
    if not membership or (membership.created_by and membership.created_by != current_user.id):
        raise NotFoundException(f"Membership with ID '{id}' was not found.", code="MEMBERSHIP_NOT_FOUND")

    return payment_repository.list_by_membership(db=db, membership_id=id)
