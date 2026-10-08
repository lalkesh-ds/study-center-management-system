from typing import Any, Generic, List, Optional, Type, TypeVar
from sqlalchemy import select, func
from sqlalchemy.orm import Session
from backend.app.db.base import Base

ModelType = TypeVar("ModelType", bound=Base)


class BaseRepository(Generic[ModelType]):
    """
    Generic Repository encapsulating standard CRUD operations
    using SQLAlchemy 2.0 select syntax.
    """
    def __init__(self, model: Type[ModelType]):
        self.model = model

    def get_by_id(self, db: Session, id_val: Any) -> Optional[ModelType]:
        stmt = select(self.model).where(self.model.id == id_val)
        return db.scalars(stmt).first()

    def list(self, db: Session, skip: int = 0, limit: int = 100) -> List[ModelType]:
        stmt = select(self.model).offset(skip).limit(limit)
        return list(db.scalars(stmt).all())

    def count(self, db: Session) -> int:
        stmt = select(func.count()).select_from(self.model)
        return db.scalar(stmt) or 0

    def create(self, db: Session, obj: ModelType) -> ModelType:
        db.add(obj)
        db.flush()
        return obj

    def delete(self, db: Session, obj: ModelType) -> None:
        db.delete(obj)
        db.flush()
