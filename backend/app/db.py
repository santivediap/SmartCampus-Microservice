"""PostgreSQL connection handling: one connection per request."""

from collections.abc import Mapping
from pathlib import Path
from typing import Any

import psycopg
from flask import Flask, current_app, g
from psycopg.rows import dict_row

SCHEMA_PATH = Path(__file__).with_name("schema.sql")

# Arbitrary key so concurrent replicas don't create the schema at the same time
SCHEMA_LOCK_ID = 7_041_131_345


def connect(config: Mapping[str, Any]) -> psycopg.Connection:
    """Open a connection that returns rows as dicts."""
    return psycopg.connect(
        host=config["DB_HOST"],
        port=config["DB_PORT"],
        dbname=config["DB_NAME"],
        user=config["DB_USER"],
        password=config["DB_PASSWORD"],
        row_factory=dict_row,
    )


def get_db() -> psycopg.Connection:
    """Return the connection for the current request, creating it if needed."""
    if "db" not in g:
        g.db = connect(current_app.config)
    return g.db


def close_db(_exc: BaseException | None = None) -> None:
    conn = g.pop("db", None)
    if conn is not None:
        conn.close()


def init_schema(conn: psycopg.Connection) -> None:
    """Create extension and tables if missing (idempotent and replica-safe)."""
    with conn.transaction():
        conn.execute("SELECT pg_advisory_xact_lock(%s)", (SCHEMA_LOCK_ID,))
        conn.execute(SCHEMA_PATH.read_text(encoding="utf-8"))


def init_app(app: Flask) -> None:
    app.teardown_appcontext(close_db)
    with connect(app.config) as conn:
        init_schema(conn)
