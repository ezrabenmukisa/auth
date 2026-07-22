"""Shared pytest fixtures for the test suite."""

import pytest
import os

from app import create_app
from app.config import TestConfig
from app.extensions import db


class UserTestConfig(TestConfig):
    """Test configuration pointing at an isolated PostgreSQL test database."""
    SQLALCHEMY_DATABASE_URI = os.getenv("TEST_DATABASE_URL")


@pytest.fixture
def app():
    """Create a Flask app configured for testing, with a fresh test DB."""
    application = create_app(UserTestConfig)

    with application.app_context():
        db.create_all()
        yield application
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    """Return a test client bound to the test app."""
    return app.test_client()
