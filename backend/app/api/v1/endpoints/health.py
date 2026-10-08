import time
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, status
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.orm import Session

from backend.app.core.config import settings
from backend.app.db.session import get_db

router = APIRouter(prefix="/health", tags=["System Health"])


@router.get("", status_code=status.HTTP_200_OK)
def liveness_check():
    """
    Service Liveness Probe:
    Confirms that the FastAPI application instance is operational and accepting requests.
    """
    return {
        "status": "healthy",
        "service": settings.PROJECT_NAME,
        "environment": settings.ENVIRONMENT,
        "version": "1.0.0",
        "timestamp": datetime.now(timezone.utc).isoformat()
    }


@router.get("/db")
def readiness_check(db: Session = Depends(get_db)):
    """
    Database Readiness Probe:
    Executes a round-trip query against PostgreSQL to verify connection pool health
    and latency.
    """
    start_time = time.perf_counter()
    try:
        db.execute(text("SELECT 1;"))
        latency_ms = round((time.perf_counter() - start_time) * 1000, 2)
        return {
            "status": "ready",
            "database": "connected",
            "latency_ms": latency_ms,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    except Exception as e:
        latency_ms = round((time.perf_counter() - start_time) * 1000, 2)
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={
                "status": "unhealthy",
                "database": "disconnected",
                "latency_ms": latency_ms,
                "error": str(e),
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        )
