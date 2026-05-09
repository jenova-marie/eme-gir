"""MCP server exposing the local ePSD2 corpus for English -> Sumerian translation.

Five tools:
    translate_english(query, limit)        - rank Sumerian candidates for an English meaning
    lookup_entry(oid)                      - full structured view of a chosen lemma
    see_examples(oid, limit, period)       - real attested lines with the target marked
    find_compound(english_phrase)          - find idiomatic multi-word Sumerian
    cuneify(spelling)                      - render transliteration as Unicode cuneiform

One resource:
    oracc://grammar/sumerian               - compact Sumerian grammar cheat sheet
                                             (Edzard 2003); fetch once per session

Bias: every tool that returns lemma candidates returns BOTH icount (raw frequency
of *this sense*) and ipct (what % of the entry's total uses are this sense), so
the agent can distinguish "the word for X" from "X is one fringe meaning of this word".

Run: python3 mcp_server.py    (stdio transport)
Add to Claude Desktop / Code MCP config under "mcpServers"."""

from __future__ import annotations

import sqlite3
import sys
from pathlib import Path
from typing import Any

from mcp.server.fastmcp import FastMCP

import cuneify as _cuneify
import text_resolver

ROOT = Path(__file__).resolve().parent
GLOSSARY_DB = ROOT / "glossary.sqlite"
TEXT_INDEX_DB = ROOT / "text_index.sqlite"
GRAMMAR_DOC = ROOT / "SUMERIAN_GRAMMAR.md"

mcp = FastMCP("oracc-epsd2")


# -----------------------------------------------------------------------------
# DB helpers
# -----------------------------------------------------------------------------

def _connect() -> sqlite3.Connection:
    if not GLOSSARY_DB.exists():
        raise FileNotFoundError(
            f"glossary.sqlite not found at {GLOSSARY_DB}. "
            "Build it with: python3 build_glossary_db.py"
        )
    con = sqlite3.connect(GLOSSARY_DB)
    con.row_factory = sqlite3.Row
    return con


def _check_casefold_columns(con: sqlite3.Connection) -> None:
    """The Flask app's first run populates *_cf mirror columns. The MCP server
    needs them too — bail with a clear hint if they're missing rather than
    fabricate them silently with a UDF."""
    row = con.execute("SELECT value FROM meta WHERE key='casefold_version'").fetchone()
    if not row:
        raise RuntimeError(
            "glossary.sqlite is missing casefolded search columns. "
            "Run `python3 app.py` once first to populate them, then restart this server."
        )


def _entry_payload(con: sqlite3.Connection, row: sqlite3.Row) -> dict[str, Any]:
    """Build the standard 'entry candidate' shape returned by translate_english
    and friends. Keep it tight: just enough for an agent to decide whether to
    dig deeper with lookup_entry."""
    return {
        "oid": row["oid"],
        "cf": row["cf"],
        "gw": row["gw"],
        "pos": row["pos"],
        "sense": row["sense_mng"],
        "sense_count": row["sense_count"] or 0,
        "sense_pct": row["sense_pct"] or 0,
        "entry_total": row["entry_total"] or 0,
    }


# -----------------------------------------------------------------------------
# Tools
# -----------------------------------------------------------------------------

