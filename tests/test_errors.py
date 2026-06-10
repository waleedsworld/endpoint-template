"""Tests for the JSON error handlers."""


def test_unknown_route_returns_json_404(client):
    resp = client.get("/definitely-not-a-route")
    assert resp.status_code == 404
    body = resp.get_json()
    assert body["error"] == "Not found"
    assert "hint" in body


def test_wrong_method_returns_json_405(client):
    # /api/echo only accepts POST, so GET should be a 405.
    resp = client.get("/api/echo")
    assert resp.status_code == 405
    assert resp.get_json()["error"] == "Method not allowed"


def test_post_to_get_only_route_is_405(client):
    resp = client.post("/api/health")
    assert resp.status_code == 405
    assert resp.get_json()["error"] == "Method not allowed"


def test_error_responses_are_json_not_html(client):
    resp = client.get("/nope")
    assert resp.mimetype == "application/json"
