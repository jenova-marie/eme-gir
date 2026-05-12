#!/usr/bin/env python3
"""Stream an Oracc gloss-{lang}.json file into a SQLite index.

Reads directly from inside a project zip (no extraction needed), uses ijson's
C backend for constant-memory parsing, and defers index creation until after
bulk insert for maximum throughput.

Default target: epsd2's gloss-sux.json (1.9 GB) inside corpus/epsd2.zip.
"""

from __future__ import annotations

import argparse
import sqlite3
import sys
import time
import zipfile
from pathlib import Path

import ijson

from eme_gir.paths import GLOSSARY_DB

SCHEMA = """
CREATE TABLE meta (key TEXT PRIMARY KEY, value TEXT);

CREATE TABLE entries (
    id       TEXT PRIMARY KEY,
    headword TEXT NOT NULL,
    cf       TEXT,
    gw       TEXT,
    pos      TEXT,
    icount   INTEGER,
    ipct     INTEGER,
    xis      TEXT
);

CREATE TABLE periods (
    entry_id TEXT NOT NULL,    -- which dictionary entry
    ord      INTEGER NOT NULL, -- position in the source list (0-based, preserves Oracc's display order)
    p        TEXT NOT NULL,    -- period name (e.g., "Ur III", "Old Babylonian")
    icount   INTEGER,
    ipct     INTEGER,
    xis      TEXT,
    PRIMARY KEY (entry_id, ord)
) WITHOUT ROWID;

CREATE TABLE compounds (
    entry_id TEXT NOT NULL,    -- the parent (simple) entry
    xcpd     TEXT NOT NULL,    -- compound headword text (e.g., "a aŋ[command]V/t")
    eref     TEXT,             -- target entry id of the compound
    PRIMARY KEY (entry_id, xcpd)
) WITHOUT ROWID;

CREATE TABLE morphology (
    cbd_id   TEXT PRIMARY KEY,    -- e.g., "o0023086.207"; globally unique within glossary
    entry_id TEXT NOT NULL,       -- the entry this morpheme belongs to
    kind     TEXT NOT NULL,       -- one of: morph, morph2, stem, base, prefix, form-sans
    n        TEXT NOT NULL,       -- the morpheme pattern (e.g., "~", "mu.na:~", "a₂", "{ŋeš}a₂", "mu-na-|A+KU₄|")
    icount   INTEGER,
    ipct     INTEGER,
    xis      TEXT
) WITHOUT ROWID;

CREATE TABLE forms (
    id       TEXT PRIMARY KEY,
    entry_id TEXT NOT NULL,
    n        TEXT NOT NULL,
    icount   INTEGER,
    ipct     INTEGER,
    xis      TEXT
);

CREATE TABLE norms (
    id       TEXT PRIMARY KEY,
    entry_id TEXT NOT NULL,
    n        TEXT NOT NULL,
    icount   INTEGER,
    ipct     INTEGER,
    xis      TEXT
);

CREATE TABLE senses (
    id       TEXT PRIMARY KEY,
    entry_id TEXT NOT NULL,
    n        TEXT,
    mng      TEXT,
    pos      TEXT,
    icount   INTEGER,
    ipct     INTEGER,
    xis      TEXT
);

CREATE TABLE sense_sigs (
    id        TEXT PRIMARY KEY,
    sense_id  TEXT NOT NULL,
    sig       TEXT NOT NULL,
    icount    INTEGER,
    ipct      INTEGER,
    xis       TEXT
);

CREATE TABLE instances (
    xis       TEXT NOT NULL,
    word_ref  TEXT NOT NULL,
    PRIMARY KEY (xis, word_ref)
) WITHOUT ROWID;
"""

