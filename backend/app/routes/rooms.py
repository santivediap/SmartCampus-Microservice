"""Room endpoints: /rooms.

Routes stay thin: parse the HTTP request, call the service, build the response.
Domain errors raised by the service are turned into JSON by app.errors.
"""

from flask import Blueprint, jsonify, request, url_for

from app.db import get_db
from app.services import rooms

bp = Blueprint("rooms", __name__, url_prefix="/rooms")


@bp.get("")
def list_rooms():
    return jsonify(rooms.list_rooms(get_db())), 200


@bp.get("/<int:room_id>")
def get_room(room_id: int):
    return jsonify(rooms.get_room(get_db(), room_id)), 200


@bp.post("")
def create_room():
    # silent=True: invalid or missing JSON becomes None and fails validation (400)
    room = rooms.create_room(get_db(), request.get_json(silent=True))
    location = url_for("rooms.get_room", room_id=room["id"])
    return jsonify(room), 201, {"Location": location}


@bp.delete("/<int:room_id>")
def delete_room(room_id: int):
    rooms.delete_room(get_db(), room_id)
    return "", 204
