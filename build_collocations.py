#!/usr/bin/env python3
"""Mine citation-form n-grams (idiomatic collocations) from every corpusjson
text we have, store counts in collocations.sqlite.

Each n-gram is a sequence of `cf` (citation form) values drawn from `l`
nodes inside a single line of a single text. Line boundaries are
respected — collocations are intra-line so they reflect actual phrasal
co-occurrence, not random adjacency across lines.

Output schema:
    unigrams(cf, count)                  per-lemma frequencies
    collocations(n, ngram, cf*, count)   bigrams, trigrams, 4-grams

Run: python3 build_collocations.py    (uses text_index.sqlite)
"""

from __future__ import annotations

import argparse
import json
import sqlite3
import sys
import time
import zipfile
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Iterator

from eme_gir.paths import COLLOCATIONS_DB, TEXT_INDEX_DB

SCHEMA = """
CREATE TABLE meta (key TEXT PRIMARY KEY, value TEXT);

CREATE TABLE unigrams (
    cf      TEXT PRIMARY KEY,
    count   INTEGER NOT NULL
) WITHOUT ROWID;

CREATE TABLE collocations (
    n       INTEGER NOT NULL,           -- 2, 3, or 4
    ngram   TEXT NOT NULL,              -- space-joined cfs (e.g. "lugal kalam")
    cf1     TEXT NOT NULL,
    cf2     TEXT NOT NULL,
    cf3     TEXT,                       -- null when n < 3
    cf4     TEXT,                       -- null when n < 4
    count   INTEGER NOT NULL,
    PRIMARY KEY (n, ngram)
) WITHOUT ROWID;
"""

INDEXES = [
    "CREATE INDEX idx_collocations_cf1   ON collocations(cf1)",
    "CREATE INDEX idx_collocations_cf2   ON collocations(cf2)",
    "CREATE INDEX idx_collocations_count ON collocations(count DESC)",
]


def walk_cdl(node: Any) -> Iterator[dict]:
    if not isinstance(node, dict):
        return
    yield node
    for child in node.get("cdl") or ():
        yield from walk_cdl(child)


def extract_lemma_sequences(doc: dict) -> list[list[str]]:
    """Return one list of cfs per line. Lines without lemmata are skipped."""
    sequences: list[list[str]] = []
    current: list[str] = []
    for node in walk_cdl(doc):
        n_type = node.get("node")
        if n_type == "d" and node.get("type") == "line-start":
            if len(current) >= 2:
                sequences.append(current)
            current = []
        elif n_type == "l":
            f = node.get("f")
            if isinstance(f, dict):
                cf = f.get("cf")
                if cf:
                    current.append(cf)
    if len(current) >= 2:
        sequences.append(current)
    return sequences


