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
    start_date: date = Query(..., description="Target start date (inclusive)"),
    end_date: date = Query(..., description="Target end date (inclusive)"),
    shift_id: int = Query(..., description="Operating shift identifier (1 to 4)"),
    db: Session = Depends(get_db)
):
    """
    Returns real-time 100-seat occupancy matrix for a requested shift and date range.
    """
    from backend.app.core.exceptions import ValidationException, NotFoundException
    from backend.app.models.shift import Shift
    from backend.app.services.allocation_service import allocation_service

    if start_date > end_date:
        raise ValidationException("Start date cannot be after end date.", code="INVALID_DATE_RANGE")

    shift = db.get(Shift, shift_id)
    if not shift:
        raise NotFoundException(f"Shift with ID {shift_id} not found.", code="SHIFT_NOT_FOUND")

    return allocation_service.get_seat_availability_matrix(
        db=db,
        start_date=start_date,
        end_date=end_date,
        shift_id=shift_id
    )


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