@mcp.tool()
def translate_english(query: str, limit: int = 10) -> dict:
    """Find Sumerian lemmas that mean a given English word or phrase.

    Returns ranked candidates with the matching SENSE inline (not just the
    headword), so the agent can distinguish "the word for X" from "X happens
    to be a fringe meaning of this word".

    Ranking: by absolute frequency of the matching sense (sense_count, DESC).
    `sense_pct` is what % of the entry's total uses are in this sense — a
    high sense_pct (e.g. 99%) means "this is essentially what the word means";
    a low sense_pct (e.g. 0%) means "tangential metaphorical extension only,
    probably not your translation".

    Returns:
        {
          "query": str,
          "results": [
            {
              "oid": "o0033341",
              "cf": "lugal", "gw": "king", "pos": "N",
              "sense": "king",
              "sense_count": 49818,    # how often this exact sense is attested
              "sense_pct": 100,        # of the entry's total uses, what % is this sense
              "entry_total": 49942,    # total attestations of the lemma overall
            },
            ...
          ],
          "total_matches": int,
        }

    Search hits BOTH the entry guide-word and the per-sense meaning, so e.g.
    "horn" finds both `si [horn]` (where it's the headword sense) and `a [arm]`
    (where it's a 0%-ipct fringe sense — visible but ranked low).
    """
    limit = max(1, min(50, int(limit)))
    needle = f"%{query.casefold().strip()}%"

    con = _connect()
    try:
        _check_casefold_columns(con)
        # Match against either the senses meaning or the entry's guide-word.
        # We surface the BEST matching sense per entry (the one with highest
        # icount that hits) so a polysemous entry only appears once.
        rows = con.execute(
            """
            WITH matched AS (
                SELECT s.entry_id, s.id AS sense_id, s.mng AS sense_mng,
                       s.icount AS sense_count, s.ipct AS sense_pct,
                       ROW_NUMBER() OVER (
                           PARTITION BY s.entry_id
                           ORDER BY s.icount DESC NULLS LAST
                       ) AS rk
                FROM senses s
                WHERE s.mng_cf LIKE ?
                UNION
                SELECT e.id AS entry_id, NULL AS sense_id, e.gw AS sense_mng,
                       e.icount AS sense_count, 100 AS sense_pct,
                       1 AS rk
                FROM entries e
                WHERE e.gw_cf LIKE ?
                  AND NOT EXISTS (SELECT 1 FROM senses s2
                                  WHERE s2.entry_id=e.id AND s2.mng_cf LIKE ?)
            ),
            best AS (
                SELECT * FROM matched WHERE rk=1
            )
            SELECT e.id AS oid, e.cf, e.gw, e.pos, e.icount AS entry_total,
                   b.sense_mng, b.sense_count, b.sense_pct
            FROM best b
            JOIN entries e ON e.id = b.entry_id
            ORDER BY b.sense_count DESC NULLS LAST, e.icount DESC NULLS LAST
            LIMIT ?
            """,
            (needle, needle, needle, limit),
        ).fetchall()

        total = con.execute(
            """
            SELECT COUNT(DISTINCT entry_id) FROM (
                SELECT entry_id FROM senses WHERE mng_cf LIKE ?
                UNION
                SELECT id AS entry_id FROM entries WHERE gw_cf LIKE ?
            )
            """,
            (needle, needle),
        ).fetchone()[0]
    finally:
        con.close()

    return {
        "query": query,
        "total_matches": total,
        "results": [_entry_payload(con, r) for r in rows],
    }


@mcp.tool()
def lookup_entry(oid: str) -> dict:
    """Get the full structured view of a single dictionary entry.

    Use after translate_english to drill into a chosen candidate. Returns:
        - headword (cf, gw, pos, total icount)
        - all senses with counts and percentages
        - top spellings (with cuneiform glyphs)
        - all time-period attestations
        - all see-compounds (idiomatic compounds containing this word)

    Args:
        oid: entry OID like 'o0033341' (returned by translate_english as 'oid').
    """
    con = _connect()
    try:
        entry = con.execute(
            "SELECT id, cf, gw, pos, icount, ipct, headword FROM entries WHERE id=?",
            (oid,),
        ).fetchone()
        if not entry:
            return {"error": f"no entry with oid={oid!r}"}

        senses = [dict(r) for r in con.execute(
            "SELECT id, mng AS meaning, pos, icount AS count, ipct AS pct "
            "FROM senses WHERE entry_id=? ORDER BY icount DESC NULLS LAST",
            (oid,),
        )]

        forms = []
        for r in con.execute(
            "SELECT n AS spelling, icount AS count, ipct AS pct "
            "FROM forms WHERE entry_id=? ORDER BY icount DESC NULLS LAST LIMIT 25",
            (oid,),
        ):
            forms.append({
                "spelling": r["spelling"],
                "count": r["count"] or 0,
                "pct": r["pct"] or 0,
                "cuneiform": _cuneify.cuneify(r["spelling"]),
            })

        periods = [dict(r) for r in con.execute(
            "SELECT p AS period, icount AS count, ipct AS pct "
            "FROM periods WHERE entry_id=? ORDER BY ord",
            (oid,),
        )]

        compounds = [dict(r) for r in con.execute(
            "SELECT xcpd AS compound, eref AS oid FROM compounds "
            "WHERE entry_id=? ORDER BY xcpd",
            (oid,),
        )]
    finally:
        con.close()

    return {
        "oid": entry["id"],
        "cf": entry["cf"],
        "gw": entry["gw"],
        "pos": entry["pos"],
        "headword": entry["headword"],
        "total_count": entry["icount"] or 0,
        "senses": senses,
        "spellings": forms,
        "periods": periods,
        "compounds": compounds,
    }


