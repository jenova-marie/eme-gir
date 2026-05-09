#!/usr/bin/env python3
"""Index every corpusjson/P*.json across all zips in corpus/.

Lets us answer "given text_id P405162, which zip + member do I open?"
in O(log n) instead of opening 208 zips per query. Output: ~ a few MB
of SQLite, built in seconds.
"""

from __future__ import annotations

import argparse
import re
import sqlite3
import sys
import time
import zipfile
from pathlib import Path

# Project prefix may be multi-level (e.g. "epsd2/admin/ur3/corpusjson/P12345.json")
# so we capture everything up to "/corpusjson/" — that prefix is exactly the
# project path used in the glossary's word_ref strings.
CORPUSJSON_RE = re.compile(r"^(.+)/corpusjson/(P\d+)\.json$")

SCHEMA = """
CREATE TABLE text_locations (
    project     TEXT NOT NULL,      -- glossary-style path, e.g., "rinap" or "epsd2/admin/ur3"
    text_id     TEXT NOT NULL,      -- e.g., "P405162"
    zip_path    TEXT NOT NULL,      -- relative path to the project zip
    member_path TEXT NOT NULL,      -- full path inside the zip
    PRIMARY KEY (project, text_id)
) WITHOUT ROWID;

CREATE INDEX idx_text_locations_text_id ON text_locations(text_id);
"""


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--corpus", default="corpus", help="folder containing the project zips")
    ap.add_argument("--db", default="text_index.sqlite", help="output SQLite path")
    args = ap.parse_args()

    corpus = Path(args.corpus)
    if not corpus.is_dir():
        print(f"corpus folder not found at {corpus}", file=sys.stderr)
        return 1

    db_path = Path(args.db)
    if db_path.exists():
        db_path.unlink()

    con = sqlite3.connect(db_path)
    con.executescript("PRAGMA journal_mode=OFF; PRAGMA synchronous=OFF;")
    con.executescript(SCHEMA)

    zips = sorted(corpus.glob("*.zip"))
    print(f"Scanning {len(zips)} zips for corpusjson/ entries ...\n")
    t0 = time.monotonic()
    total = 0
    dupes = 0
    cur = con.cursor()

    for zp in zips:
        rows = []
        with zipfile.ZipFile(zp) as z:
            for name in z.namelist():
                m = CORPUSJSON_RE.match(name)
                if m:
                    project, text_id = m.groups()
                    rows.append((project, text_id, str(zp), name))
        if rows:
            # OR IGNORE keeps the first hit deterministically (sorted zip iter).
            # Different sub-projects can hold the same P-id under different
            # project paths; the (project, text_id) PK preserves both.
            cur.executemany(
                "INSERT OR IGNORE INTO text_locations VALUES (?,?,?,?)", rows
            )
            inserted = cur.rowcount
            dupes += len(rows) - inserted
            con.commit()
            print(f"  {zp.name:<40} {len(rows):>6,} texts ({inserted:,} new)")
            total += inserted

    con.close()

    print(
        f"\n✨ {db_path} built: {total:,} unique texts "
        f"({dupes:,} duplicates skipped) in {time.monotonic() - t0:.1f}s"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
