-- SmartCampus: PostgreSQL schema (rooms and bookings)
-- Idempotent: safe to run on every startup.

-- Needed to combine "=" on aula_id with "&&" on time ranges in one EXCLUDE constraint
CREATE EXTENSION IF NOT EXISTS btree_gist;

-- Rooms
CREATE TABLE IF NOT EXISTS rooms (
    id            INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    nombre        TEXT    NOT NULL CHECK (btrim(nombre) <> ''),
    edificio      TEXT    NOT NULL CHECK (btrim(edificio) <> ''),
    capacidad     INTEGER NOT NULL CHECK (capacidad > 0),
    -- JSON array of strings, e.g. ["ordenadores", "robots"]
    equipamiento  JSONB   NOT NULL DEFAULT '[]'::jsonb
                  CHECK (jsonb_typeof(equipamiento) = 'array')
);

-- Bookings
CREATE TABLE IF NOT EXISTS bookings (
    id           INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    aula_id      INTEGER NOT NULL REFERENCES rooms (id) ON DELETE CASCADE,
    usuario      TEXT    NOT NULL CHECK (btrim(usuario) <> ''),
    fecha        DATE    NOT NULL,
    hora_inicio  TIME    NOT NULL,
    hora_fin     TIME    NOT NULL,
    CONSTRAINT bookings_start_before_end CHECK (hora_inicio < hora_fin),
    -- Business rule: no two overlapping bookings for the same room.
    -- tsrange is half-open [start, end), so 10:00-12:00 and 12:00-13:00 do NOT overlap.
    CONSTRAINT bookings_no_overlap EXCLUDE USING gist (
        aula_id WITH =,
        tsrange(fecha + hora_inicio, fecha + hora_fin) WITH &&
    )
);
