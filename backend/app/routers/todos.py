from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user_id
from app.models.todo import Todo, TodoCreate, TodoUpdate
from app.services import todo_service

router = APIRouter(prefix="/todos", tags=["todos"])


@router.get("/", response_model=list[Todo])
def get_todos(
    db: Session = Depends(get_db),
    user_id: UUID = Depends(get_current_user_id),
):
    return todo_service.list_todos(db, user_id=user_id)


@router.post("/", response_model=Todo, status_code=status.HTTP_201_CREATED)
def create_todo(
    data: TodoCreate,
    db: Session = Depends(get_db),
    user_id: UUID = Depends(get_current_user_id),
):
    return todo_service.create_todo(db, data, user_id=user_id)


@router.put("/{todo_id}", response_model=Todo)
def update_todo(
    todo_id: UUID,
    data: TodoUpdate,
    db: Session = Depends(get_db),
    user_id: UUID = Depends(get_current_user_id),
):
    todo = todo_service.update_todo(db, todo_id, data, user_id=user_id)
    if not todo:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Todo not found")
    return todo


@router.delete("/{todo_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_todo(
    todo_id: UUID,
    db: Session = Depends(get_db),
    user_id: UUID = Depends(get_current_user_id),
):
    if not todo_service.delete_todo(db, todo_id, user_id=user_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Todo not found")
