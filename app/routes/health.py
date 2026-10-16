"""Health check endpoint."""

from flask import Blueprint, current_app, jsonify

from app.db import get_db

bp = Blueprint("health", __name__)

@bp.get("/health")
def health():
    get_db().execute("SELECT 1")
    return jsonify({"status": "ok", "env": current_app.config["APP_ENV"]}), 200
