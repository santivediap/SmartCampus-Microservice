"""HTTP tests for /bookings (need a running PostgreSQL, see conftest.py)."""

import pytest

ROOM = {"nombre": "Laboratorio A", "edificio": "Edificio A", "capacidad": 30}


@pytest.fixture
def room_id(client):
    return client.post("/rooms", json=ROOM).get_json()["id"]


@pytest.fixture
def make_booking(client, room_id):
    """POST a booking (10:00-12:00 by default) and return the response."""

    def _make(**changes):
        payload = {
            "aula_id": room_id,
            "usuario": "ana.garcia",
            "fecha": "2026-11-02",
            "hora_inicio": "10:00",
            "hora_fin": "12:00",
            **changes,
        }
        return client.post("/bookings", json=payload)

    return _make


@pytest.fixture
def created_booking(make_booking):
    return make_booking().get_json()


# --- Happy path ---


def test_list_bookings_empty(client):
    response = client.get("/bookings")

    assert response.status_code == 200
    assert response.get_json() == []


def test_create_booking(make_booking, room_id):
    response = make_booking()

    assert response.status_code == 201
    body = response.get_json()
    assert body == {
        "id": body["id"],
        "aula_id": room_id,
        "usuario": "ana.garcia",
        "fecha": "2026-11-02",
        "hora_inicio": "10:00",
        "hora_fin": "12:00",
    }
    assert response.headers["Location"] == f"/bookings/{body['id']}"


def test_created_booking_appears_in_list(client, created_booking):
    assert client.get("/bookings").get_json() == [created_booking]


def test_list_is_sorted_chronologically(client, make_booking):
    make_booking(fecha="2026-11-03", hora_inicio="09:00", hora_fin="10:00")
    make_booking(fecha="2026-11-02", hora_inicio="16:00", hora_fin="17:00")
    make_booking(fecha="2026-11-02", hora_inicio="08:00", hora_fin="09:00")

    slots = [(b["fecha"], b["hora_inicio"]) for b in client.get("/bookings").get_json()]
    assert slots == [("2026-11-02", "08:00"), ("2026-11-02", "16:00"), ("2026-11-03", "09:00")]


def test_get_booking_by_id(client, created_booking):
    response = client.get(f"/bookings/{created_booking['id']}")

    assert response.status_code == 200
    assert response.get_json() == created_booking


def test_delete_booking(client, created_booking):
    response = client.delete(f"/bookings/{created_booking['id']}")

    assert response.status_code == 204
    assert client.get("/bookings").get_json() == []


# --- Business rules ---


def test_cannot_book_a_missing_room(client, make_booking):
    response = make_booking(aula_id=999)

    assert response.status_code == 404
    assert "Room 999 not found" in response.get_json()["error"]
    assert client.get("/bookings").get_json() == []


@pytest.mark.parametrize(
    ("start", "end"),
    [("11:00", "13:00"), ("09:00", "10:30"), ("10:30", "11:30"), ("09:00", "13:00")],
)
def test_overlapping_booking_returns_409(client, make_booking, created_booking, start, end):
    response = make_booking(hora_inicio=start, hora_fin=end, usuario="luis.martin")

    assert response.status_code == 409
    assert "already booked" in response.get_json()["error"]
    assert client.get("/bookings").get_json() == [created_booking]


@pytest.mark.parametrize(
    "changes",
    [
        {"hora_inicio": "12:00", "hora_fin": "13:00"},  # back-to-back
        {"hora_inicio": "08:00", "hora_fin": "10:00"},  # ends when the other starts
        {"fecha": "2026-11-03"},  # same time, another day
    ],
)
def test_non_overlapping_booking_is_allowed(make_booking, created_booking, changes):
    assert make_booking(**changes).status_code == 201


def test_same_slot_in_another_room_is_allowed(client, make_booking, created_booking):
    other_room = client.post("/rooms", json={**ROOM, "nombre": "Laboratorio B"}).get_json()

    assert make_booking(aula_id=other_room["id"]).status_code == 201


@pytest.mark.parametrize(("start", "end"), [("12:00", "10:00"), ("10:00", "10:00")])
def test_start_after_end_returns_400(make_booking, start, end):
    response = make_booking(hora_inicio=start, hora_fin=end)

    assert response.status_code == 400
    assert "earlier than" in response.get_json()["error"]


@pytest.mark.parametrize(
    ("field", "value"),
    [("hora_inicio", "25:00"), ("hora_fin", "10h"), ("fecha", "2026-02-30"), ("aula_id", "1")],
)
def test_invalid_field_returns_400(make_booking, field, value):
    response = make_booking(**{field: value})

    assert response.status_code == 400
    assert field in response.get_json()["error"]


def test_delete_missing_booking_returns_404(client):
    response = client.delete("/bookings/999")

    assert response.status_code == 404
    assert "Booking 999 not found" in response.get_json()["error"]


def test_delete_booking_twice_returns_404_the_second_time(client, created_booking):
    path = f"/bookings/{created_booking['id']}"

    assert client.delete(path).status_code == 204
    assert client.delete(path).status_code == 404


def test_freed_slot_can_be_booked_again(client, make_booking, created_booking):
    client.delete(f"/bookings/{created_booking['id']}")

    assert make_booking(usuario="luis.martin").status_code == 201
