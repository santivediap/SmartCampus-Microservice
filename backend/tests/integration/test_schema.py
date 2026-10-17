"""Business rules enforced by the database itself (last line of defence)."""

import psycopg
import pytest
from psycopg.types.json import Jsonb


@pytest.fixture
def room_id(db_conn):
    row = db_conn.execute(
        "INSERT INTO rooms (nombre, edificio, capacidad, equipamiento) "
        "VALUES ('Lab', 'A', 30, %s) RETURNING id",
        (Jsonb(["ordenadores"]),),
    ).fetchone()
    db_conn.commit()
    return row["id"]


def book(conn, room_id, start, end, day="2026-11-02"):
    conn.execute(
        "INSERT INTO bookings (aula_id, usuario, fecha, hora_inicio, hora_fin) "
        "VALUES (%s, 'test', %s, %s, %s)",
        (room_id, day, start, end),
    )
    conn.commit()


@pytest.mark.parametrize("capacidad", [0, -1])
def test_room_capacity_must_be_positive(db_conn, capacidad):
    with pytest.raises(psycopg.errors.CheckViolation):
        db_conn.execute(
            "INSERT INTO rooms (nombre, edificio, capacidad) VALUES ('X', 'A', %s)",
            (capacidad,),
        )


def test_overlapping_booking_is_rejected(db_conn, room_id):
    book(db_conn, room_id, "10:00", "12:00")

    with pytest.raises(psycopg.errors.ExclusionViolation):
        book(db_conn, room_id, "11:00", "13:00")


def test_back_to_back_bookings_are_allowed(db_conn, room_id):
    book(db_conn, room_id, "10:00", "12:00")
    book(db_conn, room_id, "12:00", "13:00")


def test_start_must_be_before_end(db_conn, room_id):
    with pytest.raises(psycopg.errors.CheckViolation):
        book(db_conn, room_id, "12:00", "10:00")


def test_booking_for_missing_room_is_rejected(db_conn):
    with pytest.raises(psycopg.errors.ForeignKeyViolation):
        book(db_conn, 999, "10:00", "11:00")


def test_deleting_room_deletes_its_bookings(db_conn, room_id):
    book(db_conn, room_id, "10:00", "11:00")

    db_conn.execute("DELETE FROM rooms WHERE id = %s", (room_id,))
    db_conn.commit()

    assert db_conn.execute("SELECT COUNT(*) AS n FROM bookings").fetchone()["n"] == 0
