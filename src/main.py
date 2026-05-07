from contextlib import asynccontextmanager
from typing import AsyncGenerator
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, HTMLResponse, RedirectResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from loguru import logger

from src.api.auth import router as auth_router
from src.api.reports import router as reports_router
from src.api.system import router as system_router
from src.core.config import settings
from src.core.logging import configure_logging


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    configure_logging()
    logger.info("Starting FastAPI application")
    logger.info(f"Environment: {settings.ENVIRONMENT}")
    yield
    logger.info("Shutting down FastAPI application")


def create_app() -> FastAPI:
    app = FastAPI(
        title="Server Hub API",
        description="Full‑stack server monitoring hub – FastAPI backend + interactive dashboard (JWT auth, MySQL, Docker, real‑time system metrics)",
        version="0.2.0",
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

    # Include API routers
    app.include_router(auth_router)
    app.include_router(reports_router)
    app.include_router(system_router)

    # --------------------------------------------------------------------------
    # Static frontend assets (CSS, JS) – must be mounted before HTML routes
    # --------------------------------------------------------------------------
    frontend_dir = Path("frontend")
    frontend_dir.mkdir(exist_ok=True)

    # Mount the entire frontend directory under /static so that browser can fetch
    # /static/css/login.css and /static/js/login.js
    app.mount("/static", StaticFiles(directory=str(frontend_dir)), name="static")

    # --------------------------------------------------------------------------
    # HTML pages (using FileResponse)
    # --------------------------------------------------------------------------
    @app.get("/", response_class=HTMLResponse)
    async def root():
        return RedirectResponse(url="/login", status_code=302)

    @app.get("/login", response_class=HTMLResponse)
    async def login_page():
        return FileResponse(frontend_dir / "login.html")

    @app.get("/dashboard", response_class=HTMLResponse)
    async def dashboard_page():
        return FileResponse(frontend_dir / "dashboard.html")
    
    @app.get("/register", response_class=HTMLResponse)
    async def register_page():
        return FileResponse(frontend_dir / "register.html")

    # --------------------------------------------------------------------------
    # Health check endpoints
    # --------------------------------------------------------------------------
    @app.get("/health/live", tags=["Health"])
    async def liveness_check() -> JSONResponse:
        return JSONResponse(content={"status": "alive"}, status_code=200)

    @app.get("/health/ready", tags=["Health"])
    async def readiness_check() -> JSONResponse:
        return JSONResponse(content={"status": "ready"}, status_code=200)

    # --------------------------------------------------------------------------
    # Request logging middleware
    # --------------------------------------------------------------------------
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


app = create_app()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "src.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.ENVIRONMENT == "development",
    )