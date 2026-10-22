"""Room business rules (no Flask imports).

Every function receives an open psycopg connection, so the same code runs from
HTTP routes, scripts or tests without depending on the request context.
"""

from typing import Any, TypedDict

import psycopg
from psycopg.types.json import Jsonb

from app.errors import NotFoundError
from app.services.validation import (
    optional_str_list,
    require_object,
    require_positive_int,
    require_str,
)

# Single source of truth for the columns returned to clients
ROOM_COLUMNS = "id, nombre, edificio, capacidad, equipamiento"


class RoomInput(TypedDict):
    nombre: str
    edificio: str
    capacidad: int
    equipamiento: list[str]


def validate_room(payload: Any) -> RoomInput:
    """Validate a create-room payload and return the cleaned data.

    Pure function: no database access, so it can be unit tested on its own.
    """
    data = require_object(payload)
    return {
        "nombre": require_str(data, "nombre"),
        "edificio": require_str(data, "edificio"),
        "capacidad": require_positive_int(data, "capacidad"),
        "equipamiento": optional_str_list(data, "equipamiento"),
    }


def list_rooms(conn: psycopg.Connection) -> list[dict]:
    """Return all rooms ordered by id."""
    return conn.execute(f"SELECT {ROOM_COLUMNS} FROM rooms ORDER BY id").fetchall()


def find_room(conn: psycopg.Connection, room_id: int) -> dict | None:
    """Return a room or None if it does not exist (for callers that branch on it)."""
    return conn.execute(f"SELECT {ROOM_COLUMNS} FROM rooms WHERE id = %s", (room_id,)).fetchone()


def get_room(conn: psycopg.Connection, room_id: int) -> dict:
    """Return a room or raise NotFoundError."""
    room = find_room(conn, room_id)
    if room is None:
        raise NotFoundError(f"Room {room_id} not found")
    return room


def create_room(conn: psycopg.Connection, payload: Any) -> dict:
    """Validate the payload, insert the room and return it with its new id."""
    room = validate_room(payload)
    created = conn.execute(
        "INSERT INTO rooms (nombre, edificio, capacidad, equipamiento) "
        f"VALUES (%s, %s, %s, %s) RETURNING {ROOM_COLUMNS}",
        (room["nombre"], room["edificio"], room["capacidad"], Jsonb(room["equipamiento"])),
    ).fetchone()
    conn.commit()
    return created


def delete_room(conn: psycopg.Connection, room_id: int) -> None:
    """Delete a room (and its bookings, via ON DELETE CASCADE) or raise NotFoundError."""
    deleted = conn.execute("DELETE FROM rooms WHERE id = %s RETURNING id", (room_id,)).fetchone()
    if deleted is None:
        raise NotFoundError(f"Room {room_id} not found")
    conn.commit()
