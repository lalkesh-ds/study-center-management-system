import uuid
from datetime import date, datetime, timezone
from typing import List, Optional
from uuid import UUID
from decimal import Decimal
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select, and_, desc
from sqlalchemy.orm import Session, joinedload

from backend.app.db.session import get_db
from backend.app.models.user import User
from backend.app.models.student import Student
from backend.app.models.membership import Membership
from backend.app.models.payment import Payment
from backend.app.models.attendance import Attendance
from backend.app.services.auth_service import require_customer, get_current_user
from backend.app.schemas.customer import CustomerDashboardStats, CustomerProfileResponse
from backend.app.schemas.user import CustomerProfileUpdate
from backend.app.schemas.membership import MembershipResponseSchema
from backend.app.schemas.payment import PaymentResponseSchema
from backend.app.schemas.attendance import AttendanceResponseSchema
from backend.app.repositories.membership_repository import membership_repository
from backend.app.repositories.payment_repository import payment_repository

router = APIRouter(prefix="/customer", tags=["Customer Self-Service Portal"])


def get_current_customer_student(
    current_user: User = Depends(require_customer),
    db: Session = Depends(get_db)
) -> Student:
    """
    Enforces customer role and resolves the linked Student record.
    Prevents BOLA/IDOR by ensuring all queries strictly derive from current_user.
    """
    if not current_user.student_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No student record linked to this customer account."
        )
    student = db.get(Student, current_user.student_id)
    if not student:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Linked student profile not found."
        )
    return student


@router.get("/dashboard", response_model=CustomerDashboardStats)
def get_customer_dashboard(
    current_user: User = Depends(require_customer),
    student: Student = Depends(get_current_customer_student),
    db: Session = Depends(get_db)
):
    """
    Returns high-level personalized overview for the authenticated customer:
    - Active seat & shift allocation
    - Subscription days remaining
    - Financial balance / dues
    - Today's check-in status
    """
    today = date.today()

    # Find currently active membership
    stmt = (
        select(Membership)
        .options(joinedload(Membership.seat), joinedload(Membership.shift))
        .where(
            and_(
                Membership.student_id == student.id,
                Membership.status == "ACTIVE",
                Membership.start_date <= today,
                Membership.end_date >= today
            )
        )
        .order_by(Membership.end_date.desc())
    )
    active_mem = db.scalars(stmt).first()

    has_active = active_mem is not None
    active_mem_id = active_mem.id if active_mem else None
    seat_num = active_mem.seat.seat_number if (active_mem and active_mem.seat) else None
    shift_name = active_mem.shift.name if (active_mem and active_mem.shift) else None
    mem_status = active_mem.status if active_mem else None
    days_remaining = (active_mem.end_date - today).days if active_mem else None

    total_fee = active_mem.final_fee if active_mem else None
    total_paid = None
    due_amount = None

    if active_mem:
        total_paid_dec, due_dec, _ = membership_repository.get_financial_summary(
            db, active_mem.id, active_mem.final_fee
        )
        total_paid = total_paid_dec
        due_amount = due_dec

    # Today's attendance status
    att_stmt = select(Attendance).where(
        and_(
            Attendance.student_id == student.id,
            Attendance.attendance_date == today
        )
    )
    today_att = db.scalars(att_stmt).first()
    is_checked_in = (today_att is not None and today_att.check_out is None)
    current_check_in_time = today_att.check_in if today_att else None

    return CustomerDashboardStats(
        has_active_membership=has_active,
        active_membership_id=active_mem_id,
        seat_number=seat_num,
        shift_name=shift_name,
        membership_status=mem_status,
        days_remaining=days_remaining,
        total_fee=total_fee,
        total_paid=total_paid,
        due_amount=due_amount,
        is_checked_in=is_checked_in,
        current_check_in_time=current_check_in_time
    )


@router.get("/profile", response_model=CustomerProfileResponse)
def get_customer_profile(
    current_user: User = Depends(require_customer),
    student: Student = Depends(get_current_customer_student)
):
    """
    Returns personal profile details combining User credentials and Student metadata.
    """
    return CustomerProfileResponse(
        id=current_user.id,
        student_id=student.id,
        username=current_user.username,
        email=current_user.email,
        mobile=current_user.mobile or student.mobile,
        full_name=current_user.full_name,
        role=current_user.role,
        student_code=student.student_code,
        id_proof_type=student.id_proof_type,
        id_proof_number=student.id_proof_number,
        emergency_contact=student.emergency_contact,
        address=student.address,
        created_at=current_user.created_at
    )