@mcp.tool()
def see_examples(oid: str, limit: int = 3, period: str | None = None) -> dict:
    """Show real attested Sumerian lines containing this lemma, with the
    target word highlighted. Use this to verify a translation choice or
    to cite primary-source evidence.

    Pulls from the corpusjson/ files inside our local Oracc zips (~92%
    of glossary refs resolve from local data). Each line includes the
    text P-id, line label (e.g. "obv. 3"), and the words in transliteration.

    Args:
        oid: entry OID
        limit: max number of unique lines to return (default 3, cap 20)
        period: optional period filter (e.g. "Ur III"). If set, only returns
                examples from texts of that period. NOT YET IMPLEMENTED — the
                period table is per-entry not per-attestation; ignored for now.

    Returns:
        {
          "oid": str,
          "lines": [
            {
              "text_id": "P347156", "project": "epsd2",
              "line_label": "o 34",
              "transliteration": "ŋa₂-e-gin₇-nam {d}en-ki lugal abzu-ke₄ ...",
              "target": "lugal",
              "target_position": 3,
            },
            ...
          ],
        }
    """
    limit = max(1, min(20, int(limit)))
    con = _connect()
    try:
        entry = con.execute(
            "SELECT cf, gw, xis FROM entries WHERE id=?", (oid,)
        ).fetchone()
        if not entry:
            return {"error": f"no entry with oid={oid!r}"}
        if not entry["xis"]:
            return {"oid": oid, "lines": [], "note": "entry has no instance refs"}
        word_refs = [
            r[0] for r in con.execute(
                "SELECT word_ref FROM instances WHERE xis=? LIMIT 500",
                (entry["xis"],),
            ).fetchall()
        ]
    finally:
        con.close()

    resolved = text_resolver.resolve_many(word_refs, limit=limit)
    lines: list[dict[str, Any]] = []
    for r in resolved:
        words = r["words"]
        target_pos = next(
            (i for i, w in enumerate(words) if w["is_target"]), None
        )
        target_frag = words[target_pos]["frag"] if target_pos is not None else None
        lines.append({
            "text_id": r["text_id"],
            "project": r["project"],
            "line_label": r["line_label"],
            "transliteration": " ".join(w["frag"] for w in words),
            "target": target_frag,
            "target_position": target_pos,
        })
    return {
        "oid": oid,
        "cf": entry["cf"],
        "gw": entry["gw"],
        "lines": lines,
    }


@mcp.tool()
def find_compound(english_phrase: str, limit: int = 10) -> dict:
    """Find Sumerian compound expressions matching an English phrase.

    Critical for translation because Sumerian uses fixed multi-word compounds
    for many concepts that English expresses as single verbs / phrases:
        "to spread the arms"  -> a bad
        "to bail water"        -> a bal [BAIL]
        "to pour out water"    -> a bala [POUR OUT WATER]
        "to draw water"        -> a bala (same)
        "in the presence of the king" -> lugal kura

    Searches across compound headwords AND English glosses of compound
    entries. Results have full entry info so the agent can immediately
    use the matched compound.

    Args:
        english_phrase: e.g. "build temple", "bail water", "swear oath"
        limit: max results (default 10, cap 25)
    """
    limit = max(1, min(25, int(limit)))
    needle = f"%{english_phrase.casefold().strip()}%"

    con = _connect()
    try:
        _check_casefold_columns(con)
        # A "compound entry" is one whose cf has a space (e.g. "a bad", "a bala").
        # We also surface entries that have see-compounds matching the phrase.
        rows = con.execute(
            """
            SELECT DISTINCT e.id AS oid, e.cf, e.gw, e.pos, e.icount AS entry_total
            FROM entries e
            WHERE instr(e.cf, ' ') > 0
              AND (e.gw_cf LIKE ?
                   OR EXISTS (SELECT 1 FROM senses s
                              WHERE s.entry_id=e.id AND s.mng_cf LIKE ?))
            ORDER BY e.icount DESC NULLS LAST
            LIMIT ?
            """,
            (needle, needle, limit),
        ).fetchall()
    finally:
        con.close()

    results = [dict(r) for r in rows]
    return {
        "query": english_phrase,
        "total_matches": len(results),
        "results": results,
    }


