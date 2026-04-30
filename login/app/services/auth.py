from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.user import UserModel
from app.security import get_password_hash, verify_password


def get_user_by_username(db: Session, username: str) -> UserModel | None:
    statement = select(UserModel).where(UserModel.username == username)
    return db.scalar(statement)


def create_user(db: Session, username: str, password: str) -> UserModel:
    user = UserModel(username=username, password_hash=get_password_hash(password))
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def authenticate_user(db: Session, username: str, password: str) -> UserModel | None:
    user = get_user_by_username(db, username)
    if user is None:
        return None
    if not verify_password(password, user.password_hash):
        return None
    return user
