"""Smoke tests for the endpoint-template Flask app.

The ``client`` fixture is provided by ``tests/conftest.py``.
"""


def test_index_renders(client):
    resp = client.get("/")
    assert resp.status_code == 200
    assert b"endpoint" in resp.data.lower()


def test_health(client):
    resp = client.get("/api/health")
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["status"] == "ok"
    assert "uptime_seconds" in body
    assert "version" in body


def test_time(client):
    resp = client.get("/api/time")
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["timezone"] == "UTC"
    assert "iso" in body


def test_echo_roundtrip(client):
    resp = client.post("/api/echo", json={"hello": "world"})
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["you_sent"] == {"hello": "world"}


def test_echo_rejects_non_json(client):
    resp = client.post("/api/echo", data="not json", content_type="text/plain")
    assert resp.status_code == 415


def test_original_hello_route(client):
    resp = client.get("/testing_api")
    assert resp.status_code == 200
    assert resp.data == b"Hello, World!"


def test_404_is_json(client):
    resp = client.get("/nope")
    assert resp.status_code == 404
    assert resp.get_json()["error"] == "Not found"
