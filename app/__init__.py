"""SmartCampus REST API."""

from flask import Flask

from app import db
from app.config import Config
from app.errors import register_error_handlers
from app.routes.bookings import bp as bookings_bp
from app.routes.health import bp as health_bp
from app.routes.rooms import bp as rooms_bp


def create_app(overrides: dict | None = None) -> Flask:
    """Application factory: builds and configures a Flask app."""
    app = Flask(__name__)
    app.config.from_object(Config)
    if overrides:
        app.config.update(overrides)

    db.init_app(app)
    register_error_handlers(app)

    app.register_blueprint(health_bp)
    app.register_blueprint(rooms_bp)
    app.register_blueprint(bookings_bp)

    return app
