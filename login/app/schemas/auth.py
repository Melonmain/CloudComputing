from pydantic import BaseModel, Field


class AuthRequest(BaseModel):
    username: str = Field(..., min_length=1, max_length=150)
    password: str = Field(..., min_length=1, max_length=255)


class AuthResponse(BaseModel):
    message: str
    username: str
    access_token: str
    token_type: str = "bearer"
