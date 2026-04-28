from uuid import UUID

from fastapi import APIRouter, HTTPException, status

from app.models.todo import Todo, TodoCreate, TodoUpdate
from app.services import todo_service

router = APIRouter(prefix="/todos", tags=["todos"])


@router.get("/", response_model=list[Todo])
def get_todos():
    """Return all todos (mock: no user filtering yet)."""
    return todo_service.list_todos()


@router.post("/", response_model=Todo, status_code=status.HTTP_201_CREATED)
def create_todo(data: TodoCreate):
    return todo_service.create_todo(data)


@router.put("/{todo_id}", response_model=Todo)
def update_todo(todo_id: UUID, data: TodoUpdate):
    todo = todo_service.update_todo(todo_id, data)
    if not todo:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Todo not found")
    return todo


@router.delete("/{todo_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_todo(todo_id: UUID):
    if not todo_service.delete_todo(todo_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Todo not found")
