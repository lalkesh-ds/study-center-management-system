import uuid
from datetime import datetime, timedelta, timezone
from typing import Optional, List
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from backend.app.core.config import settings
from backend.app.core.exceptions import ConflictException, ValidationException, NotFoundException
from backend.app.core.security import (
    verify_password,
    get_password_hash,
    create_access_token,
    decode_access_token,
    generate_refresh_token_string,
    hash_token,
)
from backend.app.db.session import get_db
from backend.app.models.user import User
from backend.app.models.student import Student
from backend.app.models.refresh_token import RefreshToken
from backend.app.repositories.user_repository import UserRepository
from backend.app.repositories.student_repository import student_repository
from backend.app.repositories.refresh_token_repository import RefreshTokenRepository
from backend.app.schemas.user import (
    UserCreate,
    UserLogin,
    Token,
    UserResponse,
    CustomerRegister,
    CustomerProfileUpdate,
    ChangePassword,
    TokenRefreshRequest,
)

oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl=f"{settings.API_V1_STR}/auth/login",
    auto_error=False
)


class AuthService:
    def __init__(self, db: Session):
        self.db = db
        self.user_repo = UserRepository(db)
        self.token_repo = RefreshTokenRepository(db)

    def authenticate_user(
        self,
        credentials: UserLogin,
        user_agent: Optional[str] = None,
        ip_address: Optional[str] = None
    ) -> Token:
        user = self.user_repo.get_by_identifier(credentials.username)
        if not user or not verify_password(credentials.password, user.password_hash):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect username or password",
                headers={"WWW-Authenticate": "Bearer"},
            )
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Inactive user account"
            )

        # 1. Generate access token
        access_token = create_access_token(
            subject=str(user.id),
            role=user.role
        )

        # 2. Generate and store refresh token
        raw_refresh_token = generate_refresh_token_string()
        token_hash = hash_token(raw_refresh_token)
        refresh_expires = datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)

        self.token_repo.create(
            user_id=user.id,
            token_hash=token_hash,
            expires_at=refresh_expires,
            user_agent=user_agent,
            ip_address=ip_address
        )

        return Token(
            access_token=access_token,
            token_type="bearer",
            refresh_token=raw_refresh_token,
            expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            user=UserResponse.model_validate(user)
        )

    def register_customer(self, reg_in: CustomerRegister) -> Token:
        """
        Public customer registration:
        1. Checks unique constraints (username, email, mobile).
        2. Links to existing Student if mobile/email matches and unlinked.
        3. Creates a new Student record if no matching student exists.
        4. Rejects with 409 Conflict if mobile is already linked to another user account.
        5. Strictly creates User with role='CUSTOMER'.
        6. Issues tokens.
        """
        # Validate uniqueness on User table
        if self.user_repo.get_by_username(reg_in.username):
            raise ConflictException(f"Username '{reg_in.username}' is already in use.", code="USERNAME_EXISTS")
        if self.user_repo.get_by_email(reg_in.email):
            raise ConflictException(f"Email '{reg_in.email}' is already registered.", code="EMAIL_EXISTS")
        if self.user_repo.get_by_mobile(reg_in.mobile):
            raise ConflictException(f"Mobile number '{reg_in.mobile}' is already registered.", code="MOBILE_EXISTS")

        # Create user account as ADMIN (Library Owner)
        new_user = User(
            id=uuid.uuid4(),
            username=reg_in.username,
            email=reg_in.email,
            mobile=reg_in.mobile,
            password_hash=get_password_hash(reg_in.password),
            full_name=reg_in.full_name.strip(),
            role="ADMIN",
            is_active=True,
            student_id=None
        )
        self.db.add(new_user)
        self.db.commit()
        self.db.refresh(new_user)

        # Issue access & refresh tokens
        access_token = create_access_token(
            subject=str(new_user.id),
            role=new_user.role
        )
        raw_refresh_token = generate_refresh_token_string()
        token_hash = hash_token(raw_refresh_token)
        refresh_expires = datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)

        self.token_repo.create(
            user_id=new_user.id,
            token_hash=token_hash,
            expires_at=refresh_expires
        )

        return Token(
            access_token=access_token,
            token_type="bearer",
            refresh_token=raw_refresh_token,
            expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            user=UserResponse.model_validate(new_user)
        )

    def refresh_access_token(
        self,
        token_in: TokenRefreshRequest,
        user_agent: Optional[str] = None,
        ip_address: Optional[str] = None
    ) -> Token:
        token_hash = hash_token(token_in.refresh_token)
        token_record = self.token_repo.get_by_token_hash(token_hash)

        if not token_record:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token",
                headers={"WWW-Authenticate": "Bearer"},
            )

        if token_record.is_revoked:
            # Token reuse detected! Revoke all tokens for this user for security
            self.token_repo.revoke_all_for_user(token_record.user_id)
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Revoked refresh token presented. All active sessions invalidated.",
                headers={"WWW-Authenticate": "Bearer"},
            )

        expires_at = token_record.expires_at
        if expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=timezone.utc)
        if expires_at < datetime.now(timezone.utc):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Refresh token expired",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # Rotate refresh token: revoke current token
        self.token_repo.revoke(token_record)

        # Retrieve user
        user = self.user_repo.get_by_id(token_record.user_id)
        if not user or not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User account inactive or not found",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # Generate new access token & new refresh token
        new_access_token = create_access_token(
            subject=str(user.id),
            role=user.role
        )
        new_raw_refresh_token = generate_refresh_token_string()
        new_token_hash = hash_token(new_raw_refresh_token)
        refresh_expires = datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)

        self.token_repo.create(
            user_id=user.id,
            token_hash=new_token_hash,
            expires_at=refresh_expires,
            user_agent=user_agent,
            ip_address=ip_address
        )

        return Token(
            access_token=new_access_token,
            token_type="bearer",
            refresh_token=new_raw_refresh_token,
            expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            user=UserResponse.model_validate(user)
        )

    def logout(self, token_in: TokenRefreshRequest) -> bool:
        token_hash = hash_token(token_in.refresh_token)
        token_record = self.token_repo.get_by_token_hash(token_hash)
        if token_record and not token_record.is_revoked:
            self.token_repo.revoke(token_record)
        return True

    def change_password(self, user: User, payload: ChangePassword) -> bool:
        if not verify_password(payload.current_password, user.password_hash):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Current password verification failed"
            )
        user.password_hash = get_password_hash(payload.new_password)
        self.db.commit()
        # Invalidate all existing refresh tokens
        self.token_repo.revoke_all_for_user(user.id)
        return True

    def register_staff_user(self, user_in: UserCreate) -> UserResponse:
        existing_username = self.user_repo.get_by_username(user_in.username)
        if existing_username:
            raise ConflictException(f"Username '{user_in.username}' already in use.", code="USERNAME_EXISTS")

        existing_email = self.user_repo.get_by_email(user_in.email)
        if existing_email:
            raise ConflictException(f"Email '{user_in.email}' already registered.", code="EMAIL_EXISTS")

        user = self.user_repo.create(user_in)
        return UserResponse.model_validate(user)


