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

import ijson

from eme_gir.paths import TEXT_INDEX_DB

# Project prefix may be multi-level (e.g. "eme-gir/admin/ur3/corpusjson/P12345.json")
# so we capture everything up to "/corpusjson/" — that prefix is exactly the
# project path used in the glossary's word_ref strings.
#
# Index BOTH P-ids (physical tablets) AND Q-ids (composite editions). Q-ids
# are common for literary / hymn texts where multiple manuscripts have been
# merged into a single critical edition; the glossary cites them just like
# P-ids in word_refs.
CORPUSJSON_RE = re.compile(r"^(.+)/corpusjson/([PQ]\d+)\.json$")
CATALOGUE_RE = re.compile(r"^(.+)/catalogue\.json$")

SCHEMA = """
CREATE TABLE text_locations (
    project     TEXT NOT NULL,      -- glossary-style path, e.g., "rinap" or "eme-gir/admin/ur3"
    text_id     TEXT NOT NULL,      -- e.g., "P405162"
    zip_path    TEXT NOT NULL,      -- relative path to the project zip
    member_path TEXT NOT NULL,      -- full path inside the zip
    period      TEXT,               -- attestation period from project catalogue (e.g., "Ur III", "Old Babylonian")
    designation TEXT,               -- publication-style citation (e.g., "YOS 14, 341")
    PRIMARY KEY (project, text_id)
) WITHOUT ROWID;

CREATE INDEX idx_text_locations_text_id ON text_locations(text_id);
CREATE INDEX idx_text_locations_period  ON text_locations(period);
"""


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--corpus", default="corpus", help="folder containing the project zips")
    ap.add_argument("--db", default=str(TEXT_INDEX_DB), help="output SQLite path")
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
        catalogue_members: dict[str, str] = {}  # project -> catalogue.json member path
        with zipfile.ZipFile(zp) as z:
            for name in z.namelist():
                m = CORPUSJSON_RE.match(name)
                if m:
                    project, text_id = m.groups()
                    rows.append([project, text_id, str(zp), name, None, None])
                    continue
                m = CATALOGUE_RE.match(name)
                if m:
                    catalogue_members[m.group(1)] = name

            # Stream-read each project's catalogue.json for period + designation.
            # Catalogues can be 100MB+ (eme-gir itself is 76MB), so use ijson.kvitems
            # to stay constant-memory.
            cat_meta: dict[tuple[str, str], tuple[str | None, str | None]] = {}
            for proj, member in catalogue_members.items():
                try:
                    with z.open(member) as f:
                        for tid, meta in ijson.kvitems(f, "members"):
                            if isinstance(meta, dict):
                                cat_meta[(proj, tid)] = (
                                    meta.get("period"),
                                    meta.get("designation"),
                                )
                except (KeyError, ijson.JSONError):
                    pass

        # Splice catalogue metadata onto rows
        for r in rows:
            r[4], r[5] = cat_meta.get((r[0], r[1]), (None, None))

        if rows:
            cur.executemany(
                "INSERT OR IGNORE INTO text_locations VALUES (?,?,?,?,?,?)", rows
            )
            inserted = cur.rowcount
            dupes += len(rows) - inserted
            con.commit()
            with_period = sum(1 for r in rows if r[4])
            print(f"  {zp.name:<40} {len(rows):>6,} texts ({inserted:,} new, {with_period:,} with period)")
            total += inserted

    con.close()

    print(
        f"\n✨ {db_path} built: {total:,} unique texts "
        f"({dupes:,} duplicates skipped) in {time.monotonic() - t0:.1f}s"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
