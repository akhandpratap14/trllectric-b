import logging
import os
from random import randint
from typing import ClassVar

# import boto3
from pydantic_settings import BaseSettings, SettingsConfigDict


class GlobalSettings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    ENVIRONMENT: str = ""
    # app settings
    ALLOWED_ORIGINS: str = (
        "https://api.trillectric.com,https://trillectric.com,https://www.trillectric.com,http://127.0.0.1:3000,http://localhost:3000"
    )

    DB_USER: str = ""
    DB_PASSWORD: str = ""
    DB_HOST: str = ""
    DB_PORT: str = "5432"
    DB_NAME: str = "trillectric"
    DB_SCHEMA: str = "trillectric"
    # specify single database url
    DATABASE_URL: str | None = None

    # authentication related
    JWT_ACCESS_SECRET_KEY: str = (
        "28e45889578502db64315a619227b200227a3a966084222e56e99f36b5527947"
    )

    JWT_REFRESH_SECRET_KEY: str = (
        "86347a4ff93492ed455433b251a4eca38f10aedfdc66883c98a18942e9b34ce6"
    )
    ENCRYPTION_ALGORITHM: str = "HS256"

    # Access Token Expire
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # New Access Token Expire
    NEW_ACCESS_TOKEN_EXPIRE_MINUTES: int = 120

    # Refresh Token Expire
    REFRESH_TOKEN_EXPIRE_MINUTES: int = 60 * 24

    # Password Reset Token Expire
    PASSWORD_RESET_TOKEN_EXPIRE_MINUTES: int = 60

    # admin
    ADMIN_SECRET_KEY: str = "adGVsupOZ34wxPyDLNBi2firqQWRDl1B"

    APP_BASE_URL: str = os.environ.get("APP_BASE_URL", "http://localhost:3000")

    # redis for caching
    REDIS_CACHE_ENABLED: bool = True
    REDIS_HOST: str = ""
    REDIS_PORT: str | int = 6379
    REDIS_PASSWORD: str | None = ""
    REDIS_CACHE_EXPIRATION_SECONDS: int = 60 * 30
    REDIS_DB: int = 0

    # static files
    STATIC_HOST: str = "http://localhost:8000"

    # email


class TestSettings(GlobalSettings):
    DB_SCHEMA: str = f"test_{randint(1, 100)}"


class DevelopmentSettings(GlobalSettings):
    APP_BASE_URL: str = os.environ.get("APP_BASE_URL", "https://staging.trillectric.com")
    pass


class ProductionSettings(GlobalSettings):

    LOG_LEVEL: int = logging.INFO

    APP_BASE_URL: str = os.environ.get("APP_BASE_URL", "https://trillectric.com")


def get_settings():
    env = os.environ.get("ENVIRONMENT", "production")
    if env == "test":
        return TestSettings()
    elif env == "development":
        return DevelopmentSettings()
    elif env == "production":
        return ProductionSettings()

    return GlobalSettings()


settings = get_settings()

LOGGING_CONFIG: dict = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "standard": {"format": "%(asctime)s [%(levelname)s] %(name)s: %(message)s"},
    },
    "handlers": {
        "default": {
            "level": getattr(settings, "LOG_LEVEL", logging.INFO),
            "formatter": "standard",
            "class": "logging.StreamHandler",
            "stream": "ext://sys.stdout",  # Default is stderr
        },
    },
    "loggers": {
        "": {
            "handlers": ["default"],
            "level": getattr(settings, "LOG_LEVEL", logging.INFO),
            "propagate": False,
        },
        "uvicorn": {
            "handlers": ["default"],
            "level": logging.ERROR,
            "propagate": False,
        },
    },
}
