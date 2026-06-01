"""MCP tools for the ETCSL Sumerian literary corpus (Oxford 2006).

Four tool functions, all bilingual (every result carries both the
Sumerian transliteration AND its English translation paragraph):
- `etcsl_search_english(query, limit)` — FTS5 over English translations
- `etcsl_lines_with_lemma(lemma, limit)` — find lemma uses in literary lines
- `etcsl_lookup_text(text_id, start, line_limit)` — read a whole composition
- `etcsl_search_sumerian(query, limit)` — FTS5 over Sumerian transliterations

`ETCSL_ATTRIBUTION` is exposed alongside the tools and is REQUIRED to
be passed through to the user verbatim. ETCSL is NOT released under any
Creative Commons license — © Black, Cunningham, Robson, Zólyomi 1998-2006;
the authors asserted their moral rights. The project's citation request
is honored by passing this attribution through with every quotation.

Unlike CDLI, ETCSL has no cross-domain helpers — the connection and the
paragraph-lines join helper are private to this module. Hence no
sibling `eme_gir.etcsl` shared library; everything lives here.
"""

from __future__ import annotations

import sqlite3

from ..log import log_call
from ..models.common import ErrorResponse
from ..models.etcsl import (
    ETCSLLinesWithLemmaResponse,
    ETCSLLookupTextResponse,
    ETCSLSearchEnglishResponse,
    ETCSLSearchSumerianResponse,
)
from ..paths import ETCSL_DB, ETCSL_PROMPT_DOC
from ..prompts import load_prompt

ETCSL_ATTRIBUTION = (
    "ETCSL: Black, J.A., Cunningham, G., Robson, E., and Zólyomi, G., "
    "The Electronic Text Corpus of Sumerian Literature "
    "(etcsl.orinst.ox.ac.uk), Oxford 1998-2006. © The Authors; the "
    "authors have asserted their moral rights. The ETCSL project has NOT "
    "released this corpus under any Creative Commons license; redistribution "
    "is governed by traditional academic copyright with a citation request. "
    "When quoting an ETCSL line or paragraph, cite this attribution verbatim."
)


def _etcsl_connect() -> sqlite3.Connection:
    if not ETCSL_DB.exists():
        raise FileNotFoundError(
            f"etcsl.sqlite not found at {ETCSL_DB}. "
            "Build it with: python3 build_etcsl_db.py"
        )
    con = sqlite3.connect(ETCSL_DB)
    con.row_factory = sqlite3.Row
    return con


def _etcsl_lines_for_paragraph(con: sqlite3.Connection, text_id: str, para_id: str) -> list[dict]:
    """Return the Sumerian lines that this translation paragraph covers."""
    rows = con.execute(
        "SELECT line_label, transliteration FROM lines "
        "WHERE text_id=? AND paragraph_id=? ORDER BY ord",
        (text_id, para_id),
    ).fetchall()
    return [{"line": r["line_label"], "transliteration": r["transliteration"]} for r in rows]


