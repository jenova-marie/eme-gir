# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

Pre-1.0 caveat: while the major version is `0`, MINOR-bump releases (`0.2.0`,
`0.3.0`, …) may include breaking changes to MCP tool signatures or response
shapes; PATCH-bump releases (`0.1.1`, `0.1.2`, …) are always backwards
compatible. Once `1.0.0` ships, MAJOR bumps signal breaking changes per
canonical semver.

The `__version__` string in [`eme_gir/__init__.py`](eme_gir/__init__.py) is the
single source of truth; bump it together with the entry below when cutting a
release, and tag the commit with `git tag -a v$VERSION -m "..."`.

## [Unreleased]

### Changed

- **`start_here()` now opens with a license banner** on all four data
  servers (epsd2, ogsl, etcsl, cdli). A `license_banner()` helper in
  `eme_gir/attribution.py` prepends a "FIRST ACTION — show the user the
  data license" directive plus the canonical `*_ATTRIBUTION` text to the
  bootstrap output, so the warm-up ritual ("use the start_here tool of
  mcp servers …") prompts the agent to immediately surface each server's
  license. Sourced from the single-source constants, so it can't drift.

### Documentation

- **Aligned the four `start_here` bootstrap docs with the new attribution
  machinery.** `prompt/{EPSD2,OGSL,ETCSL,CDLI}_PROMPT.md` now tell the agent
  about the `citation_short` + `presentation` response fields, the
  `display_markdown` blocks on quotable results, and the per-server
  `license://…` MCP resource — so the bootstrap layer reinforces the
  per-call layer instead of drifting from it. (Edits take effect on server
  restart; `load_prompt` caches read-once.)
- **Added a terms-acceptance line** ("By calling these tools you accept the
  source's terms of use.") to each data server's `make_server(instructions=)`.

### Fixed

- **Corrected the data-license statements in the MCP server `instructions`
  for all four data servers.** They previously stated the wrong licenses
  (`servers/epsd2` and `servers/cdli` said "CC0"; `servers/etcsl` said
  "CC BY 3.0 UK"). They now match `LICENSE-DATA.md` and the `*_ATTRIBUTION`
  constants: ePSD2 / OGSL = CC BY-SA 3.0; ETCSL = traditional academic
  copyright (NOT Creative Commons) with a required citation; CDLI =
  catalogue text reusable with citation, imagery non-commercial only. Also
  fixed the same "CC BY 3.0 UK" / "CC0" wording in the `eme_gir/models/etcsl.py`
  and `eme_gir/models/cdli.py` field descriptions and module docstrings.

### Changed

- **Umami analytics — split into two properties.** Server-side
  per-tool-call MCP events now go to a dedicated MCP property
  (`EME_GIR_UMAMI_MCP_ID`); browser-side click + pageview events from
  the Flask web (epsd2) and www landing apps go to the website
  property (`EME_GIR_UMAMI_WEBSITE_ID`). The legacy single-property
  mode is still honored — if `MCP_ID` is unset, the MCP client falls
  back to `WEBSITE_ID` with a one-time deprecation warning, so
  pre-split deployments keep working. See the "Umami analytics —
  two-property split" section in `CLAUDE.md` for the full env-var
  contract.
- **MCP startup banner** now reads
  `analytics=disabled (set EME_GIR_UMAMI_URL + EME_GIR_UMAMI_MCP_ID
  to enable)` to point operators at the new env var.

### Added

- **`citation_short` + `presentation` fields on every tool response**
  across the epsd2, ogsl, etcsl, and cdli servers. `citation_short` is a
  one-line attribution token (e.g. `ePSD2 (CC BY-SA 3.0)`); `presentation`
  is a point-of-use instruction telling the agent to reproduce it. Added
  as defaults on new per-domain response base classes
  (`_EPSD2Response`, `_ETCSLResponse`, `_CDLIResponse`, `_OGSLResponse`),
  so the ~20 existing tool call sites are unchanged.
- **`display_markdown` field on the four "quotable-unit" response shapes**
  — `CuneifyResponse` (glyphs + cite, with a `□` disclosure when a sign is
  unresolved), `AttestationLine` (cited line + CDLI link + dual ePSD2/CDLI
  cite, used by `see_examples` / `find_verb_form`), the ETCSL line/hit
  shapes (bilingual block + Oxford cite), and `CDLIArtifact` (one-line
  link + cite). The citation is fused into the block so it survives
  synthesis in generic chat clients.
- **`license://…` MCP resources on each data server** —
  `license://oracc-epsd2`, `license://oracc-ogsl`, `license://etcsl`,
  `license://cdli` — serving the full verbatim attribution so the per-call
  `citation_short` can stay short.
- **`eme_gir/attribution.py`** — single-source module holding every
  corpus's full attribution, short citation, and presentation strings,
  plus a `make_license_body` factory for the resources. The four
  `*_ATTRIBUTION` constants are re-exported from their original
  `eme_gir/tools/*.py` locations for backwards compatibility.
- **`EME_GIR_UMAMI_MCP_ID` env var** — dedicated MCP property UUID,
  separate from the website property. Plumbed through the
  `x-mcp-environment` anchor in `docker-compose.yml` so every MCP
  service receives it.
- **Browser-side analytics on the ePSD2 verification web app**
  (`templates/base.html`) — `<script defer src=".../script.js"
  data-website-id="..." data-cache="true">` embed is rendered only
  when both `EME_GIR_UMAMI_URL` and `EME_GIR_UMAMI_WEBSITE_ID` are
  set in the Flask app environment. 12 distinct click events
  instrumented: `masthead-logo`, `masthead-title`, `masthead-epsd2`,
  `letter-nav` (with `letter` data attribute), `search-submit`,
  `attribution-oracc-epsd2`, `attribution-oracc`,
  `attribution-cc-license`, `attribution-licensing-terms`,
  `attribution-oracc-canonical`, `footer-cc-license`,
  `footer-oracc-source`.
- **Browser-side analytics on the eme-gir.org landing page**
  (`templates/www.html`) — same gated embed; 6 distinct event types
  across 20+ elements: `service-card` (with `target` data attribute
  per card), `endpoint-url-click` and `endpoint-url-copy` (each with
  `server` data attribute per MCP endpoint), `external-link` (Oracc,
  ETCSL, CDLI, modelcontextprotocol.io, LICENSE-DATA),
  `license-link` (per source in the licensing table), `footer-link`.
- **`EME_GIR_UMAMI_URL` + `EME_GIR_UMAMI_WEBSITE_ID` now plumbed to
  the `web` and `www` services** in `docker-compose.yml` so the
  Flask apps can render the browser-side `<script>` tag in
  production. `app.py:create_app()` and `www_app.py:create_app()`
  read both env vars and expose them as `UMAMI_URL` /
  `UMAMI_WEBSITE_ID` Jinja context.

### Privacy

- **Server-side privacy boundary preserved.** MCP events continue to
  carry only tool names, arg-key names, latency, success/error
  counts, and result-item counts — never tool argument values, query
  strings, result content, IPs, session IDs, or Auth0 client
  identifiers. The boundary lives in `eme_gir/umami_analytics.py`
  and is reiterated in the new CLAUDE.md section.
- **Browser-side opt-out is fully transparent.** When any of
  `EME_GIR_UMAMI_URL`, `EME_GIR_UMAMI_WEBSITE_ID`, or
  `EME_GIR_UMAMI_MCP_ID` is unset, the relevant surface stays
  silent: MCP server logs `analytics=disabled`; the browser
  templates emit no `<script>` tag at all. `data-umami-event`
  attributes remain as harmless no-ops in the HTML.

### Documentation

- New `CLAUDE.md` section **Umami analytics — two-property split**
  covers the env-var contract, the privacy boundary, the
  backwards-compat fallback path, and the disable behavior. Sized
  to fit between Reverse-proxy headers and Containerization in the
  ops-concerns block.

## [0.1.0] — 2026-06-01

Initial tagged release. Establishes the project's public surface area —
five MCP servers, a local Oracc verification web app, a project landing
page, the Ummia teaching curriculum, and the data pipeline that builds
all of it from the upstream academic archives.

### Added

- **Five Model Context Protocol servers** along clean data-source
  boundaries, each independently deployable:
  - `eme-gir-epsd2` (port 5052) — 11 ePSD2 dictionary + corpus tools
    over a 3.4 GB SQLite index of 15,940 headwords and 35.5M attestations
  - `eme-gir-etcsl` (port 5053) — 4 bilingual Oxford literary-corpus
    tools over the 394-text ETCSL with FTS5 on Sumerian + English
  - `eme-gir-cdli` (port 5054) — 2 CDLI artifact-catalogue tools over
    the 353K-row provenience index, with photo / line-drawing URLs
    pointing directly at cdli.earth
  - `eme-gir-ogsl` (port 5055) — 2 cuneiform-sign tools (cuneify +
    lookup_sign) usable for Akkadian / Hittite / Hurrian / Elamite too
  - `eme-gir-ummia` (port 5058) — teaching surface in the persona of
    Ummia 𒌝𒈪𒀀 (Sumerian master scribe), shipping a five-lesson
    Sumerian 101 curriculum + the dual-register grammar reference
  - The legacy all-in-one `mcp_server.py` (port 5051) remains for
    backwards compatibility, re-exporting every tool in one process

- **Pagination contract** on 8 of 14 list-returning tools: uniform
  `offset` / `next_offset` / `total_matches` shape so an agent that
  learns the idiom on one tool can use it on any of them. Currently
  paginated: `translate_english`, `find_artifacts`,
  `find_phrase_pattern` (both branches), `find_collocations`,
  `analyze_form`, `etcsl_search_english`, `etcsl_search_sumerian`,
  `etcsl_lines_with_lemma`. `etcsl_lookup_text` keeps its earlier
  `start` / `next_start` (1-based ord) pattern.

- **ePSD2 verification web app** at `https://epsd2.eme-gir.org` —
  Flask + gunicorn-served local mirror of
  oracc.museum.upenn.edu/epsd2 for 1:1 corpus validation. CC BY-SA 3.0
  attribution banner pinned to every page; cuneiform-glyph rendering
  alongside every spelling.

- **Project landing page** at `https://eme-gir.org` / `https://www.eme-gir.org` —
  academic about-block sourced from the README, scope-and-purpose
  framing, MCP endpoints with drop-in client configuration, and
  step-by-step bootstrap prompts for both research and teaching paths.

- **Dual-register Sumerian grammar reference** (~80 KB combined) —
  Jagersma 2010 academic descriptive grammar + Meadow + Siri Nin temple
  liturgical companion. Exposed both as the MCP resource
  `oracc://grammar/sumerian` and via the `get_grammar_reference()`
  tool for resource-blind clients.

- **Auth0 OAuth 2.1 bearer-token support** on the HTTP transport
  (opt-in via `EME_GIR_REQUIRE_AUTH=1`), with RFC 9728 Protected
  Resource Metadata served at the host apex.

- **Reverse-proxy support** — DNS-rebinding allowlist
  (`EME_GIR_ALLOWED_HOSTS`) and `X-Forwarded-Proto` honoring
  (`EME_GIR_TRUST_PROXY=1`) for deployments behind Caddy / nginx /
  traefik.

- **Docker Compose stack** (`docker-compose.yml`) — eight services
  including init container, gunicorn web app, gunicorn www landing,
  and all five MCP servers, with `--max-requests` worker recycling
  for memory hygiene.

- **CI/CD via Forgejo Actions** — `linux/arm64` image builds pushed
  to AWS ECR on every `prod` push, with `latest` / `<branch>` /
  `sha-<short>` tags.

- **Continuous Integration restriction** — Forgejo builds fire only
  on `prod` pushes (`branches: [prod]`), so feature-branch work no
  longer churns ECR.

- **MCP server version handshake** — every server now advertises
  `serverInfo.version` to clients during `initialize`, sourced from
  `eme_gir.__version__`. Single source of truth; surfaced in the
  startup banner too.

### Project surface as of 0.1.0

| Surface | Count |
|---|---:|
| MCP servers | 5 (+ 1 legacy all-in-one) |
| MCP tools | 21 |
| Tools with pagination | 8 of 14 list-returning (57%) |
| MCP resources | 2 (`oracc://prompt/agent`, `oracc://grammar/sumerian`) |
| Sumerian headwords (ePSD2) | 15,940 |
| Attestation references | 35.5M |
| Corpus zips (Oracc) | 208 (~3.1 GB) |
| ETCSL literary compositions | 394 (bilingual) |
| CDLI artifact records | 353,283 |
| Cuneiform-sign coverage (OGSL) | ~93% of glossary spellings |
| Sumerian 101 lessons (Ummia) | 5 |

### Data licensing

- **Oracc / ePSD2 / OGSL** — CC BY-SA 3.0 Unported (attribution
  required, ShareAlike propagates)
- **ETCSL** — academic copyright with required citation; redistribution
  posture documented in [LICENSE-DATA.md](LICENSE-DATA.md)
- **CDLI** — catalogue text reusable with citation per CDLI's terms;
  imagery non-commercial only; no imagery hosted by this project (all
  image URLs link directly to cdli.earth)
- **This repository's code** — MIT ([LICENSE](LICENSE))

[Unreleased]: https://github.com/jenova-marie/eme-gir/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/jenova-marie/eme-gir/releases/tag/v0.1.0
