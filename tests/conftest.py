"""Shared pytest fixtures for the test suite."""

import pytest

from app import create_app
from app.config import TestConfig
from app.extensions import db


@pytest.fixture
def app():
    """Create a Flask app configured for testing, with a fresh test DB."""
    application = create_app(TestConfig)

    with application.app_context():
        db.create_all()
        yield application
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    """Return a test client bound to the test app."""
    return app.test_client()
