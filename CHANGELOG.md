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
