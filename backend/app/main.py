from contextlib import asynccontextmanager
from fastapi import FastAPI, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from backend.app.core.config import settings
from backend.app.core.logging import logger
from backend.app.core.exceptions import (
    AppException,
    app_exception_handler,
    validation_exception_handler,
    global_exception_handler,
)
from backend.app.api.v1.router import api_v1_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application Lifespan Event Handler.
    Executes startup verification and graceful shutdown routines.
    """
    logger.info("=" * 70)
    logger.info("STARTING: %s", settings.PROJECT_NAME)
    logger.info("ENVIRONMENT: %s | DEBUG: %s", settings.ENVIRONMENT, settings.DEBUG)
    logger.info("API DOCS: /docs | REDOC: /redoc")
    logger.info("=" * 70)
    yield
    logger.info("SHUTTING DOWN: %s - Closing connection pools.", settings.PROJECT_NAME)


def create_application() -> FastAPI:
    """
    Application Factory:
    Builds, configures, and returns the production FastAPI ASGI application instance.
    """
    app = FastAPI(
        title=settings.PROJECT_NAME,
        description=(
            "Production REST API for Smart Library & Study Center Management System. "
            "Governs 100 physical study desks, multi-shift time allocations, "
            "conflict-free admissions, financial ledgers, and attendance tracking."
        ),
        version="1.0.0",
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
        lifespan=lifespan
    )

    cors_origins = settings.get_cors_origins()
    has_wildcard = "*" in cors_origins

    # 1. CORS Configuration with strict origin handling
    app.add_middleware(
        CORSMiddleware,
        allow_origins=cors_origins,
        allow_credentials=not has_wildcard,  # Spec disallows allow_credentials=True with wildcard
        allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
        allow_headers=["Authorization", "Content-Type", "Accept", "Origin", "X-Requested-With"],
        expose_headers=["Content-Disposition"],
    )

    # 2. HTTP Security Headers Middleware
    @app.middleware("http")
    async def add_security_headers(request, call_next):
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"
        if settings.ENVIRONMENT == "production":
            response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        return response

    # 2. Register Global Exception Handlers
    app.add_exception_handler(AppException, app_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(Exception, global_exception_handler)

    # 3. Mount API v1 Routers
    app.include_router(api_v1_router, prefix=settings.API_V1_STR)

    # 4. Root Welcome / Status Endpoint
    @app.get("/", tags=["Root"])
    def root():
        return {
            "name": settings.PROJECT_NAME,
            "version": "1.0.0",
            "status": "online",
            "documentation": "/docs",
            "health_check": f"{settings.API_V1_STR}/health"
        }

    return app


app = create_application()
