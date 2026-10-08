from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.models.shift import Shift
from backend.app.repositories.base import BaseRepository


class ShiftRepository(BaseRepository[Shift]):
    """
    Data Access Layer for Operating Shifts.
    """
    def __init__(self):
        super().__init__(Shift)

    def list_shifts(self, db: Session, active_only: bool = True) -> List[Shift]:
        stmt = select(Shift)
        if active_only:
            stmt = stmt.where(Shift.is_active == True)
        stmt = stmt.order_by(Shift.start_minute.asc())
        return list(db.scalars(stmt).all())

    def get_by_name(self, db: Session, name: str) -> Optional[Shift]:
        stmt = select(Shift).where(Shift.name == name)
        return db.scalars(stmt).first()


shift_repository = ShiftRepository()
