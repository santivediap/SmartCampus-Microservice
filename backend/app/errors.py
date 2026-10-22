"""Domain errors and their mapping to HTTP responses."""

from flask import Flask, jsonify
from werkzeug.exceptions import HTTPException


class AppError(Exception):
    status_code = 400

    def __init__(self, message: str):
        super().__init__(message)
        self.message = message


class ValidationError(AppError):
    status_code = 400


class NotFoundError(AppError):
    status_code = 404


class ConflictError(AppError):
    status_code = 409


def register_error_handlers(app: Flask) -> None:
    @app.errorhandler(AppError)
    def handle_app_error(err: AppError):
        return jsonify({"error": err.message}), err.status_code

    # Flask's own errors (unknown route, wrong method...) as JSON instead of HTML
    @app.errorhandler(HTTPException)
    def handle_http_error(err: HTTPException):
        return jsonify({"error": err.description}), err.code
