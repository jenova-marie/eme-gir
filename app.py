"""Flask app that recreates Oracc's /epsd2/sux glossary browser from glossary.sqlite.

Usage:
    python3 app.py            # http://localhost:5050
    python3 app.py --port 8000

Routes:
    GET /                  -> redirect to /epsd2/sux
    GET /epsd2/sux         -> paginated glossary (supports ?page, ?zoom, ?q)
    GET /epsd2/<oid>       -> single entry detail
"""

from __future__ import annotations

import argparse
import re
import sqlite3
from pathlib import Path

from flask import Flask, abort, g, redirect, render_template, request, url_for

ROOT = Path(__file__).resolve().parent
DB_PATH = ROOT / "glossary.sqlite"

# Sumerian alphabet order (from index.html letter nav).
LETTER_ORDER = "ABCDEGŊHḪIKLMNOPRSṢŠTṬUWXYZ"
LETTER_INDEX = {ch: i for i, ch in enumerate(LETTER_ORDER)}
PER_PAGE = 25

# Search-helper substitutions documented on the Oracc search box:
#   j=ŋ  sz=š  s,=ṣ  t,=ṭ  0-9=₀-₉  '=ʾ
DIGIT_TO_SUB = str.maketrans("0123456789", "₀₁₂₃₄₅₆₇₈₉")
SEARCH_REPLACEMENTS = [("sz", "š"), ("s,", "ṣ"), ("t,", "ṭ"), ("j", "ŋ"), ("'", "ʾ")]


def normalize_query(q: str) -> str:
    q = q.strip()
    for src, dst in SEARCH_REPLACEMENTS:
        q = q.replace(src, dst)
    # turn trailing/embedded digits after a letter into subscripts: a2 -> a₂
    q = re.sub(r"(?<=[A-Za-zŋŠšḪḫṣṢṭṬʾ])(\d+)",
               lambda m: m.group(1).translate(DIGIT_TO_SUB), q)
    return q


def first_letter(cf: str) -> str:
    if not cf:
        return "?"
    c = cf[0].upper()
    return c if c in LETTER_INDEX else "?"


SORT_VERSION = "4"  # bump to force re-migration on next startup
DIGITS = "0123456789"
SUBSCRIPTS = "₀₁₂₃₄₅₆₇₈₉"


def sort_key(cf: str) -> str:
    """Sort key honoring Sumerian alphabet, case-insensitive.

    Order goal: 'a' < 'a aŋ' < 'aaba' < 'ab' < 'A.A' < 'A.AL' (matching Oracc).
    Word-level separators (space, hyphen, slash) sort BEFORE letters; sign-list
    separators ('.') and digits/subscripts sort AFTER letters. Empty < anything,
    so shorter prefixes sort first.

    Per-char encoding:
      space, '-', '/'  -> ' '             (0x20, before any letter)
      letter           -> 'NN' + ch       (NN = position in LETTER_ORDER, 00-26)
      digit, subscript -> '3D'            (after letters)
      '.'              -> '4'             (sign-list separator, after digits)
      other            -> '99' + ch       (oddities last)
    """
    out = []
    for ch in cf.lower():
        u = ch.upper()
        if u in LETTER_INDEX:
            out.append(f"{LETTER_INDEX[u]:02d}{ch}")
        elif ch in " -/":
            out.append(" ")
        elif ch in DIGITS:
            out.append(f"3{DIGITS.index(ch)}")
        elif ch in SUBSCRIPTS:
            out.append(f"3{SUBSCRIPTS.index(ch)}")
        elif ch == ".":
            out.append("4")
        else:
            out.append(f"99{ch}")
    return "".join(out)


def ensure_sort_columns(con: sqlite3.Connection) -> None:
    current = con.execute(
        "SELECT value FROM meta WHERE key='sort_version'"
    ).fetchone()
    if current and current[0] == SORT_VERSION:
        return
    print(f"Populating sort columns (version {SORT_VERSION}) ...")
    cols = {row[1] for row in con.execute("PRAGMA table_info(entries)")}
    if "letter" not in cols:
        con.execute("ALTER TABLE entries ADD COLUMN letter TEXT")
    if "sort_key" not in cols:
        con.execute("ALTER TABLE entries ADD COLUMN sort_key TEXT")
    rows = con.execute("SELECT id, cf FROM entries").fetchall()
    con.executemany(
        "UPDATE entries SET letter=?, sort_key=? WHERE id=?",
        [(first_letter(cf), sort_key(cf), oid) for oid, cf in rows],
    )
    con.execute("CREATE INDEX IF NOT EXISTS idx_entries_letter   ON entries(letter)")
    con.execute("CREATE INDEX IF NOT EXISTS idx_entries_sort_key ON entries(sort_key)")
    con.execute("INSERT OR REPLACE INTO meta VALUES ('sort_version', ?)", (SORT_VERSION,))
    con.commit()
    print("  done.")


def get_db() -> sqlite3.Connection:
    if "db" not in g:
        con = sqlite3.connect(DB_PATH)
        con.row_factory = sqlite3.Row
        g.db = con
    return g.db


