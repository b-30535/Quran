from contextlib import asynccontextmanager
import logging

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.auth import router as auth_router
from app.api.health import router as health_router
from app.api.prayers import router as prayers_router
from app.core.config import settings
from app.core.database import close_mongo_connection, connect_to_mongo

logging.basicConfig(level=logging.INFO if settings.app_env == "production" else logging.DEBUG)


@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        await connect_to_mongo()
        yield
    finally:
        await close_mongo_connection()


app = FastAPI(
    title=settings.app_name,
    description=(
        "Private development API for Noor Al-Quran Ultimate. "
        "Quran text must be sourced from trusted providers; AI output must never be presented as Quran text."
    ),
    version="0.2.0",
    docs_url="/docs" if settings.app_env != "production" else None,
    redoc_url="/redoc" if settings.app_env != "production" else None,
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type"],
)

app.include_router(health_router, prefix=settings.api_v1_prefix)
app.include_router(auth_router, prefix=settings.api_v1_prefix)
app.include_router(prayers_router, prefix=settings.api_v1_prefix)


@app.exception_handler(RuntimeError)
async def runtime_error_handler(request: Request, exc: RuntimeError):
    # Avoid leaking database internals when local developers forget configuration.
    logging.getLogger(__name__).warning("A backend service is unavailable: %s", exc)
    return JSONResponse(
        status_code=503,
        content={"detail": "This service is temporarily unavailable. Configure the database and try again."},
    )


@app.get("/", tags=["Root"])
async def root() -> dict[str, str]:
    return {"name": settings.app_name, "version": "0.2.0", "docs": "/docs"}
