import os
from typing import Optional
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Application Settings loaded from Environment Variables and .env file.
    Validates all critical runtime configurations.
    """
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=True
    )

    # Application Environment
    ENVIRONMENT: str = "development"
    PROJECT_NAME: str = "Smart Library & Study Center Management System"
    API_V1_STR: str = "/api/v1"
    DEBUG: bool = True

    # Database Configuration
    DATABASE_URL: str = Field(
        default="postgresql+psycopg://postgres:postgres@localhost:5432/library_db",
        description="PostgreSQL Database Connection URI"
    )

    @field_validator("DATABASE_URL", mode="before")
    @classmethod
    def assemble_db_connection(cls, v: str) -> str:
        if isinstance(v, str):
            if v.startswith("postgres://"):
                v = v.replace("postgres://", "postgresql+psycopg://", 1)
            elif v.startswith("postgresql://") and not v.startswith("postgresql+"):
                v = v.replace("postgresql://", "postgresql+psycopg://", 1)
        return v

    DB_POOL_SIZE: int = 10
    DB_MAX_OVERFLOW: int = 20
    DB_POOL_TIMEOUT: int = 30
    DB_POOL_RECYCLE: int = 1800

    # Security & Authentication
    SECRET_KEY: str = Field(
        default="default_insecure_development_secret_key_32_characters_minimum",
        description="Cryptographic secret key for signing JWT tokens"
    )
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 480  # 8 Hours

    # Seed Admin Credentials
    INITIAL_ADMIN_USERNAME: str = "admin"
    INITIAL_ADMIN_EMAIL: str = "admin@smartlibrary.com"
    INITIAL_ADMIN_PASSWORD: str = "Admin@Library2026!"
    INITIAL_ADMIN_FULL_NAME: str = "System Administrator"

    # Business Invariant Toggles
    ALLOW_MULTI_SHIFT_PER_STUDENT: bool = True
    EXPIRING_SOON_THRESHOLD_DAYS: int = 3
    ATTENDANCE_GRACE_MINUTES: int = 30


# Global singleton instance
settings = Settings()
