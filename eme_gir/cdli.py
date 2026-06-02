"""Shared CDLI catalogue infrastructure used across MCP servers.

The CDLI tools themselves (lookup_artifact, find_artifacts) live in
eme_gir.tools.cdli — but the connection helper and the URL-enrichment
function are infrastructure used by other servers too:

- The ePSD2 server's see_examples and find_verb_form auto-splat
  `enrichment(p_id)` onto every AttestationLine so agents can offer
  "see the actual tablet" links to the user without an extra round-trip.
- A future Translator server could call enrichment() to add CDLI links
  to citations it generates from its own pipeline.

The split (shared library here, tools/cdli.py for the MCP tool surface)
mirrors the pattern already established by cuneify.py + future
tools/signs.py — domain-shared library code lives at the package root;
the MCP tool wrapper lives under tools/.

Both functions are cheap to call repeatedly; SQLite reuses the file
handle and the connection lifecycle is per-call (open → query → close).
"""

from __future__ import annotations

import sqlite3

from .attribution import CDLI_CITATION_SHORT, EPSD2_CITATION_SHORT
from .paths import (
    CDLI_ARTIFACT_URL,
    CDLI_DB,
    CDLI_LINEART_THUMB_URL,
    CDLI_LINEART_URL,
    CDLI_PHOTO_THUMB_URL,
    CDLI_PHOTO_URL,
)


def connect() -> sqlite3.Connection | None:
    """Open the CDLI catalogue SQLite. Returns None when the DB hasn't
    been built yet — callers should fall back to the catalogue-less
    code path. Cheap to call repeatedly; SQLite reuses the file handle."""
    if not CDLI_DB.exists():
        return None
    con = sqlite3.connect(CDLI_DB)
    con.row_factory = sqlite3.Row
    return con


def enrichment(p_id: str) -> dict | None:
    """Cheap CDLI lookup for see_examples / find_verb_form. Returns a
    dict of CDLI URL fields + museum metadata for one P-id, or None when
    CDLI doesn't know the artifact OR the catalogue isn't built.

    Kept narrow on purpose — see_examples shouldn't return the whole
    CDLI record per line; just the URLs and the museum bits agents
    most often want to display alongside an attestation. Tool code that
    needs the FULL artifact record should call lookup_artifact instead.
    """
    con = connect()
    if con is None:
        return None
    try:
        row = con.execute(
            "SELECT cdli_id, has_photo, has_lineart, museum_collection, museum_no "
            "FROM artifacts WHERE p_id=?",
            (p_id,),
        ).fetchone()
    finally:
        con.close()
    if not row:
        return None
    has_photo = bool(row["has_photo"])
    has_lineart = bool(row["has_lineart"])
    return {
        "cdli_url": CDLI_ARTIFACT_URL.format(cdli_id=row["cdli_id"]),
        "photo_url": CDLI_PHOTO_URL.format(p_id=p_id) if has_photo else None,
        "photo_thumb_url": CDLI_PHOTO_THUMB_URL.format(p_id=p_id) if has_photo else None,
        "lineart_url": CDLI_LINEART_URL.format(p_id=p_id) if has_lineart else None,
        "lineart_thumb_url": CDLI_LINEART_THUMB_URL.format(p_id=p_id) if has_lineart else None,
        "museum_collection": row["museum_collection"],
        "museum_no": row["museum_no"],
    }


def attestation_markdown(line: dict) -> str:
    """Compose a pre-formatted block for one cited attestation line.

    Fuses the Sumerian transliteration + a CDLI artifact link + a DUAL
    short citation (ePSD2 for the line/lemma data, CDLI for the tablet
    catalogue/metadata) so attribution rides inside the quoted content
    rather than in a discardable sidecar field. `line` is the per-line
    dict built by see_examples / find_verb_form (already merged with the
    enrichment() fields), so CDLI keys may be absent when the artifact
    isn't in the catalogue.
    """
    translit = line.get("transliteration") or ""
    text_id = line.get("text_id") or ""
    line_label = line.get("line_label") or ""
    cdli_url = line.get("cdli_url")
    ref = f"[{text_id}]({cdli_url})" if cdli_url else text_id
    head = f"{ref} {line_label}".strip()
    loc = " · ".join(
        b
        for b in (
            line.get("designation"),
            line.get("period"),
            line.get("museum_collection"),
            line.get("museum_no"),
        )
        if b
    )
    cite = EPSD2_CITATION_SHORT + (
        f"; tablet metadata: {CDLI_CITATION_SHORT}" if cdli_url else ""
    )
    block = f"> {translit}".rstrip()
    if head:
        block += f"\n> — {head}" + (f" · {loc}" if loc else "")
    block += f"\n<sub>— line & lemma: {cite}</sub>"
    return block