@router.patch("/profile", response_model=CustomerProfileResponse)
def update_customer_profile(
    payload: CustomerProfileUpdate,
    current_user: User = Depends(require_customer),
    student: Student = Depends(get_current_customer_student),
    db: Session = Depends(get_db)
):
    """
    Allows a customer to safely update their contact details, address, and emergency contact.
    """
    if payload.full_name:
        current_user.full_name = payload.full_name.strip()
        student.full_name = payload.full_name.strip()
    if payload.email:
        # Check uniqueness if changed
        if payload.email != current_user.email:
            existing = db.execute(
                select(User).where(User.email == payload.email, User.id != current_user.id)
            ).scalar_one_or_none()
            if existing:
                raise HTTPException(status_code=409, detail="Email already registered by another user.")
            current_user.email = payload.email
            student.email = payload.email
    if payload.mobile:
        # Check uniqueness if changed
        if payload.mobile != current_user.mobile:
            existing = db.execute(
                select(User).where(User.mobile == payload.mobile, User.id != current_user.id)
            ).scalar_one_or_none()
            if existing:
                raise HTTPException(status_code=409, detail="Mobile already registered by another user.")
            current_user.mobile = payload.mobile
            student.mobile = payload.mobile
    if payload.address is not None:
        student.address = payload.address
    if payload.emergency_contact is not None:
        student.emergency_contact = payload.emergency_contact

    db.commit()
    db.refresh(current_user)
    db.refresh(student)

    return CustomerProfileResponse(
        id=current_user.id,
        student_id=student.id,
        username=current_user.username,
        email=current_user.email,
        mobile=current_user.mobile or student.mobile,
        full_name=current_user.full_name,
        role=current_user.role,
        student_code=student.student_code,
        id_proof_type=student.id_proof_type,
        id_proof_number=student.id_proof_number,
        emergency_contact=student.emergency_contact,
        address=student.address,
        created_at=current_user.created_at
    )


@router.get("/membership", response_model=List[MembershipResponseSchema])
def get_customer_memberships(
    current_user: User = Depends(require_customer),
    student: Student = Depends(get_current_customer_student),
    db: Session = Depends(get_db)
):
    """
    Lists active and historical memberships strictly belonging to the authenticated customer.
    """
    stmt = (
        select(Membership)
        .options(
            joinedload(Membership.student),
            joinedload(Membership.seat),
            joinedload(Membership.shift)
        )
        .where(Membership.student_id == student.id)
        .order_by(Membership.created_at.desc())
    )
    memberships = list(db.scalars(stmt).all())

    from backend.app.api.v1.endpoints.memberships import format_membership_response
    return [format_membership_response(m, db=db) for m in memberships]


@router.get("/payments", response_model=List[PaymentResponseSchema])
def get_customer_payments(
    current_user: User = Depends(require_customer),
    student: Student = Depends(get_current_customer_student),
    db: Session = Depends(get_db)
):
    """
    Lists payment transaction ledger records strictly belonging to the authenticated customer.
    """
    payments = payment_repository.list_by_student(db, student.id, skip=0, limit=100)
    return [PaymentResponseSchema.model_validate(p) for p in payments]


@router.get("/attendance", response_model=List[AttendanceResponseSchema])
def get_customer_attendance(
    current_user: User = Depends(require_customer),
    student: Student = Depends(get_current_customer_student),
    db: Session = Depends(get_db)
):
    """
    Lists attendance sessions strictly belonging to the authenticated customer.
    """
    stmt = (
        select(Attendance)
        .options(
            joinedload(Attendance.student),
            joinedload(Attendance.membership)
        )
        .where(Attendance.student_id == student.id)
        .order_by(Attendance.attendance_date.desc(), Attendance.check_in.desc())
        .limit(100)
    )
    records = list(db.scalars(stmt).all())

    results = []
    for att in records:
        duration_hours = None
        if att.check_out and att.check_in:
            duration_hours = round((att.check_out - att.check_in).total_seconds() / 3600.0, 2)

        res = AttendanceResponseSchema(
            id=att.id,
            student_id=att.student_id,
            student_name=att.student.full_name if att.student else None,
            membership_id=att.membership_id,
            seat_id=att.membership.seat_id if att.membership else None,
            attendance_date=att.attendance_date,
            check_in=att.check_in,
            check_out=att.check_out,
            status=att.status,
            source=att.source,
            duration_hours=duration_hours,
            notes=att.notes,
            created_at=att.created_at
        )
        results.append(res)
    return results
