from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_name: str = "Todo API"
    app_version: str = "0.1.0"
    debug: bool = False

    cors_origins: str = "http://localhost:3000"

    def get_cors_origins(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",")]

    jwt_secret_key: str = "CHANGE_ME_IN_PRODUCTION"
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 60 * 24

    database_url: str = "postgresql://postgres:postgres@localhost:5432/appdb"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
