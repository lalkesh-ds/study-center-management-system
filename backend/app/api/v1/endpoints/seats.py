from datetime import date
from typing import List, Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from backend.app.core.exceptions import NotFoundException
from backend.app.db.session import get_db
from backend.app.repositories.seat_repository import seat_repository
from backend.app.schemas.seat import SeatResponseSchema, SeatStatusUpdateSchema

router = APIRouter(prefix="/seats", tags=["Seats"])


@router.get("", response_model=List[SeatResponseSchema])
def list_seats(
    is_active: Optional[bool] = Query(None, description="Filter seats by active/maintenance state"),
    db: Session = Depends(get_db)
):
    """
    Returns inventory list of all 100 physical study seats.
    """
    return seat_repository.list_seats(db, is_active=is_active)


@router.get("/availability")
def get_seat_availability(
    start_date: Optional[date] = Query(None, description="Target start date (inclusive)"),
    end_date: Optional[date] = Query(None, description="Target end date (inclusive)"),
    shift_id: Optional[int] = Query(None, description="Operating shift identifier (1 to 4)"),
    target_date: Optional[date] = Query(None, description="Single target date evaluation (defaults to today)"),
    db: Session = Depends(get_db)
):
    """
    Returns real-time 100-seat occupancy matrix:
    - If shift_id is provided: returns single-shift matrix for [start_date, end_date].
    - If shift_id is not provided: returns comprehensive multi-shift perspective for target_date.
    """
    from backend.app.core.exceptions import ValidationException, NotFoundException
    from backend.app.models.shift import Shift
    from backend.app.services.allocation_service import allocation_service

    if shift_id is not None:
        s_date = start_date or target_date or date.today()
        e_date = end_date or target_date or s_date
        if s_date > e_date:
            raise ValidationException("Start date cannot be after end date.", code="INVALID_DATE_RANGE")

        shift = db.get(Shift, shift_id)
        if not shift:
            raise NotFoundException(f"Shift with ID {shift_id} not found.", code="SHIFT_NOT_FOUND")

        return allocation_service.get_seat_availability_matrix(
            db=db,
            start_date=s_date,
            end_date=e_date,
            shift_id=shift_id
        )

    # Multi-shift comprehensive floor map perspective
    eval_date = target_date or start_date or date.today()
    return allocation_service.get_daily_seat_matrix(
        db=db,
        target_date=eval_date
    )


@router.put("/{id}/toggle-maintenance", response_model=SeatResponseSchema)
def toggle_seat_maintenance(
    id: int,
    db: Session = Depends(get_db)
):
    """
    Toggles physical seat maintenance state between active and under maintenance.
    """
    seat = seat_repository.get_by_id(db, id)
    if not seat:
        raise NotFoundException(f"Seat #{id} does not exist in inventory.", code="SEAT_NOT_FOUND")

    seat.is_active = not seat.is_active
    db.commit()
    db.refresh(seat)
    return seat


@router.get("/{id}", response_model=SeatResponseSchema)
def get_seat(
    id: int,
    db: Session = Depends(get_db)
):
    """
    Retrieves specific seat status, amenities, and details.
    """
    seat = seat_repository.get_by_id(db, id)
    if not seat:
        raise NotFoundException(f"Seat #{id} does not exist in inventory.", code="SEAT_NOT_FOUND")
    return seat


@router.patch("/{id}/status", response_model=SeatResponseSchema)
def update_seat_status(
    id: int,
    payload: SeatStatusUpdateSchema,
    db: Session = Depends(get_db)
):
    """
    Marks a physical desk as active or places it under maintenance.
    Disabled desks cannot receive new membership allocations.
    """
    seat = seat_repository.get_by_id(db, id)
    if not seat:
        raise NotFoundException(f"Seat #{id} does not exist in inventory.", code="SEAT_NOT_FOUND")

    seat.is_active = payload.is_active
    if payload.reason:
        current_desc = seat.description or f"Seat #{seat.seat_number}"
        seat.description = f"{current_desc} (Status Note: {payload.reason})"

    db.commit()
    db.refresh(seat)
    return seat
