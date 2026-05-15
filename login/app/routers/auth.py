from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.auth import AuthRequest, AuthResponse
from app.security import ACCESS_TOKEN_COOKIE, create_access_token
from app.services.auth import authenticate_user, create_user, get_user_by_username

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=AuthResponse)
def login(body: AuthRequest, response: Response, db: Session = Depends(get_db)):
    user = authenticate_user(db, body.username, body.password)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
        )

    token = create_access_token(user_id=user.id, username=user.username)
    response.set_cookie(
        key=ACCESS_TOKEN_COOKIE,
        value=token,
        httponly=True,
        samesite="lax",
        path="/",
    )
    return AuthResponse(message="Login successful", username=user.username, access_token=token)


@router.post("/register", response_model=AuthResponse)
def register(body: AuthRequest, response: Response, db: Session = Depends(get_db)):
    if get_user_by_username(db, body.username) is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Username already exists",
        )

    try:
        user = create_user(db, body.username, body.password)
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Username already exists",
        ) from exc

    token = create_access_token(user_id=user.id, username=user.username)
    response.set_cookie(
        key=ACCESS_TOKEN_COOKIE,
        value=token,
        httponly=True,
        samesite="lax",
        path="/",
    )
    return AuthResponse(message="Registration successful", username=user.username, access_token=token)


@router.post("/logout")
def logout(response: Response):
    response.delete_cookie(key=ACCESS_TOKEN_COOKIE, path="/")
    return {"message": "Logged out"}


@router.get("/me")
def me():
    return {"message": "Use the access_token cookie to identify the user"}
