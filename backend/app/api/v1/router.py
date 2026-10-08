from fastapi import APIRouter
from backend.app.api.v1.endpoints import (
    health,
    students,
    seats,
    shifts,
    memberships,
    payments,
    attendance,
    dashboard,
    auth,
)

api_v1_router = APIRouter()

# Mount API Routers
api_v1_router.include_router(health.router)
api_v1_router.include_router(auth.router)
api_v1_router.include_router(students.router)
api_v1_router.include_router(seats.router)
api_v1_router.include_router(shifts.router)
api_v1_router.include_router(memberships.router)
api_v1_router.include_router(payments.router)
api_v1_router.include_router(attendance.router)
api_v1_router.include_router(dashboard.router)
