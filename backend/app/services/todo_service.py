from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy.orm import Session

from app.models.todo import TodoCreate, TodoModel, TodoUpdate


def list_todos(db: Session, user_id: UUID | None = None) -> list[TodoModel]:
    query = db.query(TodoModel)
    if user_id:
        query = query.filter(TodoModel.user_id == user_id)
    return query.order_by(TodoModel.created_at.desc()).all()


def get_todo(db: Session, todo_id: UUID) -> TodoModel | None:
    return db.query(TodoModel).filter(TodoModel.id == todo_id).first()


def create_todo(db: Session, data: TodoCreate, user_id: UUID | None = None) -> TodoModel:
    todo = TodoModel(
        user_id=user_id or uuid4(),
        title=data.title,
        description=data.description,
        completed=data.completed,
    )
    db.add(todo)
    db.commit()
    db.refresh(todo)
    return todo


def update_todo(
    db: Session, todo_id: UUID, data: TodoUpdate, user_id: UUID | None = None
) -> TodoModel | None:
    query = db.query(TodoModel).filter(TodoModel.id == todo_id)
    if user_id:
        query = query.filter(TodoModel.user_id == user_id)
    todo = query.first()
    if not todo:
        return None
    changes = {k: v for k, v in data.model_dump().items() if v is not None}
    changes["updated_at"] = datetime.utcnow()
    for key, value in changes.items():
        setattr(todo, key, value)
    db.commit()
    db.refresh(todo)
    return todo


def delete_todo(db: Session, todo_id: UUID, user_id: UUID | None = None) -> bool:
    query = db.query(TodoModel).filter(TodoModel.id == todo_id)
    if user_id:
        query = query.filter(TodoModel.user_id == user_id)
    todo = query.first()
    if not todo:
        return False
    db.delete(todo)
    db.commit()
    return True
