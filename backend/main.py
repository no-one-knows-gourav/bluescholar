"""BlueScholar FastAPI application — entry point."""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from config import get_settings
from routers import student, faculty, uploads


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup / shutdown hooks."""
    # Future: initialize Qdrant collections, warm caches, etc.
    yield


def create_app() -> FastAPI:
    settings = get_settings()

    app = FastAPI(
        title="BlueScholar API",
        version="0.1.0",
        description="AI-powered academic preparation and evaluation platform",
        lifespan=lifespan,
    )

    # CORS — allow the frontend origin
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[settings.frontend_url, "http://localhost:3000"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Mount routers
    app.include_router(student.router, prefix="/api/v1/student", tags=["Student"])
    app.include_router(faculty.router, prefix="/api/v1/faculty", tags=["Faculty"])
    app.include_router(uploads.router, prefix="/api/v1", tags=["Uploads"])

    @app.get("/health", tags=["System"])
    async def health():
        return {"status": "ok", "version": "0.1.0"}

    return app


app = create_app()
