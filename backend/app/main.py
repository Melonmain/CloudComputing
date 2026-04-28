from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.database import Base, engine
from app.routers import todos, auth

# Create all tables on startup (idempotent — skips existing tables)
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="Cloud-native Todo API — PostgreSQL backend",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # tighten once frontend IP is known
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
        "database": settings.database_url.split("@")[-1],  # host/db only, no credentials
    }
