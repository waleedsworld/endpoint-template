"""Behavioural tests for the JSON API endpoints."""

import math

from app import __version__


def test_health_full_payload(client):
    body = client.get("/api/health").get_json()
    assert body["status"] == "ok"
    assert body["app"] == "endpoint-template"
    assert body["version"] == __version__
    # uptime is a non-negative number of seconds
    assert isinstance(body["uptime_seconds"], (int, float))
    assert body["uptime_seconds"] >= 0
    # python version looks like "3.11.9"
    assert body["python"].count(".") == 2


def test_health_content_type_is_json(client):
    resp = client.get("/api/health")
    assert resp.mimetype == "application/json"


def test_time_shapes(client):
    body = client.get("/api/time").get_json()
    assert body["timezone"] == "UTC"
    assert body["iso"].endswith("+00:00")
    assert isinstance(body["epoch"], (int, float))
    assert not math.isnan(body["epoch"])


def test_echo_roundtrips_various_payloads(client):
    for payload in ({"a": 1}, [1, 2, 3], {"nested": {"x": [True, None]}}, {}):
        body = client.post("/api/echo", json=payload).get_json()
        assert body["you_sent"] == payload
        assert "received_at" in body


def test_echo_rejects_non_json_with_415(client):
    resp = client.post("/api/echo", data="nope", content_type="text/plain")
    assert resp.status_code == 415
    assert "error" in resp.get_json()


def test_echo_bad_json_body_returns_400(client):
    # Correct content type but a body that is not valid JSON.
    resp = client.post(
        "/api/echo",
        data="{not valid json",
        content_type="application/json",
    )
    assert resp.status_code == 400
    assert resp.get_json()["error"] == "Could not parse JSON body"


def test_original_hello_route(client):
    resp = client.get("/testing_api")
    assert resp.status_code == 200
    assert resp.data == b"Hello, World!"


def test_landing_page_lists_every_api_route(client):
    html = client.get("/").get_data(as_text=True)
    for path in ("/api/health", "/api/time", "/api/echo", "/testing_api"):
        assert path in html
