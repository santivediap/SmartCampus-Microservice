"""Seed the database with sample rooms and bookings.

Usage:
    python -m app.seeder           # seed only if the database is empty
    python -m app.seeder --reset   # wipe existing data and seed again
"""

import argparse
from datetime import date, time

import psycopg
from psycopg.types.json import Jsonb

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

# "room" is the position in ROOMS (1-based), resolved to a real id at insert time
BOOKINGS = [
    {
        "room": 1,
        "usuario": "ana.garcia",
        "fecha": date(2026, 11, 2),
        "hora_inicio": time(10, 0),
        "hora_fin": time(12, 0),
    },
    # Back-to-back with the previous one: allowed (ranges only touch)
    {
        "room": 1,
        "usuario": "luis.martin",
        "fecha": date(2026, 11, 2),
        "hora_inicio": time(12, 0),
        "hora_fin": time(13, 0),
    },
    {
        "room": 2,
        "usuario": "marta.lopez",
        "fecha": date(2026, 11, 3),
        "hora_inicio": time(9, 0),
        "hora_fin": time(11, 0),
    },
    {
        "room": 3,
        "usuario": "javier.ruiz",
        "fecha": date(2026, 11, 3),
        "hora_inicio": time(16, 0),
        "hora_fin": time(17, 30),
    },
    {
        "room": 4,
        "usuario": "ana.garcia",
        "fecha": date(2026, 11, 4),
        "hora_inicio": time(15, 0),
        "hora_fin": time(18, 0),
    },
]


def clear(conn: psycopg.Connection) -> None:
    """Delete all data and restart identity counters."""
    conn.execute("TRUNCATE bookings, rooms RESTART IDENTITY CASCADE")


def seed(conn: psycopg.Connection, reset: bool = False) -> dict[str, int]:
    """Insert sample data and return how many rows were inserted per table.

    Without reset, does nothing if rooms already exist (safe to run twice).
    Runs in a single transaction: either everything is inserted or nothing.
    """
    with conn.transaction():
        if reset:
            clear(conn)
        elif conn.execute("SELECT 1 FROM rooms LIMIT 1").fetchone():
            return {"rooms": 0, "bookings": 0}

        room_ids = []
        for room in ROOMS:
            row = conn.execute(
                "INSERT INTO rooms (nombre, edificio, capacidad, equipamiento) "
                "VALUES (%s, %s, %s, %s) RETURNING id",
                (room["nombre"], room["edificio"], room["capacidad"], Jsonb(room["equipamiento"])),
            ).fetchone()
            room_ids.append(row["id"])

        for booking in BOOKINGS:
            conn.execute(
                "INSERT INTO bookings (aula_id, usuario, fecha, hora_inicio, hora_fin) "
                "VALUES (%s, %s, %s, %s, %s)",
                (
                    room_ids[booking["room"] - 1],
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

    config = vars(Config)
    with connect(config) as conn:
        init_schema(conn)
        inserted = seed(conn, reset=args.reset)

    target = f"{Config.DB_NAME}@{Config.DB_HOST}"
    if inserted["rooms"] == 0:
        print(f"Database '{target}' already has data. Use --reset to reseed.")
    else:
        print(f"Seeded '{target}': {inserted['rooms']} rooms, {inserted['bookings']} bookings.")


if __name__ == "__main__":
    main()
