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
from datetime import datetime, timezone

from flask import Flask, jsonify, render_template, request

# App version. Bump this when you cut a release.
__version__ = "1.1.0"

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

    register_routes(app)
    register_error_handlers(app)
    return app


def register_routes(app: Flask) -> None:
    @app.route("/")
    def index():
        """Human-friendly landing page listing the available endpoints."""
        endpoints = [
            {"method": "GET", "path": "/", "desc": "This landing page"},
            {"method": "GET", "path": "/api/health", "desc": "Liveness + uptime"},
            {"method": "GET", "path": "/api/time", "desc": "Current server time"},
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
