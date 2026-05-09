"""MCP server exposing the local ePSD2 corpus for English -> Sumerian translation.

Tools:
    translate_english(query, limit)        - rank Sumerian candidates for an English meaning
    translate_sumerian(transliteration)    - reverse: parse a Sumerian phrase into English glosses
    lookup_entry(oid)                      - full structured view of a chosen lemma
    see_examples(oid, limit, period)       - real attested lines with the target marked
    find_compound(english_phrase)          - find idiomatic multi-word Sumerian
    find_collocations(word, length, limit) - phrasal n-grams attested with a word
    get_inflections(oid)                   - attested morphological inflections of a lemma
    analyze_form(spelling)                 - decompose an attested form into base+morph
    lookup_sign(query)                     - find a cuneiform sign by name or phonetic value
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
COLLOCATIONS_DB = ROOT / "collocations.sqlite"
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
    text P-id, line label (e.g. "obv. 3"), the source publication
    designation if known (e.g. "YOS 14, 341"), the period the source
    text is dated to (e.g. "Ur III"), and the words in transliteration.

    Args:
        oid: entry OID
        limit: max number of unique lines to return (default 3, cap 20)
        period: optional period filter (e.g. "Ur III", "Old Babylonian",
                "Neo-Assyrian"). When set, only returns examples whose
                source text is dated to that period (substring match,
                case-insensitive — so "babylonian" matches both Old and
                Middle Babylonian). 85% of texts have period metadata.

    Returns:
        {
          "oid": str,
          "lines": [
            {
              "text_id": "P347156", "project": "epsd2",
              "line_label": "o 34",
              "designation": "YOS 14, 341",
              "period": "Old Babylonian",
              "transliteration": "ŋa₂-e-gin₇-nam {d}en-ki lugal abzu-ke₄ ...",
              "target": "lugal",
              "target_position": 3,
            },
            ...
          ],
        }
    """
    limit = max(1, min(20, int(limit)))
    period_needle = period.casefold().strip() if period else None

    con = _connect()
    try:
        entry = con.execute(
            "SELECT cf, gw, xis FROM entries WHERE id=?", (oid,)
        ).fetchone()
        if not entry:
            return {"error": f"no entry with oid={oid!r}"}
        if not entry["xis"]:
            return {"oid": oid, "lines": [], "note": "entry has no instance refs"}
        # Pull all refs upfront when filtering — small DB op, lets us slim
        # the resolve pass to only candidates from period-matching texts.
        ref_limit = 50000 if period_needle else 500
        word_refs = [
            r[0] for r in con.execute(
                "SELECT word_ref FROM instances WHERE xis=? LIMIT ?",
                (entry["xis"], ref_limit),
            ).fetchall()
        ]
    finally:
        con.close()

    if period_needle and TEXT_INDEX_DB.exists():
        # Pre-fetch all text_ids that match the period filter, then drop refs
        # whose source text isn't in the matching set. Avoids resolving (and
        # JSON-parsing) hundreds of irrelevant texts to find a few period hits.
        ti = sqlite3.connect(TEXT_INDEX_DB)
        try:
            matching = {
                row[0]: row[1]
                for row in ti.execute(
                    "SELECT text_id, period FROM text_locations "
                    "WHERE lower(period) LIKE ?",
                    (f"%{period_needle}%",),
                )
            }
        finally:
            ti.close()
        word_refs = [
            r for r in word_refs
            if (parsed := text_resolver.parse_word_ref(r))
            and parsed[1] in matching
        ]

    over_fetch_lines = max(limit * 4, 50) if period_needle else limit
    resolved = text_resolver.resolve_many(word_refs, limit=over_fetch_lines)
    lines: list[dict[str, Any]] = []
    for r in resolved:
        if period_needle:
            r_period = (r.get("period") or "").casefold()
            if period_needle not in r_period:
                continue
        words = r["words"]
        target_pos = next(
            (i for i, w in enumerate(words) if w["is_target"]), None
        )
        target_frag = words[target_pos]["frag"] if target_pos is not None else None
        lines.append({
            "text_id": r["text_id"],
            "project": r["project"],
            "line_label": r["line_label"],
            "designation": r.get("designation"),
            "period": r.get("period"),
            "transliteration": " ".join(w["frag"] for w in words),
            "target": target_frag,
            "target_position": target_pos,
        })
        if len(lines) >= limit:
            break
    return {
        "oid": oid,
        "cf": entry["cf"],
        "gw": entry["gw"],
        "period_filter": period,
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
def get_inflections(oid: str) -> dict:
    """Show every attested morphological breakdown of a lemma.

    For each kind of morphological data, returns the patterns/forms with
    their attestation counts. Use this to understand HOW a verb actually
    inflects in the corpus, before composing a new sentence — Sumerian
    inflection is too irregular to generate from rules; better to retrieve
    real attested patterns and adapt.

    Returned `kind` values:
      - "base": attested lemma forms (e.g., 'a₂', '{ŋeš}a₂', 'A-KU₄').
      - "morph": morphology pattern, '~' marks the base position.
                 e.g., 'mu.na:~' means prefix chain 'mu.na' + base;
                       'V.e:~' means generic vowel + 'e' prefix + base;
                       '~,bi.a' means base + 'bi' (3sg.nonp.poss) + 'a' (loc).
      - "morph2": alternative/secondary morphology analyses.
      - "stem": stems (verb-specific; often absent for nouns).
      - "prefix": just the verbal prefix chain (e.g., 'mu.na', 'V.e').
                  These map 1:1 to morph rows via xis.
      - "form-sans": attested concrete spelling for the morph pattern, with
                     determinatives written explicitly (e.g., 'mu-na-|A+KU₄|').
                     This is what you'd actually see in a tablet.

    Args:
        oid: entry OID (e.g., 'o0033341' for lugal).
    """
    con = _connect()
    try:
        entry = con.execute(
            "SELECT cf, gw, pos FROM entries WHERE id=?", (oid,)
        ).fetchone()
        if not entry:
            return {"error": f"no entry with oid={oid!r}"}
        rows = con.execute(
            "SELECT kind, n, icount, ipct, xis FROM morphology "
            "WHERE entry_id=? ORDER BY kind, icount DESC NULLS LAST",
            (oid,),
        ).fetchall()
    finally:
        con.close()
    by_kind: dict[str, list[dict]] = {}
    for r in rows:
        by_kind.setdefault(r["kind"], []).append({
            "n": r["n"],
            "count": r["icount"] or 0,
            "pct": r["ipct"] or 0,
            "xis": r["xis"],
        })
    return {
        "oid": oid,
        "cf": entry["cf"],
        "gw": entry["gw"],
        "pos": entry["pos"],
        "morphology": by_kind,
        "kinds": sorted(by_kind.keys()),
    }


@mcp.tool()
def analyze_form(spelling: str, limit: int = 20) -> dict:
    """Decompose an attested Sumerian spelling into its lemma and morphology.

    Searches across forms, form-sans (sandhi-resolved spellings), and bases
    for the input transliteration, returning every entry the spelling could
    belong to along with the morphological role it plays. Use this when
    reading Sumerian or to verify that a constructed inflection matches
    something actually attested.

    Returns matches grouped by entry, each with:
      - oid, cf, gw, pos: which lemma the spelling belongs to
      - matched_in: which table the hit came from (forms / morphology.base /
                    morphology.form-sans / morphology.morph)
      - count, pct, xis: attestation stats for this specific spelling

    Args:
        spelling: a transliterated Sumerian word, e.g. 'lugal-e', 'mu-na-du₃',
                  '{ŋeš}a₂'. Case-insensitive (Unicode-aware).
        limit: max matches to return (default 20, cap 50)
    """
    limit = max(1, min(50, int(limit)))
    needle = spelling.casefold().strip()

    con = _connect()
    try:
        rows = con.execute(
            """
            SELECT 'forms' AS source, e.id AS oid, e.cf, e.gw, e.pos,
                   f.n AS matched, f.icount AS count, f.ipct AS pct, f.xis
            FROM forms f JOIN entries e ON e.id = f.entry_id
            WHERE f.n_cf = ?
            UNION ALL
            SELECT 'morphology.' || m.kind AS source, e.id AS oid, e.cf, e.gw, e.pos,
                   m.n AS matched, m.icount AS count, m.ipct AS pct, m.xis
            FROM morphology m JOIN entries e ON e.id = m.entry_id
            WHERE lower(m.n) = lower(?)
              AND m.kind IN ('base', 'form-sans', 'morph')
            ORDER BY count DESC NULLS LAST
            LIMIT ?
            """,
            (needle, spelling, limit),
        ).fetchall()
    finally:
        con.close()
    return {
        "spelling": spelling,
        "matches": [{
            "matched_in": r["source"],
            "oid": r["oid"],
            "cf": r["cf"],
            "gw": r["gw"],
            "pos": r["pos"],
            "matched_text": r["matched"],
            "count": r["count"] or 0,
            "pct": r["pct"] or 0,
            "xis": r["xis"],
        } for r in rows],
    }


@mcp.tool()
def translate_sumerian(transliteration: str, limit_per_token: int = 3) -> dict:
    """Reverse-direction lookup: parse a Sumerian transliteration into per-token
    English glosses. Use this to verify a translation you composed, or to read
    a Sumerian phrase you encountered.

    Tokenizes on whitespace then splits each token on hyphens (sign joiners)
    and dots (sign-list compounds), strips braced determinatives, and looks
    up each piece against the glossary forms + form-sans tables. Returns ALL
    candidate lemmas per token (ranked by attestation count) so the agent
    can pick the contextually right one.

    Args:
        transliteration: a Sumerian phrase like "lugal-e e₂ mu-un-du₃"
        limit_per_token: max lemma candidates returned per token (default 3)
    """
    import re as _re

    # Tokenize: split on whitespace, then on - and . within each word.
    raw_tokens: list[str] = []
    for word in transliteration.split():
        # Strip braced determinatives — they're separate tokens
        cleaned = _re.sub(r"\{[^}]*\}", "", word).strip()
        if not cleaned:
            continue
        for piece in _re.split(r"[-.]", cleaned):
            piece = piece.strip("⸢⸣[](),;:!?")
            if piece and piece not in {"x", "X"}:
                raw_tokens.append(piece)

    con = _connect()
    try:
        results: list[dict[str, Any]] = []
        for tok in raw_tokens:
            needle_cf = tok.casefold()
            rows = con.execute(
                """
                SELECT DISTINCT e.id AS oid, e.cf, e.gw, e.pos,
                       e.icount AS entry_total
                FROM entries e
                LEFT JOIN forms f ON f.entry_id = e.id
                LEFT JOIN morphology m ON m.entry_id = e.id
                                       AND m.kind IN ('base', 'form-sans')
                WHERE e.cf_cf = ? OR f.n_cf = ? OR lower(m.n) = ?
                ORDER BY e.icount DESC NULLS LAST
                LIMIT ?
                """,
                (needle_cf, needle_cf, needle_cf, limit_per_token),
            ).fetchall()
            results.append({
                "token": tok,
                "candidates": [{
                    "oid": r["oid"],
                    "cf": r["cf"],
                    "gw": r["gw"],
                    "pos": r["pos"],
                    "entry_total": r["entry_total"] or 0,
                } for r in rows],
            })
    finally:
        con.close()
    return {
        "transliteration": transliteration,
        "tokens": results,
    }


@mcp.tool()
def find_collocations(word: str, length: int | None = None, limit: int = 20) -> dict:
    """Find multi-word Sumerian collocations (idiomatic phrases) containing
    a given lemma. Mined from every corpusjson text in our local Oracc zips.

    These are PHRASAL idioms beyond what the lexical compounds table catches:
    things like 'lugal-ŋu₁₀' (vocative "my king"), 'lugal kalam-ma' (the
    standard "king of the land" formula), 'inim lugal' (the king's word),
    etc. Useful for translation: prefer attested formulas to syntactically
    correct but never-used constructions.

    Args:
        word: the lemma cf to search for (e.g. "lugal", "e₂", "diŋir").
              Searched against ALL positions in 2/3/4-grams.
        length: optional filter by n-gram length: 2, 3, or 4. None = all.
        limit: max results (default 20, cap 50)
    """
    if not COLLOCATIONS_DB.exists():
        return {
            "error": "collocations.sqlite not built; run `python3 build_collocations.py` first",
        }
    limit = max(1, min(50, int(limit)))

    where = ["(cf1=? OR cf2=? OR cf3=? OR cf4=?)"]
    params: list[Any] = [word, word, word, word]
    if length in (2, 3, 4):
        where.append("n=?")
        params.append(length)
    sql_where = "WHERE " + " AND ".join(where)

    con = sqlite3.connect(COLLOCATIONS_DB)
    con.row_factory = sqlite3.Row
    try:
        rows = con.execute(
            f"SELECT n, ngram, count FROM collocations {sql_where} "
            "ORDER BY count DESC LIMIT ?",
            (*params, limit),
        ).fetchall()
        # also pull unigram count of the word for context (MI-style intuition)
        ucount_row = con.execute(
            "SELECT count FROM unigrams WHERE cf=?", (word,)
        ).fetchone()
    finally:
        con.close()

    return {
        "word": word,
        "word_unigram_count": ucount_row["count"] if ucount_row else 0,
        "results": [{
            "n": r["n"],
            "ngram": r["ngram"],
            "count": r["count"],
        } for r in rows],
    }


@mcp.tool()
def lookup_sign(query: str, limit: int = 10) -> dict:
    """Look up a cuneiform sign by name (e.g. 'LUGAL') or phonetic value
    (e.g. 'lugal', 'lu₂', 'gal'), returning the Unicode glyph, sign name,
    and all phonetic values that map to that sign.

    Useful for: verifying which sign a transliteration syllable corresponds
    to; finding all phonetic readings of a logographic spelling; looking up
    a glyph the agent sees in attested text.

    Args:
        query: sign name or phonetic value
        limit: max matches (default 10, cap 30)
    """
    limit = max(1, min(30, int(limit)))
    lookup = _cuneify._load_lookup()

    # Lookup is cheap: search both literal and casefolded match.
    # We need access to the underlying OGSL doc for full sign metadata.
    # Reuse cuneify's loader logic.
    import zipfile
    import json
    if not _cuneify.OGSL_ZIP.exists():
        return {"error": "OGSL data missing — corpus/ogsl.zip not present"}
    with zipfile.ZipFile(_cuneify.OGSL_ZIP) as z, z.open(_cuneify.OGSL_MEMBER) as f:
        signs = json.load(f).get("signs", {})

    needle = query.strip()
    needle_lower = needle.casefold()
    results: list[dict[str, Any]] = []

    # Direct sign-name match (uppercase keys in signs dict)
    if needle in signs:
        s = signs[needle]
        results.append({
            "sign_name": needle,
            "glyph": s.get("utf8"),
            "uname": s.get("uname"),
            "hex": s.get("hex"),
            "values": s.get("values") or [],
            "matched_by": "sign_name",
        })

    # Value match (search all signs' values)
    for sign_name, s in signs.items():
        if len(results) >= limit:
            break
        for v in s.get("values") or ():
            if v == needle or v.casefold() == needle_lower:
                results.append({
                    "sign_name": sign_name,
                    "glyph": s.get("utf8"),
                    "uname": s.get("uname"),
                    "hex": s.get("hex"),
                    "values": s.get("values") or [],
                    "matched_by": f"value:{v}",
                })
                break

    # Dedupe (a name match might re-appear as a value match)
    seen = set()
    deduped = []
    for r in results:
        key = r["sign_name"]
        if key not in seen:
            seen.add(key)
            deduped.append(r)

    return {
        "query": query,
        "results": deduped[:limit],
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
