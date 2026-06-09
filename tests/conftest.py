"""Shared pytest fixtures for the endpoint-template test suite.

Keeping the fixtures here means every test module gets a fresh, isolated
application instance without importing the same boilerplate over and over.
"""

import pytest

from app import create_app


@pytest.fixture()
def app():
    """A fresh application configured for testing."""
    return create_app({"TESTING": True})


@pytest.fixture()
def client(app):
    """A test client bound to the fixture app."""
    with app.test_client() as c:
        yield c
