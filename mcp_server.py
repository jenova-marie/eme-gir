"""MCP server exposing the local ePSD2 corpus for English -> Sumerian translation.

Tools:
    translate_english(query, limit)        - rank Sumerian candidates for an English meaning
    translate_sumerian(transliteration)    - reverse: parse a Sumerian phrase into English glosses
                                             (with detected case/possessive/plural suffixes)
    parse_phrase(transliteration)          - case-aware grammatical chunking: per-token role
                                             labels (ergative/dative/equative/…), compact
                                             skeleton, ambiguous-suffix warnings
    lookup_entry(oid)                      - full structured view of a chosen lemma
    see_examples(oid, limit, period)       - real attested lines with the target marked
    find_compound(english_phrase)          - find idiomatic multi-word Sumerian
    find_collocations(word, length, limit) - phrasal n-grams attested with a word
    find_phrase_pattern(pattern, limit)    - retrieve corpus-attested n-grams matching a
                                             structural template (each slot = cf | POS | '*')
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

Two resources (fetch both once per session):
    oracc://grammar/sumerian               - comprehensive Sumerian grammar cheat sheet
                                             (Jagersma 2010)
    oracc://prompt/agent                   - drop-in agent system prompt teaching
                                             the end-to-end workflow over these tools

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
from mcp.types import ToolAnnotations

import cuneify as _cuneify
import text_resolver
import umami_analytics
from mcp_models import (
    AnalyzeFormResponse,
    CDLIArtifact,
    CaseChunk,
    CuneifyResponse,
    ETCSLLinesWithLemmaResponse,
    ETCSLLookupTextResponse,
    ETCSLSearchEnglishResponse,
    ETCSLSearchSumerianResponse,
    ErrorResponse,
    FindArtifactsResponse,
    FindCollocationsResponse,
    FindCompoundResponse,
    FindPhrasePatternResponse,
    FindVerbFormResponse,
    GetInflectionsResponse,
    LookupArtifactResponse,
    LookupEntryResponse,
    LookupSignResponse,
    ParsePhraseResponse,
    SeeExamplesResponse,
    Suffix,
    TranslateEnglishResponse,
    TranslateSumerianResponse,
)
from paths import (
    AGENT_PROMPT_DOC,
    CDLI_ARTIFACT_URL,
    CDLI_DB,
    CDLI_LINEART_THUMB_URL,
    CDLI_LINEART_URL,
    CDLI_PHOTO_THUMB_URL,
    CDLI_PHOTO_URL,
    COLLOCATIONS_DB,
    ETCSL_DB,
    GLOSSARY_DB,
    GRAMMAR_DOC,
    INFLECTED_COLLOCATIONS_DB,
    MCP_SERVER_LOG as LOG_FILE,
    ROOT,
    TEXT_INDEX_DB,
)

ETCSL_ATTRIBUTION = (
    "ETCSL: Black, J.A. et al., The Electronic Text Corpus of Sumerian "
    "Literature (etcsl.orinst.ox.ac.uk), Oxford 1998-2006. CC BY 3.0 UK."
)
CDLI_ATTRIBUTION = (
    "CDLI: Cuneiform Digital Library Initiative (cdli.earth), "
    "catalogue data CC0 / public domain. Hosted by Max Planck Institute "
    "for the History of Science (Berlin) since 2022."
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
        # arg_keys ships only the NAMES (sorted) — never the values —
        # so the analytics dashboard can answer "are agents passing
        # `period=...` to see_examples?" without leaking which period
        # any specific user queried.
        arg_keys = sorted(kwargs.keys())
        t0 = time.monotonic()
        try:
            result = fn(*args, **kwargs)
        except Exception as e:
            elapsed = (time.monotonic() - t0) * 1000
            log.exception(
                f"  ✗ {fn.__name__} ({elapsed:.0f}ms) raised "
                f"{type(e).__name__}: {e}"
            )
            umami_analytics.emit(fn.__name__, {
                "duration_ms": round(elapsed, 1),
                "outcome": "error",
                "error_kind": type(e).__name__,
                "arg_keys": arg_keys,
            })
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
        # Outcome is "error" when the result is a structured ErrorResponse
        # (tool returned cleanly but the operation failed — bad oid,
        # missing scope, etc.) and "ok" otherwise. Distinct from raised
        # exceptions, which take the except branch above.
        is_error = isinstance(result, dict) and "error" in result
        if not is_error and hasattr(result, "model_dump"):
            try:
                is_error = "error" in result.model_dump(exclude_none=True)
            except Exception:
                is_error = False
        umami_analytics.emit(fn.__name__, {
            "duration_ms": round(elapsed, 1),
            "outcome": "error" if is_error else "ok",
            "result_count": umami_analytics._count_result_items(result),
            "arg_keys": arg_keys,
        })
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

    user_hosts = [h.strip() for h in raw_hosts.split(",") if h.strip()]
    user_origins = [o.strip() for o in raw_origins.split(",") if o.strip()]

    # For each user-supplied host, also add the port-wildcard variant
    # `host:*`. The MCP SDK matches Host headers via exact-match first,
    # then wildcard-port patterns (see mcp.server.transport_security
    # _is_host_allowed: `if allowed.endswith(":*"): ... host.startswith(
    # base_host + ":")`). Reverse proxies VARY in whether they preserve
    # the port suffix on the inward Host header — Caddy chains can
    # produce `Host: example.com:443` even though the client sent
    # `Host: example.com`. Adding the `:*` variant for every operator-
    # supplied host catches both cases without forcing the operator to
    # know about it. Same treatment for origins (the SDK's
    # _is_origin_allowed also supports `origin:*` patterns).
    hosts: list[str] = []
    for h in user_hosts:
        hosts.append(h)
        if not h.endswith(":*") and ":" not in h.split("]")[-1]:
            # Skip if operator already gave a port-bound entry like
            # `host:443` or `host:*` — the second clause sidesteps the
            # `[::1]` IPv6 form where ':' lives inside brackets.
            hosts.append(h + ":*")

    origins: list[str] = []
    for o in user_origins:
        origins.append(o)
        if not o.endswith(":*"):
            # Origins are URLs (scheme://host[:port]). The SDK's port-
            # wildcard match works on the same trailing-`:*` convention.
            origins.append(o + ":*")

    # Always permit localhost variants so the in-container healthcheck
    # `curl http://localhost:5051/...` keeps working regardless of which
    # public hostname the operator added. Mirror the SDK's own default
    # set of localhost variants (see mcp.server.transport_security where
    # it adds `localhost:*` etc. when bound to a loopback host). De-dupe
    # in case the operator listed any of these explicitly.
    for default_host in (
        "localhost", "localhost:*",
        "127.0.0.1", "127.0.0.1:*",
        "::1", "[::1]:*",
    ):
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
        "════════════════════════════════════════════════════════════════════\n"
        "FIRST STEP, BEFORE ANY TOOL CALL: read these two resources via the "
        "MCP `resources/read` request. They are your bootstrap context — "
        "without them, tool calls will be uninformed.\n"
        "  • oracc://prompt/agent      — your full system prompt: the workflow, "
        "the required output format, the ETCSL attribution rule, and a worked "
        "example. Read this FIRST so the rest of the instructions make sense.\n"
        "  • oracc://grammar/sumerian  — comprehensive Jagersma-2010-based "
        "grammar reference (twelve enclitic cases, phonology, the nine-slot "
        "finite-verb template, perfective vs imperfective inflection, modal/"
        "negative preformatives, non-finite forms, nominalization-based "
        "subordination). Every grammatical rule carries an inline Jagersma "
        "§-citation for verification. Read this SECOND so you can reason "
        "about morphology when tool results return inflected forms.\n"
        "Both resources are markdown — the agent prompt is ~10–15 KB, the "
        "grammar is ~30 KB. They only need to be fetched ONCE per session — "
        "keep them in working memory thereafter.\n"
        "════════════════════════════════════════════════════════════════════\n\n"
        "Workflow for English → Sumerian translation (AFTER bootstrap):\n"
        "  1. translate_english(word) → rank Sumerian candidates. Prefer high "
        "sense_count + high sense_pct (the word for X, not a tangential meaning).\n"
        "  2. find_compound(phrase) → look for fixed multi-word expressions "
        "before composing word-by-word; Sumerian has many.\n"
        "  3. find_collocations(cf) → discover phrasal idioms (year-name "
        "templates, royal titles, formulas) attested in the corpus near "
        "a given lemma. For structural-pattern queries (e.g. 'every "
        "N+lugal pair' or 'every X attested as object of du₃'), call "
        "find_phrase_pattern(pattern) instead — same corpus, different "
        "query shape.\n"
        "  4. lookup_entry(oid) → drill into a chosen lemma for full senses, "
        "spellings, periods, compounds.\n"
        "  5. get_inflections(oid) → see real attested morphology before "
        "constructing a new form.\n"
        "  6. see_examples(oid, period='Early Dynastic') → cite primary-source "
        "lines (default to Early Dynastic = ED IIIa/IIIb when the user has not "
        "specified a period; this is Jagersma's primary descriptive ground).\n"
        "  7. cuneify(spelling) → render the final composition in Unicode "
        "cuneiform.\n\n"
        "For Sumerian → English: translate_sumerian(transliteration) parses "
        "a phrase into per-token candidate lemmas (each carrying detected "
        "case/possessive/plural suffixes when present); parse_phrase("
        "transliteration) goes further and returns a case-aware grammatical "
        "chunking with role labels (subject_ergative, oblique_dative, "
        "comparison_equative, verb_head, …) plus a compact bracket skeleton "
        "— use it when structural ambiguity matters (which noun does the "
        "case suffix attach to? is this -gin₇ equative or just adjectival?). "
        "analyze_form(spelling) decomposes a single attested word; "
        "lookup_sign(query) maps signs ↔ values.\n\n"
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


# Grammatical pre-annotation helpers (suffix table, peeler, verbal-prefix
# detector) live in sumerian_morphology.py so the same code path can be
# reused by build_inflected_collocations.py during corpus ingest. The
# module-level aliases below preserve the existing private names used
# elsewhere in this file, so the refactor is import-only — no logic change.
from sumerian_morphology import (
    SUMERIAN_SUFFIX_TABLE,
    VERBAL_PREFIXES,
    detect_verbal_prefixes as _detect_verbal_prefixes,
    peel_suffixes as _peel_suffixes,
    strip_token as _strip_token,
)


# -----------------------------------------------------------------------------
# Tools
# -----------------------------------------------------------------------------
#
# All tools are read-only point-lookups against local SQLite indexes built
# from the CC0 Oracc / ETCSL corpora. No network calls. No writes. Same
# inputs always return the same outputs (modulo the corpus being rebuilt
# between sessions, but the data is treated as immutable). So every tool
# advertises:
#   readOnlyHint=True       — no mutations
#   destructiveHint=False   — nothing to destroy
#   idempotentHint=True     — safe to call repeatedly
#   openWorldHint=False     — closed world (no external systems queried)
# This corrects the MCP client UI badges, which otherwise default to the
# pessimistic case (PUBLIC WRITE / DESTRUCTIVE / OPEN WORLD).

READ_ONLY_ANNOTATIONS = ToolAnnotations(
    readOnlyHint=True,
    destructiveHint=False,
    idempotentHint=True,
    openWorldHint=False,
)


@mcp.tool(annotations=READ_ONLY_ANNOTATIONS)
@_log_call
def translate_english(query: str, limit: int = 10) -> TranslateEnglishResponse:
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

    return TranslateEnglishResponse(
        query=query,
        total_matches=total,
        results=[_entry_payload(con, r) for r in rows],
    )


@mcp.tool(annotations=READ_ONLY_ANNOTATIONS)
@_log_call
def lookup_entry(oid: str) -> LookupEntryResponse | ErrorResponse:
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
            return ErrorResponse(error=f"no entry with oid={oid!r}")

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

    return LookupEntryResponse(
        oid=entry["id"],
        cf=entry["cf"],
        gw=entry["gw"],
        pos=entry["pos"],
        headword=entry["headword"],
        total_count=entry["icount"] or 0,
        senses=senses,
        spellings=forms,
        periods=periods,
        compounds=compounds,
    )


@mcp.tool(annotations=READ_ONLY_ANNOTATIONS)
@_log_call
def see_examples(oid: str, limit: int = 3, period: str | None = None) -> SeeExamplesResponse | ErrorResponse:
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
            return ErrorResponse(error=f"no entry with oid={oid!r}")
        if not entry["xis"]:
            return SeeExamplesResponse(oid=oid, lines=[], note="entry has no instance refs")
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
            return SeeExamplesResponse(
                oid=oid, cf=entry["cf"], gw=entry["gw"],
                period_filter=period, lines=[],
                note=f"no periods matched filter {period!r}",
            )
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
        line: dict[str, Any] = {
            "text_id": r["text_id"],
            "project": r["project"],
            "line_label": r["line_label"],
            "designation": r.get("designation"),
            "period": r.get("period"),
            "transliteration": " ".join(w["frag"] for w in words),
            "target": target_frag,
            "target_position": target_pos,
        }
        # CDLI enrichment — splat in cdli_url, photo/lineart URLs, and
        # museum metadata so the caller can offer "see the actual
        # tablet" links without a follow-up tool call. None when the
        # CDLI catalogue isn't built or doesn't know this artifact.
        cdli = _cdli_enrichment(r["text_id"])
        if cdli:
            line.update(cdli)
        lines.append(line)
        if len(lines) >= limit:
            break
    diagnostic: str | None = None
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
        diagnostic = (
            f"Tried {len(word_refs):,} refs ({kind_breakdown}); "
            f"top source projects: {top_projects}. "
            f"Empty result usually means those projects' corpusjson files "
            f"aren't in our local corpus/, or the texts exist as empty "
            f"composite-edition placeholders. Try a higher-attested lemma, "
            f"a different period, or download the missing project zips."
        )
    return SeeExamplesResponse(
        oid=oid,
        cf=entry["cf"],
        gw=entry["gw"],
        period_filter=period,
        lines=lines,
        diagnostic=diagnostic,
    )


@mcp.tool(annotations=READ_ONLY_ANNOTATIONS)
@_log_call
def find_compound(english_phrase: str, limit: int = 10) -> FindCompoundResponse:
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
    return FindCompoundResponse(
        query=english_phrase,
        total_matches=len(results),
        results=results,
    )


@mcp.tool(annotations=READ_ONLY_ANNOTATIONS)
@_log_call
def get_inflections(
    oid: str, min_count: int = 2, limit_per_kind: int = 25,
) -> GetInflectionsResponse | ErrorResponse:
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
            return ErrorResponse(error=f"no entry with oid={oid!r}")
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

    return GetInflectionsResponse(
        oid=oid,
        cf=entry["cf"],
        gw=entry["gw"],
        pos=entry["pos"],
        morphology=by_kind,
        kinds=sorted(by_kind.keys()),
        truncated=truncated,
        filters={"min_count": min_count, "limit_per_kind": limit_per_kind},
    )


@mcp.tool(annotations=READ_ONLY_ANNOTATIONS)
@_log_call
def analyze_form(spelling: str, limit: int = 20) -> AnalyzeFormResponse:
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
    return AnalyzeFormResponse(
        spelling=spelling,
        matches=[{
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
    )


@mcp.tool(annotations=READ_ONLY_ANNOTATIONS)
@_log_call
def translate_sumerian(transliteration: str, limit_per_token: int = 3) -> TranslateSumerianResponse:
    """Reverse-direction lookup: parse a Sumerian transliteration into per-token
    English glosses. Use this to verify a translation you composed, or to read
    a Sumerian phrase you encountered.

    Tokenization is **whole-token-first**: splits the input only on whitespace,
    then for each token tries the WHOLE thing (with hyphens intact) against
    `entries.cf`, `forms.n`, and `morphology.n` (kind in 'base','form-sans').
    Only if the whole-token lookup yields zero candidates does the parser fall
    back to splitting on hyphens/dots and gloss each piece individually. This
    matches the Sumerian convention that hyphens join signs WITHIN one word —
    so `lu₂-gal` resolves cleanly as the lemma `lugal`, `mu-un-du₃` resolves
    as the inflected form of `du₃`, etc. — instead of shattering every
    hyphenated word into orphan signs.

    Each returned entry carries a `match_kind` signal:
      - "whole"          : the token resolved as-is (the preferred reading)
      - "split_fallback" : whole-token lookup failed; this is one piece of
                            the hyphen-split fallback. `from_word` names the
                            original hyphenated token.
      - "unmatched"      : neither the whole token nor any split piece
                            resolved (no candidates).

    Args:
        transliteration: a Sumerian phrase like "lugal-e e₂ mu-un-du₃"
        limit_per_token: max lemma candidates returned per token (default 3)
    """
    import re as _re

    def _lookup(cur: sqlite3.Cursor, needle_cf: str, limit: int) -> list[dict[str, Any]]:
        # UNION of three indexed equality lookups against entries.cf_cf,
        # forms.n_cf, and morphology.n_cf (kind in base/form-sans). Each
        # branch is a single index hit; the union and ORDER BY happen at
        # the SQLite layer. ~sub-ms per call on the glossary index.
        rows = cur.execute(
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
            (needle_cf, needle_cf, needle_cf, limit),
        ).fetchall()
        return [{
            "oid": r["oid"],
            "cf": r["cf"],
            "gw": r["gw"],
            "pos": r["pos"],
            "entry_total": r["entry_total"] or 0,
        } for r in rows]

    _STRIP_CHARS = "⸢⸣[](),;:!?"

    def _clean(s: str) -> str:
        # Strip braced determinatives, surrounding bracketing/punctuation,
        # and obvious damage placeholders (`x`).
        s = _re.sub(r"\{[^}]*\}", "", s).strip().strip(_STRIP_CHARS)
        return "" if s in {"x", "X"} else s

    # Tokenize on whitespace ONLY. Hyphens stay intact inside each token
    # so we can try the whole hyphenated word as a form-spelling lookup first.
    words = [w for w in (_clean(piece) for piece in transliteration.split()) if w]

    con = _connect()
    try:
        cur = con.cursor()
        results: list[dict[str, Any]] = []
        for word in words:
            whole = _lookup(cur, word.casefold(), limit_per_token)
            if whole:
                # Lexicographer-blessed whole-token reading. Prefer this.
                # Additionally surface the detected suffix chain so the
                # agent has the grammatical-role signal even when the
                # whole spelling was already in forms.n (Option 3).
                base, suffixes = _peel_suffixes(word)
                entry: dict[str, Any] = {
                    "token": word,
                    "candidates": whole,
                    "match_kind": "whole",
                }
                if suffixes:
                    entry["base"] = base
                    entry["suffixes"] = [s.model_dump() for s in suffixes]
                results.append(entry)
                continue

            # Whole-token lookup failed. If the word has hyphens or dots,
            # fall back to splitting and glossing each piece. If it's a
            # single bare piece with no separators, there's nowhere to
            # fall back to — emit an empty "unmatched" entry so the
            # agent can see we tried and found nothing.
            pieces = [p for p in (_clean(s) for s in _re.split(r"[-.]", word)) if p]
            if len(pieces) <= 1:
                results.append({
                    "token": word,
                    "candidates": [],
                    "match_kind": "unmatched",
                })
                continue

            for piece in pieces:
                results.append({
                    "token": piece,
                    "candidates": _lookup(cur, piece.casefold(), limit_per_token),
                    "match_kind": "split_fallback",
                    "from_word": word,
                })
    finally:
        con.close()
    return TranslateSumerianResponse(
        transliteration=transliteration,
        tokens=results,
    )


@mcp.tool(annotations=READ_ONLY_ANNOTATIONS)
@_log_call
def parse_phrase(transliteration: str) -> ParsePhraseResponse:
    """Case-aware grammatical pre-annotation of a Sumerian phrase.

    Goes BEYOND translate_sumerian's per-token glossing by classifying each
    token's syntactic role in the phrase based on its morphology:

      - **Nominal tokens** get their case/possessive/plural suffixes peeled
        and annotated (ergative, dative, locative, equative, etc.). The
        base after peeling is looked up for clean lemma candidates.
      - **Verbal tokens** are detected by the prefix chain (mu-, ba-, bi₂-,
        i₃-, ḫe₂-, …) and reported with the prefix chain extracted; case-
        suffix peeling is skipped (verb-final suffixes are agreement, not
        case).
      - Each chunk carries an inferred `role` (subject_ergative,
        object_absolutive, oblique_dative, verb_head, …) and a
        `phrase_boundary_after` flag the agent uses to chunk the input
        into NP/VP/clause units.

    This is **not a true syntactic parser** — it does not produce a
    constituency or dependency tree, makes no claim about phrase
    attachment, and cannot disambiguate genuine syntactic ambiguity. It
    surfaces the grammatical role markers that are explicitly encoded in
    the morphology and lets the agent build the parse on top.

    The agent should call this BEFORE attempting an interlinear gloss when
    facing structural ambiguity (e.g. "in the distant lapis-blue sky" vs.
    "the sky, lapis-like, far away" — the difference often hinges on
    whether `za-gin₃` carries `-gin₇` equative, which this tool detects
    explicitly). For straightforward word-by-word lookup, translate_sumerian
    is lighter and sufficient.

    Args:
        transliteration: a Sumerian phrase like "lugal-e e₂ mu-na-du₃"
    """
    words = [w for w in (_strip_token(piece) for piece in transliteration.split()) if w]

    # Map outermost case suffix → inferred phrase role
    CASE_TO_ROLE = {
        "ergative":                "subject_ergative",
        "dative":                  "oblique_dative",
        "locative":                "oblique_locative",
        "comitative":              "oblique_comitative",
        "ablative_instrumental":   "oblique_ablative",
        "terminative":             "oblique_terminative",
        "equative":                "comparison_equative",
        "genitive":                "genitive_modifier",
    }
    # Short labels for the skeleton string.
    ROLE_TO_LABEL = {
        "subject_ergative":       "ERG",
        "object_absolutive":      "ABS",
        "noun_head_unmarked":     "ABS",  # zero-marked absolutive
        "oblique_dative":         "DAT",
        "oblique_locative":       "LOC",
        "oblique_comitative":     "COM",
        "oblique_ablative":       "ABL",
        "oblique_terminative":    "TERM",
        "comparison_equative":    "EQUATIVE",
        "genitive_modifier":      "GEN",
        "adjective_modifier":     "ADJ",
        "verb_head":              "V",
        "unknown":                "?",
    }

    con = _connect()
    try:
        cur = con.cursor()

        def _lookup(needle: str, limit: int = 3) -> list[dict[str, Any]]:
            rows = cur.execute(
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
                (needle, needle, needle, limit),
            ).fetchall()
            return [{
                "oid": r["oid"], "cf": r["cf"], "gw": r["gw"],
                "pos": r["pos"], "entry_total": r["entry_total"] or 0,
            } for r in rows]

        chunks: list[CaseChunk] = []
        skeleton_parts: list[str] = []
        seen_roles: list[str] = []

        for word in words:
            # First check if this looks like a verb form by its prefix chain.
            # We prefer this signal over POS-of-whole-token because verb
            # forms often fail to whole-token-lookup if the inflected surface
            # isn't in forms.n; we don't want to mis-treat them as nouns
            # and start peeling case suffixes.
            verbal_prefixes = _detect_verbal_prefixes(word)

            # Whole-token lookup against the lexicon.
            whole_candidates = _lookup(word.casefold())
            top_pos = whole_candidates[0]["pos"] if whole_candidates else None
            is_verb = (top_pos or "").startswith("V") or (
                verbal_prefixes is not None and top_pos in (None, "")
            )

            if is_verb:
                # Verbal head. Don't peel case suffixes — verb-final
                # endings are person/aspect agreement, not nominal case.
                # Reuse the existing whole-token candidates if any.
                chunks.append(CaseChunk(
                    token=word,
                    base=word.split("-")[-1] if verbal_prefixes else None,
                    suffixes=[],
                    candidates=whole_candidates,
                    pos_head=top_pos,
                    is_verb_form=True,
                    verbal_prefixes=verbal_prefixes,
                    role="verb_head",
                    phrase_boundary_after=True,
                ))
                skeleton_parts.append(
                    f"[V {whole_candidates[0]['cf'] if whole_candidates else word.split('-')[-1]}"
                    + (f" ({verbal_prefixes}-)" if verbal_prefixes else "")
                    + "]"
                )
                seen_roles.append("verb_head")
                continue

            # Nominal token. Try suffix-peeling for grammatical role.
            base, suffixes = _peel_suffixes(word)

            # If peeling stripped at least one suffix and the whole-token
            # lookup didn't succeed, re-lookup with the bare base —
            # often the base IS in entries.cf even when the inflected
            # surface isn't in forms.n.
            if suffixes and not whole_candidates:
                base_candidates = _lookup(base.casefold())
                candidates = base_candidates
                top_pos = base_candidates[0]["pos"] if base_candidates else None
            else:
                candidates = whole_candidates

            # Determine the chunk's phrase role from the OUTERMOST case
            # suffix (last in left-to-right order). Possessive/plural
            # suffixes don't change phrase role on their own — only
            # case does.
            outermost_case = next(
                (s for s in reversed(suffixes) if s.kind == "case"),
                None,
            )
            if outermost_case:
                role = CASE_TO_ROLE.get(outermost_case.role, "unknown")
            elif top_pos == "AJ":
                role = "adjective_modifier"
            elif candidates:
                # Bare noun (no case marker) → zero-marked absolutive.
                role = "noun_head_unmarked"
            else:
                role = "unknown"

            # Adjectives modify the preceding head and don't close the phrase.
            # Everything else with a recognized role closes the phrase.
            phrase_boundary_after = role != "adjective_modifier"

            chunks.append(CaseChunk(
                token=word,
                base=base if suffixes else None,
                suffixes=suffixes,
                candidates=candidates,
                pos_head=top_pos,
                is_verb_form=False,
                verbal_prefixes=None,
                role=role,
                phrase_boundary_after=phrase_boundary_after,
            ))

            # Build the skeleton chunk.
            label = ROLE_TO_LABEL.get(role, "?")
            head_str = (candidates[0]["cf"] if candidates else (base if suffixes else word))
            if role == "adjective_modifier":
                # Adjectives glue to the previous bracket — render as
                # "+ADJ:head" inside the existing chunk if there is one.
                if skeleton_parts and skeleton_parts[-1].endswith("]"):
                    # Insert before the closing bracket.
                    skeleton_parts[-1] = skeleton_parts[-1][:-1] + f" +ADJ:{head_str}]"
                else:
                    skeleton_parts.append(f"[ADJ {head_str}]")
            elif outermost_case:
                skeleton_parts.append(f"[NP {head_str}-{label}]")
            elif role == "noun_head_unmarked":
                skeleton_parts.append(f"[NP {head_str}-ABS]")
            else:
                skeleton_parts.append(f"[? {head_str}]")
            seen_roles.append(role)

        # Heuristic notes.
        notes: list[str] = []
        has_ergative = "subject_ergative" in seen_roles
        has_absolutive = "noun_head_unmarked" in seen_roles or "object_absolutive" in seen_roles
        has_verb = "verb_head" in seen_roles
        if has_ergative and has_absolutive and has_verb:
            notes.append(
                "ergative subject + absolutive object + verb head: "
                "transitive clause (canonical SOV pattern)"
            )
        elif has_absolutive and has_verb and not has_ergative:
            notes.append(
                "absolutive subject + verb head, no ergative marker: "
                "likely INTRANSITIVE clause (or the ergative-marked subject "
                "was elided in this fragment)"
            )
        if "comparison_equative" in seen_roles:
            notes.append(
                "equative -gin₇ detected: the marked noun is being "
                "compared LIKE the head, not described AS the head — "
                "rules out an attributive-adjective reading"
            )
        # Flag any chunks with ambiguous suffixes so the agent knows
        # to disambiguate manually.
        for ch in chunks:
            for s in ch.suffixes:
                if s.ambiguous_with:
                    notes.append(
                        f"token {ch.token!r}: suffix {s.spelling!r} read as "
                        f"{s.role!r}, but ambiguous with: "
                        f"{', '.join(s.ambiguous_with)}"
                    )

    finally:
        con.close()

    return ParsePhraseResponse(
        transliteration=transliteration,
        chunks=chunks,
        skeleton=" ".join(skeleton_parts) if skeleton_parts else "(empty input)",
        notes=notes,
    )


@mcp.tool(annotations=READ_ONLY_ANNOTATIONS)
@_log_call
def find_collocations(word: str, length: int | None = None, limit: int = 20) -> FindCollocationsResponse | ErrorResponse:
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
        return ErrorResponse(
            error="collocations.sqlite not built; run `python3 build_collocations.py` first",
        )
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

    note: str | None = None
    if resolved_from:
        note = (
            f"input {resolved_from!r} appears to be a spelling/form; "
            f"resolved to citation form {word!r} for the lookup. The "
            "collocations index is keyed by cf, not by spelling."
        )
    return FindCollocationsResponse(
        word=word,
        word_unigram_count=unigram,
        results=results,
        resolved_from=resolved_from,
        note=note,
    )


import re as _re_slot

# Slot grammar:
#   slot ::= TARGET ('[' GW ']')? (':' CASE)?
#   TARGET ::= cf | POS | '*'   (POS may end in '*' for family glob)
#   GW    ::= ('!')? freetext   (sense disambiguator)
#   CASE  ::= ('!')? role       (case marker constraint)
#
# Examples:
#   "lugal"                — cf=lugal (homographs aggregated)
#   "lugal[king]"          — cf=lugal AND gw=king (v3 sense)
#   "lugal[!king]"         — cf=lugal AND gw != king (negated sense)
#   "lugal:ergative"       — cf=lugal AND case=ergative (v2 case)
#   "lugal[king]:ergative" — cf=lugal AND gw=king AND case=ergative
#   "N"                    — POS=N
#   "N:locative"           — POS=N AND case=locative
#   "N:!ergative"          — POS=N AND case != ergative
#   "V*"                   — POS family glob (V/t, V/i, etc.)
#   "V*:ergative"          — any verb whose agreement reads ergative
#   "*"                    — wildcard (any cf at this slot)
#   "*:locative"           — any cf whose case is locative
_SLOT_RE = _re_slot.compile(
    r"^"
    r"(?P<target>\*|[^\[:]+)"           # cf, POS (with optional *), or *
    r"(?:\[(?P<gw>!?[^\]]+)\])?"        # optional [gw] with optional !
    r"(?::(?P<case>!?[^:]+))?"          # optional :case with optional !
    r"$"
)


def _parse_slot(slot: str) -> dict[str, Any] | None:
    """Parse a slot spec into a constraint dict. Returns None on syntax error."""
    if not slot:
        return None
    m = _SLOT_RE.match(slot.strip())
    if not m:
        return None
    target = m.group("target").strip()
    gw_raw = m.group("gw")
    case_raw = m.group("case")

    out: dict[str, Any] = {
        "target_kind": None,   # 'cf' | 'pos' | 'pos_family' | 'wildcard'
        "target": None,
        "gw": None, "gw_negate": False,
        "case": None, "case_negate": False,
    }

    # Classify the target as cf, POS, or wildcard. POS heuristic same as
    # the v1 implementation: uppercase-leading or contains '/' or ends '*'.
    if target == "*":
        out["target_kind"] = "wildcard"
    elif target.endswith("*"):
        out["target_kind"] = "pos_family"
        out["target"] = target[:-1] + "%"   # 'V*' → LIKE 'V%'
    elif "/" in target or (target.isupper() and len(target) <= 4):
        out["target_kind"] = "pos"
        out["target"] = target
    else:
        out["target_kind"] = "cf"
        out["target"] = target

    if gw_raw:
        gw_raw = gw_raw.strip()
        if gw_raw.startswith("!"):
            out["gw_negate"] = True
            out["gw"] = gw_raw[1:].strip()
        else:
            out["gw"] = gw_raw

    if case_raw:
        case_raw = case_raw.strip()
        if case_raw.startswith("!"):
            out["case_negate"] = True
            out["case"] = case_raw[1:].strip()
        else:
            out["case"] = case_raw

    return out


@mcp.tool(annotations=READ_ONLY_ANNOTATIONS)
@_log_call
def find_phrase_pattern(pattern: list[str], limit: int = 20) -> FindPhrasePatternResponse | ErrorResponse:
    """Retrieve corpus-attested n-grams that match a structural template.

    Use this to ground a candidate phrasing in real attestation. Given a
    pattern of length 2-4 where each slot uses this grammar:

        slot = TARGET (':' CASE)?
        TARGET = cf | POS | '*'
                 (optionally annotated with '[gw]' for sense disambig)
        CASE   = case_role          e.g. ergative, dative, locative,
                                    equative, terminative, comitative,
                                    ablative_instrumental, genitive

        Negation: prefix the gw or case value with '!'.

    Slot examples:
      "lugal"                — cf=lugal, homographs aggregated
      "lugal[king]"          — only the king-sense lugal (v3 sense disambig)
      "lugal[!king]"         — any lugal sense EXCEPT king
      "lugal:ergative"       — lugal in ergative case
      "lugal[king]:ergative" — king-sense lugal in ergative
      "N"                    — any noun, any case
      "N:locative"           — any locative-marked noun (v2 case)
      "N:!ergative"          — any noun NOT in ergative
      "V*"                   — any verb (POS family glob)
      "*:locative"           — any cf in locative case
      "*"                    — wildcard (any cf, any case)

    Pattern examples (with sample value):
      ["lugal","N"]
          → king + X — every noun attested next to lugal
      ["RN","lugal"]
          → every royal name attested with king (year-name templates)
      ["N:ergative","N:locative","V*"]
          → transitive-clause skeletons with locative complement
      ["lugal[king]:ergative","N","du"]
          → "the king(-erg) builds a/the X" attested patterns
      ["za-gin₃:equative","N"]
          → "lapis-like" comparative constructions

    Routing: when `data/inflected_collocations.sqlite` exists, the tool
    queries that (sense + case aware). When it's missing, the tool falls
    back to `data/collocations.sqlite` for v1-style queries; queries that
    use `[gw]` or `:case` syntax error out with a hint.

    Results include per-slot annotation: cf, pos, gw, case (where
    available). Returned rows are keyed by the FULL distinct
    (cf, gw, pos, case) tuple per slot, so homographs and case-variants
    appear as separate rows — that's the disambiguation the agent wants.

    Args:
        pattern: list of 2-4 slot specifiers (see grammar above).
        limit: max number of attested n-grams to return (default 20).
    """
    if not isinstance(pattern, list) or not pattern:
        return ErrorResponse(error="pattern must be a non-empty list of slot specifiers")
    if len(pattern) < 2 or len(pattern) > 4:
        return ErrorResponse(
            error=f"pattern length must be 2, 3, or 4 (got {len(pattern)})",
            hint="The collocation index only stores 2/3/4-grams.",
        )
    pattern = [p.strip() for p in pattern]
    n = len(pattern)
    limit = max(1, min(200, int(limit)))

    parsed_slots: list[dict[str, Any]] = []
    for raw in pattern:
        ps = _parse_slot(raw)
        if ps is None:
            return ErrorResponse(
                error=f"could not parse slot {raw!r}",
                hint="See the docstring for slot grammar examples.",
            )
        parsed_slots.append(ps)

    uses_v2_v3 = any(ps["gw"] or ps["case"] for ps in parsed_slots)

    # Routing: prefer inflected (v2/v3) index when available.
    if INFLECTED_COLLOCATIONS_DB.exists():
        return _find_phrase_pattern_inflected(pattern, parsed_slots, n, limit)

    # Inflected index missing — fall back to legacy cf-only index, but
    # only if no slot uses the new gw/case syntax.
    if uses_v2_v3:
        return ErrorResponse(
            error="pattern uses [gw] or :case syntax but inflected_collocations.sqlite is missing",
            hint=("Run `python3 build_inflected_collocations.py` to build it "
                  "(~25-40 min over the full corpus). Until then, restrict "
                  "the pattern to v1 syntax (cf | POS | '*') and the legacy "
                  "cf-only index will serve."),
        )
    if not COLLOCATIONS_DB.exists():
        return ErrorResponse(
            error=f"neither inflected_collocations.sqlite nor collocations.sqlite exists at {COLLOCATIONS_DB.parent}",
            hint="Run `python3 build_collocations.py` (cf-only, ~5 min) OR `python3 build_inflected_collocations.py` (case+sense aware, ~30 min).",
        )

    return _find_phrase_pattern_legacy(pattern, parsed_slots, n, limit)


def _find_phrase_pattern_inflected(
    pattern: list[str],
    parsed_slots: list[dict[str, Any]],
    n: int,
    limit: int,
) -> FindPhrasePatternResponse:
    """Query the inflected_collocations.sqlite index (v2/v3 path).

    Rows in the inflected table are already keyed by the full distinct
    (cf, gw, pos, case) tuple per slot, so the result naturally surfaces
    homograph + case variants as separate rows. No aggregation needed at
    query time; the row IS the answer.
    """
    where_parts: list[str] = ["n = ?"]
    params: list[Any] = [n]

    for i, ps in enumerate(parsed_slots, start=1):
        # Target constraint
        if ps["target_kind"] == "cf":
            where_parts.append(f"cf{i} = ?")
            params.append(ps["target"])
        elif ps["target_kind"] == "pos":
            where_parts.append(f"pos{i} = ?")
            params.append(ps["target"])
        elif ps["target_kind"] == "pos_family":
            where_parts.append(f"pos{i} LIKE ?")
            params.append(ps["target"])
        # wildcard → no target constraint

        # Sense (gw) constraint
        if ps["gw"]:
            op = "!=" if ps["gw_negate"] else "="
            where_parts.append(f"gw{i} {op} ?")
            params.append(ps["gw"])

        # Case constraint. Note: 'absolutive' (zero-marked) is stored as
        # NULL in the table. Treat 'absolutive' and 'none' as aliases for
        # the NULL test.
        if ps["case"]:
            case_value = ps["case"].lower()
            if case_value in ("absolutive", "none", "null"):
                op = "IS NOT" if ps["case_negate"] else "IS"
                where_parts.append(f"case{i} {op} NULL")
            else:
                if ps["case_negate"]:
                    # `case != X` is true for both other-case AND NULL.
                    # We want "NOT this specific case," so include NULL.
                    where_parts.append(f"(case{i} != ? OR case{i} IS NULL)")
                    params.append(ps["case"])
                else:
                    where_parts.append(f"case{i} = ?")
                    params.append(ps["case"])

    where_clause = " AND ".join(where_parts)

    con = sqlite3.connect(str(INFLECTED_COLLOCATIONS_DB))
    con.row_factory = sqlite3.Row
    try:
        total_row = con.execute(
            f"SELECT COUNT(*) AS n FROM inflected_ngrams WHERE {where_clause}",
            params,
        ).fetchone()
        total = total_row["n"]

        rows = con.execute(
            f"""
            SELECT cf1, cf2, cf3, cf4, gw1, gw2, gw3, gw4,
                   pos1, pos2, pos3, pos4, case1, case2, case3, case4,
                   count
            FROM inflected_ngrams
            WHERE {where_clause}
            ORDER BY count DESC
            LIMIT ?
            """,
            params + [limit],
        ).fetchall()

        results: list[dict[str, Any]] = []
        for r in rows:
            tokens = []
            for i in range(1, n + 1):
                tokens.append({
                    "cf": r[f"cf{i}"],
                    "pos": r[f"pos{i}"],
                    "gw": r[f"gw{i}"],
                    "case": r[f"case{i}"],
                })
            ngram_str = " ".join(t["cf"] for t in tokens)
            results.append({
                "ngram": ngram_str,
                "count": r["count"],
                "tokens": tokens,
            })
    finally:
        con.close()

    return FindPhrasePatternResponse(
        pattern=pattern,
        n=n,
        total_matches=total,
        results=results,
    )


def _find_phrase_pattern_legacy(
    pattern: list[str],
    parsed_slots: list[dict[str, Any]],
    n: int,
    limit: int,
) -> FindPhrasePatternResponse:
    """Query the legacy cf-only collocations.sqlite index (v1 fallback).

    Only invoked when:
      - the inflected index is missing, AND
      - no slot uses gw/case syntax (those would be unanswerable here).
    """
    where_parts: list[str] = ["c.n = ?"]
    params: list[Any] = [n]

    for i, ps in enumerate(parsed_slots, start=1):
        col = f"c.cf{i}"
        if ps["target_kind"] == "wildcard":
            continue
        if ps["target_kind"] == "cf":
            where_parts.append(f"{col} = ?")
            params.append(ps["target"])
        elif ps["target_kind"] == "pos":
            where_parts.append(
                f"EXISTS (SELECT 1 FROM glossary.entries e WHERE e.cf = {col} AND e.pos = ?)"
            )
            params.append(ps["target"])
        elif ps["target_kind"] == "pos_family":
            where_parts.append(
                f"EXISTS (SELECT 1 FROM glossary.entries e WHERE e.cf = {col} AND e.pos LIKE ?)"
            )
            params.append(ps["target"])

    where_clause = " AND ".join(where_parts)
    con = sqlite3.connect(str(COLLOCATIONS_DB))
    con.row_factory = sqlite3.Row
    try:
        con.execute(f"ATTACH DATABASE '{GLOSSARY_DB}' AS glossary")

        total = con.execute(
            f"SELECT COUNT(*) AS n FROM collocations c WHERE {where_clause}",
            params,
        ).fetchone()["n"]

        rows = con.execute(
            f"""
            SELECT c.ngram, c.count, c.cf1, c.cf2, c.cf3, c.cf4
            FROM collocations c
            WHERE {where_clause}
            ORDER BY c.count DESC
            LIMIT ?
            """,
            params + [limit],
        ).fetchall()

        # Annotate cfs with POS+gw from the highest-icount entry per cf
        # (homograph display fix, same as v1 path).
        all_cfs: set[str] = set()
        for r in rows:
            for k in ("cf1", "cf2", "cf3", "cf4"):
                if r[k]:
                    all_cfs.add(r[k])
        entry_lookup: dict[str, tuple[str | None, str | None]] = {}
        if all_cfs:
            placeholders = ",".join("?" * len(all_cfs))
            for er in con.execute(
                f"""
                SELECT cf, pos, gw FROM (
                    SELECT cf, pos, gw, icount,
                           ROW_NUMBER() OVER (PARTITION BY cf ORDER BY icount DESC NULLS LAST) AS rk
                    FROM glossary.entries
                    WHERE cf IN ({placeholders})
                ) WHERE rk = 1
                """,
                list(all_cfs),
            ):
                entry_lookup[er["cf"]] = (er["pos"], er["gw"])

        results: list[dict[str, Any]] = []
        for r in rows:
            tokens = []
            for i in range(1, n + 1):
                cf = r[f"cf{i}"]
                pos, gw = entry_lookup.get(cf, (None, None))
                tokens.append({"cf": cf, "pos": pos, "gw": gw, "case": None})
            results.append({
                "ngram": r["ngram"],
                "count": r["count"],
                "tokens": tokens,
            })
    finally:
        con.close()

    return FindPhrasePatternResponse(
        pattern=pattern,
        n=n,
        total_matches=total,
        results=results,
    )


@mcp.tool(annotations=READ_ONLY_ANNOTATIONS)
@_log_call
def lookup_sign(query: str, limit: int = 10) -> LookupSignResponse | ErrorResponse:
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
        return ErrorResponse(error="OGSL data missing — corpus/ogsl.zip not present")
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

    return LookupSignResponse(
        query=query,
        results=deduped[:limit],
    )


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


@mcp.tool(annotations=READ_ONLY_ANNOTATIONS)
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
) -> FindVerbFormResponse | ErrorResponse:
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
        return ErrorResponse(error=f"polarity must be 'affirm' or 'neg', got {polarity!r}")
    if aspect is not None and aspect not in ("hamtu", "maru"):
        return ErrorResponse(error=f"aspect must be 'hamtu' or 'maru' or None, got {aspect!r}")
    if prefix is not None and prefix not in _VERB_PREFIX_MAP:
        return ErrorResponse(
            error=f"unknown prefix={prefix!r}; expected one of {sorted(_VERB_PREFIX_MAP)}"
        )
    if object_person is not None and object_person not in _VERB_OBJ_MAP:
        return ErrorResponse(
            error=f"unknown object_person={object_person!r}; expected one of {sorted(_VERB_OBJ_MAP)}"
        )
    if dimensional:
        unknown = [d for d in dimensional if d not in _VERB_DIM_MAP]
        if unknown:
            return ErrorResponse(
                error=f"unknown dimensional={unknown}; expected subset of {_VERB_DIM_ORDER}"
            )

    con = _connect()
    try:
        entry = con.execute(
            "SELECT id, cf, gw, pos, icount FROM entries "
            "WHERE cf=? AND pos=? ORDER BY icount DESC LIMIT 1",
            (cf, pos),
        ).fetchone()
        if not entry:
            return ErrorResponse(
                error=f"no entry with cf={cf!r} and pos={pos!r}",
                hint="try translate_english or analyze_form to find the right cf/pos",
            )
        eid = entry["id"]
        total_attestations = entry["icount"] or 0

        base = con.execute(
            "SELECT n FROM morphology WHERE entry_id=? AND kind='base' "
            "ORDER BY icount DESC LIMIT 1",
            (eid,),
        ).fetchone()
        if not base:
            return ErrorResponse(
                error=f"entry {eid} has no morphology base; "
                       "this verb may be irregular/unanalyzed in epsd2"
            )
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
                        "text_id": line["text_id"],
                        "project": line["project"],
                        "line_label": line["line_label"],
                        "designation": line.get("designation"),
                        "period": line.get("period"),
                        "transliteration": " ".join(w["frag"] for w in line["words"]),
                        "target_position": target_pos,
                    }
                    # CDLI enrichment — same pattern as see_examples
                    cdli = _cdli_enrichment(line["text_id"])
                    if cdli:
                        example.update(cdli)

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

    return FindVerbFormResponse(
        cf=entry["cf"],
        pos=entry["pos"],
        gw=entry["gw"],
        entry_oid=eid,
        base=base_n,
        total_attestations_for_entry=total_attestations,
        candidates_scanned=len(all_rows),
        filter_spec={
            "prefix": prefix,
            "polarity": polarity,
            "object_person": object_person,
            "dimensional": dimensional or [],
            "aspect": aspect,
            "suffix_a": suffix_a,
            "reduplicated": reduplicated,
        },
        matches=matches,
        warnings=warnings,
    )


@mcp.tool(annotations=READ_ONLY_ANNOTATIONS)
@_log_call
def cuneify(spelling: str) -> CuneifyResponse:
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
    return CuneifyResponse(
        spelling=spelling,
        cuneiform=glyphs,
        complete=not has_placeholder,
        placeholder_count=glyphs.count("□"),
    )


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


@mcp.tool(annotations=READ_ONLY_ANNOTATIONS)
@_log_call
def etcsl_search_english(query: str, limit: int = 10) -> ETCSLSearchEnglishResponse:
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
    return ETCSLSearchEnglishResponse(
        query=query,
        results=results,
        attribution=ETCSL_ATTRIBUTION,
    )


@mcp.tool(annotations=READ_ONLY_ANNOTATIONS)
@_log_call
def etcsl_lines_with_lemma(lemma: str, limit: int = 10) -> ETCSLLinesWithLemmaResponse:
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
    return ETCSLLinesWithLemmaResponse(
        lemma=lemma,
        results=results,
        attribution=ETCSL_ATTRIBUTION,
    )


@mcp.tool(annotations=READ_ONLY_ANNOTATIONS)
@_log_call
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


@mcp.tool(annotations=READ_ONLY_ANNOTATIONS)
@_log_call
def etcsl_search_sumerian(query: str, limit: int = 10) -> ETCSLSearchSumerianResponse:
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
    return ETCSLSearchSumerianResponse(
        query=query,
        results=results,
        attribution=ETCSL_ATTRIBUTION,
    )


# -----------------------------------------------------------------------------
# CDLI artifact catalogue — provenience, museum holdings, image links
# -----------------------------------------------------------------------------
#
# CDLI (Cuneiform Digital Library Initiative, cdli.earth) maintains the
# canonical per-artifact metadata catalogue: 353K+ tablets with their
# provenience (find spot), period, museum custody, dimensions, and
# bibliographic citations. Oracc references CDLI's P-numbers as the
# primary text identifier, but doesn't redistribute CDLI's full
# catalogue — that's what cdli.sqlite is for.
#
# We DON'T host any imagery. The image URLs we surface point straight
# to cdli.earth so callers (and end users they're serving) navigate
# to CDLI's hosted JPEGs directly. Saves us multi-GB of image bytes
# and keeps CDLI as the source of truth for artifact reproductions.


def _cdli_connect() -> sqlite3.Connection | None:
    """Open the CDLI catalogue SQLite. Returns None when the DB hasn't
    been built yet — callers should fall back to the catalogue-less
    code path. Cheap to call repeatedly; SQLite reuses the file handle."""
    if not CDLI_DB.exists():
        return None
    con = sqlite3.connect(CDLI_DB)
    con.row_factory = sqlite3.Row
    return con


def _build_cdli_artifact(row: sqlite3.Row) -> CDLIArtifact:
    """Convert a cdli.artifacts SQLite row into the response model,
    computing image + page URLs from the p_id + has_photo / has_lineart
    flags. URL fields are None when the corresponding flag is false so
    agents can tell whether the link will actually return an image
    (vs. a 404 because CDLI never had the imagery for that artifact)."""
    p_id = row["p_id"]
    cdli_id = row["cdli_id"]
    has_photo = bool(row["has_photo"])
    has_lineart = bool(row["has_lineart"])
    return CDLIArtifact(
        p_id=p_id,
        cdli_id=cdli_id,
        cdli_url=CDLI_ARTIFACT_URL.format(cdli_id=cdli_id),
        photo_url=CDLI_PHOTO_URL.format(p_id=p_id) if has_photo else None,
        photo_thumb_url=CDLI_PHOTO_THUMB_URL.format(p_id=p_id) if has_photo else None,
        lineart_url=CDLI_LINEART_URL.format(p_id=p_id) if has_lineart else None,
        lineart_thumb_url=CDLI_LINEART_THUMB_URL.format(p_id=p_id) if has_lineart else None,
        has_photo=has_photo,
        has_lineart=has_lineart,
        designation=row["designation"],
        primary_publication=row["primary_publication"],
        publication_history=row["publication_history"],
        citation=row["citation"],
        composite_id=row["composite_id"],
        period=row["period"],
        period_remarks=row["period_remarks"],
        accounting_period=row["accounting_period"],
        dates_referenced=row["dates_referenced"],
        provenience=row["provenience"],
        provenience_remarks=row["provenience_remarks"],
        findspot_remarks=row["findspot_remarks"],
        findspot_square=row["findspot_square"],
        excavation_no=row["excavation_no"],
        museum_collection=row["museum_collection"],
        museum_no=row["museum_no"],
        accession_no=row["accession_no"],
        genre=row["genre"],
        subgenre=row["subgenre"],
        language=row["language"],
        material=row["material"],
        object_type=row["object_type"],
        height=row["height"],
        width=row["width"],
        thickness=row["thickness"],
        condition_description=row["condition_description"],
        object_remarks=row["object_remarks"],
    )


def _cdli_enrichment(p_id: str) -> dict | None:
    """Cheap lookup helper for see_examples / find_verb_form. Returns
    a dict of CDLI URL fields + museum metadata for one P-id, or None
    when CDLI doesn't know the artifact OR the catalogue isn't built.

    Kept narrow on purpose — see_examples shouldn't return the whole
    CDLI record per line; just the URLs and the museum bits agents
    most often want to display alongside an attestation."""
    con = _cdli_connect()
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


@mcp.tool(annotations=READ_ONLY_ANNOTATIONS)
@_log_call
def lookup_artifact(p_id: str) -> LookupArtifactResponse | ErrorResponse:
    """Look up the full CDLI catalogue record for a single cuneiform
    artifact by its P-id (P-number).

    Returns provenience (find spot), period, museum custody, dimensions,
    citations, AND links to CDLI's hosted photographs / line drawings
    when available. Use this to ground an attested line in its
    archaeological + custodial context — "this tablet is from Drehem,
    Ur III period (~2050 BCE), now at the British Museum (BM 103437),
    photographed at <link>".

    Args:
        p_id: P-id like 'P347156' or just '347156' (numeric form OK,
              we normalize). Returned by see_examples / find_verb_form
              as `text_id`.

    Returns LookupArtifactResponse on hit, ErrorResponse when:
      - cdli.sqlite hasn't been built (run build_cdli_db.py)
      - the P-id isn't in CDLI's catalogue (rare — CDLI is comprehensive)

    The image URLs in the response are None when CDLI doesn't have the
    corresponding asset, so you can tell up front whether a "see the
    actual tablet" link will work without making a wasted HTTP request.
    """
    # Normalize the P-id — accept '347156', 'P347156', 'p347156', etc.
    s = (p_id or "").strip().lstrip("Pp")
    if not s.isdigit():
        return ErrorResponse(
            error=f"p_id must be 'P{{nnnnnn}}' or a bare integer (got {p_id!r})",
            hint="Try the text_id from a see_examples result, e.g. 'P347156'.",
        )
    canonical = f"P{int(s):06d}"

    con = _cdli_connect()
    if con is None:
        return ErrorResponse(
            error=f"cdli.sqlite missing at {CDLI_DB}",
            hint="Run `python3 build_cdli_db.py` to build it (~15s after a 147 MB download).",
        )
    try:
        row = con.execute(
            "SELECT * FROM artifacts WHERE p_id=?", (canonical,)
        ).fetchone()
    finally:
        con.close()
    if not row:
        return ErrorResponse(
            error=f"no CDLI artifact with p_id={canonical!r}",
            hint=(
                "CDLI's catalogue covers ~353K artifacts but the August "
                "2022 snapshot we ingested may not include very recent "
                "additions. Verify at https://cdli.earth/search."
            ),
        )
    return LookupArtifactResponse(
        artifact=_build_cdli_artifact(row),
        attribution=CDLI_ATTRIBUTION,
    )


@mcp.tool(annotations=READ_ONLY_ANNOTATIONS)
@_log_call
def find_artifacts(
    provenience: str | None = None,
    period: str | None = None,
    museum_collection: str | None = None,
    genre: str | None = None,
    language: str | None = None,
    limit: int = 20,
) -> FindArtifactsResponse | ErrorResponse:
    """Filter the CDLI catalogue by archaeological / curatorial criteria.

    Use this for "show me every artifact matching X" questions that
    Oracc's lemma-centric tools don't answer:
      - "Every Ur III tablet from Drehem in the British Museum"
      - "Every Old Babylonian literary tablet from Nippur"
      - "Every Akkadian text in the Yale Babylonian Collection"

    Each filter argument is matched as a case-insensitive SUBSTRING
    against the corresponding catalogue column, so partial values work:
      - provenience='Drehem'      matches 'Drehem (mod. Puzriš-Dagan)'
      - period='Ur III'           matches 'Ur III (ca. 2100-2000 BC)'
      - museum_collection='Berlin' matches 'Vorderasiatisches Museum, Berlin, Germany'

    All filter arguments are optional — pass none to get an unfiltered
    sample (useful for browsing what CDLI looks like). Filters AND
    together when multiple are supplied.

    Args:
        provenience: find-spot substring, e.g. 'Drehem', 'Nippur', 'Uruk'.
        period: historical period substring, e.g. 'Ur III', 'Old Babylonian'.
        museum_collection: holding institution substring, e.g. 'British
                          Museum', 'Yale', 'Berlin'.
        genre: text genre substring, e.g. 'Administrative', 'Literary',
               'Lexical', 'Royal Inscription'.
        language: language substring, e.g. 'Sumerian', 'Akkadian', 'Hittite'.
        limit: max artifacts to return (default 20, cap 200).

    Each result carries the same image / page URLs as lookup_artifact,
    so the agent can offer "see the actual tablet" links for any item
    in the list without a follow-up call.
    """
    limit = max(1, min(200, int(limit)))

    con = _cdli_connect()
    if con is None:
        return ErrorResponse(
            error=f"cdli.sqlite missing at {CDLI_DB}",
            hint="Run `python3 build_cdli_db.py` to build it (~15s after a 147 MB download).",
        )

    where: list[str] = []
    params: list[str] = []
    for col, needle in (
        ("provenience", provenience),
        ("period", period),
        ("museum_collection", museum_collection),
        ("genre", genre),
        ("language", language),
    ):
        if needle and needle.strip():
            where.append(f"{col} LIKE ?")
            params.append(f"%{needle.strip()}%")

    sql_where = ("WHERE " + " AND ".join(where)) if where else ""
    filter_spec = {
        "provenience": provenience,
        "period": period,
        "museum_collection": museum_collection,
        "genre": genre,
        "language": language,
    }

    try:
        total = con.execute(
            f"SELECT COUNT(*) FROM artifacts {sql_where}", params
        ).fetchone()[0]
        rows = con.execute(
            f"SELECT * FROM artifacts {sql_where} "
            "ORDER BY p_id LIMIT ?",
            (*params, limit),
        ).fetchall()
    finally:
        con.close()

    return FindArtifactsResponse(
        filter_spec=filter_spec,
        total_matches=total,
        results=[_build_cdli_artifact(r) for r in rows],
        attribution=CDLI_ATTRIBUTION,
    )


# -----------------------------------------------------------------------------
# Resources
# -----------------------------------------------------------------------------

_GRAMMAR_CACHE: str | None = None
_AGENT_PROMPT_CACHE: str | None = None


def _load_grammar() -> str:
    """Read + cache the Sumerian grammar cheat sheet from disk."""
    global _GRAMMAR_CACHE
    if _GRAMMAR_CACHE is None:
        if not GRAMMAR_DOC.exists():
            return (
                "# prompt/SUMERIAN_GRAMMAR.md missing\n\n"
                f"Expected at {GRAMMAR_DOC}. Re-run the project setup."
            )
        _GRAMMAR_CACHE = GRAMMAR_DOC.read_text(encoding="utf-8")
    return _GRAMMAR_CACHE


def _load_agent_prompt() -> str:
    """Read + cache the agent system prompt from disk."""
    global _AGENT_PROMPT_CACHE
    if _AGENT_PROMPT_CACHE is None:
        if not AGENT_PROMPT_DOC.exists():
            return (
                "# prompt/AGENT_PROMPT.md missing\n\n"
                f"Expected at {AGENT_PROMPT_DOC}. Re-run the project setup."
            )
        _AGENT_PROMPT_CACHE = AGENT_PROMPT_DOC.read_text(encoding="utf-8")
    return _AGENT_PROMPT_CACHE


@mcp.resource(
    "oracc://grammar/sumerian",
    name="Sumerian grammar cheat sheet",
    title="Sumerian grammar (Jagersma 2010) — comprehensive reference",
    description=(
        "A comprehensive Sumerian grammar reference distilled from Bram "
        "Jagersma, A Descriptive Grammar of Sumerian (PhD dissertation, "
        "Universiteit Leiden, 2010, 776 pp). Covers transliteration "
        "conventions, phonology (consonant + vowel inventories, the OS "
        "vowel-harmony rule, syllable-final stop loss, stress), the twelve "
        "enclitic cases with surface-form ambiguity tables, gender + plural, "
        "pronouns + numerals + adjectives, the nine-slot finite-verb template, "
        "perfective vs imperfective inflection patterns (ergative + accusative "
        "+ tripartite alignments by subsystem), all preformatives (vocalic + "
        "modal + negative), the dimensional prefixes (IO/OO/local/comitative/"
        "ablative/terminative), the ventive {mu} and middle {ba}, the four "
        "non-finite forms, copular and nominal clauses, nominalization-based "
        "subordination via {÷a}, period notes for ED/Old Akkadian/Lagash II/"
        "Ur III/OB, and a translation workflow tailored to the tools in this "
        "server. Every grammatical claim carries an inline Jagersma section "
        "citation (e.g. §7.3) for verification. Default period when "
        "unspecified: ED (Early Dynastic, ~2900-2350 BCE) = Jagersma's "
        "primary descriptive ground (Old Sumerian, ED IIIa-IIIb). Fetch this "
        "once per translation session and keep the rules in working memory."
    ),
    mime_type="text/markdown",
)
@_log_call
def grammar_cheatsheet() -> str:
    return _load_grammar()


@mcp.resource(
    "oracc://prompt/agent",
    name="Sumerian translation agent — system prompt",
    title="Agent system prompt: how to use these tools end-to-end",
    description=(
        "A drop-in system prompt teaching an LLM agent the recommended "
        "workflow for using this server's tools: decompose English → rank "
        "candidates with translate_english → check find_compound + "
        "find_collocations for fixed idioms → choose ḫamṭu vs marû aspect "
        "→ apply case suffixes mirrored in the verbal prefix chain → use "
        "find_verb_form / get_inflections to pull attested morphology → "
        "verify with see_examples → render with cuneify. Also covers the "
        "reverse direction (Sumerian → English), the four etcsl_* "
        "literary tools, the CC BY 3.0 UK Oxford-attribution requirement "
        "for any ETCSL-derived data, the required output format "
        "(transliteration + cuneiform + interlinear gloss + lexical "
        "justification + cited attestation + caveats), and a fully "
        "worked example. Fetch once at session start alongside "
        "oracc://grammar/sumerian to bootstrap the agent's working memory."
    ),
    mime_type="text/markdown",
)
@_log_call
def agent_prompt() -> str:
    return _load_agent_prompt()


# ─── Tool wrappers around the two bootstrap resources ─────────────
#
# The MCP spec exposes these as RESOURCES, which spec-complete clients
# discover via resources/list and read via resources/read. But in
# practice many production MCP clients only wire up tools/list (Claude
# variants, agent runtimes, IDE integrations) — for those, the
# bootstrap content is invisible no matter how cleanly the resource is
# declared. These two tools are belt-and-suspenders: they expose the
# same content via the universally-supported tools surface so the
# resource-blind clients can still self-bootstrap. Spec-complete
# clients should prefer the resource form (cheaper, no tool round-trip,
# semantically the right primitive); the tools are a compatibility
# shim, not the architectural primary.


@mcp.tool(annotations=READ_ONLY_ANNOTATIONS)
@_log_call
def start_here() -> str:
    """⭐ CALL THIS FIRST. Returns the Sumerian translation agent's
    system prompt as text — the bootstrap that teaches you how to use
    the rest of the tools end-to-end.

    The returned markdown covers:
      • Recommended workflow for English → Sumerian translation
        (decompose → translate_english → find_compound →
        find_collocations → choose ḫamṭu vs marû aspect → apply
        case suffixes → find_verb_form / get_inflections →
        see_examples → cuneify)
      • Reverse direction (Sumerian → English) tools
      • The four etcsl_* literary tools and when to reach for them
      • REQUIRED Oxford attribution for any ETCSL-derived data
        (CC BY 3.0 UK)
      • Required output format and a fully worked example

    The prompt also instructs you to call `get_grammar_reference()`
    next to fetch the Sumerian grammar cheat sheet for working
    memory. That's the second and final bootstrap step.

    (Spec-complete MCP clients can read this content from the
    `oracc://prompt/agent` resource instead — but most production
    clients only surface tools, so this is exposed as a tool too.)
    """
    return _load_agent_prompt()


@mcp.tool(annotations=READ_ONLY_ANNOTATIONS)
@_log_call
def get_grammar_reference() -> str:
    """Return the Sumerian grammar cheat sheet (Jagersma 2010) as text.

    Call this after start_here(). The returned markdown (~30 KB) is a
    comprehensive Jagersma-2010-based reference covering transliteration
    conventions, phonology, the twelve enclitic cases with ambiguity
    tables, gender/plural, pronouns/numerals/adjectives, the nine-slot
    finite-verb template, perfective vs imperfective inflection,
    preformatives (vocalic + modal + negative), dimensional prefixes,
    ventive + middle, non-finite forms, copular/nominal clauses, and
    nominalization-based subordination. Every grammatical rule carries
    an inline Jagersma section citation for verification.

    Default period for unspecified-period translations: ED (Early
    Dynastic, ~2900-2350 BCE) — Jagersma's primary descriptive ground.

    (Spec-complete MCP clients can read this content from the
    `oracc://grammar/sumerian` resource instead — but most production
    clients only surface tools, so this is exposed as a tool too.)
    """
    return _load_grammar()


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
    # Umami analytics — fire-and-forget tool-call telemetry. Off unless
    # EPSD2_UMAMI_URL + EPSD2_UMAMI_WEBSITE_ID are both set. See
    # umami_analytics.init_from_env() for the env-var contract.
    _umami = umami_analytics.init_from_env()
    if _umami is not None:
        log.info(
            f"  analytics=ENABLED (Umami endpoint={_umami.endpoint}, "
            f"website={_umami.website_id}, hostname={_umami.hostname!r}, "
            f"api_key={'set' if _umami.api_key else 'unset'})"
        )
    else:
        log.info(
            "  analytics=disabled (set EPSD2_UMAMI_URL + "
            "EPSD2_UMAMI_WEBSITE_ID to enable)"
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
