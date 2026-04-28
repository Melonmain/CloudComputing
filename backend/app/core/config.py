from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_name: str = "Todo API"
    app_version: str = "0.1.0"
    debug: bool = True

    cors_origins: list[str] = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ]

    jwt_secret_key: str = "CHANGE_ME_IN_PRODUCTION"
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 60 * 24

    # PostgreSQL — set via DATABASE_URL env var on the server
    # Format: postgresql://user:password@host:5432/dbname
    database_url: str = "postgresql://postgres:postgres@localhost:5432/appdb"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
