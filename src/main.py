from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from loguru import logger

from src.api.auth import router as auth_router
from src.core.config import settings
from src.core.logging import configure_logging


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Handle startup and shutdown events."""
    configure_logging()
    logger.info("Starting FastAPI application")
    logger.info(f"Environment: {settings.ENVIRONMENT}")
    yield
    logger.info("Shutting down FastAPI application")


def create_app() -> FastAPI:
    """Application factory."""
    app = FastAPI(
        title="FastAPI Application",
        description="Production-ready FastAPI backend with JWT auth, MySQL, observability",
        version="0.1.0",
        docs_url="/docs" if settings.ENVIRONMENT == "development" else None,
        redoc_url="/redoc" if settings.ENVIRONMENT == "development" else None,
        lifespan=lifespan,
    )

    # CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Include authentication routes
    app.include_router(auth_router)

    # Health check endpoints
    @app.get("/health/live", tags=["Health"])
    async def liveness_check() -> JSONResponse:
        """Kubernetes liveness probe."""
        return JSONResponse(content={"status": "alive"}, status_code=200)

    @app.get("/health/ready", tags=["Health"])
    async def readiness_check() -> JSONResponse:
        """Kubernetes readiness probe."""
        return JSONResponse(content={"status": "ready"}, status_code=200)

    # Root endpoint
    @app.get("/", tags=["Info"])
    async def root() -> JSONResponse:
        return JSONResponse(
            content={
                "name": "FastAPI Application",
                "version": "0.1.0",
                "environment": settings.ENVIRONMENT,
                "docs": "/docs" if settings.ENVIRONMENT == "development" else "Disabled",
            }
        )

    # Request logging middleware
    @app.middleware("http")
    async def log_requests(request: Request, call_next):
        import time

        start = time.perf_counter()
        response = await call_next(request)
        duration = time.perf_counter() - start
        logger.bind(
            request_id=request.headers.get("X-Request-ID", "unknown"),
            method=request.method,
            path=request.url.path,
            status=response.status_code,
            duration_ms=duration * 1000,
        ).info("Request completed")
        return response

    return app


# Create global app instance
app = create_app()

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "src.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.ENVIRONMENT == "development",
    )