def ngrams(seq: list[str], n: int) -> Iterator[tuple[str, ...]]:
    for i in range(len(seq) - n + 1):
        yield tuple(seq[i : i + n])


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--db", default=str(COLLOCATIONS_DB), help="output SQLite path")
    ap.add_argument("--min-count", type=int, default=3,
                    help="drop n-grams with fewer than this many occurrences "
                         "across the whole corpus (default 3, keeps the index "
                         "small while preserving genuine collocations)")
    ap.add_argument("--max-n", type=int, default=4, choices=(2, 3, 4))
    ap.add_argument("--limit-texts", type=int, default=None,
                    help="for debugging: stop after processing N texts")
    args = ap.parse_args()

    if not TEXT_INDEX_DB.exists():
        print("text_index.sqlite missing; run build_text_index.py first", file=sys.stderr)
        return 1

    db_path = Path(args.db)
    if db_path.exists():
        db_path.unlink()
    con = sqlite3.connect(db_path)
    con.executescript("PRAGMA journal_mode=OFF; PRAGMA synchronous=OFF;")
    con.executescript(SCHEMA)

    # Pull every (zip, member) pair to scan
    ti = sqlite3.connect(TEXT_INDEX_DB)
    locations = ti.execute(
        "SELECT zip_path, member_path FROM text_locations ORDER BY zip_path"
    ).fetchall()
    ti.close()
    if args.limit_texts:
        locations = locations[: args.limit_texts]
    print(f"Scanning {len(locations):,} corpusjson texts ...", flush=True)

    unigram_counts: Counter[str] = Counter()
    # ngram_counts[n] is a Counter of tuples
    ngram_counts: dict[int, Counter[tuple[str, ...]]] = {
        n: Counter() for n in range(2, args.max_n + 1)
    }

    # Group by zip so we open each zip only once
    by_zip: dict[str, list[str]] = defaultdict(list)
    for zp, member in locations:
        by_zip[zp].append(member)

    t0 = time.monotonic()
    texts_done = 0
    parse_failures = 0
    for zp, members in by_zip.items():
        try:
            zf = zipfile.ZipFile(zp)
        except Exception as e:
            print(f"  WARN: cannot open {zp}: {e}", file=sys.stderr)
            continue
        try:
            for member in members:
                try:
                    with zf.open(member) as f:
                        doc = json.load(f)
                except (json.JSONDecodeError, KeyError, OSError):
                    parse_failures += 1
                    continue
                for seq in extract_lemma_sequences(doc):
                    unigram_counts.update(seq)
                    for n in range(2, args.max_n + 1):
                        if len(seq) >= n:
                            ngram_counts[n].update(ngrams(seq, n))
                texts_done += 1
                if texts_done % 5000 == 0:
                    rate = texts_done / (time.monotonic() - t0)
                    print(f"  {texts_done:>7,} texts ({rate:,.0f}/s, "
                          f"{len(unigram_counts):,} unigrams, "
                          f"{sum(len(c) for c in ngram_counts.values()):,} distinct ngrams)",
                          flush=True)
        finally:
            zf.close()

    print(f"\nScan complete in {time.monotonic() - t0:.1f}s. "
          f"{texts_done:,} texts processed, {parse_failures:,} unreadable.\n")

    # Persist unigrams
    print("Writing unigrams ...", flush=True)
    con.executemany(
        "INSERT INTO unigrams VALUES (?, ?)",
        unigram_counts.items(),
    )
    con.commit()
    print(f"  {len(unigram_counts):,} unigrams\n")

    # Persist collocations, filtering by min_count
    total_kept = 0
    for n, counter in ngram_counts.items():
        kept = [
            (n, " ".join(ng), ng[0], ng[1],
             ng[2] if n >= 3 else None,
             ng[3] if n >= 4 else None,
             c)
            for ng, c in counter.items() if c >= args.min_count
        ]
        print(f"  {n}-grams: {len(counter):,} distinct, {len(kept):,} kept (count >= {args.min_count})")
        if kept:
            con.executemany(
                "INSERT INTO collocations VALUES (?, ?, ?, ?, ?, ?, ?)", kept
            )
            con.commit()
            total_kept += len(kept)

    print("\nBuilding indexes ...")
    t1 = time.monotonic()
    for stmt in INDEXES:
        con.execute(stmt)
    con.commit()
    print(f"  done in {time.monotonic() - t1:.1f}s")

    con.executemany("INSERT OR REPLACE INTO meta VALUES (?, ?)", [
        ("texts_scanned", str(texts_done)),
        ("parse_failures", str(parse_failures)),
        ("unigrams", str(len(unigram_counts))),
        ("collocations", str(total_kept)),
        ("min_count", str(args.min_count)),
        ("max_n", str(args.max_n)),
        ("built_at", time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())),
    ])
    con.commit()

    print("Optimizing ...")
    con.executescript("PRAGMA journal_mode=WAL; ANALYZE; VACUUM;")
    con.close()

    final_mb = db_path.stat().st_size / 1024 / 1024
    print(f"\n{db_path} built: {final_mb:,.1f} MB ({total_kept:,} collocations kept)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
