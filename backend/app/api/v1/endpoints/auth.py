import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, Request, status, Query, HTTPException
from sqlalchemy.orm import Session

from backend.app.db.session import get_db
from backend.app.models.user import User
from backend.app.schemas.user import (
    UserCreate,
    UserLogin,
    UserResponse,
    Token,
    CustomerRegister,
    ChangePassword,
    TokenRefreshRequest,
)
from backend.app.services.auth_service import (
    AuthService,
    get_current_user,
    require_admin,
    require_staff_or_admin,
)
from backend.app.repositories.user_repository import UserRepository
from backend.app.core.rate_limit import rate_limiter

router = APIRouter(prefix="/auth", tags=["Authentication & User Management"])


@router.post(
    "/register",
    response_model=Token,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(rate_limiter(max_requests=20, window_seconds=60))]
)
def register_customer(
    payload: CustomerRegister,
    db: Session = Depends(get_db)
):
    """
    Public customer self-registration.
    Strictly assigns CUSTOMER role and links/provisions a student record.
    """
    service = AuthService(db)
    return service.register_customer(payload)


@router.post(
    "/login",
    response_model=Token,
    dependencies=[Depends(rate_limiter(max_requests=30, window_seconds=60))]
)
def login(
    credentials: UserLogin,
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Authenticate user via username, email, or mobile with password.
    Returns access token, refresh token, and user metadata.
    """
    service = AuthService(db)
    user_agent = request.headers.get("user-agent")
    ip_address = request.client.host if request.client else None
    return service.authenticate_user(credentials, user_agent=user_agent, ip_address=ip_address)


@router.post(
    "/refresh",
    response_model=Token,
    dependencies=[Depends(rate_limiter(max_requests=60, window_seconds=60))]
)
def refresh_token(
    payload: TokenRefreshRequest,
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Rotate and reissue access & refresh tokens using an active refresh token.
    """
    service = AuthService(db)
    user_agent = request.headers.get("user-agent")
    ip_address = request.client.host if request.client else None
    return service.refresh_access_token(payload, user_agent=user_agent, ip_address=ip_address)


@router.post("/logout", status_code=status.HTTP_200_OK)
def logout(
    payload: Optional[TokenRefreshRequest] = None,
    db: Session = Depends(get_db)
):
    """
    Revoke refresh token and invalidate the persistent session.
    """
    if payload and payload.refresh_token:
        service = AuthService(db)
        service.logout(payload)
    return {"message": "Successfully logged out and session revoked."}


@router.post(
    "/change-password",
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(rate_limiter(max_requests=10, window_seconds=60))]
)
def change_password(
    payload: ChangePassword,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Change user password for the authenticated account and invalidate existing sessions.
    """
    service = AuthService(db)
    service.change_password(current_user, payload)
    return {"message": "Password updated successfully."}


@router.get("/me", response_model=UserResponse)
def get_current_user_profile(
    current_user: User = Depends(get_current_user)
):
    """
    Fetch the currently logged-in user profile (Admin, Staff, or Customer).
    """
    return UserResponse.model_validate(current_user)


# ---------------------------------------------------------------------------
# Administrative & Staff User Management (Admin Only)
# ---------------------------------------------------------------------------

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
    return service.register_staff_user(user_in)


@router.get("/users", response_model=List[UserResponse])
def list_users(
    role: Optional[str] = Query(None, pattern="^(ADMIN|STAFF|CUSTOMER)$"),
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db),
    admin_user: User = Depends(require_admin)
):
    """
    List user accounts with optional role filter (Restricted to ADMIN).
    """
    repo = UserRepository(db)
    users = repo.list(skip=skip, limit=limit, role=role)
    return [UserResponse.model_validate(u) for u in users]


@router.patch("/users/{user_id}/status", response_model=UserResponse)
def update_user_status(
    user_id: uuid.UUID,
    is_active: bool,
    db: Session = Depends(get_db),
    admin_user: User = Depends(require_admin)
):
    """
    Activate or deactivate a user account (Restricted to ADMIN).
    """
    repo = UserRepository(db)
    user = repo.get_by_id(user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    user.is_active = is_active
    db.commit()
    db.refresh(user)
    return UserResponse.model_validate(user)
