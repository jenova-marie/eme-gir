"""Build inflected_collocations.sqlite — case-aware + sense-aware n-grams.

Mirrors build_collocations.py but extracts FOUR fields per lemma instead
of one:
    cf    - citation form (from f.cf)
    gw    - guide-word / sense disambiguator (from f.gw)
    pos   - part of speech (from f.pos)
    case  - detected outermost case suffix from the visible spelling
            (via sumerian_morphology.peel_suffixes)

This lets find_phrase_pattern answer questions the cf-only index can't:
  - "every transitive clause where N-ergative + N-absolutive + V"
  - "lugal[king]" (specifically the king sense, not the plant homograph)
  - "any noun in locative followed by du₃ (build)"

Sense (gw) disambiguation lets us keep `lugal[king]` and `lugal[plant]`
separate even though they share cf="lugal". Case detection comes from
the same suffix peeler the MCP server's parse_phrase tool uses, so the
two surfaces (live agent query + corpus-mined index) stay consistent.

Output schema (data/inflected_collocations.sqlite):
    meta(key, value)                       build metadata
    inflected_ngrams(n, ngram, cf1..cf4,
                     gw1..gw4, pos1..pos4,
                     case1..case4, count)  case+sense-aware n-grams

The `ngram` column is a tab-separated composite key string used solely
as the table PK (`(n, ngram)`). The denormalized cfN/gwN/posN/caseN
columns are what callers actually filter on, and each has its own
index for fast pattern matching.

Run after build_text_index.py + build_glossary_db.py:
    python3 build_inflected_collocations.py
    # ~25-40 min over the full corpus
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

from eme_gir.paths import INFLECTED_COLLOCATIONS_DB, TEXT_INDEX_DB
from eme_gir.sumerian_morphology import outermost_case, peel_suffixes, strip_token


SCHEMA = """
CREATE TABLE meta (key TEXT PRIMARY KEY, value TEXT);

CREATE TABLE inflected_ngrams (
    n      INTEGER NOT NULL,
    ngram  TEXT    NOT NULL,    -- composite key (tab-joined per-slot tuples)
    cf1    TEXT NOT NULL,
    cf2    TEXT NOT NULL,
    cf3    TEXT,
    cf4    TEXT,
    gw1    TEXT,
    gw2    TEXT,
    gw3    TEXT,
    gw4    TEXT,
    pos1   TEXT,
    pos2   TEXT,
    pos3   TEXT,
    pos4   TEXT,
    case1  TEXT,
    case2  TEXT,
    case3  TEXT,
    case4  TEXT,
    count  INTEGER NOT NULL,
    PRIMARY KEY (n, ngram)
) WITHOUT ROWID;

