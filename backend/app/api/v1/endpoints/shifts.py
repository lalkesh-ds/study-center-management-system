from typing import List
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from backend.app.core.exceptions import NotFoundException
from backend.app.db.session import get_db
from backend.app.repositories.shift_repository import shift_repository
from backend.app.schemas.shift import ShiftResponseSchema

router = APIRouter(prefix="/shifts", tags=["Shifts"])


@router.get("", response_model=List[ShiftResponseSchema])
def list_shifts(
    active_only: bool = Query(True, description="Filter for active operating shifts only"),
    db: Session = Depends(get_db)
):
    """
    Returns configured operating shifts (Morning, Afternoon, Evening, Full Day).
    """
    return shift_repository.list_shifts(db, active_only=active_only)


@router.get("/{id}", response_model=ShiftResponseSchema)
def get_shift(
    id: int,
    db: Session = Depends(get_db)
):
    """
    Retrieves specific shift timing and base fee details.
    """
    shift = shift_repository.get_by_id(db, id)
    if not shift:
        raise NotFoundException(f"Shift with ID {id} does not exist.", code="SHIFT_NOT_FOUND")
    return shift
