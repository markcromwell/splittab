from pydantic_settings import BaseSettings, SettingsConfigDict


MAX_PEOPLE = 100000


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_name: str = "SplitTab"
    version: str = "0.1.0"
    database_url: str = "sqlite:///./app.db"  # override via env for Postgres
    expose_openapi: bool = False


settings = Settings()
