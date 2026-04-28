from datetime import datetime
from uuid import UUID, uuid4

from pydantic import BaseModel, Field
from sqlalchemy import Boolean, Column, DateTime, String, Text
from sqlalchemy.dialects.postgresql import UUID as PGUUID

from app.core.database import Base


# ── SQLAlchemy ORM model (maps to the todos table in PostgreSQL) ──────────────

class TodoModel(Base):
    __tablename__ = "todos"

    id          = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id     = Column(PGUUID(as_uuid=True), nullable=False)
    title       = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    completed   = Column(Boolean, default=False, nullable=False)
    created_at  = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at  = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)


# ── Pydantic schemas (used by FastAPI for request/response validation) ─────────

class Todo(BaseModel):
    id: UUID
    user_id: UUID
    title: str
    description: str | None = None
    completed: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class TodoCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    description: str | None = Field(default=None, max_length=2000)
    completed: bool = False


class TodoUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = Field(default=None, max_length=2000)
    completed: bool | None = None
