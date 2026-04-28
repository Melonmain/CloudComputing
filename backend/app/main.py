from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.routers import todos, auth

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="Cloud-native Todo API — mock mode (no DB required)",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(todos.router)
app.include_router(auth.router)


@app.get("/health", tags=["system"])
def health_check():
    return {
        "status": "ok",
        "version": settings.app_version,
        "mode": "mock — no database connected",
    }
