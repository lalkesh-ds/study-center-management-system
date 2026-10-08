from typing import List
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from backend.app.db.session import get_db
from backend.app.models.user import User
from backend.app.schemas.user import (
    UserCreate,
    UserLogin,
    UserResponse,
    Token
)
from backend.app.services.auth_service import AuthService, get_current_user, require_admin
from backend.app.repositories.user_repository import UserRepository

router = APIRouter(prefix="/auth", tags=["Authentication & Staff Accounts"])


@router.post("/login", response_model=Token)
def login(
    credentials: UserLogin,
    db: Session = Depends(get_db)
):
    """
    Authenticate user with username and password, returns JWT Bearer token.
    """
    service = AuthService(db)
    return service.authenticate_user(credentials)


@router.get("/me", response_model=UserResponse)
def get_current_user_profile(
    current_user: User = Depends(get_current_user)
):
    """
    Fetch the currently logged-in user profile.
    """
    return UserResponse.model_validate(current_user)


@router.post("/users", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def create_staff_user(
    user_in: UserCreate,
    db: Session = Depends(get_db),
    admin_user: User = Depends(require_admin)
):
    """
    Create a new staff or admin user account (Restricted to ADMIN).
    """
    service = AuthService(db)
    return service.register_user(user_in)


@router.get("/users", response_model=List[UserResponse])
def list_staff_users(
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db),
    admin_user: User = Depends(require_admin)
):
    """
    List staff and admin accounts (Restricted to ADMIN).
    """
    repo = UserRepository(db)
    users = repo.list(skip=skip, limit=limit)
    return [UserResponse.model_validate(u) for u in users]
