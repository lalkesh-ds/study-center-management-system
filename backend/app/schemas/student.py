import re
from datetime import datetime
from typing import Optional
from uuid import UUID
from pydantic import BaseModel, Field, EmailStr, field_validator, AliasChoices, computed_field


class StudentBaseSchema(BaseModel):
    full_name: str = Field(..., min_length=2, max_length=100, description="Full name of student")
    mobile: str = Field(..., validation_alias=AliasChoices("mobile", "mobile_number"), description="Unique mobile number (10 to 15 digits)")
    email: Optional[EmailStr] = Field(None, description="Optional email address")
    id_proof_type: Optional[str] = Field(None, max_length=50, description="E.g. AADHAAR, PAN, PASSPORT")
    id_proof_number: Optional[str] = Field(None, max_length=100, description="Government ID reference")
    emergency_contact: Optional[str] = Field(None, description="Emergency guardian mobile number")
    address: Optional[str] = Field(None, description="Current residential address")
    notes: Optional[str] = Field(None, description="Special notes or administrative flags")

    @field_validator("mobile", mode="before")
    @classmethod
    def normalize_mobile(cls, v: str) -> str:
        if not isinstance(v, str):
            v = str(v)
        # Strip spaces, hyphens, plus signs
        cleaned = re.sub(r"[\s\-\+]", "", v)
        if not re.match(r"^\d{10,15}$", cleaned):
            raise ValueError("Mobile number must contain between 10 and 15 digits.")
        return cleaned

    @field_validator("emergency_contact", mode="before")
    @classmethod
    def normalize_emergency_contact(cls, v: Optional[str]) -> Optional[str]:
        if not v:
            return None
        cleaned = re.sub(r"[\s\-\+]", "", str(v))
        if not re.match(r"^\d{10,15}$", cleaned):
            raise ValueError("Emergency contact must contain between 10 and 15 digits.")
        return cleaned


class StudentCreateSchema(StudentBaseSchema):
    """Payload to register a new student."""
    pass


class StudentUpdateSchema(BaseModel):
    """Payload to update an existing student profile."""
    full_name: Optional[str] = Field(None, min_length=2, max_length=100)
    mobile: Optional[str] = None
    email: Optional[EmailStr] = None
    id_proof_type: Optional[str] = None
    id_proof_number: Optional[str] = None
    emergency_contact: Optional[str] = None
    address: Optional[str] = None
    status: Optional[str] = Field(None, pattern="^(ACTIVE|INACTIVE|BLOCKED)$")
    notes: Optional[str] = None

    @field_validator("mobile", mode="before")
    @classmethod
    def normalize_mobile(cls, v: Optional[str]) -> Optional[str]:
        if not v:
            return None
        cleaned = re.sub(r"[\s\-\+]", "", str(v))
        if not re.match(r"^\d{10,15}$", cleaned):
            raise ValueError("Mobile number must contain between 10 and 15 digits.")
        return cleaned


class StudentResponseSchema(StudentBaseSchema):
    """Full student entity response."""
    id: UUID
    student_code: str
    status: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}

    @computed_field
    def mobile_number(self) -> str:
        return self.mobile
