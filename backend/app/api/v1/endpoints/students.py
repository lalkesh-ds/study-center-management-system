from typing import Optional
from uuid import UUID
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from backend.app.core.exceptions import NotFoundException, ConflictException
from backend.app.db.session import get_db
from backend.app.models.student import Student
from backend.app.repositories.student_repository import student_repository
from backend.app.schemas.common import PaginatedResponse, PaginationMeta
from backend.app.schemas.student import (
    StudentCreateSchema,
    StudentUpdateSchema,
    StudentResponseSchema,
)

router = APIRouter(prefix="/students", tags=["Students"])


@router.post("", response_model=StudentResponseSchema, status_code=status.HTTP_201_CREATED)
def register_student(
    payload: StudentCreateSchema,
    db: Session = Depends(get_db)
):
    """
    Enrolls a new student into the study center registry.
    Enforces mobile uniqueness and assigns an official STU-YYYY-XXXX identifier.
    """
    # 1. Verify mobile uniqueness
    existing_student = student_repository.get_by_mobile(db, payload.mobile)
    if existing_student:
        raise ConflictException(
            f"A student with mobile number '{payload.mobile}' is already registered (Student: {existing_student.full_name}, Code: {existing_student.student_code}).",
            code="MOBILE_ALREADY_EXISTS"
        )

    # 2. Generate sequential student code
    student_code = student_repository.generate_next_code(db)

    # 3. Create student entity
    student = Student(
        student_code=student_code,
        full_name=payload.full_name.strip(),
        mobile=payload.mobile,
        email=payload.email,
        id_proof_type=payload.id_proof_type,
        id_proof_number=payload.id_proof_number,
        emergency_contact=payload.emergency_contact,
        address=payload.address,
        notes=payload.notes,
        status="ACTIVE"
    )

    db.add(student)
    db.commit()
    db.refresh(student)
    return student


@router.get("", response_model=PaginatedResponse[StudentResponseSchema])
def list_students(
    search: Optional[str] = Query(None, description="Search by name, mobile, code, or email"),
    status: Optional[str] = Query(None, pattern="^(ACTIVE|INACTIVE|BLOCKED)$", description="Filter by student status"),
    skip: int = Query(0, ge=0, description="Offset for pagination"),
    limit: int = Query(50, ge=1, le=100, description="Records limit per page"),
    db: Session = Depends(get_db)
):
    """
    Search and paginate through enrolled students directory.
    """
    items, total = student_repository.search_and_paginate(
        db, search=search, status=status, skip=skip, limit=limit
    )

    return PaginatedResponse(
        items=items,
        pagination=PaginationMeta(
            total=total,
            skip=skip,
            limit=limit,
            has_more=(skip + len(items)) < total
        )
    )


@router.get("/{id}", response_model=StudentResponseSchema)
def get_student_profile(
    id: UUID,
    db: Session = Depends(get_db)
):
    """
    Retrieves full details of a specific student by unique identifier.
    """
    student = student_repository.get_by_id(db, id)
    if not student:
        raise NotFoundException(f"Student with ID '{id}' was not found.", code="STUDENT_NOT_FOUND")
    return student


@router.patch("/{id}", response_model=StudentResponseSchema)
def update_student_profile(
    id: UUID,
    payload: StudentUpdateSchema,
    db: Session = Depends(get_db)
):
    """
    Updates profile attributes, status, or contact details of an existing student.
    """
    student = student_repository.get_by_id(db, id)
    if not student:
        raise NotFoundException(f"Student with ID '{id}' was not found.", code="STUDENT_NOT_FOUND")

    # If mobile is being changed, ensure new mobile is not taken
    if payload.mobile and payload.mobile != student.mobile:
        collision = student_repository.get_by_mobile(db, payload.mobile)
        if collision:
            raise ConflictException(
                f"Mobile number '{payload.mobile}' is already in use by student '{collision.full_name}'.",
                code="MOBILE_ALREADY_EXISTS"
            )

    update_data = payload.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(student, field, value)

    db.commit()
    db.refresh(student)
    return student
