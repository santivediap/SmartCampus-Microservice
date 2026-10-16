"""Shared fixtures: each test gets a fresh, isolated database."""

import pytest

from app import create_app


@pytest.fixture
def app(tmp_path):
    return create_app({"DB_PATH": str(tmp_path / "test.db"), "TESTING": True})


@pytest.fixture
def client(app):
    return app.test_client()