INDEXES = [
    "CREATE INDEX idx_entries_cf       ON entries(cf)",
    "CREATE INDEX idx_entries_gw       ON entries(gw)",
    "CREATE INDEX idx_entries_pos      ON entries(pos)",
    "CREATE INDEX idx_entries_xis      ON entries(xis)",
    "CREATE INDEX idx_forms_entry      ON forms(entry_id)",
    "CREATE INDEX idx_forms_n          ON forms(n)",
    "CREATE INDEX idx_forms_xis        ON forms(xis)",
    "CREATE INDEX idx_norms_entry      ON norms(entry_id)",
    "CREATE INDEX idx_norms_n          ON norms(n)",
    "CREATE INDEX idx_senses_entry     ON senses(entry_id)",
    "CREATE INDEX idx_senses_mng       ON senses(mng)",
    "CREATE INDEX idx_sense_sigs_sense ON sense_sigs(sense_id)",
    "CREATE INDEX idx_sense_sigs_sig   ON sense_sigs(sig)",
    "CREATE INDEX idx_instances_ref    ON instances(word_ref)",
    "CREATE INDEX idx_periods_p        ON periods(p)",
    "CREATE INDEX idx_compounds_eref   ON compounds(eref)",
    "CREATE INDEX idx_morph_entry_kind ON morphology(entry_id, kind)",
    "CREATE INDEX idx_morph_kind_n     ON morphology(kind, n)",
    "CREATE INDEX idx_morph_xis        ON morphology(xis)",
]

BATCH = 5000


def to_int(v):
    if v is None or v == "":
        return None
    try:
        return int(v)
    except (TypeError, ValueError):
        return None


def open_stream(zip_path: Path | None, member: str | None, json_path: Path | None):
    """Return a context manager yielding a binary file-like object."""
    if zip_path:
        z = zipfile.ZipFile(zip_path)
        return z, z.open(member)
    return None, open(json_path, "rb")


def configure(con: sqlite3.Connection):
    con.executescript("""
        PRAGMA journal_mode = OFF;
        PRAGMA synchronous = OFF;
        PRAGMA temp_store = MEMORY;
        PRAGMA cache_size = -200000;
        PRAGMA locking_mode = EXCLUSIVE;
    """)


MORPH_FIELDS = (
    ("morphs",     "morph"),
    ("morph2s",    "morph2"),
    ("stems",      "stem"),
    ("bases",      "base"),
    ("prefixs",    "prefix"),
    ("form-sanss", "form-sans"),
)