def create_app() -> Flask:
    if not DB_PATH.exists():
        raise SystemExit(f"glossary.sqlite not found at {DB_PATH}. Run build_glossary_db.py first.")

    # Run the migration once on a dedicated connection.
    bootstrap = sqlite3.connect(DB_PATH)
    ensure_sort_columns(bootstrap)
    bootstrap.close()

    app = Flask(__name__)

    @app.teardown_appcontext
    def _close(_exc):
        db = g.pop("db", None)
        if db is not None:
            db.close()

    @app.context_processor
    def _ctx():
        return {"LETTER_ORDER": LETTER_ORDER}

    # ----- routes -----

    @app.route("/")
    def index():
        return redirect(url_for("glossary"))

    @app.route("/epsd2/sux")
    def glossary():
        db = get_db()
        page = max(1, int(request.args.get("page", 1)))
        zoom = request.args.get("zoom", "")
        raw_q = request.args.get("q", "")
        q = normalize_query(raw_q) if raw_q else ""

        where, params = [], []
        if q:
            where.append("(cf LIKE ? OR gw LIKE ?)")
            params += [f"%{q}%", f"%{q}%"]
        elif zoom and zoom in LETTER_INDEX:
            where.append("letter = ?")
            params.append(zoom)

        sql_where = ("WHERE " + " AND ".join(where)) if where else ""
        total = db.execute(f"SELECT COUNT(*) FROM entries {sql_where}", params).fetchone()[0]
        pages = max(1, (total + PER_PAGE - 1) // PER_PAGE)
        page = min(page, pages)
        offset = (page - 1) * PER_PAGE

        rows = db.execute(
            f"SELECT id, cf, gw, pos, icount FROM entries {sql_where} "
            "ORDER BY sort_key, gw LIMIT ? OFFSET ?",
            (*params, PER_PAGE, offset),
        ).fetchall()

        ids = [r["id"] for r in rows]
        forms_by_entry = _fetch_grouped(
            db, "SELECT entry_id, n FROM forms WHERE entry_id IN (%s) ORDER BY icount DESC",
            ids, key="entry_id", val="n",
        )
        senses_by_entry = _fetch_grouped(
            db, "SELECT entry_id, mng FROM senses WHERE entry_id IN (%s) "
                "AND mng IS NOT NULL AND mng <> '' ORDER BY icount DESC",
            ids, key="entry_id", val="mng",
        )
        periods_by_entry = _fetch_grouped(
            db, "SELECT entry_id, p FROM periods WHERE entry_id IN (%s) ORDER BY entry_id, ord",
            ids, key="entry_id", val="p",
        )

        return render_template(
            "glossary.html",
            entries=rows,
            forms_by_entry=forms_by_entry,
            senses_by_entry=senses_by_entry,
            periods_by_entry=periods_by_entry,
            total=total, page=page, pages=pages, zoom=zoom, q=raw_q, per_page=PER_PAGE,
        )

    @app.route("/epsd2/<oid>")
    def entry(oid: str):
        db = get_db()
        entry = db.execute(
            "SELECT id, headword, cf, gw, pos, icount, ipct, xis FROM entries WHERE id = ?",
            (oid,),
        ).fetchone()
        if not entry:
            abort(404)
        forms = db.execute(
            "SELECT n, icount, ipct FROM forms WHERE entry_id=? ORDER BY icount DESC",
            (oid,),
        ).fetchall()
        norms = db.execute(
            "SELECT n, icount, ipct FROM norms WHERE entry_id=? ORDER BY icount DESC",
            (oid,),
        ).fetchall()
        senses = db.execute(
            "SELECT id, n, mng, pos, icount, ipct FROM senses WHERE entry_id=? ORDER BY icount DESC",
            (oid,),
        ).fetchall()
        sense_sigs = {}
        if senses:
            sense_ids = [s["id"] for s in senses]
            placeholders = ",".join("?" * len(sense_ids))
            for row in db.execute(
                f"SELECT sense_id, sig, icount FROM sense_sigs "
                f"WHERE sense_id IN ({placeholders}) ORDER BY icount DESC",
                sense_ids,
            ):
                sense_sigs.setdefault(row["sense_id"], []).append(row)
        sample_instances = db.execute(
            "SELECT word_ref FROM instances WHERE xis=? LIMIT 50",
            (entry["xis"],),
        ).fetchall() if entry["xis"] else []
        periods = db.execute(
            "SELECT p, icount, ipct FROM periods WHERE entry_id=? ORDER BY ord", (oid,),
        ).fetchall()
        compounds = db.execute(
            "SELECT xcpd, eref FROM compounds WHERE entry_id=? ORDER BY xcpd", (oid,),
        ).fetchall()
        return render_template(
            "entry.html",
            entry=entry, forms=forms, norms=norms, senses=senses,
            sense_sigs=sense_sigs, sample_instances=sample_instances,
            periods=periods, compounds=compounds,
        )

    return app


def _fetch_grouped(db, sql_template, ids, *, key, val):
    if not ids:
        return {}
    placeholders = ",".join("?" * len(ids))
    grouped = {}
    for row in db.execute(sql_template % placeholders, ids):
        grouped.setdefault(row[key], []).append(row[val])
    return grouped


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--host", default="127.0.0.1")
    ap.add_argument("--port", type=int, default=5050)
    ap.add_argument("--debug", action="store_true")
    args = ap.parse_args()
    create_app().run(host=args.host, port=args.port, debug=args.debug)