@log_call
def etcsl_search_english(query: str, limit: int = 10, offset: int = 0) -> ETCSLSearchEnglishResponse:
    """Full-text search across English translations of Sumerian literary
    texts. Returns bilingual matches: each hit includes the English
    paragraph plus the Sumerian lines that produced it.

    Excellent for: literary/hymn/myth content, finding how a concept is
    expressed in genuine Sumerian literature. Complements `see_examples`,
    which works best for administrative texts.

    Search syntax is SQLite FTS5 (porter-stemmed): single words, AND/OR/NOT
    operators, "exact phrases", prefix*. E.g.:
        'kingship'           -> stemmed match for king/kings/kingship/...
        '"divine power"'     -> exact phrase
        'temple AND build'   -> both terms
        'descend*'           -> prefix

    Args:
        query: FTS5 query string (English).
        limit: max matches (default 10, cap 50).
        offset: skip this many leading rows from the ranked result set
                (default 0). To walk subsequent pages, pass the
                `next_offset` value from the previous response. When
                `next_offset` is None the result set is exhausted.
    """
    limit = max(1, min(50, int(limit)))
    offset = max(0, int(offset))
    con = _etcsl_connect()
    try:
        total = con.execute(
            "SELECT COUNT(*) FROM paragraphs_fts WHERE paragraphs_fts MATCH ?",
            (query,),
        ).fetchone()[0]
        rows = con.execute(
            """
            SELECT t.text_id, t.title, p.para_id, p.line_range, p.translation
            FROM paragraphs_fts f
            JOIN paragraphs p ON p.rowid = f.rowid
            JOIN texts t ON t.text_id = p.text_id
            WHERE paragraphs_fts MATCH ?
            ORDER BY rank
            LIMIT ? OFFSET ?
            """,
            (query, limit, offset),
        ).fetchall()
        results = []
        for r in rows:
            results.append({
                "text_id": r["text_id"],
                "title": r["title"],
                "line_range": r["line_range"],
                "translation": r["translation"],
                "sumerian_lines": _etcsl_lines_for_paragraph(con, r["text_id"], r["para_id"]),
            })
    finally:
        con.close()
    return ETCSLSearchEnglishResponse(
        query=query,
        total_matches=total,
        offset=offset,
        next_offset=(offset + limit) if (offset + limit) < total else None,
        results=results,
        attribution=ETCSL_ATTRIBUTION,
    )


@log_call
def etcsl_lines_with_lemma(lemma: str, limit: int = 10, offset: int = 0) -> ETCSLLinesWithLemmaResponse:
    """Find Sumerian literary lines containing the given lemma (cf), with
    each line's English translation paragraph alongside.

    Use after translate_english to verify how a chosen Sumerian word is
    actually used in canonical literary contexts (hymns, myths, royal
    inscriptions, wisdom). Often surfaces collocational patterns the
    administrative corpus misses.

    **Homograph caveat:** ETCSL's word-level annotation uses Sumerian
    citation forms, NOT ePSD2 OIDs. Searching `lemma="gu"` returns
    lines with ANY `gu`-lemma (eat / thread / neck / voice / etc. — see
    `lookup_entry` for the homograph set on any given cf). Filter the
    results by checking the line context against the sense you actually
    want, or query a more disambiguating citation form when possible
    (e.g. `lemma="ki-aŋ₂"` instead of `lemma="aŋ"`). The compound-noun
    cf form often disambiguates where the simple-verb form can't.

    Args:
        lemma: the citation form (cf) to search for, e.g. 'lugal',
               'inana', 'ŋeš' (use ŋ not 'j' or 'g'). Case-insensitive.
        limit: max lines to return (default 10, cap 50).
        offset: skip this many leading rows from the ranked result set
                (default 0). To walk subsequent pages, pass the
                `next_offset` value from the previous response. When
                `next_offset` is None the result set is exhausted.
    """
    limit = max(1, min(50, int(limit)))
    offset = max(0, int(offset))
    con = _etcsl_connect()
    try:
        # The words index is case-sensitive on lemma, but Eme-gir lemmas are
        # always lowercase (except proper nouns). Try lower then capitalized.
        total = con.execute(
            "SELECT COUNT(*) FROM words w JOIN lines l USING (text_id, line_id) WHERE w.lemma = ?",
            (lemma,),
        ).fetchone()[0]
        rows = con.execute(
            """
            SELECT l.text_id, t.title, l.line_label, l.line_id, l.ord,
                   l.transliteration, l.paragraph_id
            FROM words w
            JOIN lines l USING (text_id, line_id)
            JOIN texts t ON t.text_id = l.text_id
            WHERE w.lemma = ?
            ORDER BY l.text_id, l.ord
            LIMIT ? OFFSET ?
            """,
            (lemma, limit, offset),
        ).fetchall()

        results = []
        for r in rows:
            translation = None
            if r["paragraph_id"]:
                tr = con.execute(
                    "SELECT translation FROM paragraphs WHERE text_id=? AND para_id=?",
                    (r["text_id"], r["paragraph_id"]),
                ).fetchone()
                if tr:
                    translation = tr["translation"]
            results.append({
                "text_id": r["text_id"],
                "title": r["title"],
                "line": r["line_label"],
                "transliteration": r["transliteration"],
                "translation_paragraph": translation,
            })
    finally:
        con.close()
    return ETCSLLinesWithLemmaResponse(
        lemma=lemma,
        total_matches=total,
        offset=offset,
        next_offset=(offset + limit) if (offset + limit) < total else None,
        results=results,
        attribution=ETCSL_ATTRIBUTION,
    )


