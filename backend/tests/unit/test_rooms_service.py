"""Unit tests for room validation (no database needed)."""

import pytest

from app.errors import ValidationError
from app.services.rooms import validate_room

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
