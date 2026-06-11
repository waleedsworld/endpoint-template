"""endpoint-template — a tiny, batteries-included Flask API starter.

Drop your routes in and go. This app ships a small landing page, a
health check, and a couple of example JSON endpoints so you have a
working reference to copy from instead of a blank file.

Run it:
    python app.py
Then open http://127.0.0.1:5000
"""

from __future__ import annotations

import os
import platform
import uuid
from datetime import datetime, timezone

from flask import Flask, g, jsonify, render_template, request

# App version. Bump this when you cut a release.
__version__ = "1.2.0"

# Header used to carry a request-correlation id in and out of the app.
REQUEST_ID_HEADER = "X-Request-ID"

# Remember when the process booted so /api/health can report uptime.
STARTED_AT = datetime.now(timezone.utc)


def create_app(config: dict | None = None) -> Flask:
    """Application factory.

    Using a factory keeps the app easy to configure and test — you can
    spin up isolated instances in your test suite without global state.
    """
    app = Flask(__name__)
    app.config.update(
        JSON_SORT_KEYS=False,
        APP_NAME="endpoint-template",
    )
    if config:
        app.config.update(config)

    register_request_id(app)
    register_routes(app)
    register_error_handlers(app)
    return app


def register_request_id(app: Flask) -> None:
    """Give every request a correlation id you can trace across logs.

    If the caller already sent an ``X-Request-ID`` we honour it (so a
    front proxy or client can stitch a request together end-to-end);
    otherwise we mint a fresh UUID4. The id is stashed on ``g`` for use
    inside handlers and echoed back on the response header. This is the
    kind of plumbing every real service ends up wanting on day two.
    """

    @app.before_request
    def _assign_request_id():
        incoming = request.headers.get(REQUEST_ID_HEADER, "").strip()
        g.request_id = incoming or uuid.uuid4().hex

    @app.after_request
    def _emit_request_id(response):
        # g.request_id may be missing for responses raised before the
        # before_request hook ran (rare), so fall back defensively.
        response.headers[REQUEST_ID_HEADER] = getattr(g, "request_id", "")
        return response


def register_routes(app: Flask) -> None:
    @app.route("/")
    def index():
        """Human-friendly landing page listing the available endpoints."""
        endpoints = [
            {"method": "GET", "path": "/", "desc": "This landing page"},
            {"method": "GET", "path": "/api/health", "desc": "Liveness + uptime"},
            {"method": "GET", "path": "/api/time", "desc": "Current server time"},
            {"method": "GET", "path": "/api/uuid", "desc": "Generate UUID4(s), ?count=1..100"},
            {"method": "POST", "path": "/api/echo", "desc": "Echo back your JSON"},
            {"method": "GET", "path": "/testing_api", "desc": "The original hello route"},
        ]
        return render_template(
            "index.html",
            version=__version__,
            endpoints=endpoints,
        )

    @app.route("/api/health")
    def health():
        """Return liveness info. Handy for load balancers and uptime checks."""
        uptime = (datetime.now(timezone.utc) - STARTED_AT).total_seconds()
        return jsonify(
            status="ok",
            app=app.config["APP_NAME"],
            version=__version__,
            uptime_seconds=round(uptime, 3),
            python=platform.python_version(),
        )

    @app.route("/api/time")
    def server_time():
        """Return the current server time in a few useful formats."""
        now = datetime.now(timezone.utc)
        return jsonify(
            iso=now.isoformat(),
            epoch=now.timestamp(),
            timezone="UTC",
        )

    @app.route("/api/uuid")
    def make_uuid():
        """Generate one or more random UUID4s.

        A handy stand-in for the id-generator endpoint most services need
        eventually. Pass ``?count=N`` (1-100) to get a batch; anything
        outside that range — or non-numeric — is rejected with a 400 so
        callers get a clear signal instead of a silent surprise.
        """
        raw = request.args.get("count", "1")
        try:
            count = int(raw)
        except ValueError:
            return jsonify(error="count must be an integer"), 400
        if not 1 <= count <= 100:
            return jsonify(error="count must be between 1 and 100"), 400
        ids = [str(uuid.uuid4()) for _ in range(count)]
        return jsonify(uuids=ids, count=count, version=4)

    @app.route("/api/echo", methods=["POST"])
    def echo():
        """Echo the JSON body back to the caller.

        A minimal example of reading a request, validating it, and
        returning a structured response.
        """
        if not request.is_json:
            return (
                jsonify(error="Send a JSON body with Content-Type: application/json"),
                415,
            )
        payload = request.get_json(silent=True)
        if payload is None:
            return jsonify(error="Could not parse JSON body"), 400
        return jsonify(you_sent=payload, received_at=datetime.now(timezone.utc).isoformat())

    @app.route("/testing_api")
    def hello_world():
        """The original template route, kept for old habits."""
        return "Hello, World!"


def register_error_handlers(app: Flask) -> None:
    @app.errorhandler(404)
    def not_found(_err):
        return jsonify(error="Not found", hint="See / for available endpoints"), 404

    @app.errorhandler(405)
    def method_not_allowed(_err):
        return jsonify(error="Method not allowed"), 405


# Module-level app so `flask run` and WSGI servers (gunicorn app:app) work.
app = create_app()


if __name__ == "__main__":
    port = int(os.environ.get("PORT", "5000"))
    debug = os.environ.get("FLASK_DEBUG", "1") == "1"
    app.run(host="0.0.0.0", port=port, debug=debug)
