from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.models.seat import Seat
from backend.app.repositories.base import BaseRepository


class SeatRepository(BaseRepository[Seat]):
    """
    Data Access Layer for 100 Physical Seats Inventory.
    """
    def __init__(self):
        super().__init__(Seat)

    def list_seats(self, db: Session, is_active: Optional[bool] = None) -> List[Seat]:
        stmt = select(Seat)
        if is_active is not None:
            stmt = stmt.where(Seat.is_active == is_active)
        stmt = stmt.order_by(Seat.seat_number.asc())
        return list(db.scalars(stmt).all())

    def get_by_seat_number(self, db: Session, seat_number: int) -> Optional[Seat]:
        stmt = select(Seat).where(Seat.seat_number == seat_number)
        return db.scalars(stmt).first()


seat_repository = SeatRepository()
