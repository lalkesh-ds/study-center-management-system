import uuid
from typing import Optional, List
from sqlalchemy import select, or_
from sqlalchemy.orm import Session

from backend.app.models.user import User
from backend.app.schemas.user import UserCreate, UserUpdate
from backend.app.core.security import get_password_hash


class UserRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, user_id: uuid.UUID) -> Optional[User]:
        return self.db.execute(select(User).where(User.id == user_id)).scalar_one_or_none()

    def get_by_username(self, username: str) -> Optional[User]:
        return self.db.execute(select(User).where(User.username == username)).scalar_one_or_none()

    def get_by_email(self, email: str) -> Optional[User]:
        return self.db.execute(select(User).where(User.email == email)).scalar_one_or_none()

    def get_by_mobile(self, mobile: str) -> Optional[User]:
        return self.db.execute(select(User).where(User.mobile == mobile)).scalar_one_or_none()

    def get_by_student_id(self, student_id: uuid.UUID) -> Optional[User]:
        return self.db.execute(select(User).where(User.student_id == student_id)).scalar_one_or_none()

    def get_by_identifier(self, identifier: str) -> Optional[User]:
        """
        Allows flexible login by username, email, or mobile.
        """
        stmt = select(User).where(
            or_(
                User.username == identifier,
                User.email == identifier,
                User.mobile == identifier
            )
        )
        return self.db.execute(stmt).scalars().first()

    def list(self, skip: int = 0, limit: int = 50, role: Optional[str] = None) -> List[User]:
        stmt = select(User)
        if role:
            stmt = stmt.where(User.role == role)
        stmt = stmt.order_by(User.created_at.desc()).offset(skip).limit(limit)
        return list(self.db.execute(stmt).scalars().all())

    def create(self, user_in: UserCreate, student_id: Optional[uuid.UUID] = None) -> User:
        user = User(
            id=uuid.uuid4(),
            username=user_in.username,
            email=user_in.email,
            mobile=getattr(user_in, "mobile", None),
            password_hash=get_password_hash(user_in.password),
            full_name=user_in.full_name,
            role=user_in.role,
            is_active=user_in.is_active,
            student_id=student_id,
        )
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        return user

    def update(self, user: User, user_in: UserUpdate) -> User:
        update_data = user_in.model_dump(exclude_unset=True)
        if "password" in update_data and update_data["password"]:
            user.password_hash = get_password_hash(update_data.pop("password"))
        for field, value in update_data.items():
            setattr(user, field, value)
        self.db.commit()
        self.db.refresh(user)
        return user
