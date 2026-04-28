"""
Mock auth router.

Later: replace mock logic with calls to the real login server.
The login server returns a JWT cookie — this router currently
sets a dummy cookie so the frontend flow already works end-to-end.

Migration path:
  1. Call external login server: POST /login -> set-cookie: jwt=<token>
  2. Validate incoming JWT with the login server's public key.
  3. Extract user_id from JWT claims and pass it to todo_service.
"""
from fastapi import APIRouter, Response
from pydantic import BaseModel

router = APIRouter(prefix="/auth", tags=["auth"])

MOCK_COOKIE_NAME = "access_token"
MOCK_TOKEN = "mock-jwt-token-replace-with-real"


class AuthRequest(BaseModel):
    username: str
    password: str


class AuthResponse(BaseModel):
    message: str
    username: str


@router.post("/login", response_model=AuthResponse)
def login(body: AuthRequest, response: Response):
    # TODO: forward credentials to the real login server
    # token = external_login_client.login(body.username, body.password)
    response.set_cookie(
        key=MOCK_COOKIE_NAME,
        value=MOCK_TOKEN,
        httponly=True,
        samesite="lax",
    )
    return AuthResponse(message="Login successful (mock)", username=body.username)


@router.post("/register", response_model=AuthResponse)
def register(body: AuthRequest, response: Response):
    # TODO: forward to real registration endpoint
    response.set_cookie(
        key=MOCK_COOKIE_NAME,
        value=MOCK_TOKEN,
        httponly=True,
        samesite="lax",
    )
    return AuthResponse(message="Registration successful (mock)", username=body.username)


@router.post("/logout")
def logout(response: Response):
    response.delete_cookie(key=MOCK_COOKIE_NAME)
    return {"message": "Logged out"}
