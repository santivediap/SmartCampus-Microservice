"""Booking endpoints: /bookings.

Routes stay thin: parse the HTTP request, call the service, build the response.
Domain errors raised by the service are turned into JSON by app.errors.
"""

from flask import Blueprint, jsonify, request, url_for

from app.db import get_db
from app.services import bookings

bp = Blueprint("bookings", __name__, url_prefix="/bookings")


@bp.get("")
def list_bookings():
    return jsonify(bookings.list_bookings(get_db())), 200


@bp.get("/<int:booking_id>")
def get_booking(booking_id: int):
    return jsonify(bookings.get_booking(get_db(), booking_id)), 200


@bp.post("")
def create_booking():
    # silent=True: invalid or missing JSON becomes None and fails validation (400)
    booking = bookings.create_booking(get_db(), request.get_json(silent=True))
    location = url_for("bookings.get_booking", booking_id=booking["id"])
    return jsonify(booking), 201, {"Location": location}


@bp.delete("/<int:booking_id>")
def delete_booking(booking_id: int):
    bookings.delete_booking(get_db(), booking_id)
    return "", 204
