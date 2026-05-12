"""Build data/cdli.sqlite from the CDLI bulk catalogue.

Source: cdli_cat.csv from the cdli-gh/data GitHub mirror, pulled via
media.githubusercontent.com (the actual LFS blob, no git-lfs install
needed). ~147 MB CSV, 353,283 artifact rows × 64 columns. Last data
update was August 2022 — stale but acceptable for catalogue metadata
(provenience, museum, period don't change once an artifact is
excavated and accessioned).

What we ingest:
- The ~25 columns we actually use for filtering, display, and
  citation. The full 64-column CSV is bigger than we need; the curated
  subset keeps cdli.sqlite under ~75 MB.
- Indexes on the columns agents will most-commonly filter by:
  period, provenience, collection (museum), genre, language.

What we DON'T ingest:
- Photographs / line drawings — links built from the p_id at query
  time (see paths.CDLI_PHOTO_URL etc.); the bytes stay on cdli.earth.
- Free-text remarks columns we don't surface (date_remarks,
  surface_preservation, stratigraphic_level, etc.) — easy to add
  later if a use case appears.

License: CDLI catalogue data is released as CC0 public-domain. No
attribution required, but customary — we surface the cdli_url on
every artifact response so end users can navigate to the canonical
record.

Run:
    python3 build_cdli_db.py            # download + build
    python3 build_cdli_db.py --no-fetch # skip download if cached
"""

from __future__ import annotations

import argparse
import csv
import sqlite3
import ssl
import sys
import time
import urllib.request
from pathlib import Path

import certifi

from paths import CDLI_CSV, CDLI_CSV_URL, CDLI_DB

# Curated subset of CSV columns we actually want in the SQLite. Each
# tuple is (csv_column_name, sqlite_column_name) — we rename a few for
# clarity (e.g. 'collection' → 'museum_collection' so it's self-
# describing without context).
COLUMNS: list[tuple[str, str]] = [
    # Identity
    ("id_text", "_cdli_id_raw"),    # numeric id from CSV; we derive p_id from it
    ("composite_id", "composite_id"),  # Q-id if part of a reconstructed composite
    # Citation / publication
    ("designation", "designation"),
    ("primary_publication", "primary_publication"),
    ("publication_history", "publication_history"),
    ("citation", "citation"),
    # Period + dating
    ("period", "period"),
    ("period_remarks", "period_remarks"),
    ("accounting_period", "accounting_period"),
    ("dates_referenced", "dates_referenced"),
    # Provenience
    ("provenience", "provenience"),
    ("provenience_remarks", "provenience_remarks"),
    ("findspot_remarks", "findspot_remarks"),
    ("findspot_square", "findspot_square"),
    ("excavation_no", "excavation_no"),
    # Custody (museum)
    ("collection", "museum_collection"),
    ("museum_no", "museum_no"),
    ("accession_no", "accession_no"),
    # Classification
    ("genre", "genre"),
    ("subgenre", "subgenre"),
    ("language", "language"),
    ("material", "material"),
    ("object_type", "object_type"),
    # Physical
    ("height", "height"),
    ("width", "width"),
    ("thickness", "thickness"),
    ("condition_description", "condition_description"),
    ("object_remarks", "object_remarks"),
    # Image-availability flags (derive image URLs from these + p_id)
    ("photo_up", "_photo_up_raw"),    # boolean string in CSV
    ("lineart_up", "_lineart_up_raw"),
]


def _format_p_id(raw_id: str) -> str | None:
    """CDLI's CSV stores id_text as a bare integer string. Convert to
    the canonical 'P{nnnnnn}' form (zero-padded to 6 digits, matching
    what Oracc text references use). Returns None for missing/invalid."""
    s = (raw_id or "").strip()
    if not s.isdigit():
        return None
    return f"P{int(s):06d}"


def _truthy(s: str) -> int:
    """CSV boolean fields use '1'/'0', 'true'/'false', or empty. Coerce
    to 0/1 for SQLite (which has no native bool)."""
    s = (s or "").strip().lower()
    return 1 if s in {"1", "true", "t", "yes", "y"} else 0


def _norm(s: str | None) -> str | None:
    """Strip whitespace and turn empty strings into NULL so SQLite
    queries with `WHERE x IS NOT NULL` work as expected."""
    if s is None:
        return None
    s = s.strip()
    return s or None


def fetch_csv(url: str, dest: Path, force: bool = False) -> None:
    """Download cdli_cat.csv to dest if not already cached.

    The URL serves the LFS-managed blob via media.githubusercontent.com;
    no auth, no git-lfs needed. ~147 MB, takes ~15-60s depending on
    network."""
    if dest.exists() and not force:
        print(f"  ✓ {dest.name} already cached ({dest.stat().st_size:,} bytes)", flush=True)
        return
    print(f"  ↓ fetching {url}", flush=True)
    print(f"    → {dest}", flush=True)
    ctx = ssl.create_default_context(cafile=certifi.where())
    t0 = time.monotonic()
    with urllib.request.urlopen(url, context=ctx, timeout=300) as resp:
        total = int(resp.headers.get("Content-Length", 0))
        chunk_size = 1 << 16  # 64 KB
        downloaded = 0
        last_log = t0
        with open(dest, "wb") as out:
            while True:
                chunk = resp.read(chunk_size)
                if not chunk:
                    break
                out.write(chunk)
                downloaded += len(chunk)
                now = time.monotonic()
                if now - last_log >= 2.0 and total:
                    pct = 100 * downloaded / total
                    rate = downloaded / (now - t0) / (1024 * 1024)
                    print(
                        f"    {downloaded:>11,} / {total:,} bytes "
                        f"({pct:5.1f}%, {rate:.1f} MB/s)",
                        flush=True,
                    )
                    last_log = now
    print(
        f"  ✓ downloaded {downloaded:,} bytes in {time.monotonic() - t0:.1f}s",
        flush=True,
    )


