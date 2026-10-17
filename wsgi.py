"""Entry point: `flask --app wsgi run` or a WSGI server."""

from app import create_app

app = create_app()
