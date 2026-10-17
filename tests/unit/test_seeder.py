import pytest

from app.db import connect, init_schema
from app.seeder import BOOKINGS, ROOMS, seed


@pytest.fixture
def conn():
    # In-memory DB: fast and isolated, no files or Flask app needed
    conn = connect(":memory:")
    init_schema(conn)
    yield conn
    conn.close()


def count(conn, table):
    return conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]


def test_seed_inserts_all_sample_data(conn):
    inserted = seed(conn)

    assert inserted == {"rooms": len(ROOMS), "bookings": len(BOOKINGS)}
    assert count(conn, "rooms") == len(ROOMS)
    assert count(conn, "bookings") == len(BOOKINGS)


def test_seeded_bookings_reference_existing_rooms(conn):
    seed(conn)

    orphans = conn.execute(
        "SELECT COUNT(*) FROM bookings b LEFT JOIN rooms r ON r.id = b.aula_id WHERE r.id IS NULL"
    ).fetchone()[0]
    assert orphans == 0


def test_seed_twice_does_not_duplicate(conn):
    seed(conn)
    inserted = seed(conn)

    assert inserted == {"rooms": 0, "bookings": 0}
    assert count(conn, "rooms") == len(ROOMS)


def test_seed_with_reset_replaces_data_and_restarts_ids(conn):
    seed(conn)
    conn.execute("INSERT INTO rooms (nombre, edificio, capacidad) VALUES ('Extra', 'Z', 5)")
    conn.commit()

    seed(conn, reset=True)

    assert count(conn, "rooms") == len(ROOMS)
    assert conn.execute("SELECT MIN(id) FROM rooms").fetchone()[0] == 1
