"""Booking business rules (no Flask imports).

Every function receives an open psycopg connection, like the room service.
Dates travel as 'YYYY-MM-DD' strings and times as zero-padded 'HH:MM' strings,
so they are JSON-ready and compare chronologically as plain strings.
"""

from collections.abc import Iterable
from typing import Any, TypedDict

import psycopg

from app.errors import ConflictError, NotFoundError, ValidationError
from app.services.rooms import find_room
from app.services.validation import (
    require_date,
    require_object,
    require_positive_int,
    require_str,
    require_time,
)

# Single source of truth for the columns returned to clients (already serialized)
BOOKING_COLUMNS = (
    "id, aula_id, usuario, "
    "to_char(fecha, 'YYYY-MM-DD') AS fecha, "
    "to_char(hora_inicio, 'HH24:MI') AS hora_inicio, "
    "to_char(hora_fin, 'HH24:MI') AS hora_fin"
)


class BookingInput(TypedDict):
    aula_id: int
    usuario: str
    fecha: str
    hora_inicio: str
    hora_fin: str


def overlaps(start_a: str, end_a: str, start_b: str, end_b: str) -> bool:
    """Return True if two HH:MM time ranges overlap.

    Ranges that only touch (10:00-12:00 and 12:00-13:00) do not overlap.
    """
    return start_a < end_b and end_a > start_b


def find_conflict(existing: Iterable[dict], start: str, end: str) -> dict | None:
    """Return the first booking whose time range overlaps [start, end), or None."""
    return next(
        (b for b in existing if overlaps(start, end, b["hora_inicio"], b["hora_fin"])),
        None,
    )


def validate_booking(payload: Any) -> BookingInput:
    """Validate a create-booking payload and return the cleaned data.

    Pure function: no database access, so it can be unit tested on its own.
    """
    data = require_object(payload)
    booking: BookingInput = {
        "aula_id": require_positive_int(data, "aula_id"),
        "usuario": require_str(data, "usuario"),
        "fecha": require_date(data, "fecha"),
        "hora_inicio": require_time(data, "hora_inicio"),
        "hora_fin": require_time(data, "hora_fin"),
    }
    if booking["hora_inicio"] >= booking["hora_fin"]:
        raise ValidationError("'hora_inicio' must be earlier than 'hora_fin'")
    return booking


def list_bookings(conn: psycopg.Connection) -> list[dict]:
    """Return all bookings in chronological order."""
    return conn.execute(
        f"SELECT {BOOKING_COLUMNS} FROM bookings ORDER BY fecha, hora_inicio, id"
    ).fetchall()


def get_booking(conn: psycopg.Connection, booking_id: int) -> dict:
    """Return a booking or raise NotFoundError."""
    booking = conn.execute(
        f"SELECT {BOOKING_COLUMNS} FROM bookings WHERE id = %s", (booking_id,)
    ).fetchone()
    if booking is None:
        raise NotFoundError(f"Booking {booking_id} not found")
    return booking


def _bookings_for_room_on(conn: psycopg.Connection, room_id: int, day: str) -> list[dict]:
    return conn.execute(
        f"SELECT {BOOKING_COLUMNS} FROM bookings WHERE aula_id = %s AND fecha = %s",
        (room_id, day),
    ).fetchall()


def _conflict_message(booking: dict) -> str:
    return (
        f"Room {booking['aula_id']} is already booked on {booking['fecha']} "
        f"from {booking['hora_inicio']} to {booking['hora_fin']}"
    )


def create_booking(conn: psycopg.Connection, payload: Any) -> dict:
    """Validate the payload, apply the business rules and insert the booking.

    Rules: the room must exist and the slot must not overlap another booking
    of the same room. The database enforces both again (foreign key and
    exclusion constraint), which also covers two requests racing each other.
    """
    booking = validate_booking(payload)
    room_id = booking["aula_id"]

    if find_room(conn, room_id) is None:
        raise NotFoundError(f"Room {room_id} not found")

    same_day = _bookings_for_room_on(conn, room_id, booking["fecha"])
    conflict = find_conflict(same_day, booking["hora_inicio"], booking["hora_fin"])
    if conflict is not None:
        raise ConflictError(_conflict_message(conflict))

    try:
        created = conn.execute(
            "INSERT INTO bookings (aula_id, usuario, fecha, hora_inicio, hora_fin) "
            f"VALUES (%s, %s, %s, %s, %s) RETURNING {BOOKING_COLUMNS}",
            (
                room_id,
                booking["usuario"],
                booking["fecha"],
                booking["hora_inicio"],
                booking["hora_fin"],
            ),
        ).fetchone()
    except psycopg.errors.ExclusionViolation:
        # Another request booked the same slot between our check and the insert
        conn.rollback()
        raise ConflictError(f"Room {room_id} is already booked at that time") from None
    except psycopg.errors.ForeignKeyViolation:
        # The room was deleted between our check and the insert
        conn.rollback()
        raise NotFoundError(f"Room {room_id} not found") from None

    conn.commit()
    return created


def delete_booking(conn: psycopg.Connection, booking_id: int) -> None:
    """Delete a booking or raise NotFoundError."""
    deleted = conn.execute(
        "DELETE FROM bookings WHERE id = %s RETURNING id", (booking_id,)
    ).fetchone()
    if deleted is None:
        raise NotFoundError(f"Booking {booking_id} not found")
    conn.commit()
