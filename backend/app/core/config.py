from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_name: str = "Todo API"
    app_version: str = "0.1.0"
    debug: bool = True

    # CORS — list of allowed origins
    cors_origins: list[str] = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ]

    # JWT — not validated yet, prepared for real login server integration
    # Replace with: secret_key = os.environ["SECRET_KEY"]
    jwt_secret_key: str = "CHANGE_ME_IN_PRODUCTION"
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 60 * 24  # 24 h

    # --- PostgreSQL (uncomment and fill when ready) ---
    # database_url: str = "postgresql+asyncpg://user:password@localhost:5432/todos"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