def build_db(csv_path: Path, db_path: Path, batch: int = 5000) -> int:
    """Stream cdli_cat.csv into a fresh cdli.sqlite. Returns the row
    count ingested."""
    if db_path.exists():
        db_path.unlink()
    con = sqlite3.connect(db_path)
    con.executescript("""
        PRAGMA journal_mode = OFF;
        PRAGMA synchronous = OFF;
        PRAGMA temp_store = MEMORY;
    """)

    sqlite_cols = [sql for _, sql in COLUMNS if not sql.startswith("_")]
    cols_sql = ",\n  ".join(f"{c} TEXT" for c in sqlite_cols)
    con.execute(f"""
        CREATE TABLE artifacts (
          p_id TEXT PRIMARY KEY,
          cdli_id INTEGER NOT NULL,
          has_photo INTEGER NOT NULL DEFAULT 0,
          has_lineart INTEGER NOT NULL DEFAULT 0,
          {cols_sql}
        ) WITHOUT ROWID
    """)

    insert_sql = (
        "INSERT OR REPLACE INTO artifacts "
        f"(p_id, cdli_id, has_photo, has_lineart, {', '.join(sqlite_cols)}) "
        f"VALUES ({', '.join('?' * (4 + len(sqlite_cols)))})"
    )

    print(f"  ⤷ ingesting {csv_path.name} → {db_path.name}", flush=True)
    t0 = time.monotonic()
    n_total = 0
    n_skipped = 0
    buf: list[tuple] = []
    with open(csv_path, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        # Detect header drift early — if CDLI ever renames a column
        # we want a loud failure, not silent NULL ingestion.
        missing = [csv_col for csv_col, _ in COLUMNS if csv_col not in reader.fieldnames]
        if missing:
            raise SystemExit(
                f"  ✗ CDLI CSV is missing expected columns: {missing}.\n"
                f"  CDLI may have renamed fields. Inspect the CSV header "
                f"and update build_cdli_db.py COLUMNS."
            )
        for row in reader:
            p_id = _format_p_id(row.get("id_text", ""))
            if not p_id:
                n_skipped += 1
                continue
            cdli_id = int(row["id_text"])
            values: list[object] = [
                p_id,
                cdli_id,
                _truthy(row.get("photo_up", "")),
                _truthy(row.get("lineart_up", "")),
            ]
            for csv_col, sql_col in COLUMNS:
                if sql_col.startswith("_"):
                    continue
                values.append(_norm(row.get(csv_col, "")))
            buf.append(tuple(values))
            n_total += 1
            if len(buf) >= batch:
                con.executemany(insert_sql, buf)
                con.commit()
                buf.clear()
                if n_total % (batch * 10) == 0:
                    rate = n_total / (time.monotonic() - t0)
                    print(
                        f"    rows: {n_total:>7,}  ({rate:>6,.0f}/s)",
                        flush=True,
                    )
        if buf:
            con.executemany(insert_sql, buf)
            con.commit()

    print(f"  ✓ ingested {n_total:,} rows ({n_skipped:,} skipped, no id_text)", flush=True)

    print("  ⤷ building indexes ...", flush=True)
    for col in ("period", "provenience", "museum_collection", "genre", "language", "composite_id"):
        con.execute(f"CREATE INDEX idx_artifacts_{col} ON artifacts({col})")
    con.execute("ANALYZE")
    con.executescript("PRAGMA journal_mode = WAL;")
    con.close()

    elapsed = time.monotonic() - t0
    size_mb = db_path.stat().st_size / (1024 * 1024)
    print(f"  ✓ {db_path} ({size_mb:.1f} MB) in {elapsed:.1f}s", flush=True)
    return n_total


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--csv", type=Path, default=CDLI_CSV,
                    help=f"path to cdli_cat.csv (default: {CDLI_CSV})")
    ap.add_argument("--db", type=Path, default=CDLI_DB,
                    help=f"output SQLite path (default: {CDLI_DB})")
    ap.add_argument("--no-fetch", action="store_true",
                    help="skip the download step (use cached CSV)")
    ap.add_argument("--force-fetch", action="store_true",
                    help="re-download even if cached")
    args = ap.parse_args()

    if not args.no_fetch:
        fetch_csv(CDLI_CSV_URL, args.csv, force=args.force_fetch)
    elif not args.csv.exists():
        print(f"  ✗ --no-fetch but {args.csv} doesn't exist", file=sys.stderr)
        return 1

    build_db(args.csv, args.db)
    return 0


if __name__ == "__main__":
    sys.exit(main())