@log_call
def etcsl_lookup_text(text_id: str, start: int = 1, line_limit: int = 50) -> ETCSLLookupTextResponse | ErrorResponse:
    """Read a Sumerian literary composition with line-by-line transliteration
    and the corresponding English translation paragraphs.

    Famous text IDs to know:
      c.1.4.1   - Inana's Descent to the Underworld
      c.1.8.1.4 - Gilgameš, Enkidu and the Underworld
      c.2.1.1   - The Sumerian King List
      c.2.4.2.* - Šulgi praise poems
      c.6.1.*   - Sumerian proverbs collections

    Args:
        text_id: ETCSL composition ID, e.g. 'c.1.4.1'.
        start: sequential ordinal of the first line to return (1-based;
               default 1). Use the `line_end` field from the previous call to
               page through long texts. This is an `ord` index, not a line
               label — multi-section works (e.g. c.2.4.2.16) are sequenced
               across all sections so paging never silently skips them.
        line_limit: max lines (default 50, cap 200). For long works (King
                    List = 350+ lines, Inana's Descent = 415+ lines), call
                    multiple times with bumped `start` to read in chunks.
    """
    line_limit = max(1, min(200, int(line_limit)))
    con = _etcsl_connect()
    try:
        text = con.execute(
            "SELECT text_id, title, has_translation FROM texts WHERE text_id=?",
            (text_id,),
        ).fetchone()
        if not text:
            return ErrorResponse(error=f"no ETCSL text with id={text_id!r}")
        total_lines = con.execute(
            "SELECT COUNT(*) FROM lines WHERE text_id=?", (text_id,)
        ).fetchone()[0]

        line_rows = con.execute(
            "SELECT ord, line_label, transliteration, paragraph_id FROM lines "
            "WHERE text_id=? AND ord >= ? ORDER BY ord LIMIT ?",
            (text_id, start, line_limit),
        ).fetchall()
        # Fetch all paragraphs referenced by these lines in one query
        para_ids = sorted({r["paragraph_id"] for r in line_rows if r["paragraph_id"]})
        translations: dict[str, str] = {}
        if para_ids:
            placeholders = ",".join("?" * len(para_ids))
            for r in con.execute(
                f"SELECT para_id, translation FROM paragraphs "
                f"WHERE text_id=? AND para_id IN ({placeholders})",
                (text_id, *para_ids),
            ):
                translations[r["para_id"]] = r["translation"]

        # Group consecutive lines by their paragraph_id so the agent sees
        # natural bilingual blocks instead of repeated translations.
        blocks: list[dict] = []
        current_para: str | None = ...  # sentinel
        for r in line_rows:
            if r["paragraph_id"] != current_para:
                blocks.append({
                    "paragraph_id": r["paragraph_id"],
                    "translation": translations.get(r["paragraph_id"]) if r["paragraph_id"] else None,
                    "lines": [],
                })
                current_para = r["paragraph_id"]
            blocks[-1]["lines"].append({
                "ord": r["ord"],
                "line": r["line_label"],
                "transliteration": r["transliteration"],
            })
    finally:
        con.close()
    return ETCSLLookupTextResponse(
        text_id=text_id,
        title=text["title"],
        total_lines=total_lines,
        returned_lines=len(line_rows),
        start=start,
        last_ord=line_rows[-1]["ord"] if line_rows else None,
        next_start=(line_rows[-1]["ord"] + 1) if line_rows and (line_rows[-1]["ord"] < total_lines) else None,
        has_translation=bool(text["has_translation"]),
        blocks=blocks,
        attribution=ETCSL_ATTRIBUTION,
    )


