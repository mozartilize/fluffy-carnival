from functools import lru_cache

from pydantic import BaseSettings


class Settings(BaseSettings):
    sqlalchemy_database_uri: str

    class Config:
        env_file = ".env"


@lru_cache()
def get_settings() -> Settings:
    return Settings()