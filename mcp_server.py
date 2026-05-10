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
    find_verb_form(cf, pos, ...)           - attested verb forms matching a feature spec
                                             (prefix, dimensional infixes, object agreement, …)
    lookup_sign(query)                     - find a cuneiform sign by name or phonetic value
    cuneify(spelling)                      - render transliteration as Unicode cuneiform

ETCSL (Sumerian literary corpus + English translations) — Oxford 2006:
    etcsl_search_english(query, limit)     - FTS over English translations; returns bilingual lines
    etcsl_lines_with_lemma(lemma, limit)   - literary attestations of a Sumerian lemma + their English
    etcsl_lookup_text(text_id, line_range) - read a whole composition (e.g. c.1.4.1 = Inana's Descent)
    etcsl_search_sumerian(query, limit)    - FTS over Sumerian transliteration; returns bilingual lines

One resource:
    oracc://grammar/sumerian               - compact Sumerian grammar cheat sheet
                                             (Edzard 2003); fetch once per session

Bias: every tool that returns lemma candidates returns BOTH icount (raw frequency
of *this sense*) and ipct (what % of the entry's total uses are this sense), so
the agent can distinguish "the word for X" from "X is one fringe meaning of this word".

Run: python3 mcp_server.py    (stdio transport)
Add to Claude Desktop / Code MCP config under "mcpServers"."""

from __future__ import annotations

import functools
import logging
import os
import sqlite3
import sys
import time
from pathlib import Path
from typing import Any

from mcp.server.fastmcp import FastMCP

import cuneify as _cuneify
import text_resolver
from paths import (
    COLLOCATIONS_DB,
    ETCSL_DB,
    GLOSSARY_DB,
    GRAMMAR_DOC,
    MCP_SERVER_LOG as LOG_FILE,
    ROOT,
    TEXT_INDEX_DB,
)

ETCSL_ATTRIBUTION = (
    "ETCSL: Black, J.A. et al., The Electronic Text Corpus of Sumerian "
    "Literature (etcsl.orinst.ox.ac.uk), Oxford 1998-2006. CC BY 3.0 UK."
)

# Logs go to TWO places so they're visible no matter how the server is run:
#   - stderr (visible if launched directly: `python3 mcp_server.py 2>&1`)
#   - log/mcp_server.log (always — Claude Code discards stderr, so without
#     this file the logs would be invisible to its users; tail with
#     `tail -F log/mcp_server.log` while chatting with the agent).
# stdout is intentionally NOT a log target — it's reserved for the JSON-RPC
# protocol stream and any extra writes there would corrupt the connection.
_log_format = logging.Formatter(
    "%(asctime)s.%(msecs)03d [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
_root = logging.getLogger()
_root.setLevel(logging.INFO)
_stderr_h = logging.StreamHandler(sys.stderr)
_stderr_h.setFormatter(_log_format)
_root.addHandler(_stderr_h)
# Use a RotatingFileHandler so the log file doesn't grow unbounded across
# many sessions. 5 MB × 3 backups = ~15 MB ceiling.
from logging.handlers import RotatingFileHandler
_file_h = RotatingFileHandler(LOG_FILE, maxBytes=5 * 1024 * 1024, backupCount=3)
_file_h.setFormatter(_log_format)
_root.addHandler(_file_h)
log = logging.getLogger("epsd2")


def _log_call(fn):
    """Wrap a tool function so each invocation logs entry + exit + timing.

    Sits between @mcp.tool() and the bare function so FastMCP's pydantic
    schema sees the original signature (preserved by functools.wraps).
    """
    @functools.wraps(fn)
    def wrapper(*args, **kwargs):
        arg_bits = []
        for k, v in kwargs.items():
            r = repr(v)
            if len(r) > 60:
                r = r[:57] + "..."
            arg_bits.append(f"{k}={r}")
        log.info(f"→ {fn.__name__}({', '.join(arg_bits)})")
        t0 = time.monotonic()
        try:
            result = fn(*args, **kwargs)
        except Exception as e:
            elapsed = (time.monotonic() - t0) * 1000
            log.exception(
                f"  ✗ {fn.__name__} ({elapsed:.0f}ms) raised "
                f"{type(e).__name__}: {e}"
            )
            raise
        elapsed = (time.monotonic() - t0) * 1000
        # Summarize the result shape concisely so logs stay scannable.
        summary = ""
        if isinstance(result, dict):
            if "error" in result:
                summary = f" ⚠ ERROR: {str(result['error'])[:80]}"
            elif "results" in result and isinstance(result["results"], list):
                summary = f" → {len(result['results'])} results"
                if "total_matches" in result:
                    summary += f" (of {result['total_matches']} total)"
            elif "lines" in result and isinstance(result["lines"], list):
                summary = f" → {len(result['lines'])} lines"
                if result.get("period_filter"):
                    summary += f" [period={result['period_filter']!r}]"
            elif "matches" in result and isinstance(result["matches"], list):
                summary = f" → {len(result['matches'])} matches"
            elif "tokens" in result and isinstance(result["tokens"], list):
                summary = f" → {len(result['tokens'])} tokens"
            elif "cuneiform" in result:
                cu = result["cuneiform"]
                summary = f" → {cu[:40]}"
                if not result.get("complete", True):
                    summary += f" ({result.get('placeholder_count', 0)} □)"
            elif "morphology" in result:
                kinds = result.get("kinds") or []
                counts = {k: len(result["morphology"][k]) for k in kinds}
                summary = f" → {counts}"
            elif "spellings" in result:
                summary = (
                    f" → {result.get('cf','?')} [{result.get('gw','?')}], "
                    f"{len(result['spellings'])} spellings, "
                    f"{len(result.get('senses', []))} senses"
                )
        log.info(f"  ← {fn.__name__} ({elapsed:.0f}ms){summary}")
        return result
    return wrapper

def _build_auth_kwargs() -> dict:
    """Read EPSD2_AUTH0_* env vars and return auth/token_verifier kwargs.

    Returns an empty dict (auth disabled) unless EPSD2_REQUIRE_AUTH=1.
    When enabled, returns {'auth': AuthSettings, 'token_verifier': Auth0TokenVerifier}
    suitable for splatting into the FastMCP constructor.

    Auth is OPT-IN and only meaningful for the streamable-HTTP transport;
    stdio runs unauthenticated regardless (per MCP spec, stdio uses
    environment-based credentials, not OAuth). The transport check
    happens at run() time — if EPSD2_REQUIRE_AUTH=1 is set but stdio is
    selected, the constructed verifier sits idle, which is harmless.

    Required env vars when EPSD2_REQUIRE_AUTH=1:
        EPSD2_AUTH0_TENANT_URL          e.g. https://my-tenant.auth0.com
        EPSD2_AUTH0_AUDIENCE            e.g. https://epsd2.example.com
        EPSD2_AUTH0_RESOURCE_SERVER_URL e.g. https://epsd2.example.com
                                        (the public-facing URL of THIS
                                        server; goes into the RFC 9728
                                        Protected Resource Metadata)
    Optional:
        EPSD2_AUTH0_REQUIRED_SCOPE      defaults to 'mcp:access'
    """
    # Accept the conventional set of truthy strings so operators don't have
    # to remember our exact magic string. Anything not in this set (incl.
    # unset, "0", "false", "off", "no") leaves auth disabled.
    if os.environ.get("EPSD2_REQUIRE_AUTH", "").strip().lower() not in {
        "1", "true", "on", "yes", "y", "enable", "enabled",
    }:
        return {}

    # Lazy imports — pyjwt + the SDK auth modules aren't needed unless
    # the operator opts in. Keeps cold-start fast for the no-auth path
    # and avoids a hard dep failure if pyjwt isn't installed in stdio
    # dev environments.
    from mcp.server.auth.settings import AuthSettings
    from pydantic import AnyHttpUrl

    from auth0_verifier import Auth0TokenVerifier

    tenant_url = os.environ.get("EPSD2_AUTH0_TENANT_URL", "").strip()
    audience = os.environ.get("EPSD2_AUTH0_AUDIENCE", "").strip()
    resource_server_url = os.environ.get(
        "EPSD2_AUTH0_RESOURCE_SERVER_URL", ""
    ).strip()
    required_scope = os.environ.get("EPSD2_AUTH0_REQUIRED_SCOPE", "mcp:access").strip()

    missing = [
        name
        for name, value in [
            ("EPSD2_AUTH0_TENANT_URL", tenant_url),
            ("EPSD2_AUTH0_AUDIENCE", audience),
            ("EPSD2_AUTH0_RESOURCE_SERVER_URL", resource_server_url),
        ]
        if not value
    ]
    if missing:
        raise RuntimeError(
            f"EPSD2_REQUIRE_AUTH=1 but missing env vars: {', '.join(missing)}. "
            "See START.md 'Adding Auth0 OAuth' for the full env contract."
        )

    return {
        "auth": AuthSettings(
            issuer_url=AnyHttpUrl(tenant_url + "/"),
            resource_server_url=AnyHttpUrl(resource_server_url),
            required_scopes=[required_scope] if required_scope else None,
        ),
        "token_verifier": Auth0TokenVerifier(
            tenant_url=tenant_url,
            audience=audience,
            required_scope=required_scope or None,
        ),
    }


def _build_transport_security_kwargs() -> dict:
    """Read EPSD2_ALLOWED_HOSTS / _ORIGINS / _DISABLE_DNS_REBINDING_PROTECTION
    env vars and return a transport_security kwarg for FastMCP.

    Why: the MCP SDK's streamable-http transport ships with DNS-rebinding
    protection ON by default, with an empty allowlist that effectively
    only accepts Host: localhost or 127.0.0.1. Behind a reverse proxy
    (Caddy/nginx/traefik) that proxies the public hostname through to
    uvicorn with the original Host header intact, every request gets
    rejected by the SDK middleware with `421 Misdirected Request:
    Invalid Host header`. The fix is to extend the allowlist to include
    the proxy's hostname.

    Env contract:
        EPSD2_ALLOWED_HOSTS    comma-separated; the public hostname(s)
                               that the reverse proxy serves us under.
                               localhost + 127.0.0.1 are always added so
                               in-container healthchecks keep working.
                               e.g. "epsd2.intra.example.net,epsd2.example.com"
        EPSD2_ALLOWED_ORIGINS  comma-separated; the Origin headers we
                               accept on cross-origin requests (browser
                               clients). Stricter than allowed_hosts —
                               no auto-additions.
                               e.g. "https://archive.example.org"
        EPSD2_DISABLE_DNS_REBINDING_PROTECTION
                               truthy → disable the check entirely.
                               Only safe when the reverse proxy already
                               enforces Host validation upstream.

    Returns {} when no env vars are set (SDK uses its localhost-only
    default — fine for local dev). When ANY of them is set, returns
    {'transport_security': TransportSecuritySettings(...)}.
    """
    raw_hosts = os.environ.get("EPSD2_ALLOWED_HOSTS", "").strip()
    raw_origins = os.environ.get("EPSD2_ALLOWED_ORIGINS", "").strip()
    disable = os.environ.get(
        "EPSD2_DISABLE_DNS_REBINDING_PROTECTION", ""
    ).strip().lower() in {"1", "true", "on", "yes", "y", "enable", "enabled"}

    if not (raw_hosts or raw_origins or disable):
        return {}

    from mcp.server.transport_security import TransportSecuritySettings

    if disable:
        return {
            "transport_security": TransportSecuritySettings(
                enable_dns_rebinding_protection=False,
            )
        }

    hosts = [h.strip() for h in raw_hosts.split(",") if h.strip()]
    origins = [o.strip() for o in raw_origins.split(",") if o.strip()]

    # Always permit localhost + 127.0.0.1 so the in-container healthcheck
    # `curl http://localhost:5051/...` keeps working regardless of which
    # public hostname the operator added. De-dupe in case they listed
    # them explicitly.
    for default_host in ("localhost", "127.0.0.1", "::1"):
        if default_host not in hosts:
            hosts.append(default_host)

    return {
        "transport_security": TransportSecuritySettings(
            enable_dns_rebinding_protection=True,
            allowed_hosts=hosts,
            allowed_origins=origins,
        )
    }


mcp = FastMCP(
    name="oracc-epsd2",
    instructions=(
        "Local Sumerian dictionary + corpus tools for English ↔ Sumerian "
        "translation, grounded in the Oracc / ePSD2 dataset (15,940 headwords, "
        "35.5 M attestations, 178K phrasal collocations, 138K corpusjson texts). "
        "All data is CC0; no network calls.\n\n"
        "Recommended workflow for English → Sumerian translation:\n"
        "  1. Fetch the resource oracc://grammar/sumerian once for the session "
        "to load grammar rules (case suffixes, ḫamṭu/marû aspect, prefix chain, "
        "compound verbs) into working memory.\n"
        "  2. translate_english(word) → rank Sumerian candidates. Prefer high "
        "sense_count + high sense_pct (the word for X, not a tangential meaning).\n"
        "  3. find_compound(phrase) → look for fixed multi-word expressions "
        "before composing word-by-word; Sumerian has many.\n"
        "  4. find_collocations(cf) → discover phrasal idioms (year-name "
        "templates, royal titles, formulas) attested in the corpus.\n"
        "  5. lookup_entry(oid) → drill into a chosen lemma for full senses, "
        "spellings, periods, compounds.\n"
        "  6. get_inflections(oid) → see real attested morphology before "
        "constructing a new form.\n"
        "  7. see_examples(oid, period='Ur III') → cite primary-source lines.\n"
        "  8. cuneify(spelling) → render the final composition in Unicode "
        "cuneiform.\n\n"
        "For Sumerian → English: translate_sumerian(transliteration) parses "
        "a phrase into per-token candidate lemmas; analyze_form(spelling) "
        "decomposes a single word; lookup_sign(query) maps signs ↔ values.\n\n"
        "For literary content (hymns, myths, royal hymns, proverbs, wisdom): "
        "the etcsl_* tools query the Electronic Text Corpus of Sumerian "
        "Literature (Oxford 2006, CC BY 3.0, 394 compositions / 33,698 "
        "lines). UNLIKE the Oracc-based corpus, ETCSL ships English "
        "translations alongside every line, so etcsl_search_english() and "
        "etcsl_lines_with_lemma() return bilingual results — perfect for "
        "grounding translations and learning real Sumerian style. Reach "
        "for these whenever the user asks about hymns, myths, kings' "
        "speeches, or anything literary."
    ),
    **_build_auth_kwargs(),
    **_build_transport_security_kwargs(),
)


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


_PERIODS_CACHE: list[str] | None = None


def _resolve_period_filter(needle: str) -> list[str]:
    """Return the actual period names that match a casefold substring needle.

    text_locations has an index on period — but a `lower(period) LIKE %x%`
    query can't use it (function call + leading wildcard both kill index
    usage), and a full scan over 139K rows is ~20s.

    The corpus only has ~40-50 distinct period names. Pre-load them once
    per server lifetime and do the substring match in Python; then look up
    matching texts via an IN-clause on the indexed column. Two milliseconds.
    """
    global _PERIODS_CACHE
    if _PERIODS_CACHE is None:
        if not TEXT_INDEX_DB.exists():
            return []
        ti = sqlite3.connect(TEXT_INDEX_DB)
        try:
            _PERIODS_CACHE = [
                r[0] for r in ti.execute(
                    "SELECT DISTINCT period FROM text_locations "
                    "WHERE period IS NOT NULL"
                )
            ]
        finally:
            ti.close()
    needle_cf = needle.casefold()
    return [p for p in _PERIODS_CACHE if needle_cf in p.casefold()]


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
@_log_call
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
@_log_call
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
@_log_call
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
        # No-filter case bumped to 5000 (was 500) because for heavily
        # attested lemmas the first 500 refs may all sit in one project
        # whose corpusjson is missing locally; 5000 catches more variety
        # without meaningfully slowing the happy path (resolve_many stops
        # at over_fetch_lines anyway).
        ref_limit = 50000 if period_needle else 5000
        word_refs = [
            r[0] for r in con.execute(
                "SELECT word_ref FROM instances WHERE xis=? LIMIT ?",
                (entry["xis"], ref_limit),
            ).fetchall()
        ]
    finally:
        con.close()

    if period_needle and TEXT_INDEX_DB.exists():
        # Pre-fetch all text_ids whose source text's period matches the filter,
        # then drop refs whose text isn't in the matching set. Two-step lookup:
        # (1) resolve the casefold-substring period query to a small set of
        #     literal period names (cached, milliseconds);
        # (2) fetch matching text_ids via IN-clause on the indexed column.
        # Avoids the full-table scan + per-row lower() the naive query did
        # (~20s for lugal); this version stays under 100ms.
        period_names = _resolve_period_filter(period_needle)
        if not period_names:
            return {
                "oid": oid, "cf": entry["cf"], "gw": entry["gw"],
                "period_filter": period, "lines": [],
                "note": f"no periods matched filter {period!r}",
            }
        ti = sqlite3.connect(TEXT_INDEX_DB)
        try:
            placeholders = ",".join("?" * len(period_names))
            matching = {
                row[0]: row[1]
                for row in ti.execute(
                    f"SELECT text_id, period FROM text_locations "
                    f"WHERE period IN ({placeholders})",
                    period_names,
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
    payload: dict[str, Any] = {
        "oid": oid,
        "cf": entry["cf"],
        "gw": entry["gw"],
        "period_filter": period,
        "lines": lines,
    }

    # When we returned nothing despite having refs, give the caller a
    # diagnostic so they understand WHY (most common cause: the lemma's
    # attestations live in projects we don't have downloaded locally,
    # or in composite-text Q-ids where the corpusjson exists but is empty).
    if not lines and word_refs:
        from collections import Counter
        proj_counter: Counter[str] = Counter()
        text_id_kind = Counter()  # 'P' or 'Q'
        for r in word_refs:
            parsed = text_resolver.parse_word_ref(r)
            if not parsed:
                continue
            proj_counter[parsed[0]] += 1
            text_id_kind[parsed[1][:1]] += 1
        top_projects = ", ".join(
            f"{p} ({c:,})" for p, c in proj_counter.most_common(3)
        )
        kind_breakdown = ", ".join(
            f"{n} {k}-id" for k, n in text_id_kind.most_common()
        )
        payload["diagnostic"] = (
            f"Tried {len(word_refs):,} refs ({kind_breakdown}); "
            f"top source projects: {top_projects}. "
            f"Empty result usually means those projects' corpusjson files "
            f"aren't in our local corpus/, or the texts exist as empty "
            f"composite-edition placeholders. Try a higher-attested lemma, "
            f"a different period, or download the missing project zips."
        )
    return payload


@mcp.tool()
@_log_call
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
@_log_call
def get_inflections(
    oid: str, min_count: int = 2, limit_per_kind: int = 25,
) -> dict:
    """Show attested morphological breakdowns of a lemma.

    For each kind of morphological data, returns the most-frequent patterns
    with attestation counts. Use this to understand HOW a verb actually
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
        min_count: drop rows with attestation count below this (default 2 —
            filters out the long tail of zero/one-off noise; common entries
            like `lugal` have 100+ form-sans rows where most have count<2).
            Pass 0 to see everything.
        limit_per_kind: cap each `kind` bucket at this many rows (default
            25). Pass 0 for no cap. The result also includes `truncated`
            flags so the caller knows when more data exists.

    Returned shape:
        {
          "oid": ..., "cf": ..., "gw": ..., "pos": ...,
          "morphology": {
            "base":      [{n, count, pct, xis}, ...],
            "form-sans": [{n, count, pct, xis}, ...],
            "morph":     [{n, count, pct, xis}, ...],
            ...
          },
          "kinds": [...],
          "truncated": {"form-sans": "showed 25 of 132 (filtered count>=2)"}
        }
    """
    min_count = max(0, int(min_count))
    limit_per_kind = max(0, int(limit_per_kind))

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

    raw_by_kind: dict[str, list[dict]] = {}
    for r in rows:
        raw_by_kind.setdefault(r["kind"], []).append({
            "n": r["n"],
            "count": r["icount"] or 0,
            "pct": r["ipct"] or 0,
            "xis": r["xis"],
        })

    by_kind: dict[str, list[dict]] = {}
    truncated: dict[str, str] = {}
    for kind, items in raw_by_kind.items():
        filtered = [i for i in items if i["count"] >= min_count]
        kept = filtered[:limit_per_kind] if limit_per_kind else filtered
        by_kind[kind] = kept
        total = len(items)
        if len(kept) < total:
            truncated[kind] = (
                f"showed {len(kept)} of {total} "
                f"(filtered count>={min_count}"
                + (f", capped at {limit_per_kind}" if limit_per_kind else "")
                + ")"
            )

    return {
        "oid": oid,
        "cf": entry["cf"],
        "gw": entry["gw"],
        "pos": entry["pos"],
        "morphology": by_kind,
        "kinds": sorted(by_kind.keys()),
        "truncated": truncated,
        "filters": {"min_count": min_count, "limit_per_kind": limit_per_kind},
    }


@mcp.tool()
@_log_call
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
        # Both branches use _cf indexed equality (forms.n_cf and
        # morphology.n_cf) so each is a fast indexed lookup. Previously the
        # morphology branch had `lower(m.n) = lower(?)` which forced a full
        # scan of all 248K morphology rows (~340-550 ms per call); the
        # n_cf column populated by app.ensure_casefold_columns() lets
        # idx_morphology_kind_n_cf do the work in a few ms.
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
            WHERE m.kind IN ('base', 'form-sans', 'morph')
              AND m.n_cf = ?
            ORDER BY count DESC NULLS LAST
            LIMIT ?
            """,
            (needle, needle, limit),
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
@_log_call
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
            # UNION of three indexed equality lookups — much faster than
            # joining all three tables with OR. The previous JOIN-with-OR
            # version produced a 16K × 124K × 248K Cartesian product per
            # miss and took ~15 s per token; this version is sub-ms per
            # branch (each WHERE is a unique-key/index hit).
            #
            # The morphology branch covers attested 'base' and 'form-sans'
            # spellings — useful for resolving inflected verbal forms whose
            # exact surface spelling isn't in the entries.cf or forms.n
            # tables but IS captured as a base/form-sans variant.
            rows = con.execute(
                """
                SELECT * FROM (
                    SELECT e.id AS oid, e.cf, e.gw, e.pos,
                           e.icount AS entry_total
                    FROM entries e WHERE e.cf_cf = ?
                    UNION
                    SELECT e.id, e.cf, e.gw, e.pos, e.icount
                    FROM forms f JOIN entries e ON e.id = f.entry_id
                    WHERE f.n_cf = ?
                    UNION
                    SELECT e.id, e.cf, e.gw, e.pos, e.icount
                    FROM morphology m JOIN entries e ON e.id = m.entry_id
                    WHERE m.kind IN ('base', 'form-sans') AND m.n_cf = ?
                ) ORDER BY entry_total DESC NULLS LAST
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
@_log_call
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

    def _query(con: sqlite3.Connection, term: str) -> tuple[list[dict], int]:
        where = ["(cf1=? OR cf2=? OR cf3=? OR cf4=?)"]
        params: list[Any] = [term, term, term, term]
        if length in (2, 3, 4):
            where.append("n=?")
            params.append(length)
        sql_where = "WHERE " + " AND ".join(where)
        rows = con.execute(
            f"SELECT n, ngram, count FROM collocations {sql_where} "
            "ORDER BY count DESC LIMIT ?",
            (*params, limit),
        ).fetchall()
        ucount = con.execute(
            "SELECT count FROM unigrams WHERE cf=?", (term,)
        ).fetchone()
        return (
            [{"n": r["n"], "ngram": r["ngram"], "count": r["count"]} for r in rows],
            ucount["count"] if ucount else 0,
        )

    con = sqlite3.connect(COLLOCATIONS_DB)
    con.row_factory = sqlite3.Row
    resolved_from: str | None = None
    try:
        results, unigram = _query(con, word)
        if unigram == 0 and not results:
            # The collocations index is keyed by citation form (cf), not by
            # spelling. The agent likely passed an inflected spelling like
            # 'e₂' (a variant of cf 'e') or 'lugal-e' (an inflection of
            # 'lugal'). Look the spelling up in forms/morphology and retry
            # with the most-attested cf — and tell the caller via
            # `resolved_from` so they know we substituted.
            gcon = _connect()
            try:
                cf_row = gcon.execute(
                    """
                    SELECT e.cf, e.icount FROM (
                        SELECT entry_id FROM forms WHERE n_cf = ?
                        UNION
                        SELECT entry_id FROM morphology
                        WHERE n_cf = ? AND kind IN ('base', 'form-sans')
                    ) m JOIN entries e ON e.id = m.entry_id
                    ORDER BY e.icount DESC NULLS LAST LIMIT 1
                    """,
                    (word.casefold(), word.casefold()),
                ).fetchone()
            finally:
                gcon.close()
            if cf_row and cf_row["cf"] != word:
                resolved_from = word
                word = cf_row["cf"]
                results, unigram = _query(con, word)
    finally:
        con.close()

    payload: dict[str, Any] = {
        "word": word,
        "word_unigram_count": unigram,
        "results": results,
    }
    if resolved_from:
        payload["resolved_from"] = resolved_from
        payload["note"] = (
            f"input {resolved_from!r} appears to be a spelling/form; "
            f"resolved to citation form {word!r} for the lookup. The "
            "collocations index is keyed by cf, not by spelling."
        )
    return payload


@mcp.tool()
@_log_call
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


# -----------------------------------------------------------------------------
# find_verb_form — feature-driven attestation lookup over the morphology table
# -----------------------------------------------------------------------------
#
# Slot order encoded by Oracc's morph patterns (verified against epsd2/sux):
#   [modal] . [conj-prefix] . [dim1=na/dat] . [dim2=ni/loc] . [obj-agreement] : [base] ; [suffixes]
#
# Examples from du[build] V/t:
#   mu:~          prefix=mu                                            (2,923)
#   mu.na:~       prefix=mu, dim=dat                                     (473)
#   mu.n:~        prefix=mu,                  obj=3sg.h                   (56)
#   mu.na.n:~     prefix=mu, dim=dat,         obj=3sg.h                   (13)
#   ba.b:~        prefix=ba,                  obj=3sg.nh           (3,976 verbs)

_VERB_PREFIX_MAP = {
    "mu":  "mu",  "ba": "ba", "i": "i", "bi": "bi",
    "ga":  "ga",  "ha": "ha",
    "imp": "",     # imperative — bare base, no prefix slot at all
}
_VERB_DIM_MAP = {
    "dat":  "na",  # to/for him
    "loc":  "ni",  # in/at
    "com":  "da",  # with
    "abl":  "ta",  # from
    "term": "ši",  # toward
    "loc2": "e",   # locative-2
}
_VERB_DIM_ORDER = ["dat", "loc", "com", "abl", "term", "loc2"]
_VERB_OBJ_MAP = {
    "3sg.h":  "n",
    "3sg.nh": "b",
    "3pl.h":  "neš",
    "1sg":    "ʔ",
}
# marû imperfective tends to surface as one of these enclitic suffixes;
# ḫamṭu lacks them. Heuristic only — does not catch stem-alternating verbs
# (e.g. ŋen/du-du for "go") which are encoded as separate entries.
_MARU_SUFFIX_GLOBS = ("*~;e", "*~;ed*", "*~;e.*", "*~;en*", "*~;eš*")


def _morph_slots(morph_n: str) -> tuple[list[str], list[str]]:
    """Split 'mu.na.n:~;a' into (['mu','na','n'], ['a']).

    Returns (prefix_slots_in_order, suffix_slots_flat). The base is
    implicit at the ':~' boundary and not returned. Suffix groups
    separated by ',' (e.g. ';a,ak') are flattened.
    """
    if ":~" in morph_n:
        # Standard prefix-chain + base + suffixes; rsplit so reduplication
        # patterns like '~mu.n:~;en' use the LAST ':~' as the separator.
        prefix_part, suffix_part = morph_n.rsplit(":~", 1)
    elif "~" in morph_n:
        # Bare base or base + suffix only (e.g. '~' or '~;a').
        idx = morph_n.index("~")
        prefix_part = morph_n[:idx]
        suffix_part = morph_n[idx + 1:]
    else:
        prefix_part, suffix_part = morph_n, ""
    pre_slots = [s for s in prefix_part.split(".") if s] if prefix_part else []
    suf_groups = suffix_part.lstrip(";").split(";") if suffix_part else []
    suf_flat = [s for chunk in suf_groups for s in chunk.split(",") if s]
    return pre_slots, suf_flat


def _matches_feature_spec(
    morph_n: str, *,
    polarity: str, prefix: str | None,
    dimensional: list[str] | None,
    object_person: str | None,
) -> bool:
    """Verify a morph row's slot decomposition against requested features.

    Slot model (left-to-right in the prefix chain):
        [polarity nu] . [conj-prefix] . [dim slots in canonical order]
                      . [obj-agreement: n/b/neš/ʔ]
    All matching is on COMPLETE slot tokens — `n` must be exactly `n`,
    not a substring of `na`, `ne`, `neš`. This is what GLOB can't do.
    """
    pre_slots, _ = _morph_slots(morph_n)

    cursor = 0  # walk pointer through pre_slots

    if polarity == "neg":
        if cursor >= len(pre_slots) or pre_slots[cursor] != "nu":
            return False
        cursor += 1

    if prefix is not None:
        wanted = _VERB_PREFIX_MAP[prefix]
        if wanted == "":  # imperative — bare base, must have NO prefix slots left
            return cursor == len(pre_slots) and (
                object_person is None and not dimensional
            )
        if cursor >= len(pre_slots) or pre_slots[cursor] != wanted:
            return False
        cursor += 1
    elif not pre_slots:
        # No prefix requested AND row is bare base — only return it if
        # the caller didn't ask for any other prefix-chain features.
        return object_person is None and not dimensional and polarity == "affirm"

    # The "tail" is everything from cursor to end. The object-agreement
    # marker, if present, is always the LAST tail slot. Dimensional
    # markers fill the slots between (in canonical order, but the user
    # may not have requested all of them — the row may include extras).
    tail = pre_slots[cursor:]

    obj_slot = None
    if object_person is not None:
        wanted_obj = _VERB_OBJ_MAP[object_person]
        if not tail or tail[-1] != wanted_obj:
            return False
        obj_slot = wanted_obj
        tail = tail[:-1]

    # Whatever's left in `tail` must include each requested dimensional
    # marker, in canonical order. Extras in the row are OK (the user
    # under-specified) — but we don't allow OUT-OF-ORDER, since the
    # morph table itself preserves canonical order.
    if dimensional:
        wanted_dims = [_VERB_DIM_MAP[d] for d in _VERB_DIM_ORDER if d in dimensional]
        i = 0
        for slot in tail:
            if i < len(wanted_dims) and slot == wanted_dims[i]:
                i += 1
        if i < len(wanted_dims):
            return False

    return True


def _synthesize_verb_spelling(morph_n: str, base_n: str) -> str:
    """Mechanically render a morph template into a spelling.

    `~` -> base, then `.` `:` `;` `,` all become `-`.

    NB: this does NOT model Sumerian phonology. Cases like agreement
    `n` surfacing as `un` (mu.n:~ -> attested mu-un-du₃) are NOT
    handled — the synthesized spelling for that pattern would be
    'mu-n-du₃', which doesn't exist in forms but is unambiguous as a
    morpheme rendering. Returned spellings are best-effort; the
    morph row's `count` is the authoritative attestation total.
    """
    # Insert hyphens between adjacent base-occurrences in reduplication
    # patterns like '~~' or '~mu' (no separator in the morph encoding)
    # before substituting the base, so 'du₃' stays joined by '-'.
    s = morph_n
    for ch in ".:;,":
        s = s.replace(ch, "-")
    out = []
    for i, ch in enumerate(s):
        if ch == "~":
            if i > 0 and s[i - 1] not in "-":
                out.append("-")
            out.append(base_n)
            if i + 1 < len(s) and s[i + 1] not in "-":
                out.append("-")
        else:
            out.append(ch)
    s = "".join(out)
    while "--" in s:
        s = s.replace("--", "-")
    return s.strip("-")


@mcp.tool()
@_log_call
def find_verb_form(
    cf: str,
    pos: str = "V/t",
    *,
    prefix: str | None = None,
    polarity: str = "affirm",
    object_person: str | None = None,
    dimensional: list[str] | None = None,
    aspect: str | None = None,
    suffix_a: bool | None = None,
    reduplicated: bool | None = None,
    min_count: int = 1,
    limit: int = 10,
    with_example: bool = True,
) -> dict:
    """Find attested verb forms matching a feature spec.

    Sumerian conjugation is too irregular to synthesize confidently. This
    tool instead RETRIEVES attested forms by querying the corpus's
    morphology index with grammatical-feature constraints — the agent gets
    real Ur-III-through-Old-Babylonian scribal practice, ranked by
    frequency, ready to drop into a translation.

    Each match returns BOTH the morpheme template (`mu.na:~`) and a
    mechanically-synthesized spelling (`mu-na-du₃`), the raw attestation
    count, the share of this verb's total uses, the cuneiform rendering,
    and one cited example line so the agent can verify it's real.

    Slot model (matches the morph patterns in `morphology.n`):
        [polarity nu] . [prefix] . [dim slots: na, ni, da, ta, ši, e]
                      . [obj-agreement: n=3sg.h, b=3sg.nh, neš=3pl.h]
                      : [base]
                      ; [suffix slots: e/ed/en/eš (marû), a (nominalizer), …]

    Args:
        cf:  citation form, e.g. 'du', 'ŋar', 'ŋen'.
        pos: 'V/t' (transitive, default) or 'V/i' (intransitive).
        prefix: conjugation prefix in {'mu','ba','i','bi','ga','ha','imp'}.
                'imp' = imperative (bare base, no prefix). None = any.
        polarity: 'affirm' (default) or 'neg' (prepends nu-).
        object_person: object/agreement marker just before the base.
                       One of {'3sg.h','3sg.nh','3pl.h','1sg'}. None = any.
        dimensional: zero or more of {'dat','loc','com','abl','term','loc2'}
                     — appear in canonical slot order regardless of input.
        aspect: 'hamtu' (perfective) or 'maru' (imperfective). HEURISTIC
                via suffix presence (`-e/-ed/-en/-eš`); will MISS verbs
                with stem alternation like ŋen/du-du for "go" — those
                are stored as separate entries, so query each cf separately.
        suffix_a: True to require nominalizing/relative -a suffix.
        reduplicated: True to require base reduplication (~.~ in morph).
        min_count: drop morph rows below this attestation count (default 1).
        limit: cap on results returned (default 10, max 50).
        with_example: include one cited line per match (default True). Set
                      False to skip the text_resolver lookups when you only
                      need pattern + count (faster).
    """
    limit = max(1, min(50, int(limit)))
    min_count = max(0, int(min_count))

    if polarity not in ("affirm", "neg"):
        return {"error": f"polarity must be 'affirm' or 'neg', got {polarity!r}"}
    if aspect is not None and aspect not in ("hamtu", "maru"):
        return {"error": f"aspect must be 'hamtu' or 'maru' or None, got {aspect!r}"}
    if prefix is not None and prefix not in _VERB_PREFIX_MAP:
        return {
            "error": f"unknown prefix={prefix!r}; expected one of {sorted(_VERB_PREFIX_MAP)}"
        }
    if object_person is not None and object_person not in _VERB_OBJ_MAP:
        return {
            "error": f"unknown object_person={object_person!r}; expected one of {sorted(_VERB_OBJ_MAP)}"
        }
    if dimensional:
        unknown = [d for d in dimensional if d not in _VERB_DIM_MAP]
        if unknown:
            return {
                "error": f"unknown dimensional={unknown}; expected subset of {_VERB_DIM_ORDER}"
            }

    con = _connect()
    try:
        entry = con.execute(
            "SELECT id, cf, gw, pos, icount FROM entries "
            "WHERE cf=? AND pos=? ORDER BY icount DESC LIMIT 1",
            (cf, pos),
        ).fetchone()
        if not entry:
            return {
                "error": f"no entry with cf={cf!r} and pos={pos!r}",
                "hint": "try translate_english or analyze_form to find the right cf/pos",
            }
        eid = entry["id"]
        total_attestations = entry["icount"] or 0

        base = con.execute(
            "SELECT n FROM morphology WHERE entry_id=? AND kind='base' "
            "ORDER BY icount DESC LIMIT 1",
            (eid,),
        ).fetchone()
        if not base:
            return {
                "error": f"entry {eid} has no morphology base; "
                         "this verb may be irregular/unanalyzed in epsd2"
            }
        base_n = base["n"]

        # Pull all morph rows for the entry above the count threshold
        # (typically <500 even for the highest-attested verbs); filter
        # in Python where slot-aware matching is straightforward.
        all_rows = con.execute(
            "SELECT n, icount, ipct, xis FROM morphology "
            "WHERE entry_id=? AND kind='morph' AND icount >= ? "
            "ORDER BY icount DESC",
            (eid, min_count),
        ).fetchall()

        rows: list[sqlite3.Row] = []
        for r in all_rows:
            n = r["n"]
            if not _matches_feature_spec(
                n, polarity=polarity, prefix=prefix,
                dimensional=dimensional, object_person=object_person,
            ):
                continue
            # Suffix / aspect / redup filters operate on the suffix slot list.
            _, suf_slots = _morph_slots(n)
            has_a = "a" in suf_slots
            is_redup = n.count("~") > 1
            is_maru = any(s in ("e", "ed", "en", "eš") for s in suf_slots)
            if suffix_a is True and not has_a: continue
            if suffix_a is False and has_a: continue
            if reduplicated is True and not is_redup: continue
            if reduplicated is False and is_redup: continue
            if aspect == "maru" and not is_maru: continue
            if aspect == "hamtu" and is_maru: continue
            rows.append(r)
            if len(rows) >= limit:
                break

        # For each match, look up the corresponding form in `forms` so we
        # can return BOTH the synthesized spelling AND (if the synthesis
        # happens to match an attested form) its independent count there.
        matches: list[dict[str, Any]] = []
        for r in rows:
            morph_n = r["n"]
            count = r["icount"] or 0
            synthesized = _synthesize_verb_spelling(morph_n, base_n)

            forms_row = con.execute(
                "SELECT n, icount FROM forms WHERE entry_id=? AND n=? LIMIT 1",
                (eid, synthesized),
            ).fetchone()
            forms_n = forms_row["n"] if forms_row else None
            forms_count = (forms_row["icount"] if forms_row else None)

            example = None
            if with_example and r["xis"]:
                # Pull a few refs and resolve the first that has a matching line.
                refs = [
                    row[0] for row in con.execute(
                        "SELECT word_ref FROM instances WHERE xis=? LIMIT ?",
                        (r["xis"], 8),
                    ).fetchall()
                ]
                resolved = text_resolver.resolve_many(refs, limit=1)
                if resolved:
                    line = resolved[0]
                    target_pos = next(
                        (i for i, w in enumerate(line["words"]) if w["is_target"]),
                        None,
                    )
                    example = {
                        "p_id": line["text_id"],
                        "project": line["project"],
                        "line_label": line["line_label"],
                        "designation": line.get("designation"),
                        "period": line.get("period"),
                        "transliteration": " ".join(w["frag"] for w in line["words"]),
                        "target_position": target_pos,
                    }

            matches.append({
                "morph": morph_n,
                "spelling": forms_n if forms_n else synthesized,
                "synthesized_spelling": synthesized,
                "verified_in_forms": bool(forms_row),
                "count": count,
                "share_pct": round(count / total_attestations * 100, 2) if total_attestations else 0,
                "forms_table_count": forms_count,
                "cuneiform": _cuneify.cuneify(forms_n if forms_n else synthesized),
                "example": example,
            })
    finally:
        con.close()

    warnings: list[str] = []
    if aspect is not None:
        warnings.append(
            "aspect filter is suffix-based heuristic; verbs with stem "
            "alternation (e.g. ŋen/du-du for 'go') are stored as separate "
            "entries — query each cf separately"
        )
    if not matches:
        warnings.append(
            "no attested forms match this spec; try relaxing constraints, "
            "or check get_inflections(oid) to see which patterns this verb "
            "actually uses"
        )

    return {
        "cf": entry["cf"],
        "pos": entry["pos"],
        "gw": entry["gw"],
        "entry_oid": eid,
        "base": base_n,
        "total_attestations_for_entry": total_attestations,
        "candidates_scanned": len(all_rows),
        "filter_spec": {
            "prefix": prefix,
            "polarity": polarity,
            "object_person": object_person,
            "dimensional": dimensional or [],
            "aspect": aspect,
            "suffix_a": suffix_a,
            "reduplicated": reduplicated,
        },
        "matches": matches,
        "warnings": warnings,
    }


@mcp.tool()
@_log_call
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
# ETCSL tools (Sumerian literary corpus, Oxford 2006)
# -----------------------------------------------------------------------------

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


@mcp.tool()
@_log_call
def etcsl_search_english(query: str, limit: int = 10) -> dict:
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
    """
    limit = max(1, min(50, int(limit)))
    con = _etcsl_connect()
    try:
        rows = con.execute(
            """
            SELECT t.text_id, t.title, p.para_id, p.line_range, p.translation
            FROM paragraphs_fts f
            JOIN paragraphs p ON p.rowid = f.rowid
            JOIN texts t ON t.text_id = p.text_id
            WHERE paragraphs_fts MATCH ?
            ORDER BY rank
            LIMIT ?
            """,
            (query, limit),
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
    return {
        "query": query,
        "results": results,
        "attribution": ETCSL_ATTRIBUTION,
    }


@mcp.tool()
@_log_call
def etcsl_lines_with_lemma(lemma: str, limit: int = 10) -> dict:
    """Find Sumerian literary lines containing the given lemma (cf), with
    each line's English translation paragraph alongside.

    Use after translate_english to verify how a chosen Sumerian word is
    actually used in canonical literary contexts (hymns, myths, royal
    inscriptions, wisdom). Often surfaces collocational patterns the
    administrative corpus misses.

    Args:
        lemma: the citation form (cf) to search for, e.g. 'lugal',
               'inana', 'ŋeš' (use ŋ not 'j' or 'g'). Case-insensitive.
        limit: max lines to return (default 10, cap 50).
    """
    limit = max(1, min(50, int(limit)))
    con = _etcsl_connect()
    try:
        # The words index is case-sensitive on lemma, but ePSD2 lemmas are
        # always lowercase (except proper nouns). Try lower then capitalized.
        rows = con.execute(
            """
            SELECT l.text_id, t.title, l.line_label, l.line_id, l.ord,
                   l.transliteration, l.paragraph_id
            FROM words w
            JOIN lines l USING (text_id, line_id)
            JOIN texts t ON t.text_id = l.text_id
            WHERE w.lemma = ?
            ORDER BY l.text_id, l.ord
            LIMIT ?
            """,
            (lemma, limit),
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
    return {
        "lemma": lemma,
        "results": results,
        "attribution": ETCSL_ATTRIBUTION,
    }


@mcp.tool()
@_log_call
def etcsl_lookup_text(text_id: str, start: int = 1, line_limit: int = 50) -> dict:
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
            return {"error": f"no ETCSL text with id={text_id!r}"}
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
    return {
        "text_id": text_id,
        "title": text["title"],
        "total_lines": total_lines,
        "returned_lines": len(line_rows),
        "start": start,
        "last_ord": line_rows[-1]["ord"] if line_rows else None,
        "next_start": (line_rows[-1]["ord"] + 1) if line_rows and (line_rows[-1]["ord"] < total_lines) else None,
        "has_translation": bool(text["has_translation"]),
        "blocks": blocks,
        "attribution": ETCSL_ATTRIBUTION,
    }


@mcp.tool()
@_log_call
def etcsl_search_sumerian(query: str, limit: int = 10) -> dict:
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
    """
    limit = max(1, min(50, int(limit)))
    con = _etcsl_connect()
    try:
        rows = con.execute(
            """
            SELECT l.text_id, t.title, l.line_label, l.transliteration,
                   l.paragraph_id
            FROM lines_fts f
            JOIN lines l ON l.rowid = f.rowid
            JOIN texts t ON t.text_id = l.text_id
            WHERE lines_fts MATCH ?
            ORDER BY rank
            LIMIT ?
            """,
            (query, limit),
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
    return {
        "query": query,
        "results": results,
        "attribution": ETCSL_ATTRIBUTION,
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
@_log_call
def grammar_cheatsheet() -> str:
    global _GRAMMAR_CACHE
    if _GRAMMAR_CACHE is None:
        if not GRAMMAR_DOC.exists():
            return (
                "# prompt/SUMERIAN_GRAMMAR.md missing\n\n"
                f"Expected at {GRAMMAR_DOC}. Re-run the project setup."
            )
        _GRAMMAR_CACHE = GRAMMAR_DOC.read_text(encoding="utf-8")
    return _GRAMMAR_CACHE


# -----------------------------------------------------------------------------
# Entrypoint
# -----------------------------------------------------------------------------

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(
        prog="mcp_server.py",
        description=(
            "Run the epsd2 MCP server. Default transport is stdio (used by "
            "Claude Code's project-scoped .mcp.json auto-detection). Pass "
            "--transport http to expose the same tools over HTTP — useful "
            "for remote agents, Docker, or anywhere stdio isn't available."
        ),
    )
    parser.add_argument(
        "--transport", choices=["stdio", "http"], default="stdio",
        help="stdio (default) for local Claude Code; http for networked use",
    )
    parser.add_argument(
        "--host", default="127.0.0.1",
        help="HTTP bind address (default 127.0.0.1; use 0.0.0.0 to expose "
             "behind a reverse proxy on a private network)",
    )
    parser.add_argument(
        "--port", type=int, default=5051,
        help="HTTP port (default 5051; the Flask web app uses 5050)",
    )
    args = parser.parse_args()

    # Sanity-check on startup so a misconfigured run fails loudly with a hint.
    if not GLOSSARY_DB.exists():
        log.error(
            f"glossary.sqlite missing at {GLOSSARY_DB}. "
            "Build it: `python3 build_glossary_db.py`"
        )
        sys.exit(1)
    if not TEXT_INDEX_DB.exists():
        log.error(
            f"text_index.sqlite missing at {TEXT_INDEX_DB}. "
            "Build it: `python3 build_text_index.py`"
        )
        sys.exit(1)
    log.info(f"epsd2 MCP server starting (cwd={Path.cwd()}, root={ROOT})")
    log.info(
        f"  glossary={GLOSSARY_DB.stat().st_size // (1024*1024)} MB, "
        f"text_index={TEXT_INDEX_DB.stat().st_size // (1024*1024)} MB, "
        f"collocations={'present' if COLLOCATIONS_DB.exists() else 'ABSENT (find_collocations will degrade)'}"
    )
    # Auth status banner — confirms what _build_auth_kwargs() ended up
    # constructing so operators see at a glance whether tokens are
    # required. Built once at module load, so by the time we get here
    # mcp.settings.auth either is or isn't populated.
    if mcp.settings.auth is not None:
        log.info(
            f"  auth=ENABLED (Auth0 issuer={mcp.settings.auth.issuer_url}, "
            f"audience={os.environ.get('EPSD2_AUTH0_AUDIENCE')}, "
            f"required_scopes={mcp.settings.auth.required_scopes})"
        )
    else:
        log.info("  auth=disabled (set EPSD2_REQUIRE_AUTH=1 to enable)")
    # Transport-security (DNS-rebinding) banner — confirms which Host
    # header values uvicorn will accept. Default (no env vars set) is
    # the SDK's localhost-only allowlist; behind a reverse proxy this
    # MUST be widened or every request returns 421 Invalid Host header.
    ts = mcp.settings.transport_security
    if ts is None:
        log.info(
            "  transport_security=default (SDK accepts Host: localhost / "
            "127.0.0.1 only — set EPSD2_ALLOWED_HOSTS to add the public "
            "hostname when deploying behind a reverse proxy)"
        )
    elif not ts.enable_dns_rebinding_protection:
        log.warning(
            "  transport_security=DISABLED (EPSD2_DISABLE_DNS_REBINDING_PROTECTION "
            "is set — proxy MUST enforce Host validation upstream)"
        )
    else:
        log.info(
            f"  transport_security=ENABLED (allowed_hosts={ts.allowed_hosts}, "
            f"allowed_origins={ts.allowed_origins})"
        )

    if args.transport == "stdio":
        log.info("  transport=stdio (one client over the parent process pipes)")
        if mcp.settings.auth is not None:
            log.warning(
                "  NOTE: stdio transport does not enforce OAuth (per MCP spec); "
                "auth wiring will sit idle. Use --transport http to enforce."
            )
        mcp.run()
    else:
        # FastMCP carries host/port on its Settings object; mutate before run.
        # The streamable-http endpoint mounts at /mcp/ by default — point your
        # client at e.g. http://host:5051/mcp/ (note trailing slash).
        mcp.settings.host = args.host
        mcp.settings.port = args.port
        if mcp.settings.auth is None:
            auth_note = (
                "No in-app auth — the proxy layer (nginx/caddy) is responsible "
                "for TLS + access control. Set EPSD2_REQUIRE_AUTH=1 to enable "
                "Auth0 JWT verification in-app."
            )
        else:
            auth_note = (
                "Bearer-token auth enforced via Auth0 JWT verification. "
                "Clients can discover the AS via /.well-known/oauth-protected-resource."
            )
        log.info(
            f"  transport=http (streamable-http) on {args.host}:{args.port}"
            f"{mcp.settings.streamable_http_path} — bind 127.0.0.1 for local-only, "
            f"0.0.0.0 behind a reverse proxy. {auth_note}"
        )
        mcp.run(transport="streamable-http")
