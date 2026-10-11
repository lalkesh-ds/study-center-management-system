from datetime import datetime
from typing import Optional
from uuid import UUID
from pydantic import BaseModel, EmailStr, Field, field_validator


class UserBase(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    full_name: str = Field(..., min_length=2, max_length=100)
    role: str = Field(default="CUSTOMER", pattern="^(ADMIN|STAFF|CUSTOMER)$")
    mobile: Optional[str] = Field(None, max_length=15)
    is_active: bool = True


class UserCreate(UserBase):
    password: str = Field(..., min_length=8)

    @field_validator("password")
    @classmethod
    def validate_password_length(cls, v: str) -> str:
        if len(v.encode("utf-8")) > 72:
            raise ValueError("Password cannot exceed 72 bytes due to cryptographic limits.")
        return v


class CustomerRegister(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    mobile: str = Field(..., min_length=10, max_length=15, pattern=r"^\+?[0-9]{10,15}$")
    full_name: str = Field(..., min_length=2, max_length=100)
    password: str = Field(..., min_length=8)

    @field_validator("password")
    @classmethod
    def validate_password_length(cls, v: str) -> str:
        if len(v.encode("utf-8")) > 72:
            raise ValueError("Password cannot exceed 72 bytes due to cryptographic limits.")
        return v


class CustomerProfileUpdate(BaseModel):
    full_name: Optional[str] = Field(None, min_length=2, max_length=100)
    email: Optional[EmailStr] = None
    mobile: Optional[str] = Field(None, min_length=10, max_length=15, pattern=r"^\+?[0-9]{10,15}$")
    address: Optional[str] = None
    emergency_contact: Optional[str] = None


class ChangePassword(BaseModel):
    current_password: str = Field(..., min_length=1)
    new_password: str = Field(..., min_length=8)

    @field_validator("new_password")
    @classmethod
    def validate_password_length(cls, v: str) -> str:
        if len(v.encode("utf-8")) > 72:
            raise ValueError("New password cannot exceed 72 bytes due to cryptographic limits.")
        return v


class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    full_name: Optional[str] = Field(None, min_length=2, max_length=100)
    role: Optional[str] = Field(None, pattern="^(ADMIN|STAFF|CUSTOMER)$")
    mobile: Optional[str] = None
    is_active: Optional[bool] = None
    password: Optional[str] = Field(None, min_length=8)

    @field_validator("password")
    @classmethod
    def validate_password_length(cls, v: Optional[str]) -> Optional[str]:
        if v and len(v.encode("utf-8")) > 72:
            raise ValueError("Password cannot exceed 72 bytes due to cryptographic limits.")
        return v


class UserResponse(UserBase):
    id: UUID
    student_id: Optional[UUID] = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class UserLogin(BaseModel):
    username: str = Field(..., min_length=1, description="Username or email or mobile")
    password: str = Field(..., min_length=1)


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    refresh_token: Optional[str] = None
    expires_in: int = 3600  # seconds
    user: UserResponse


class TokenRefreshRequest(BaseModel):
    refresh_token: str = Field(..., min_length=1)


class TokenPayload(BaseModel):
    sub: Optional[str] = None
    role: Optional[str] = None
    exp: Optional[int] = None
