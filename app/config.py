"""Configuration loaded from environment variables."""

import os


class Config:
    APP_ENV = os.getenv("APP_ENV", "development")
    DB_PATH = os.getenv("DB_PATH", "database.db")
