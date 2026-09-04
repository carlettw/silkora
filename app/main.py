from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.core.config import settings
from app.api.v1.api import api_router

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="Centralia Tours uchun sayohat agentligi backend API (tours, bookings, payments, auth)",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
)

if settings.BACKEND_CORS_ORIGINS:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.BACKEND_CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

app.mount(settings.MEDIA_URL, StaticFiles(directory=settings.MEDIA_ROOT, check_dir=False), name="media")

app.include_router(api_router, prefix=settings.API_V1_PREFIX)


@app.get("/api/health", tags=["Health"])
def health_check():
    return {"status": "ok"}