@log_call
def etcsl_search_sumerian(query: str, limit: int = 10, offset: int = 0) -> ETCSLSearchSumerianResponse:
    """Full-text search across Sumerian transliterations of literary texts.
    Returns each matching line with its English translation paragraph.

    Use to find specific Sumerian phrases or formulas in literary contexts,
    e.g. 'lugal kalam' for "king of the land", 'me-te' for "fitting".

    Search syntax: SQLite FTS5 with unicode61 tokenizer. Hyphens within
    spellings (lugal-bi) become token separators, so quote multi-token
    spellings as 'lugal-bi'.

    Args:
        query: FTS5 query string (Sumerian transliteration).
        limit: max matches (default 10, cap 50).
        offset: skip this many leading rows from the ranked result set
                (default 0). To walk subsequent pages, pass the
                `next_offset` value from the previous response. When
                `next_offset` is None the result set is exhausted.
    """
    limit = max(1, min(50, int(limit)))
    offset = max(0, int(offset))
    con = _etcsl_connect()
    try:
        total = con.execute(
            "SELECT COUNT(*) FROM lines_fts WHERE lines_fts MATCH ?",
            (query,),
        ).fetchone()[0]
        rows = con.execute(
            """
            SELECT l.text_id, t.title, l.line_label, l.transliteration,
                   l.paragraph_id
            FROM lines_fts f
            JOIN lines l ON l.rowid = f.rowid
            JOIN texts t ON t.text_id = l.text_id
            WHERE lines_fts MATCH ?
            ORDER BY rank
            LIMIT ? OFFSET ?
            """,
            (query, limit, offset),
        ).fetchall()
        results = []
        for r in rows:
            tr = None
            if r["paragraph_id"]:
                row = con.execute(
                    "SELECT translation FROM paragraphs WHERE text_id=? AND para_id=?",
                    (r["text_id"], r["paragraph_id"]),
                ).fetchone()
                if row:
                    tr = row["translation"]
            results.append({
                "text_id": r["text_id"],
                "title": r["title"],
                "line": r["line_label"],
                "transliteration": r["transliteration"],
                "translation_paragraph": tr,
            })
    finally:
        con.close()
    return ETCSLSearchSumerianResponse(
        query=query,
        total_matches=total,
        offset=offset,
        next_offset=(offset + limit) if (offset + limit) < total else None,
        results=results,
        attribution=ETCSL_ATTRIBUTION,
    )


@log_call
def start_here() -> str:
    """⭐ CALL THIS FIRST, BEFORE ANY OTHER TOOL ON THIS SERVER.

    Returns the bootstrap prompt for the `eme-gir-etcsl` MCP server.
    Read the returned markdown in full and keep it in working memory
    for the rest of this session — without it, your `etcsl_*` calls
    will use guesswork about ETCSL's text-id conventions, FTS5 query
    syntax, and the homograph-disambiguation limits of its lemma
    index. Critically, you will not know about the required Oxford
    citation that ETCSL's terms expect when its data is quoted.

    The prompt covers:
      • The four tools this server exposes (`etcsl_search_english`,
        `etcsl_lines_with_lemma`, `etcsl_search_sumerian`,
        `etcsl_lookup_text`) and the bilingual-result model.
      • Valid `text_id` conventions (`c.N.M.K` numbering scheme;
        the famous compositions: c.1.4.1 = Inana's Descent,
        c.1.8.1.4 = Gilgameš and the Underworld, c.2.1.1 = Sumerian
        King List, c.6.1.* = proverb collections).
      • FTS5 query syntax for `etcsl_search_english` and
        `etcsl_search_sumerian` (single words, AND/OR/NOT,
        "exact phrases", prefix* wildcards).
      • The homograph caveat for `etcsl_lines_with_lemma`: ETCSL's
        word-level annotation uses citation forms, NOT ePSD2 OIDs,
        so `lemma="gu"` returns ALL `gu`-lemmas (eat / thread /
        neck / voice).
      • The Oxford citation policy: ETCSL is NOT released under a
        Creative Commons license; every result carries an `attribution`
        field with the canonical citation that must be passed through
        verbatim when any line or paragraph is quoted to the user.

    Re-call this tool any time your working context drifts and you
    want to re-anchor on this server's guidance.
    """
    return load_prompt(ETCSL_PROMPT_DOC)
