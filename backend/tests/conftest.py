"""Shared fixtures.

Unit tests need nothing from here. Integration tests need a running PostgreSQL
(e.g. `docker compose up -d database`). They use a separate database, named
by TEST_DB_NAME (default "smartcampus_test"), so they never touch dev data.
"""

import os

import psycopg
import pytest
from psycopg import sql

from app import create_app
from app.config import Config
from app.db import connect, init_schema

TEST_DB_NAME = os.getenv("TEST_DB_NAME", "smartcampus_test")


@pytest.fixture(scope="session")
def db_config():
    """DB settings pointing at the test database, created on first use."""
    config = {key: getattr(Config, key) for key in dir(Config) if key.isupper()}
    config["DB_NAME"] = TEST_DB_NAME

    admin = {**config, "DB_NAME": "postgres"}
    with psycopg.connect(
        host=admin["DB_HOST"],
        port=admin["DB_PORT"],
        dbname=admin["DB_NAME"],
        user=admin["DB_USER"],
        password=admin["DB_PASSWORD"],
        autocommit=True,
    ) as conn:
        exists = conn.execute(
            "SELECT 1 FROM pg_database WHERE datname = %s", (TEST_DB_NAME,)
        ).fetchone()
        if not exists:
            conn.execute(sql.SQL("CREATE DATABASE {}").format(sql.Identifier(TEST_DB_NAME)))

    with connect(config) as conn:
        init_schema(conn)
    return config


@pytest.fixture
def db_conn(db_config):
    """Connection to an empty test database."""
    with connect(db_config) as conn:
        conn.execute("TRUNCATE bookings, rooms RESTART IDENTITY CASCADE")
        conn.commit()
        yield conn


@pytest.fixture
def app(db_config, db_conn):
    return create_app({**db_config, "TESTING": True})


@pytest.fixture
def client(app):
    return app.test_client()
