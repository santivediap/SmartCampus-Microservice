"""Unit tests for the room service (no database needed).

Functions that use the database receive a mocked connection, so these tests
run in the pre-commit hook without PostgreSQL.
"""

from unittest.mock import MagicMock

import pytest

from app.errors import NotFoundError, ValidationError
from app.services.rooms import create_room, delete_room, get_room, validate_room

VALID = {
    "nombre": "Laboratorio de Robótica",
    "edificio": "Edificio A",
    "capacidad": 30,
    "equipamiento": ["ordenadores", "robots"],
}


def with_changes(**changes):
    """Copy of VALID with some fields replaced; a value of ... removes the field."""
    data = {**VALID, **changes}
    return {key: value for key, value in data.items() if value is not ...}


def test_valid_room_is_accepted():
    assert validate_room(VALID) == VALID


def test_strings_are_trimmed():
    room = validate_room(with_changes(nombre="  Aula 1  ", equipamiento=[" proyector "]))

    assert room["nombre"] == "Aula 1"
    assert room["equipamiento"] == ["proyector"]


@pytest.mark.parametrize("equipamiento", [..., None, []])
def test_equipment_defaults_to_empty_list(equipamiento):
    assert validate_room(with_changes(equipamiento=equipamiento))["equipamiento"] == []


@pytest.mark.parametrize("capacidad", [0, -1])
def test_capacity_must_be_positive(capacidad):
    with pytest.raises(ValidationError, match="greater than 0"):
        validate_room(with_changes(capacidad=capacidad))


@pytest.mark.parametrize("capacidad", ["30", 30.5, True, None, ...])
def test_capacity_must_be_an_integer(capacidad):
    with pytest.raises(ValidationError, match="capacidad"):
        validate_room(with_changes(capacidad=capacidad))


@pytest.mark.parametrize("field", ["nombre", "edificio"])
@pytest.mark.parametrize("value", [..., None, "", "   ", 123])
def test_text_fields_are_required(field, value):
    with pytest.raises(ValidationError, match=field):
        validate_room(with_changes(**{field: value}))


@pytest.mark.parametrize("equipamiento", ["proyector", [""], [1, 2], ["ok", None]])
def test_equipment_must_be_list_of_strings(equipamiento):
    with pytest.raises(ValidationError, match="equipamiento"):
        validate_room(with_changes(equipamiento=equipamiento))


@pytest.mark.parametrize("payload", [None, [], "room", 42])
def test_body_must_be_an_object(payload):
    with pytest.raises(ValidationError, match="JSON object"):
        validate_room(payload)


# --- Service functions with a mocked connection ---


def fake_conn(row):
    """Mocked psycopg connection whose next query returns `row` from fetchone()."""
    conn = MagicMock()
    conn.execute.return_value.fetchone.return_value = row
    return conn


def test_create_room_inserts_and_commits():
    created = {"id": 1, **VALID}
    conn = fake_conn(created)

    assert create_room(conn, VALID) == created
    params = conn.execute.call_args.args[1]
    assert params[:3] == (VALID["nombre"], VALID["edificio"], VALID["capacidad"])
    conn.commit.assert_called_once()


@pytest.mark.parametrize("capacidad", [0, -1])
def test_create_room_with_invalid_capacity_never_touches_db(capacidad):
    conn = fake_conn(None)

    with pytest.raises(ValidationError):
        create_room(conn, with_changes(capacidad=capacidad))

    conn.execute.assert_not_called()
    conn.commit.assert_not_called()


def test_get_room_returns_existing_room():
    room = {"id": 1, **VALID}

    assert get_room(fake_conn(room), 1) == room


def test_get_missing_room_raises_not_found():
    with pytest.raises(NotFoundError, match="Room 99 not found"):
        get_room(fake_conn(None), 99)


def test_delete_existing_room_commits():
    conn = fake_conn({"id": 1})

    delete_room(conn, 1)

    assert conn.execute.call_args.args[1] == (1,)
    conn.commit.assert_called_once()


def test_delete_missing_room_raises_not_found_and_does_not_commit():
    conn = fake_conn(None)

    with pytest.raises(NotFoundError, match="Room 99 not found"):
        delete_room(conn, 99)

    conn.commit.assert_not_called()
