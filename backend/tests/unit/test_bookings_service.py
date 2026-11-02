"""Unit tests for the booking service (no database needed).

Functions that use the database receive a mocked connection, so these tests
run in the pre-commit hook without PostgreSQL.
"""

from unittest.mock import MagicMock

import psycopg
import pytest

from app.errors import ConflictError, NotFoundError, ValidationError
from app.services.bookings import (
    create_booking,
    delete_booking,
    find_conflict,
    overlaps,
    validate_booking,
)

VALID = {
    "aula_id": 1,
    "usuario": "ana.garcia",
    "fecha": "2026-11-02",
    "hora_inicio": "10:00",
    "hora_fin": "12:00",
}
ROOM = {"id": 1, "nombre": "Lab", "edificio": "A", "capacidad": 30, "equipamiento": []}


def with_changes(**changes):
    """Copy of VALID with some fields replaced; a value of ... removes the field."""
    data = {**VALID, **changes}
    return {key: value for key, value in data.items() if value is not ...}


def booking(start, end, booking_id=1):
    return {**VALID, "id": booking_id, "hora_inicio": start, "hora_fin": end}


def fake_conn(*results):
    """Mocked connection: the n-th execute() returns the n-th result.

    Each result feeds both fetchone() and fetchall(); an exception is raised instead.
    """
    cursors = []
    for result in results:
        if isinstance(result, Exception):
            cursors.append(result)
        else:
            cursor = MagicMock()
            cursor.fetchone.return_value = result
            cursor.fetchall.return_value = result
            cursors.append(cursor)
    conn = MagicMock()
    conn.execute.side_effect = cursors
    return conn


# --- Overlap detection ---


@pytest.mark.parametrize(
    ("a", "b", "expected"),
    [
        (("10:00", "12:00"), ("11:00", "13:00"), True),  # partial overlap
        (("10:00", "12:00"), ("09:00", "10:30"), True),  # overlaps the start
        (("10:00", "12:00"), ("10:30", "11:30"), True),  # contained
        (("10:00", "12:00"), ("09:00", "13:00"), True),  # contains
        (("10:00", "12:00"), ("10:00", "12:00"), True),  # identical
        (("10:00", "12:00"), ("12:00", "13:00"), False),  # touching after
        (("10:00", "12:00"), ("08:00", "10:00"), False),  # touching before
        (("10:00", "12:00"), ("08:00", "09:00"), False),  # before
    ],
)
def test_overlaps(a, b, expected):
    assert overlaps(*a, *b) is expected
    assert overlaps(*b, *a) is expected  # symmetric


def test_find_conflict_returns_the_overlapping_booking():
    existing = [booking("08:00", "09:00", 1), booking("11:00", "13:00", 2)]

    assert find_conflict(existing, "10:00", "12:00")["id"] == 2


def test_find_conflict_returns_none_when_slot_is_free():
    existing = [booking("08:00", "10:00", 1), booking("12:00", "13:00", 2)]

    assert find_conflict(existing, "10:00", "12:00") is None


# --- Validation ---


def test_valid_booking_is_accepted():
    assert validate_booking(VALID) == VALID


def test_values_are_normalized():
    result = validate_booking(with_changes(usuario=" ana ", hora_inicio="9:00", fecha="2026-11-2"))

    assert result["usuario"] == "ana"
    assert result["hora_inicio"] == "09:00"
    assert result["fecha"] == "2026-11-02"


@pytest.mark.parametrize(("start", "end"), [("12:00", "10:00"), ("10:00", "10:00")])
def test_start_must_be_before_end(start, end):
    with pytest.raises(ValidationError, match="earlier than"):
        validate_booking(with_changes(hora_inicio=start, hora_fin=end))


@pytest.mark.parametrize("value", ["25:00", "10:60", "10", "10h", 1000, "", ..., None])
@pytest.mark.parametrize("field", ["hora_inicio", "hora_fin"])
def test_invalid_time_is_rejected(field, value):
    with pytest.raises(ValidationError, match=field):
        validate_booking(with_changes(**{field: value}))


@pytest.mark.parametrize("value", ["2026-02-30", "02/11/2026", "mañana", 20261102, ..., None])
def test_invalid_date_is_rejected(value):
    with pytest.raises(ValidationError, match="fecha"):
        validate_booking(with_changes(fecha=value))


@pytest.mark.parametrize("value", [0, -1, "1", 1.5, True, ..., None])
def test_invalid_room_id_is_rejected(value):
    with pytest.raises(ValidationError, match="aula_id"):
        validate_booking(with_changes(aula_id=value))


@pytest.mark.parametrize("value", ["", "   ", 123, ..., None])
def test_user_is_required(value):
    with pytest.raises(ValidationError, match="usuario"):
        validate_booking(with_changes(usuario=value))


@pytest.mark.parametrize("payload", [None, [], "booking", 42])
def test_body_must_be_an_object(payload):
    with pytest.raises(ValidationError, match="JSON object"):
        validate_booking(payload)


# --- Creation (mocked connection: find room, same-day bookings, insert) ---


def test_create_booking_inserts_and_commits():
    created = {"id": 7, **VALID}
    conn = fake_conn(ROOM, [booking("12:00", "13:00")], created)

    assert create_booking(conn, VALID) == created
    insert_params = conn.execute.call_args.args[1]
    assert insert_params == (1, "ana.garcia", "2026-11-02", "10:00", "12:00")
    conn.commit.assert_called_once()


def test_cannot_book_a_missing_room():
    conn = fake_conn(None)

    with pytest.raises(NotFoundError, match="Room 1 not found"):
        create_booking(conn, VALID)

    assert conn.execute.call_count == 1  # never reaches the insert
    conn.commit.assert_not_called()


def test_cannot_book_an_overlapping_slot():
    conn = fake_conn(ROOM, [booking("11:00", "13:00")])

    with pytest.raises(ConflictError, match="already booked on 2026-11-02 from 11:00 to 13:00"):
        create_booking(conn, VALID)

    assert conn.execute.call_count == 2  # never reaches the insert
    conn.commit.assert_not_called()


def test_invalid_booking_never_touches_db():
    conn = fake_conn()

    with pytest.raises(ValidationError):
        create_booking(conn, with_changes(hora_inicio="12:00", hora_fin="10:00"))

    conn.execute.assert_not_called()


def test_concurrent_overlap_detected_by_db_becomes_conflict():
    conn = fake_conn(ROOM, [], psycopg.errors.ExclusionViolation())

    with pytest.raises(ConflictError):
        create_booking(conn, VALID)

    conn.rollback.assert_called_once()
    conn.commit.assert_not_called()


def test_room_deleted_meanwhile_becomes_not_found():
    conn = fake_conn(ROOM, [], psycopg.errors.ForeignKeyViolation())

    with pytest.raises(NotFoundError):
        create_booking(conn, VALID)

    conn.rollback.assert_called_once()


# --- Deletion ---


def test_delete_existing_booking_commits():
    conn = fake_conn({"id": 3})

    delete_booking(conn, 3)

    assert conn.execute.call_args.args[1] == (3,)
    conn.commit.assert_called_once()


def test_delete_missing_booking_raises_not_found_and_does_not_commit():
    conn = fake_conn(None)

    with pytest.raises(NotFoundError, match="Booking 99 not found"):
        delete_booking(conn, 99)

    conn.commit.assert_not_called()
