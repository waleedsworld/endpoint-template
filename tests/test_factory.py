"""Tests for the application factory and configuration wiring."""

from app import create_app


def test_factory_returns_distinct_instances():
    a = create_app()
    b = create_app()
    assert a is not b


def test_default_config_defaults():
    app = create_app()
    assert app.config["APP_NAME"] == "endpoint-template"
    # JSON key order is preserved so response fields stay predictable.
    assert app.config["JSON_SORT_KEYS"] is False


def test_config_override_is_applied():
    app = create_app({"APP_NAME": "custom-name", "TESTING": True})
    assert app.config["APP_NAME"] == "custom-name"
    assert app.config["TESTING"] is True


def test_health_reflects_overridden_app_name():
    app = create_app({"APP_NAME": "renamed"})
    with app.test_client() as c:
        assert c.get("/api/health").get_json()["app"] == "renamed"


def test_module_level_app_is_wsgi_ready():
    # gunicorn imports `app:app`; make sure that symbol exists and serves.
    from app import app as wsgi_app

    with wsgi_app.test_client() as c:
        assert c.get("/api/health").status_code == 200
