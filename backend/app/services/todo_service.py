"""
Mock todo service — stores todos in memory.

Migration path to PostgreSQL:
  1. Add SQLAlchemy async session dependency.
  2. Replace the `_store` dict with async DB queries.
  3. Keep the same function signatures so routers need no changes.
"""
from datetime import datetime
from uuid import UUID, uuid4

from app.models.todo import Todo, TodoCreate, TodoUpdate

# In-memory store: { todo_id -> Todo }
_store: dict[UUID, Todo] = {}

# Seed with some example todos so the UI isn't empty on first start
def _seed() -> None:
    _mock_user = uuid4()
    items = [
        TodoCreate(
            title="Cloud Computing Projekt einreichen",
            description="FastAPI Backend und Next.js Frontend fertigstellen und deployen.",
        ),
        TodoCreate(
            title="PostgreSQL anbinden",
            description="Datenbank-Layer mit SQLAlchemy und asyncpg implementieren.",
            completed=True,
        ),
        TodoCreate(
            title="Login-Server integrieren",
            description="JWT-Auth-Flow mit echtem Login-Server verdrahten.",
        ),
        TodoCreate(
            title="Deployment auf AWS / Hetzner vorbereiten",
        ),
    ]
    for item in items:
        todo = Todo(user_id=_mock_user, **item.model_dump())
        _store[todo.id] = todo


_seed()


def list_todos(user_id: UUID | None = None) -> list[Todo]:
    todos = list(_store.values())
    if user_id:
        todos = [t for t in todos if t.user_id == user_id]
    return sorted(todos, key=lambda t: t.created_at, reverse=True)


def get_todo(todo_id: UUID) -> Todo | None:
    return _store.get(todo_id)


def create_todo(data: TodoCreate, user_id: UUID | None = None) -> Todo:
    todo = Todo(
        user_id=user_id or uuid4(),
        **data.model_dump(),
    )
    _store[todo.id] = todo
    return todo


def update_todo(todo_id: UUID, data: TodoUpdate) -> Todo | None:
    todo = _store.get(todo_id)
    if not todo:
        return None
    updated = todo.model_copy(
        update={k: v for k, v in data.model_dump().items() if v is not None}
        | {"updated_at": datetime.utcnow()}
    )
    _store[todo_id] = updated
    return updated


def delete_todo(todo_id: UUID) -> bool:
    if todo_id not in _store:
        return False
    del _store[todo_id]
    return True
