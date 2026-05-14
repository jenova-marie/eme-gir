"""MCP server exposing the local Eme-gir corpus for English -> Sumerian translation.

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

import os
import sqlite3
import sys
from pathlib import Path
from typing import Any

from mcp.server.fastmcp import FastMCP
from mcp.types import ToolAnnotations

from eme_gir import cdli as _cdli
from eme_gir import cuneify as _cuneify
from eme_gir import text_resolver
from eme_gir import umami_analytics
from eme_gir.models import (
    AnalyzeFormResponse,
    CaseChunk,
    ErrorResponse,
    FindCollocationsResponse,
    FindCompoundResponse,
    FindPhrasePatternResponse,
    FindVerbFormResponse,
    GetInflectionsResponse,
    GrammarReferenceResponse,
    LookupEntryResponse,
    ParsePhraseResponse,
    SeeExamplesResponse,
    Suffix,
    TranslateEnglishResponse,
    TranslateSumerianResponse,
)
from eme_gir.paths import (
    COLLOCATIONS_DB,
    GLOSSARY_DB,
    GRAMMAR_DOC,
    INFLECTED_COLLOCATIONS_DB,
    ROOT,
    MEADOW_GRAMMAR_DOC,
    TEXT_INDEX_DB,
)

# Logging + per-tool-call telemetry decorator are now provided by the
# shared `eme_gir.log` module so every MCP server in the suite uses the
# same configuration. `init_logging("mcp_server")` configures the root
# logger (stderr + log/mcp_server.log rotating file) and returns the
# package's `eme-gir` logger; the `log_call` decorator wraps each tool
# function for entry/exit/timing logs + umami analytics emission. The
# alias preserves the pre-extraction `@_log_call` decorator usage at
# every tool definition below.
from eme_gir.log import init_logging, log_call as _log_call

log = init_logging("mcp_server")

def _build_auth_kwargs() -> dict:
    """Read EME_GIR_AUTH0_* env vars and return auth/token_verifier kwargs.

    Returns an empty dict (auth disabled) unless EME_GIR_REQUIRE_AUTH=1.
    When enabled, returns {'auth': AuthSettings, 'token_verifier': Auth0TokenVerifier}
    suitable for splatting into the FastMCP constructor.

    Auth is OPT-IN and only meaningful for the streamable-HTTP transport;
    stdio runs unauthenticated regardless (per MCP spec, stdio uses
    environment-based credentials, not OAuth). The transport check
    happens at run() time — if EME_GIR_REQUIRE_AUTH=1 is set but stdio is
    selected, the constructed verifier sits idle, which is harmless.

    Required env vars when EME_GIR_REQUIRE_AUTH=1:
        EME_GIR_AUTH0_TENANT_URL          e.g. https://my-tenant.auth0.com
        EME_GIR_AUTH0_AUDIENCE            e.g. https://eme-gir.example.com
        EME_GIR_AUTH0_RESOURCE_SERVER_URL e.g. https://eme-gir.example.com
                                        (the public-facing URL of THIS
                                        server; goes into the RFC 9728
                                        Protected Resource Metadata)
    Optional:
        EME_GIR_AUTH0_REQUIRED_SCOPE      defaults to 'mcp:access'
    """
    # Accept the conventional set of truthy strings so operators don't have
    # to remember our exact magic string. Anything not in this set (incl.
    # unset, "0", "false", "off", "no") leaves auth disabled.
    if os.environ.get("EME_GIR_REQUIRE_AUTH", "").strip().lower() not in {
        "1", "true", "on", "yes", "y", "enable", "enabled",
    }:
        return {}

    # Lazy imports — pyjwt + the SDK auth modules aren't needed unless
    # the operator opts in. Keeps cold-start fast for the no-auth path
    # and avoids a hard dep failure if pyjwt isn't installed in stdio
    # dev environments.
    from mcp.server.auth.settings import AuthSettings
    from pydantic import AnyHttpUrl

    from eme_gir.auth0_verifier import Auth0TokenVerifier

    tenant_url = os.environ.get("EME_GIR_AUTH0_TENANT_URL", "").strip()
    audience = os.environ.get("EME_GIR_AUTH0_AUDIENCE", "").strip()
    resource_server_url = os.environ.get(
        "EME_GIR_AUTH0_RESOURCE_SERVER_URL", ""
    ).strip()
    required_scope = os.environ.get("EME_GIR_AUTH0_REQUIRED_SCOPE", "mcp:access").strip()

    missing = [
        name
        for name, value in [
            ("EME_GIR_AUTH0_TENANT_URL", tenant_url),
            ("EME_GIR_AUTH0_AUDIENCE", audience),
            ("EME_GIR_AUTH0_RESOURCE_SERVER_URL", resource_server_url),
        ]
        if not value
    ]
    if missing:
        raise RuntimeError(
            f"EME_GIR_REQUIRE_AUTH=1 but missing env vars: {', '.join(missing)}. "
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
    """Read EME_GIR_ALLOWED_HOSTS / _ORIGINS / _DISABLE_DNS_REBINDING_PROTECTION
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
        EME_GIR_ALLOWED_HOSTS    comma-separated; the public hostname(s)
                               that the reverse proxy serves us under.
                               localhost + 127.0.0.1 are always added so
                               in-container healthchecks keep working.
                               e.g. "eme-gir.intra.example.net,eme-gir.example.com"
        EME_GIR_ALLOWED_ORIGINS  comma-separated; the Origin headers we
                               accept on cross-origin requests (browser
                               clients). Stricter than allowed_hosts —
                               no auto-additions.
                               e.g. "https://archive.example.org"
        EME_GIR_DISABLE_DNS_REBINDING_PROTECTION
                               truthy → disable the check entirely.
                               Only safe when the reverse proxy already
                               enforces Host validation upstream.

    Returns {} when no env vars are set (SDK uses its localhost-only
    default — fine for local dev). When ANY of them is set, returns
    {'transport_security': TransportSecuritySettings(...)}.
    """
    raw_hosts = os.environ.get("EME_GIR_ALLOWED_HOSTS", "").strip()
    raw_origins = os.environ.get("EME_GIR_ALLOWED_ORIGINS", "").strip()
    disable = os.environ.get(
        "EME_GIR_DISABLE_DNS_REBINDING_PROTECTION", ""
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
    name="oracc-eme-gir",
    instructions=(
        "Local Sumerian dictionary + corpus tools for English ↔ Sumerian "
        "translation, grounded in the Oracc / Eme-gir dataset (15,940 headwords, "
        "35.5 M attestations, 178K phrasal collocations, 138K corpusjson texts). "
        "All data is CC0; no network calls.\n\n"
        "════════════════════════════════════════════════════════════════════\n"
        "FIRST STEP, BEFORE ANY TOOL CALL: read these two resources via the "
        "MCP `resources/read` request. They are your bootstrap context — "
        "without them, tool calls will be uninformed.\n"
        "  • oracc://prompt/agent      — your full system prompt: the workflow, "
        "the required output format, the ETCSL attribution rule, and a worked "
        "example. Read this FIRST so the rest of the instructions make sense.\n"
        "  • oracc://grammar/sumerian  — TWO grammar references concatenated: "
        "(1) the comprehensive Jagersma-2010-based academic reference "
        "(twelve enclitic cases, phonology, the nine-slot finite-verb "
        "template, perfective vs imperfective inflection, modal/negative "
        "preformatives, non-finite forms, nominalization-based subordination "
        "— every rule §-cited to Jagersma), followed by (2) the temple-"
        "register companion from Meadow's Sumerian 101 classroom-e₂-nun-na "
        "lessons + Siri Nin's commentary (the PNC mnemonic, the 'pesky -a' "
        "three-tip heuristic, the Emesal liturgical register, worked temple "
        "examples). Use academic part for rigor, temple part for prayer "
        "composition. Read this SECOND so you can reason about morphology "
        "when tool results return inflected forms.\n"
        "Both resources are markdown — the agent prompt is ~10–15 KB, the "
        "combined grammar is ~80 KB. They only need to be fetched ONCE per "
        "session — keep them in working memory thereafter.\n"
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

# Every tool in this server is a read-only SQLite query against a local
# index — no mutations, no side effects, idempotent. Setting these
# annotations correctly avoids the pessimistic UI badges (PUBLIC WRITE /
# DESTRUCTIVE / OPEN WORLD) some MCP clients show by default.
READ_ONLY_ANNOTATIONS = ToolAnnotations(
    readOnlyHint=True,
    destructiveHint=False,
    idempotentHint=True,
    openWorldHint=False,
)

# -----------------------------------------------------------------------------
# ePSD2 dictionary + corpus tools
# -----------------------------------------------------------------------------
#
# All thirteen ePSD2 tools (translate_english, lookup_entry, see_examples,
# find_compound, get_inflections, analyze_form, translate_sumerian,
# parse_phrase, find_collocations, find_phrase_pattern, find_verb_form +
# the lookup_sign / cuneify pair) now live in `eme_gir.tools.epsd2`.
# Helper functions (DB connection, period resolver, casefold-version
# check, entry payload builder, verb-form synthesis helpers) moved with
# them. We register the tools with this server's FastMCP instance below;
# Phase 5 will split this into per-server entry points.

from eme_gir.tools.epsd2 import (
    analyze_form as _analyze_form_impl,
    find_collocations as _find_collocations_impl,
    find_compound as _find_compound_impl,
    find_phrase_pattern as _find_phrase_pattern_impl,
    find_verb_form as _find_verb_form_impl,
    get_inflections as _get_inflections_impl,
    lookup_entry as _lookup_entry_impl,
    parse_phrase as _parse_phrase_impl,
    see_examples as _see_examples_impl,
    translate_english as _translate_english_impl,
    translate_sumerian as _translate_sumerian_impl,
)

translate_english = mcp.tool(annotations=READ_ONLY_ANNOTATIONS)(_translate_english_impl)
lookup_entry = mcp.tool(annotations=READ_ONLY_ANNOTATIONS)(_lookup_entry_impl)
see_examples = mcp.tool(annotations=READ_ONLY_ANNOTATIONS)(_see_examples_impl)
find_compound = mcp.tool(annotations=READ_ONLY_ANNOTATIONS)(_find_compound_impl)
get_inflections = mcp.tool(annotations=READ_ONLY_ANNOTATIONS)(_get_inflections_impl)
analyze_form = mcp.tool(annotations=READ_ONLY_ANNOTATIONS)(_analyze_form_impl)
translate_sumerian = mcp.tool(annotations=READ_ONLY_ANNOTATIONS)(_translate_sumerian_impl)
parse_phrase = mcp.tool(annotations=READ_ONLY_ANNOTATIONS)(_parse_phrase_impl)
find_collocations = mcp.tool(annotations=READ_ONLY_ANNOTATIONS)(_find_collocations_impl)
find_phrase_pattern = mcp.tool(annotations=READ_ONLY_ANNOTATIONS)(_find_phrase_pattern_impl)
find_verb_form = mcp.tool(annotations=READ_ONLY_ANNOTATIONS)(_find_verb_form_impl)




# lookup_sign now lives in eme_gir.tools.ogsl and is registered with
# this server's FastMCP instance below the cuneify tool (we keep them
# together since both belong to the same domain).


# cuneify + lookup_sign are now defined in eme_gir.tools.ogsl.
# Registration shim:
from eme_gir.tools.ogsl import cuneify as _cuneify_tool_impl
from eme_gir.tools.ogsl import lookup_sign as _lookup_sign_impl

cuneify = mcp.tool(annotations=READ_ONLY_ANNOTATIONS)(_cuneify_tool_impl)
lookup_sign = mcp.tool(annotations=READ_ONLY_ANNOTATIONS)(_lookup_sign_impl)


# -----------------------------------------------------------------------------
# ETCSL tools (Sumerian literary corpus, Oxford 2006)
# -----------------------------------------------------------------------------
#
# ETCSL tool implementations now live in `eme_gir.tools.etcsl`. The
# ETCSL_ATTRIBUTION constant (REQUIRED to display under CC BY 3.0 UK)
# moved with them. We register the four tools with this server's
# FastMCP instance below.

from eme_gir.tools.etcsl import etcsl_lines_with_lemma as _etcsl_lines_with_lemma_impl
from eme_gir.tools.etcsl import etcsl_lookup_text as _etcsl_lookup_text_impl
from eme_gir.tools.etcsl import etcsl_search_english as _etcsl_search_english_impl
from eme_gir.tools.etcsl import etcsl_search_sumerian as _etcsl_search_sumerian_impl

etcsl_search_english = mcp.tool(annotations=READ_ONLY_ANNOTATIONS)(_etcsl_search_english_impl)
etcsl_lines_with_lemma = mcp.tool(annotations=READ_ONLY_ANNOTATIONS)(_etcsl_lines_with_lemma_impl)
etcsl_lookup_text = mcp.tool(annotations=READ_ONLY_ANNOTATIONS)(_etcsl_lookup_text_impl)
etcsl_search_sumerian = mcp.tool(annotations=READ_ONLY_ANNOTATIONS)(_etcsl_search_sumerian_impl)


# -----------------------------------------------------------------------------
# CDLI artifact catalogue
# -----------------------------------------------------------------------------
#
# CDLI tool implementations now live in `eme_gir.tools.cdli`; the
# connection helper + the cross-domain enrichment function (used by
# see_examples / find_verb_form to splat photo/lineart/museum metadata
# onto each AttestationLine) live in `eme_gir.cdli`. We register the
# two CDLI tools with this server's FastMCP instance via the standard
# `mcp.tool(...)` decorator pattern; the per-tool docstrings + log_call
# decorator are preserved at the definition site in eme_gir.tools.cdli.


from eme_gir.tools.cdli import find_artifacts as _find_artifacts_impl
from eme_gir.tools.cdli import lookup_artifact as _lookup_artifact_impl

lookup_artifact = mcp.tool(annotations=READ_ONLY_ANNOTATIONS)(_lookup_artifact_impl)
find_artifacts = mcp.tool(annotations=READ_ONLY_ANNOTATIONS)(_find_artifacts_impl)




# -----------------------------------------------------------------------------
# Grammar reference resource + tool wrapper
# -----------------------------------------------------------------------------
#
# The dual-register Sumerian grammar reference (Jagersma 2010 academic +
# Meadow / Siri Nin temple companion) lives in `eme_gir.tools.ummia`. We
# expose it here as both an MCP resource and a tool wrapper for
# tools-only clients. The per-server `start_here()` bootstraps on the
# five per-domain MCPs are the canonical entry points; the legacy
# all-in-one server keeps the grammar surface for backwards compat with
# pre-Phase-5 clients pointed at port 5051.

from eme_gir.tools.ummia import (
    get_grammar_reference as _get_grammar_reference_impl,
)
from eme_gir.tools.ummia import grammar_cheatsheet as _grammar_cheatsheet_body


grammar_cheatsheet = mcp.resource(
    "oracc://grammar/sumerian",
    name="Sumerian grammar — academic + temple references",
    title="Sumerian grammar: Jagersma 2010 + Meadow's temple-register lessons",
    description=(
        "Two grammar references concatenated. FIRST: the academic reference "
        "distilled from Bram Jagersma, A Descriptive Grammar of Sumerian "
        "(PhD dissertation, Universiteit Leiden, 2010, 776 pp) — "
        "transliteration conventions, phonology, the twelve enclitic cases "
        "with surface-form ambiguity tables, gender + plural, pronouns + "
        "numerals + adjectives, the nine-slot finite-verb template, "
        "perfective vs imperfective inflection patterns (ergative + "
        "accusative + tripartite alignments by subsystem), all preformatives, "
        "dimensional prefixes, ventive {mu} and middle {ba}, the four "
        "non-finite forms, copular and nominal clauses, nominalization-based "
        "subordination via {÷a}, period notes for ED/Old Akkadian/Lagash II/"
        "Ur III/OB. Every grammatical claim carries an inline Jagersma "
        "section citation (e.g. §7.3) for verification. SECOND: the temple-"
        "register companion (MEADOW_GRAMMAR.md) distilled from Meadow's "
        "Sumerian 101 classroom-e₂-nun-na lessons plus Entu Siri Nin's "
        "commentary — prayer-ready pedagogy, the PNC mnemonic, the 'pesky -a' "
        "three-tip heuristic, the Emesal liturgical register, and worked "
        "temple examples. Cite as (Jagersma §N.M) for the academic claims "
        "and (Meadow §101-N) or (Siri Nin) for the temple claims. Default "
        "period when unspecified: ED (Early Dynastic, ~2900-2350 BCE) = "
        "Jagersma's primary descriptive ground. Fetch once per translation "
        "session and keep both in working memory."
    ),
    mime_type="text/markdown",
)(_grammar_cheatsheet_body)

# Tool wrapper around the grammar resource (compat shim for tools-only
# clients that don't surface MCP resources):
get_grammar_reference = mcp.tool(annotations=READ_ONLY_ANNOTATIONS)(_get_grammar_reference_impl)


# -----------------------------------------------------------------------------
# Entrypoint
# -----------------------------------------------------------------------------

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(
        prog="mcp_server.py",
        description=(
            "Run the eme-gir MCP server. Default transport is stdio (used by "
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
    log.info(f"eme-gir MCP server starting (cwd={Path.cwd()}, root={ROOT})")
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
            f"audience={os.environ.get('EME_GIR_AUTH0_AUDIENCE')}, "
            f"required_scopes={mcp.settings.auth.required_scopes})"
        )
    else:
        log.info("  auth=disabled (set EME_GIR_REQUIRE_AUTH=1 to enable)")
    # Transport-security (DNS-rebinding) banner — confirms which Host
    # header values uvicorn will accept. Default (no env vars set) is
    # the SDK's localhost-only allowlist; behind a reverse proxy this
    # MUST be widened or every request returns 421 Invalid Host header.
    ts = mcp.settings.transport_security
    if ts is None:
        log.info(
            "  transport_security=default (SDK accepts Host: localhost / "
            "127.0.0.1 only — set EME_GIR_ALLOWED_HOSTS to add the public "
            "hostname when deploying behind a reverse proxy)"
        )
    elif not ts.enable_dns_rebinding_protection:
        log.warning(
            "  transport_security=DISABLED (EME_GIR_DISABLE_DNS_REBINDING_PROTECTION "
            "is set — proxy MUST enforce Host validation upstream)"
        )
    else:
        log.info(
            f"  transport_security=ENABLED (allowed_hosts={ts.allowed_hosts}, "
            f"allowed_origins={ts.allowed_origins})"
        )
    # Umami analytics — fire-and-forget tool-call telemetry. Off unless
    # EME_GIR_UMAMI_URL + EME_GIR_UMAMI_WEBSITE_ID are both set. See
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
            "  analytics=disabled (set EME_GIR_UMAMI_URL + "
            "EME_GIR_UMAMI_WEBSITE_ID to enable)"
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
                "for TLS + access control. Set EME_GIR_REQUIRE_AUTH=1 to enable "
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
