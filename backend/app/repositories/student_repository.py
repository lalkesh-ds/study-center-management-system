import uuid
from datetime import datetime
from typing import List, Optional, Tuple
from sqlalchemy import select, or_, func
from sqlalchemy.orm import Session

from backend.app.models.student import Student
from backend.app.repositories.base import BaseRepository


class StudentRepository(BaseRepository[Student]):
    """
    Data Access Layer for Student directory operations.
    """
    def __init__(self):
        super().__init__(Student)

    def get_by_mobile(self, db: Session, mobile: str) -> Optional[Student]:
        stmt = select(Student).where(Student.mobile == mobile)
        return db.scalars(stmt).first()

    def get_by_code(self, db: Session, student_code: str) -> Optional[Student]:
        stmt = select(Student).where(Student.student_code == student_code)
        return db.scalars(stmt).first()

    def generate_next_code(self, db: Session) -> str:
        """
        Generates deterministic student code format: STU-YYYY-XXXX (e.g. STU-2026-0001)
        """
        year = datetime.now().year
        prefix = f"STU-{year}-"
        
        # Count existing students with this year's prefix
        stmt = select(func.count()).select_from(Student).where(Student.student_code.like(f"{prefix}%"))
        count = db.scalar(stmt) or 0
        next_seq = count + 1
        return f"{prefix}{next_seq:04d}"

    def search_and_paginate(
        self,
        db: Session,
        search: Optional[str] = None,
        status: Optional[str] = None,
        skip: int = 0,
        limit: int = 50
    ) -> Tuple[List[Student], int]:
        """
        Searches students by name, mobile, or student_code with pagination.
        Returns (list_of_students, total_count).
        """
        query = select(Student)
        count_query = select(func.count()).select_from(Student)

        # Filters
        if status:
            query = query.where(Student.status == status)
            count_query = count_query.where(Student.status == status)

        if search:
            search_pattern = f"%{search.strip()}%"
            filter_cond = or_(
                Student.full_name.ilike(search_pattern),
                Student.mobile.ilike(search_pattern),
                Student.student_code.ilike(search_pattern),
                Student.email.ilike(search_pattern)
            )
            query = query.where(filter_cond)
            count_query = count_query.where(filter_cond)

        total = db.scalar(count_query) or 0
        items = list(db.scalars(query.order_by(Student.created_at.desc()).offset(skip).limit(limit)).all())
        return items, total


student_repository = StudentRepository()
