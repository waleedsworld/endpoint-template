"""Tests for the endpoint-template Flask app."""

import json

import pytest

from app import create_app


@pytest.fixture()
def client():
    app = create_app({"TESTING": True})
    with app.test_client() as c:
        yield c


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


def test_uuid_default_single(client):
    resp = client.get("/api/uuid")
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["count"] == 1
    assert body["version"] == 4
    assert len(body["uuids"]) == 1


def test_uuid_batch(client):
    resp = client.get("/api/uuid?count=5")
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["count"] == 5
    assert len(body["uuids"]) == 5
    assert len(set(body["uuids"])) == 5  # all distinct


def test_uuid_rejects_out_of_range(client):
    assert client.get("/api/uuid?count=0").status_code == 400
    assert client.get("/api/uuid?count=101").status_code == 400


def test_uuid_rejects_non_integer(client):
    resp = client.get("/api/uuid?count=abc")
    assert resp.status_code == 400
    assert "error" in resp.get_json()


def test_request_id_generated(client):
    resp = client.get("/api/health")
    rid = resp.headers.get("X-Request-ID")
    assert rid
    assert len(rid) >= 8


def test_request_id_honoured_from_caller(client):
    resp = client.get("/api/health", headers={"X-Request-ID": "trace-123"})
    assert resp.headers.get("X-Request-ID") == "trace-123"


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
