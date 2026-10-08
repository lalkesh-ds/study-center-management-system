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
from backend.app.services.payment_service import payment_service

router = APIRouter(tags=["Payments"])


@router.post("/payments", response_model=PaymentResponseSchema, status_code=status.HTTP_201_CREATED)
def record_payment_installment(
    payload: PaymentCreateSchema,
    db: Session = Depends(get_db)
):
    """
    Records an installment payment towards a membership contract.
    Issues a verified receipt number and updates the live due balance.
    """
    return payment_service.record_payment(db=db, payload=payload)


@router.post("/payments/{id}/void", response_model=PaymentResponseSchema)
def void_payment(
    id: UUID,
    payload: PaymentVoidSchema,
    db: Session = Depends(get_db)
):
    """
    Voids an erroneous payment record. Restores the due amount immediately.
    Permanent audit fields (voided_at, void_reason) are preserved.
    """
    return payment_service.void_payment(db=db, payment_id=id, void_reason=payload.void_reason)


@router.get("/memberships/{id}/payments", response_model=List[PaymentResponseSchema])
def list_membership_payments(
    id: UUID,
    db: Session = Depends(get_db)
):
    """
    Retrieves the complete immutable payment history for a specific membership.
    """
    return payment_repository.list_by_membership(db=db, membership_id=id)
