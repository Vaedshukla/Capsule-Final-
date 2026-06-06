"""
Project Capsule — FastAPI Application Entry Point
AI Workflow Memory & Context Continuity Infrastructure
"""
from contextlib import asynccontextmanager
import structlog
from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.config import settings
from app.core.logging import setup_logging
from app.core.middleware import RequestIDMiddleware
from app.api.v1.api import api_router

# Setup structured JSON logging first
setup_logging()
logger = structlog.get_logger()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Startup / shutdown lifecycle handler.
    """
    logger.info(
        "capsule_starting",
        project=settings.PROJECT_NAME,
        environment=settings.ENVIRONMENT,
        embedding_provider=settings.EMBEDDING_PROVIDER,
    )

    # Seed default local user and default sources on startup
    await _seed_defaults()

    yield

    logger.info("capsule_shutting_down")


async def _seed_defaults():
    """
    Ensure the default local user and known source platforms exist in DB.
    Idempotent — safe to run on every startup.
    """
    import uuid
    from sqlalchemy.future import select
    from app.db.session import async_session_maker
    from app.models.user import User
    from app.models.source import Source

    DEFAULT_USER_ID = uuid.UUID("00000000-0000-0000-0000-000000000001")
    DEFAULT_SOURCES = [
        {"name": "ChatGPT", "slug": "chatgpt", "base_url": "https://chatgpt.com"},
        {"name": "Claude", "slug": "claude", "base_url": "https://claude.ai"},
        {"name": "Gemini", "slug": "gemini", "base_url": "https://gemini.google.com"},
        {"name": "Cursor", "slug": "cursor", "base_url": "https://cursor.sh"},
        {"name": "Antigravity", "slug": "antigravity", "base_url": ""},
        {"name": "Unknown", "slug": "unknown", "base_url": ""},
    ]

    async with async_session_maker() as db:
        # Seed default user
        result = await db.execute(select(User).where(User.id == DEFAULT_USER_ID))
        if not result.scalars().first():
            db.add(User(id=DEFAULT_USER_ID, display_name="Local User"))
            logger.info("seeded_default_user")

        # Seed known sources
        for src_data in DEFAULT_SOURCES:
            result = await db.execute(select(Source).where(Source.slug == src_data["slug"]))
            if not result.scalars().first():
                db.add(Source(**src_data))

        await db.commit()
        logger.info("seeded_default_sources")


# ─── Application ──────────────────────────────────────────────────────────────

app = FastAPI(
    title=settings.PROJECT_NAME,
    description=(
        "AI Workflow Memory & Context Continuity Infrastructure. "
        "Captures, compresses, and semantically retrieves AI conversation memory."
    ),
    version="0.1.0",
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# ─── Middleware ────────────────────────────────────────────────────────────────

class LocalhostOnlyMiddleware(BaseHTTPMiddleware):
    """Rejects requests not from localhost when LOCALHOST_ONLY=True."""
    async def dispatch(self, request: Request, call_next):
        if settings.LOCALHOST_ONLY and settings.ENVIRONMENT != "development":
            client_host = request.client.host if request.client else ""
            if client_host not in ("127.0.0.1", "::1", "localhost"):
                return Response("Access restricted to localhost.", status_code=403)
        return await call_next(request)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(RequestIDMiddleware)
app.add_middleware(LocalhostOnlyMiddleware)

# ─── Routes ───────────────────────────────────────────────────────────────────

app.include_router(api_router, prefix=settings.API_V1_STR)


@app.get("/health", tags=["System"])
async def health():
    return {
        "status": "ok",
        "project": settings.PROJECT_NAME,
        "version": "0.1.0",
        "environment": settings.ENVIRONMENT,
        "embedding_provider": settings.EMBEDDING_PROVIDER,
    }
