"""HTTP tests for /rooms (need a running PostgreSQL, see conftest.py)."""

import pytest

ROOM = {
    "nombre": "Laboratorio de Robótica",
    "edificio": "Edificio A",
    "capacidad": 30,
    "equipamiento": ["ordenadores", "robots", "impresora 3D"],
}


@pytest.fixture
def created_room(client):
    return client.post("/rooms", json=ROOM).get_json()


def test_list_rooms_empty(client):
    response = client.get("/rooms")

    assert response.status_code == 200
    assert response.get_json() == []


def test_create_room(client):
    response = client.post("/rooms", json=ROOM)

    assert response.status_code == 201
    body = response.get_json()
    assert body == {"id": body["id"], **ROOM}
    assert response.headers["Location"] == f"/rooms/{body['id']}"


def test_created_room_appears_in_list(client, created_room):
    assert client.get("/rooms").get_json() == [created_room]


def test_get_room_by_id(client, created_room):
    response = client.get(f"/rooms/{created_room['id']}")

    assert response.status_code == 200
    assert response.get_json() == created_room


def test_get_missing_room_returns_404(client):
    response = client.get("/rooms/999")

    assert response.status_code == 404
    assert "999" in response.get_json()["error"]


def test_delete_room(client, created_room):
    response = client.delete(f"/rooms/{created_room['id']}")

    assert response.status_code == 204
    assert client.get(f"/rooms/{created_room['id']}").status_code == 404


def test_delete_missing_room_returns_404(client):
    response = client.delete("/rooms/999")

    assert response.status_code == 404
    assert "error" in response.get_json()


@pytest.mark.parametrize("capacidad", [0, -5])
def test_create_room_with_invalid_capacity_returns_400(client, capacidad):
    response = client.post("/rooms", json={**ROOM, "capacidad": capacidad})

    assert response.status_code == 400
    assert "capacidad" in response.get_json()["error"]
    assert client.get("/rooms").get_json() == []


def test_create_room_without_json_body_returns_400(client):
    response = client.post("/rooms", data="not json", content_type="text/plain")

    assert response.status_code == 400
    assert "JSON object" in response.get_json()["error"]


def test_non_numeric_id_returns_json_404(client):
    response = client.get("/rooms/abc")

    assert response.status_code == 404
    assert "error" in response.get_json()
