from app.seeder import BOOKINGS, ROOMS, seed


def count(conn, table):
    return conn.execute(f"SELECT COUNT(*) AS n FROM {table}").fetchone()["n"]


def test_seed_inserts_all_sample_data(db_conn):
    inserted = seed(db_conn)

    assert inserted == {"rooms": len(ROOMS), "bookings": len(BOOKINGS)}
    assert count(db_conn, "rooms") == len(ROOMS)
    assert count(db_conn, "bookings") == len(BOOKINGS)


def test_seeded_bookings_reference_existing_rooms(db_conn):
    seed(db_conn)

    orphans = db_conn.execute(
        "SELECT COUNT(*) AS n FROM bookings b LEFT JOIN rooms r ON r.id = b.aula_id "
        "WHERE r.id IS NULL"
    ).fetchone()["n"]
    assert orphans == 0


def test_seed_twice_does_not_duplicate(db_conn):
    seed(db_conn)
    inserted = seed(db_conn)

    assert inserted == {"rooms": 0, "bookings": 0}
    assert count(db_conn, "rooms") == len(ROOMS)


def test_seed_with_reset_replaces_data_and_restarts_ids(db_conn):
    seed(db_conn)
    db_conn.execute("INSERT INTO rooms (nombre, edificio, capacidad) VALUES ('Extra', 'Z', 5)")
    db_conn.commit()

    seed(db_conn, reset=True)

    assert count(db_conn, "rooms") == len(ROOMS)
    assert db_conn.execute("SELECT MIN(id) AS id FROM rooms").fetchone()["id"] == 1
