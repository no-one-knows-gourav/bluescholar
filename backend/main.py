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

    # Rate Limiting Middleware (Strategy 13)
    @app.middleware("http")
    async def rate_limit_middleware(request, call_next):
        if not request.url.path.startswith("/api/"):
            return await call_next(request)
        try:
            import redis.asyncio as aioredis
            from fastapi.responses import JSONResponse
            # Fallback to local celery_broker if upstash is unavailable
            r_url = settings.upstash_redis_url or settings.celery_broker_url
            redis_client = aioredis.from_url(r_url)
            
            client_ip = request.client.host if request.client else "unknown"
            key = f"rate_limit:{client_ip}"
            
            req_count = await redis_client.incr(key)
            if req_count == 1:
                await redis_client.expire(key, 60)
                
            if req_count > 100:  # Hard stop representing daily tier limits
                return JSONResponse(status_code=429, content={"detail": "Tokens exhausted. Please wait."})
        except Exception:
            pass  # Fail open if redis is unreachable
            
        return await call_next(request)

    # Mount routers
    app.include_router(student.router, prefix="/api/v1/student", tags=["Student"])
    app.include_router(faculty.router, prefix="/api/v1/faculty", tags=["Faculty"])
    app.include_router(uploads.router, prefix="/api/v1", tags=["Uploads"])

    @app.get("/health", tags=["System"])
    async def health():
        return {"status": "ok", "version": "0.1.0"}

    return app


app = create_app()
