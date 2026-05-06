from contextlib import asynccontextmanager
from typing import AsyncGenerator
from pathlib import Path

from fastapi import FastAPI, Request, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from loguru import logger

from src.api.auth import router as auth_router
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

    # Static files (CSS, JS)
    static_dir = Path("src/static")
    static_dir.mkdir(parents=True, exist_ok=True)
    app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

    # Jinja2 templates
    templates_dir = Path("src/templates")
    templates_dir.mkdir(parents=True, exist_ok=True)
    templates = Jinja2Templates(directory=str(templates_dir))

    # Include authentication API routes
    app.include_router(auth_router)

    # --------------------------------------------------------------------------
    # Frontend HTML routes
    # --------------------------------------------------------------------------
    @app.get("/login", response_class=HTMLResponse)
    async def login_page(request: Request):
        return templates.TemplateResponse("login.html", {"request": request})

    @app.get("/register", response_class=HTMLResponse)
    async def register_page(request: Request):
        return templates.TemplateResponse("register.html", {"request": request})

    @app.get("/dashboard", response_class=HTMLResponse)
    async def dashboard_page(request: Request):
        return templates.TemplateResponse("dashboard.html", {"request": request})

    @app.get("/", response_class=HTMLResponse)
    async def root_page(request: Request):
        # Redirect to login or dashboard? Simple redirect to login for now.
        return RedirectResponse(url="/login", status_code=302)

    # --------------------------------------------------------------------------
    # Health check endpoints (unchanged)
    # --------------------------------------------------------------------------
    @app.get("/health/live", tags=["Health"])
    async def liveness_check() -> JSONResponse:
        return JSONResponse(content={"status": "alive"}, status_code=200)

    @app.get("/health/ready", tags=["Health"])
    async def readiness_check() -> JSONResponse:
        return JSONResponse(content={"status": "ready"}, status_code=200)

    # --------------------------------------------------------------------------
    # Request logging middleware (unchanged)
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