CREATE INDEX idx_in_cf1     ON inflected_ngrams(cf1);
CREATE INDEX idx_in_cf2     ON inflected_ngrams(cf2);
CREATE INDEX idx_in_cf3     ON inflected_ngrams(cf3);
CREATE INDEX idx_in_cf4     ON inflected_ngrams(cf4);
CREATE INDEX idx_in_pos1_case1 ON inflected_ngrams(pos1, case1);
CREATE INDEX idx_in_pos2_case2 ON inflected_ngrams(pos2, case2);
CREATE INDEX idx_in_pos3_case3 ON inflected_ngrams(pos3, case3);
CREATE INDEX idx_in_pos4_case4 ON inflected_ngrams(pos4, case4);
CREATE INDEX idx_in_count   ON inflected_ngrams(count DESC);
"""


# One token in a per-line lemma sequence. Tuples are hashable so they
# work directly as Counter keys.
TokenTuple = tuple[str, str | None, str | None, str | None]
# Layout: (cf, gw, pos, case). gw/pos/case may be None.


def walk_cdl(node: Any) -> Iterator[dict]:
    """Depth-first walk over the cdl tree, yielding every node."""
    if not isinstance(node, dict):
        return
    yield node
    for child in node.get("cdl") or ():
        yield from walk_cdl(child)


def detect_case_from_frag(frag: str | None) -> str | None:
    """Run the suffix peeler over a visible spelling and return the
    outermost-case role, or None if no case suffix was detected.

    Returns None when:
      - frag is missing or empty (broken/unlemmatized word)
      - the peeler stripped only possessive/plural (no case bearer)
      - the peeler found nothing at all (zero-marked / bare)

    None semantically reads as "absolutive (implicit) or no case marker."
    """
    if not frag:
        return None
    cleaned = strip_token(frag)
    if not cleaned:
        return None
    _, suffixes = peel_suffixes(cleaned)
    return outermost_case(suffixes)


def extract_lemma_sequences(doc: dict) -> list[list[TokenTuple]]:
    """Return one list of (cf, gw, pos, case) tuples per line, in input
    order. Lines with fewer than 2 lemmas are skipped (can't form bigrams).

    Verbal tokens still get a case slot, but it'll usually be None
    because verb-final suffixes (-en, -e, -eš) aren't in the case
    table — the peeler skips them. That's intentional: agents shouldn't
    interpret None as "absolutive verb"; they should interpret it as
    "no nominal case marker detected." The verb's POS column carries
    the verb-ness signal.
    """
    sequences: list[list[TokenTuple]] = []
    current: list[TokenTuple] = []
    for node in walk_cdl(doc):
        n_type = node.get("node")
        if n_type == "d" and node.get("type") == "line-start":
            if len(current) >= 2:
                sequences.append(current)
            current = []
        elif n_type == "l":
            f = node.get("f")
            if not isinstance(f, dict):
                continue
            # Sumerian-only: the corpus is multilingual (Akkadian Amarna
            # letters, Hittite Ugarit tablets, etc.) but the suffix peeler
            # only knows Sumerian morphology. Indexing Akkadian here
            # would yield (cf, gw, pos, None) rows with no case signal —
            # noise that dilutes pattern queries. Skip non-Sumerian lang
            # tags. Lemmas without an explicit lang tag default through.
            lang = f.get("lang") or ""
            if lang and not lang.startswith("sux"):
                continue
            cf = f.get("cf")
            if not cf:
                continue
            gw = f.get("gw") or None       # None preserves NULL in SQLite
            pos = f.get("pos") or None
            case = detect_case_from_frag(node.get("frag"))
            current.append((cf, gw, pos, case))
    if len(current) >= 2:
        sequences.append(current)
    return sequences


def ngrams(seq: list[TokenTuple], n: int) -> Iterator[tuple[TokenTuple, ...]]:
    """Yield contiguous n-grams from a sequence of tokens."""
    for i in range(len(seq) - n + 1):
        yield tuple(seq[i : i + n])


def encode_ngram(tokens: tuple[TokenTuple, ...]) -> str:
    """Build the composite-key string for the (n, ngram) PK. Tab-separates
    per-slot tuples, pipe-separates within-slot fields. None becomes the
    empty string so the key stays a stable hash of the tuple."""
    parts = []
    for cf, gw, pos, case in tokens:
        parts.append(f"{cf}|{gw or ''}|{pos or ''}|{case or ''}")
    return "\t".join(parts)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--db", default=str(INFLECTED_COLLOCATIONS_DB), help="output SQLite path")
    ap.add_argument("--min-count", type=int, default=3,
                    help="drop n-grams with fewer than this many occurrences "
                         "(default 3). Lower → bigger index + more long-tail "
                         "rows; higher → smaller + only common patterns.")
    ap.add_argument("--max-n", type=int, default=4, choices=(2, 3, 4))
    ap.add_argument("--limit-texts", type=int, default=None,
                    help="for debugging: stop after processing N texts")
    args = ap.parse_args()

    if not TEXT_INDEX_DB.exists():
        print(f"text_index.sqlite missing at {TEXT_INDEX_DB}; "
              "run build_text_index.py first", file=sys.stderr)
        return 1

    db_path = Path(args.db)
    if db_path.exists():
        db_path.unlink()
    con = sqlite3.connect(db_path)
    con.executescript("PRAGMA journal_mode=OFF; PRAGMA synchronous=OFF;")
    con.executescript(SCHEMA)

    ti = sqlite3.connect(TEXT_INDEX_DB)
    locations = ti.execute(
        "SELECT zip_path, member_path FROM text_locations ORDER BY zip_path"
    ).fetchall()
    ti.close()
    if args.limit_texts:
        locations = locations[: args.limit_texts]
    print(f"Scanning {len(locations):,} corpusjson texts for inflected n-grams ...",
          flush=True)

    # Counters keyed by tuple of tokens (each token being a 4-tuple).
    # Memory budget: a single Counter for each n. Rough sizing for the
    # full corpus is well under 1 GB before filtering.
    ngram_counts: dict[int, Counter[tuple[TokenTuple, ...]]] = {
        n: Counter() for n in range(2, args.max_n + 1)
    }

    # Group by zip so we open each zip exactly once.
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
                    for n in range(2, args.max_n + 1):
                        if len(seq) >= n:
                            ngram_counts[n].update(ngrams(seq, n))
                texts_done += 1
                if texts_done % 5000 == 0:
                    rate = texts_done / (time.monotonic() - t0)
                    distinct = sum(len(c) for c in ngram_counts.values())
                    print(f"  {texts_done:>7,} texts ({rate:,.0f}/s, "
                          f"{distinct:,} distinct ngrams)", flush=True)
        finally:
            zf.close()

    elapsed = time.monotonic() - t0
    print(f"\nScan complete in {elapsed:.1f}s. "
          f"{texts_done:,} texts processed, {parse_failures:,} unreadable.\n")

    # Filter by min_count and bulk-insert.
    total_kept = 0
    total_dropped = 0
    print(f"Filtering at min-count={args.min_count} and inserting ...", flush=True)
    for n, counter in ngram_counts.items():
        before = len(counter)
        kept_rows = []
        for tokens, cnt in counter.items():
            if cnt < args.min_count:
                total_dropped += 1
                continue
            # Pad tuples shorter than 4 with Nones for the unused slots.
            padded = list(tokens) + [(None, None, None, None)] * (4 - len(tokens))
            row = [n, encode_ngram(tokens)]
            for cf, gw, pos, case in padded:
                row.extend([cf, gw, pos, case])
            # Rearrange to schema order: cf1..cf4, gw1..gw4, pos1..pos4, case1..case4.
            # Current order in row after extend: [n, ngram, cf1,gw1,pos1,case1, cf2,gw2,pos2,case2, ...]
            cfs   = [row[2 + 4*i + 0] for i in range(4)]
            gws   = [row[2 + 4*i + 1] for i in range(4)]
            poss  = [row[2 + 4*i + 2] for i in range(4)]
            cases = [row[2 + 4*i + 3] for i in range(4)]
            kept_rows.append([n, row[1]] + cfs + gws + poss + cases + [cnt])

        if kept_rows:
            con.executemany(
                "INSERT INTO inflected_ngrams "
                "(n, ngram, cf1, cf2, cf3, cf4, gw1, gw2, gw3, gw4, "
                "pos1, pos2, pos3, pos4, case1, case2, case3, case4, count) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                kept_rows,
            )
            con.commit()
        kept = len(kept_rows)
        total_kept += kept
        print(f"  n={n}: {kept:,} rows kept (of {before:,} distinct)", flush=True)

    con.executemany("INSERT OR REPLACE INTO meta VALUES (?, ?)", [
        ("source", "Oracc corpusjson + sumerian_morphology suffix peeler"),
        ("texts_scanned", str(texts_done)),
        ("parse_failures", str(parse_failures)),
        ("min_count", str(args.min_count)),
        ("max_n", str(args.max_n)),
        ("total_rows_kept", str(total_kept)),
        ("total_rows_dropped", str(total_dropped)),
        ("elapsed_s", f"{elapsed:.1f}"),
    ])
    con.commit()
    con.close()
    print(f"\nDone. Total {total_kept:,} rows in {db_path} "
          f"(dropped {total_dropped:,} below min-count).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