def get_current_user(
    token: Optional[str] = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
) -> User:
    """
    Dependency to authenticate and return the current user.
    If no token is supplied or invalid, raises 401.
    """
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    payload = decode_access_token(token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    user_id_str = payload.get("sub")
    if not user_id_str:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token payload missing subject identifier",
            headers={"WWW-Authenticate": "Bearer"},
        )
    try:
        user_uuid = uuid.UUID(user_id_str)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid user identifier format",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user = UserRepository(db).get_by_id(user_uuid)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user account"
        )
    return user


def require_admin(current_user: User = Depends(get_current_user)) -> User:
    """
    Enforces that current user holds role == ADMIN.
    """
    if current_user.role != "ADMIN":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Operation requires ADMIN privileges"
        )
    return current_user


def require_staff_or_admin(current_user: User = Depends(get_current_user)) -> User:
    """
    Enforces that current user holds role in ('ADMIN', 'STAFF').
    """
    if current_user.role not in ("ADMIN", "STAFF"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Operation requires STAFF or ADMIN privileges"
        )
    return current_user


def require_customer(current_user: User = Depends(get_current_user)) -> User:
    """
    Enforces that current user holds role == CUSTOMER.
    """
    if current_user.role != "CUSTOMER":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Operation requires CUSTOMER privileges"
        )
    return current_user
