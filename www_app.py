"""www landing page — a single-route Flask app that serves the project
home page at https://www.eme-gir.org and https://eme-gir.org.

Separate from app.py (the ePSD2 glossary browser at epsd2.eme-gir.org)
because the landing page and the dictionary have different audiences
(general visitors vs. lookup-driven researchers), different chrome
(minimal landing vs. Oracc-style sidebar), and different content
shapes (static + live stats vs. paginated query results). Sharing
the Flask process would force both audiences through the same app
config + middleware stack for no benefit; running it as its own
gunicorn worker pool isolates the landing-page load profile (mostly
cache hits on the rendered template) from the dictionary's
query-heavy traffic.

Live corpus stats are computed once at process start (from the same
SQLite indexes the MCP servers use) and cached in module state.
We deliberately do NOT recompute on every request — these numbers
change only when init.sh rebuilds, which is once per release cycle.
A gunicorn worker restart picks up the new counts.

Run directly for development:

    python3 www_app.py --port 5057 --debug

Or via gunicorn in production (docker-compose `www` service):

    gunicorn -w 2 -b 0.0.0.0:5057 'www_app:create_app()'
"""

from __future__ import annotations

import sqlite3
from pathlib import Path

from flask import Flask, render_template

from eme_gir import cuneify as _cuneify
from eme_gir.paths import CDLI_DB, ETCSL_DB, GLOSSARY_DB, ROOT


def _safe_count(db_path: Path, sql: str) -> int | None:
    """Return COUNT result, or None if the DB is missing / unreadable.

    None lets the template render a "—" placeholder so a partially-built
    deployment (e.g. ETCSL skipped via EME_GIR_BUILD_ETCSL=0) still
    serves a landing page instead of 500ing.
    """
    if not db_path.exists():
        return None
    try:
        with sqlite3.connect(f"file:{db_path}?mode=ro", uri=True) as con:
            return con.execute(sql).fetchone()[0]
    except sqlite3.Error:
        return None


def _collect_stats() -> dict[str, int | None]:
    """Run all the COUNT queries once at app boot."""
    return {
        "lemmas": _safe_count(GLOSSARY_DB, "SELECT COUNT(*) FROM entries"),
        "spellings": _safe_count(GLOSSARY_DB, "SELECT COUNT(*) FROM forms"),
        "attestations": _safe_count(GLOSSARY_DB, "SELECT COUNT(*) FROM instances"),
        "etcsl_texts": _safe_count(ETCSL_DB, "SELECT COUNT(*) FROM texts"),
        "etcsl_lines": _safe_count(ETCSL_DB, "SELECT COUNT(*) FROM lines"),
        "cdli_artifacts": _safe_count(CDLI_DB, "SELECT COUNT(*) FROM artifacts"),
    }


def create_app() -> Flask:
    """Flask app factory. gunicorn calls this at worker boot."""
    app = Flask(
        __name__,
        template_folder=str(ROOT / "templates"),
        static_folder=str(ROOT / "static"),
    )

    # Stats are frozen at app boot — see module docstring.
    app.config["CORPUS_STATS"] = _collect_stats()

    # A handful of pre-rendered cuneiform samples for the visual flourish.
    # Computed once at boot; never re-rendered per-request.
    samples = [
        ("lugal-e e₂ mu-na-du₃", "the king built the temple for him"),
        ("inana an gal-ta ki gal-še₃", "Inana, from the great heaven to the great below"),
        ("ŋeštug₂ daŋal", "broad wisdom"),
    ]
    app.config["CUNEIFORM_SAMPLES"] = [
        {
            "transliteration": s,
            "gloss": gloss,
            "cuneiform": _cuneify.cuneify(s),
        }
        for s, gloss in samples
    ]

    @app.route("/")
    def index() -> str:
        return render_template(
            "www.html",
            stats=app.config["CORPUS_STATS"],
            samples=app.config["CUNEIFORM_SAMPLES"],
        )

    # Health endpoint for the compose healthcheck.
    @app.route("/healthz")
    def healthz() -> tuple[str, int]:
        return "ok", 200

    return app


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=5057)
    parser.add_argument("--debug", action="store_true")
    args = parser.parse_args()
    create_app().run(host=args.host, port=args.port, debug=args.debug)
