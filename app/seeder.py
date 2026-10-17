"""Seed the database with sample rooms and bookings.

Usage:
    python -m app.seeder           # seed only if the database is empty
    python -m app.seeder --reset   # wipe existing data and seed again
"""

import argparse
import json
import sqlite3

from app.config import Config
from app.db import connect, init_schema

ROOMS = [
    {
        "nombre": "Laboratorio de Robótica",
        "edificio": "Edificio A",
        "capacidad": 30,
        "equipamiento": ["ordenadores", "robots", "impresora 3D"],
    },
    {
        "nombre": "Aula Magna",
        "edificio": "Edificio Central",
        "capacidad": 200,
        "equipamiento": ["proyector", "microfonía", "pizarra digital"],
    },
    {
        "nombre": "Sala de Reuniones B2",
        "edificio": "Edificio B",
        "capacidad": 12,
        "equipamiento": ["pantalla", "videoconferencia"],
    },
    {
        "nombre": "Aula de Informática 1",
        "edificio": "Edificio A",
        "capacidad": 40,
        "equipamiento": ["ordenadores", "proyector"],
    },
]

# aula_id refers to the position in ROOMS (1-based), resolved at insert time
BOOKINGS = [
    {
        "aula_id": 1,
        "usuario": "ana.garcia",
        "fecha": "2026-11-02",
        "hora_inicio": "10:00",
        "hora_fin": "12:00",
    },
    # Back-to-back with the previous one: allowed (ranges only touch)
    {
        "aula_id": 1,
        "usuario": "luis.martin",
        "fecha": "2026-11-02",
        "hora_inicio": "12:00",
        "hora_fin": "13:00",
    },
    {
        "aula_id": 2,
        "usuario": "marta.lopez",
        "fecha": "2026-11-03",
        "hora_inicio": "09:00",
        "hora_fin": "11:00",
    },
    {
        "aula_id": 3,
        "usuario": "javier.ruiz",
        "fecha": "2026-11-03",
        "hora_inicio": "16:00",
        "hora_fin": "17:30",
    },
    {
        "aula_id": 4,
        "usuario": "ana.garcia",
        "fecha": "2026-11-04",
        "hora_inicio": "15:00",
        "hora_fin": "18:00",
    },
]


def clear(conn: sqlite3.Connection) -> None:
    """Delete all data and reset AUTOINCREMENT counters."""
    conn.execute("DELETE FROM bookings")
    conn.execute("DELETE FROM rooms")
    conn.execute("DELETE FROM sqlite_sequence WHERE name IN ('rooms', 'bookings')")


def seed(conn: sqlite3.Connection, reset: bool = False) -> dict[str, int]:
    """Insert sample data and return how many rows were inserted per table.

    Without reset, does nothing if rooms already exist (safe to run twice).
    Runs in a single transaction: either everything is inserted or nothing.
    """
    with conn:
        if reset:
            clear(conn)
        elif conn.execute("SELECT 1 FROM rooms LIMIT 1").fetchone():
            return {"rooms": 0, "bookings": 0}

        room_ids = []
        for room in ROOMS:
            cur = conn.execute(
                "INSERT INTO rooms (nombre, edificio, capacidad, equipamiento) VALUES (?, ?, ?, ?)",
                (
                    room["nombre"],
                    room["edificio"],
                    room["capacidad"],
                    json.dumps(room["equipamiento"], ensure_ascii=False),
                ),
            )
            room_ids.append(cur.lastrowid)

        for booking in BOOKINGS:
            conn.execute(
                "INSERT INTO bookings (aula_id, usuario, fecha, hora_inicio, hora_fin) "
                "VALUES (?, ?, ?, ?, ?)",
                (
                    room_ids[booking["aula_id"] - 1],
                    booking["usuario"],
                    booking["fecha"],
                    booking["hora_inicio"],
                    booking["hora_fin"],
                ),
            )

    return {"rooms": len(ROOMS), "bookings": len(BOOKINGS)}


def main() -> None:
    parser = argparse.ArgumentParser(description="Seed the SmartCampus database.")
    parser.add_argument("--reset", action="store_true", help="wipe existing data first")
    args = parser.parse_args()

    conn = connect(Config.DB_PATH)
    try:
        init_schema(conn)
        inserted = seed(conn, reset=args.reset)
    finally:
        conn.close()

    if inserted["rooms"] == 0:
        print(f"Database '{Config.DB_PATH}' already has data. Use --reset to reseed.")
    else:
        print(
            f"Seeded '{Config.DB_PATH}': {inserted['rooms']} rooms, "
            f"{inserted['bookings']} bookings."
        )


if __name__ == "__main__":
    main()