@mcp.tool()
def cuneify(spelling: str) -> dict:
    """Convert an Oracc-style Sumerian transliteration into Unicode cuneiform.

    Handles every spelling pattern in the corpus:
      - hyphen-joined sign sequences:  'lu₂-gal'         -> 𒇽𒃲
      - sign-list dot compounds:        'AB.GAR'
      - braced determinatives:          '{d}lugal'        -> 𒀭𒈗
                                        'lugal{mušen}'    -> 𒈗𒄷
      - whitespace-separated words:     'gu₃ mu-un-de₂'   -> 𒅗 𒈬𒌦…
      - morphology tails (\\X dropped): 'lugal-bi\\a'      -> 𒈗𒁉
      - compound graphemes:             'muₓ(|KA×GAN₂@t|)'-> uses the | … | inner

    Unknown signs render as □ (U+25A1) so the agent sees explicitly which
    parts didn't resolve. Use this as the final step after composing a
    translation, to render it in the script the original would have used.

    Args:
        spelling: transliteration like 'lugal-e e₂ mu-un-du₃'
    """
    glyphs = _cuneify.cuneify(spelling)
    has_placeholder = "□" in glyphs
    return {
        "spelling": spelling,
        "cuneiform": glyphs,
        "complete": not has_placeholder,
        "placeholder_count": glyphs.count("□"),
    }


# -----------------------------------------------------------------------------
# Resources
# -----------------------------------------------------------------------------

_GRAMMAR_CACHE: str | None = None


@mcp.resource(
    "oracc://grammar/sumerian",
    name="Sumerian grammar cheat sheet",
    title="Sumerian grammar (Edzard 2003) — compact reference",
    description=(
        "A scannable Sumerian grammar reference distilled from D. O. Edzard, "
        "Sumerian Grammar (Brill HdO 71, 2003). Covers transliteration "
        "conventions, SOV/ergative word order, the 10 noun cases with suffixes, "
        "possessive/demonstrative clitics, ḫamṭu vs marû verbal aspect, the "
        "verbal prefix chain, conjugation patterns 1/2a/2b, compound verbs, "
        "pronouns, conjunctions, period-flavor notes, and a 9-step "
        "translation workflow tailored to the tools in this server. Fetch "
        "this once per translation session and keep the rules in working memory."
    ),
    mime_type="text/markdown",
)
def grammar_cheatsheet() -> str:
    global _GRAMMAR_CACHE
    if _GRAMMAR_CACHE is None:
        if not GRAMMAR_DOC.exists():
            return (
                "# SUMERIAN_GRAMMAR.md missing\n\n"
                f"Expected at {GRAMMAR_DOC}. Re-run the project setup."
            )
        _GRAMMAR_CACHE = GRAMMAR_DOC.read_text(encoding="utf-8")
    return _GRAMMAR_CACHE


# -----------------------------------------------------------------------------
# Entrypoint
# -----------------------------------------------------------------------------

if __name__ == "__main__":
    # Sanity-check on startup so a misconfigured run fails loudly with a hint.
    if not GLOSSARY_DB.exists():
        print(
            f"glossary.sqlite missing at {GLOSSARY_DB}. "
            "Build it: `python3 build_glossary_db.py`",
            file=sys.stderr,
        )
        sys.exit(1)
    if not TEXT_INDEX_DB.exists():
        print(
            f"text_index.sqlite missing at {TEXT_INDEX_DB}. "
            "Build it: `python3 build_text_index.py`",
            file=sys.stderr,
        )
        sys.exit(1)
    mcp.run()
