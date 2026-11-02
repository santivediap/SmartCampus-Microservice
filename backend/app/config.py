"""Configuration loaded from environment variables."""

import os

from dotenv import load_dotenv

# Load a local .env file if present; real environment variables take precedence
load_dotenv()


class Config:
    APP_ENV = os.getenv("APP_ENV", "development")

    DB_HOST = os.getenv("DB_HOST", "localhost")
    DB_PORT = int(os.getenv("DB_PORT", "5432"))
    DB_NAME = os.getenv("DB_NAME", "smartcampus")
    DB_USER = os.getenv("DB_USER", "smartcampus")
    DB_PASSWORD = os.getenv("DB_PASSWORD", "")
