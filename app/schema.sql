-- SmartCampus: SQLite schema (rooms and bookings)
-- Note: SQLite only enforces FOREIGN KEY constraints if every connection runs
-- PRAGMA foreign_keys = ON;

PRAGMA foreign_keys = ON;

-- Rooms
CREATE TABLE IF NOT EXISTS rooms (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre        TEXT    NOT NULL CHECK (length(trim(nombre)) > 0),
    edificio      TEXT    NOT NULL CHECK (length(trim(edificio)) > 0),
    capacidad     INTEGER NOT NULL CHECK (capacidad > 0),
    -- JSON array of strings, e.g. '["ordenadores","robots"]'
    equipamiento  TEXT    NOT NULL DEFAULT '[]'
                  CHECK (json_valid(equipamiento) AND json_type(equipamiento) = 'array')
);

-- Bookings
CREATE TABLE IF NOT EXISTS bookings (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    aula_id      INTEGER NOT NULL REFERENCES rooms(id) ON DELETE CASCADE,
    usuario      TEXT    NOT NULL CHECK (length(trim(usuario)) > 0),
    fecha        TEXT    NOT NULL
                 CHECK (fecha GLOB '[0-9][0-9][0-9][0-9]-[0-1][0-9]-[0-3][0-9]'
                        AND date(fecha) = fecha),                -- valid YYYY-MM-DD
    hora_inicio  TEXT    NOT NULL
                 CHECK (hora_inicio GLOB '[0-2][0-9]:[0-5][0-9]'
                        AND time(hora_inicio) IS NOT NULL),       -- HH:MM
    hora_fin     TEXT    NOT NULL
                 CHECK (hora_fin GLOB '[0-2][0-9]:[0-5][0-9]'
                        AND time(hora_fin) IS NOT NULL),          -- HH:MM
    CHECK (hora_inicio < hora_fin)
);

-- Speeds up overlap lookups per room and day
CREATE INDEX IF NOT EXISTS idx_bookings_aula_fecha ON bookings (aula_id, fecha);

-- Business rule: no two overlapping bookings for the same room.
-- Two bookings overlap if new_start < existing_end AND new_end > existing_start
-- (10:00-12:00 and 12:00-13:00 do NOT overlap).
CREATE TRIGGER IF NOT EXISTS trg_bookings_no_overlap_insert
BEFORE INSERT ON bookings
WHEN EXISTS (
    SELECT 1 FROM bookings b
    WHERE b.aula_id = NEW.aula_id
      AND b.fecha   = NEW.fecha
      AND NEW.hora_inicio < b.hora_fin
      AND NEW.hora_fin    > b.hora_inicio
)
BEGIN
    SELECT RAISE(ABORT, 'Reserva solapada para esta aula');
END;

-- Same rule on UPDATE; excludes the row being updated so it doesn't clash with itself
CREATE TRIGGER IF NOT EXISTS trg_bookings_no_overlap_update
BEFORE UPDATE ON bookings
WHEN EXISTS (
    SELECT 1 FROM bookings b
    WHERE b.id     <> NEW.id
      AND b.aula_id = NEW.aula_id
      AND b.fecha   = NEW.fecha
      AND NEW.hora_inicio < b.hora_fin
      AND NEW.hora_fin    > b.hora_inicio
)
BEGIN
    SELECT RAISE(ABORT, 'Reserva solapada para esta aula');
END;