def ingest_entries(con, stream, log_every: int) -> tuple[int, int, int, int, int, int, int, int]:
    e_buf, f_buf, n_buf, s_buf, sig_buf, p_buf, c_buf, m_buf = [], [], [], [], [], [], [], []
    n_e = n_f = n_n = n_s = n_sig = n_p = n_c = n_m = 0
    t0 = time.monotonic()

    cur = con.cursor()
    for entry in ijson.items(stream, "entries.item", use_float=True):
        eid = entry.get("id")
        if not eid:
            continue
        e_buf.append((
            eid,
            entry.get("headword", ""),
            entry.get("cf"),
            entry.get("gw"),
            entry.get("pos"),
            to_int(entry.get("icount")),
            to_int(entry.get("ipct")),
            entry.get("xis"),
        ))
        for ord_, period in enumerate(entry.get("periods") or ()):
            name = period.get("p") if isinstance(period, dict) else period
            if not name:
                continue
            p_buf.append((eid, ord_, name,
                          to_int(period.get("icount")) if isinstance(period, dict) else None,
                          to_int(period.get("ipct"))   if isinstance(period, dict) else None,
                          period.get("xis")            if isinstance(period, dict) else None))
        for cmpd in entry.get("see-compounds") or ():
            xcpd = cmpd.get("xcpd")
            if not xcpd:
                continue
            c_buf.append((eid, xcpd, cmpd.get("eref")))
        for json_field, kind in MORPH_FIELDS:
            for item in entry.get(json_field) or ():
                cbd_id = item.get("cbd_id")
                n_val = item.get("n")
                if not cbd_id or n_val is None:
                    continue
                m_buf.append((
                    cbd_id, eid, kind, n_val,
                    to_int(item.get("icount")),
                    to_int(item.get("ipct")),
                    item.get("xis"),
                ))
        for form in entry.get("forms") or ():
            fid = form.get("id")
            if not fid:
                continue
            f_buf.append((fid, eid, form.get("n", ""),
                          to_int(form.get("icount")), to_int(form.get("ipct")),
                          form.get("xis")))
        for norm in entry.get("norms") or ():
            nid = norm.get("id")
            if not nid:
                continue
            n_buf.append((nid, eid, norm.get("n", ""),
                          to_int(norm.get("icount")), to_int(norm.get("ipct")),
                          norm.get("xis")))
        for sense in entry.get("senses") or ():
            sid = sense.get("id")
            if not sid:
                continue
            s_buf.append((sid, eid, sense.get("n"), sense.get("mng"),
                          sense.get("pos"),
                          to_int(sense.get("icount")), to_int(sense.get("ipct")),
                          sense.get("xis")))
            for sig in sense.get("sigs") or ():
                sigid = sig.get("id")
                if not sigid:
                    continue
                sig_buf.append((sigid, sid, sig.get("sig", ""),
                                to_int(sig.get("icount")), to_int(sig.get("ipct")),
                                sig.get("xis")))

        n_e += 1
        if len(e_buf) >= BATCH:
            cur.executemany("INSERT OR IGNORE INTO entries    VALUES (?,?,?,?,?,?,?,?)",   e_buf)
            cur.executemany("INSERT OR IGNORE INTO forms      VALUES (?,?,?,?,?,?)",       f_buf)
            cur.executemany("INSERT OR IGNORE INTO norms      VALUES (?,?,?,?,?,?)",       n_buf)
            cur.executemany("INSERT OR IGNORE INTO senses     VALUES (?,?,?,?,?,?,?,?)",   s_buf)
            cur.executemany("INSERT OR IGNORE INTO sense_sigs VALUES (?,?,?,?,?,?)",       sig_buf)
            cur.executemany("INSERT OR IGNORE INTO periods    VALUES (?,?,?,?,?,?)",       p_buf)
            cur.executemany("INSERT OR IGNORE INTO compounds  VALUES (?,?,?)",             c_buf)
            cur.executemany("INSERT OR IGNORE INTO morphology VALUES (?,?,?,?,?,?,?)",     m_buf)
            n_f += len(f_buf); n_n += len(n_buf); n_s += len(s_buf); n_sig += len(sig_buf); n_p += len(p_buf); n_c += len(c_buf); n_m += len(m_buf)
            e_buf.clear(); f_buf.clear(); n_buf.clear(); s_buf.clear(); sig_buf.clear(); p_buf.clear(); c_buf.clear(); m_buf.clear()
            con.commit()
            if n_e % log_every == 0:
                rate = n_e / (time.monotonic() - t0)
                print(f"  entries: {n_e:>8,}  ({rate:,.0f}/s)", flush=True)

    if e_buf:
        cur.executemany("INSERT OR IGNORE INTO entries    VALUES (?,?,?,?,?,?,?,?)",   e_buf)
        cur.executemany("INSERT OR IGNORE INTO forms      VALUES (?,?,?,?,?,?)",       f_buf)
        cur.executemany("INSERT OR IGNORE INTO norms      VALUES (?,?,?,?,?,?)",       n_buf)
        cur.executemany("INSERT OR IGNORE INTO senses     VALUES (?,?,?,?,?,?,?,?)",   s_buf)
        cur.executemany("INSERT OR IGNORE INTO sense_sigs VALUES (?,?,?,?,?,?)",       sig_buf)
        cur.executemany("INSERT OR IGNORE INTO periods    VALUES (?,?,?,?,?,?)",       p_buf)
        cur.executemany("INSERT OR IGNORE INTO compounds  VALUES (?,?,?)",             c_buf)
        cur.executemany("INSERT OR IGNORE INTO morphology VALUES (?,?,?,?,?,?,?)",     m_buf)
        n_f += len(f_buf); n_n += len(n_buf); n_s += len(s_buf); n_sig += len(sig_buf); n_p += len(p_buf); n_c += len(c_buf); n_m += len(m_buf)
        con.commit()

    return n_e, n_f, n_n, n_s, n_sig, n_p, n_c, n_m


