from datetime import datetime
from uuid import UUID, uuid4
from pydantic import BaseModel, Field


class Todo(BaseModel):
    """Full todo as stored / returned from the API."""
    id: UUID = Field(default_factory=uuid4)
    user_id: UUID = Field(default_factory=uuid4)
    title: str
    description: str | None = None
    completed: bool = False
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    # --- PostgreSQL migration hint ---
    # Replace in-memory store with SQLAlchemy model:
    #
    # class TodoModel(Base):
    #     __tablename__ = "todos"
    #     id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    #     user_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    #     title = Column(String, nullable=False)
    #     description = Column(String, nullable=True)
    #     completed = Column(Boolean, default=False)
    #     created_at = Column(DateTime, default=datetime.utcnow)
    #     updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class TodoCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    description: str | None = Field(default=None, max_length=2000)
    completed: bool = False


class TodoUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = Field(default=None, max_length=2000)
    completed: bool | None = None
