from typing import Generator
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from backend.app.core.config import settings

# Configure SQLAlchemy 2.0 Engine with Connection Pooling
# pool_pre_ping=True tests connections prior to checkout, recovering from stale connections (vital for Cloud DBs)
engine = create_engine(
    settings.DATABASE_URL,
    pool_size=settings.DB_POOL_SIZE,
    max_overflow=settings.DB_MAX_OVERFLOW,
    pool_timeout=settings.DB_POOL_TIMEOUT,
    pool_recycle=settings.DB_POOL_RECYCLE,
    pool_pre_ping=True,
    echo=False  # Set to True only when debugging raw SQL queries
)

# Session factory bound to engine
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
    expire_on_commit=False
)


def get_db() -> Generator[Session, None, None]:
    """
    FastAPI Dependency that yields an isolated database session per request,
    guaranteeing rollback on unhandled exceptions and deterministic session closure.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