def ingest_instances(con, stream, log_every: int) -> int:
    cur = con.cursor()
    buf, total = [], 0
    t0 = time.monotonic()
    for xis, refs in ijson.kvitems(stream, "instances", use_float=True):
        for ref in refs or ():
            buf.append((xis, ref))
        if len(buf) >= BATCH * 4:
            cur.executemany("INSERT OR IGNORE INTO instances VALUES (?,?)", buf)
            total += len(buf)
            buf.clear()
            con.commit()
            if total and (total // (BATCH * 4)) % (log_every // (BATCH * 4) or 1) == 0:
                rate = total / (time.monotonic() - t0)
                print(f"  instance refs: {total:>10,}  ({rate:,.0f}/s)", flush=True)
    if buf:
        cur.executemany("INSERT OR IGNORE INTO instances VALUES (?,?)", buf)
        total += len(buf)
        con.commit()
    return total


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--zip", default="corpus/epsd2.zip",
                    help="zip archive to read from (default: corpus/epsd2.zip)")
    ap.add_argument("--member", default="epsd2/gloss-sux.json",
                    help="path inside the zip (default: epsd2/gloss-sux.json)")
    ap.add_argument("--json", help="alternative: read this loose JSON file directly")
    ap.add_argument("--db", default=str(GLOSSARY_DB), help="output SQLite path")
    ap.add_argument("--log-every", type=int, default=20000,
                    help="print progress every N entries (default: 20000)")
    args = ap.parse_args()

    db_path = Path(args.db)
    if db_path.exists():
        db_path.unlink()
    print(f"Building {db_path} ...", flush=True)

    con = sqlite3.connect(db_path)
    configure(con)
    con.executescript(SCHEMA)

    if args.json:
        zip_path, member = None, None
        json_path = Path(args.json)
        size = json_path.stat().st_size
        src_label = str(json_path)
    else:
        zip_path = Path(args.zip)
        member = args.member
        json_path = None
        with zipfile.ZipFile(zip_path) as z:
            info = z.getinfo(member)
            size = info.file_size
        src_label = f"{zip_path}::{member}"

    print(f"Source: {src_label}  ({size / 1024 / 1024:,.1f} MB uncompressed)\n")

    # Pass 1 — entries (and nested forms/norms/senses/sigs/compounds)
    print("Pass 1/2: entries")
    t0 = time.monotonic()
    z, stream = open_stream(zip_path, member, json_path)
    try:
        n_e, n_f, n_n, n_s, n_sig, n_p, n_c, n_m = ingest_entries(con, stream, args.log_every)
    finally:
        stream.close()
        if z:
            z.close()
    print(f"  -> {n_e:,} entries, {n_f:,} forms, {n_n:,} norms, "
          f"{n_s:,} senses, {n_sig:,} sigs, {n_p:,} period rows, "
          f"{n_c:,} compound refs, {n_m:,} morphology rows in "
          f"{time.monotonic() - t0:.1f}s\n")

    # Pass 2 — instances map
    print("Pass 2/2: instances")
    t0 = time.monotonic()
    z, stream = open_stream(zip_path, member, json_path)
    try:
        n_i = ingest_instances(con, stream, args.log_every)
    finally:
        stream.close()
        if z:
            z.close()
    print(f"  -> {n_i:,} instance refs in {time.monotonic() - t0:.1f}s\n")

    # Metadata
    con.executemany("INSERT OR REPLACE INTO meta VALUES (?,?)", [
        ("source", src_label),
        ("source_bytes", str(size)),
        ("entries", str(n_e)),
        ("forms", str(n_f)),
        ("norms", str(n_n)),
        ("senses", str(n_s)),
        ("sigs", str(n_sig)),
        ("periods", str(n_p)),
        ("compounds", str(n_c)),
        ("morphology", str(n_m)),
        ("instances", str(n_i)),
        ("ingested_at", time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())),
    ])
    con.commit()

    # Build indexes last (much faster than incremental)
    print("Building indexes ...")
    t0 = time.monotonic()
    for stmt in INDEXES:
        con.execute(stmt)
    con.commit()
    print(f"  -> done in {time.monotonic() - t0:.1f}s\n")

    print("Optimizing ...")
    con.executescript("PRAGMA journal_mode = WAL; ANALYZE; VACUUM;")
    con.close()

    final_mb = db_path.stat().st_size / 1024 / 1024
    print(f"\n✨ {db_path} built: {final_mb:,.1f} MB")
    return 0


if __name__ == "__main__":
    sys.exit(main())
