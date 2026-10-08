from datetime import date
from decimal import Decimal
from typing import Optional
from uuid import UUID
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from backend.app.core.exceptions import NotFoundException
from backend.app.db.session import get_db
from backend.app.repositories.membership_repository import membership_repository
from backend.app.schemas.common import PaginatedResponse, PaginationMeta
from backend.app.schemas.membership import (
    MembershipCreateSchema,
    MembershipRenewSchema,
    MembershipCancelSchema,
    MembershipResponseSchema,
    MembershipDetailSchema,
)
from backend.app.services.membership_service import membership_service

router = APIRouter(prefix="/memberships", tags=["Memberships"])


def format_membership_response(m, db: Optional[Session] = None) -> MembershipResponseSchema:
    """Helper to enrich membership with related names, derived status, and financial balances."""
    total_paid = Decimal("0.00")
    due_amount = m.final_fee
    pay_status = "PENDING"
    if db:
        total_paid, due_amount, pay_status = membership_repository.get_financial_summary(db, m.id, m.final_fee)

    return MembershipResponseSchema(
        id=m.id,
        student_id=m.student_id,
        student_name=m.student.full_name if m.student else None,
        seat_id=m.seat_id,
        seat_number=m.seat.seat_number if m.seat else m.seat_id,
        shift_id=m.shift_id,
        shift_name=m.shift.name if m.shift else None,
        start_date=m.start_date,
        end_date=m.end_date,
        start_minute=m.start_minute,
        end_minute=m.end_minute,
        base_fee=m.base_fee,
        discount_amount=m.discount_amount,
        final_fee=m.final_fee,
        status=m.status,
        derived_status=m.get_derived_status(),
        renewed_from_id=m.renewed_from_id,
        total_paid=total_paid,
        due_amount=due_amount,
        payment_status=pay_status,
        created_at=m.created_at
    )


@router.post("", response_model=MembershipResponseSchema, status_code=status.HTTP_201_CREATED)
def create_membership_admission(
    payload: MembershipCreateSchema,
    db: Session = Depends(get_db)
):
    """
    Executes student admission and temporal seat reservation within an isolated ACID transaction.
    Enforces pessimistic row locking and rejects collisions with HTTP 409.
    """
    membership = membership_service.create_admission_atomic(db=db, payload=payload)
    return format_membership_response(membership, db=db)


@router.post("/{id}/renew", response_model=MembershipResponseSchema, status_code=status.HTTP_201_CREATED)
def renew_membership(
    id: UUID,
    payload: MembershipRenewSchema,
    db: Session = Depends(get_db)
):
    """
    Extends subscription into a new renewal cycle.
    Preserves prior membership history and establishes lineage link (renewed_from_id).
    Supports retaining seat or migrating to an available new desk/shift.
    """
    renewed = membership_service.renew_membership_atomic(db=db, old_membership_id=id, payload=payload)
    return format_membership_response(renewed, db=db)


@router.post("/{id}/cancel", response_model=MembershipResponseSchema)
def cancel_membership(
    id: UUID,
    payload: MembershipCancelSchema,
    db: Session = Depends(get_db)
):
    """
    Cancels an active membership immediately.
    Releases seat capacity for subsequent bookings while preserving financial history.
    """
    cancelled = membership_service.cancel_membership_atomic(db=db, membership_id=id, cancel_reason=payload.cancel_reason)
    return format_membership_response(cancelled, db=db)



@router.get("", response_model=PaginatedResponse[MembershipResponseSchema])
def list_memberships(
    student_id: Optional[UUID] = Query(None, description="Filter by student ID"),
    seat_id: Optional[int] = Query(None, description="Filter by physical seat ID"),
    shift_id: Optional[int] = Query(None, description="Filter by shift ID"),
    status: Optional[str] = Query(None, pattern="^(ACTIVE|CANCELLED)$", description="Filter by persisted status"),
    target_date: Optional[date] = Query(None, description="Filter active on specific date"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """
    Search and paginate memberships with relational filters.
    """
    items, total = membership_repository.search_and_paginate(
        db,
        student_id=student_id,
        seat_id=seat_id,
        shift_id=shift_id,
        status=status,
        target_date=target_date,
        skip=skip,
        limit=limit
    )

    formatted_items = [format_membership_response(m, db=db) for m in items]

    return PaginatedResponse(
        items=formatted_items,
        pagination=PaginationMeta(
            total=total,
            skip=skip,
            limit=limit,
            has_more=(skip + len(items)) < total
        )
    )


@router.get("/{id}", response_model=MembershipDetailSchema)
def get_membership_details(
    id: UUID,
    db: Session = Depends(get_db)
):
    """
    Retrieves full membership details including live financial ledger balances
    (total_paid, due_amount, payment_status).
    """
    m = membership_repository.get_with_relations(db, id)
    if not m:
        raise NotFoundException(f"Membership with ID '{id}' was not found.", code="MEMBERSHIP_NOT_FOUND")

    total_paid, due_amount, pay_status = membership_repository.get_financial_summary(db, m.id, m.final_fee)

    return MembershipDetailSchema(
        id=m.id,
        student_id=m.student_id,
        student_name=m.student.full_name if m.student else None,
        seat_id=m.seat_id,
        seat_number=m.seat.seat_number if m.seat else m.seat_id,
        shift_id=m.shift_id,
        shift_name=m.shift.name if m.shift else None,
        start_date=m.start_date,
        end_date=m.end_date,
        start_minute=m.start_minute,
        end_minute=m.end_minute,
        base_fee=m.base_fee,
        discount_amount=m.discount_amount,
        final_fee=m.final_fee,
        status=m.status,
        derived_status=m.get_derived_status(),
        renewed_from_id=m.renewed_from_id,
        created_at=m.created_at,
        total_paid=total_paid,
        due_amount=due_amount,
        payment_status=pay_status,
        cancelled_at=m.cancelled_at,
        cancel_reason=m.cancel_reason
    )
