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

- **Added a `© 2026 Jenova Marie` copyright notice to the landing-page
  footer** (`templates/www.html`). The notice establishes authorship
  of the original creative work (website copy, layout, project
  framing, build scripts, prompt docs) without contradicting the MIT
  grant on the code or the separately-held copyrights on the data
  layer (Oracc CC BY-SA 3.0, ETCSL academic, CDLI mixed). The footer
  now reads `© 2026 Jenova Marie · Code released under MIT · Data
  carries source licenses (see above) · Source on GitHub`; the
  earlier "Built by Jenova Marie" wording is folded into the ©
  attribution and the MIT label becomes a direct link to the LICENSE
  file. The Jenova Marie name still links to the GitHub profile; new
  MIT link fires `data-umami-event-target="mit-license"` alongside
  the existing footer-link telemetry.

### Documentation

- **Refocused `README.md` on the MCP-server framing** as the project's
  primary surface, with the local ePSD2 web browser repositioned as a
  complementary 1:1 verification feature against the canonical
  `oracc.museum.upenn.edu/epsd2` rather than as a co-equal "second
  project". The opening paragraph now leads with "A Sumerian-language
  MCP tool server for LLM agents" and names the five servers; the
  "Two projects in one repository" framing is replaced by "Primary
  surface — five MCP servers" + "Additional feature — the ePSD2
  verification browser". Updated the stale `eme-gir-translator` (port
  5056, deprecated) server-table row to `eme-gir-ummia` (port 5058,
  the current teaching surface persona). Reordered the "What this
  enables" subsections to put LLM applications first ahead of
  Sumerologists. Redrew the architecture diagram so the MCP-servers
  box leads and the verification browser is the secondary box; the
  Ummia row replaces the old `eme-gir-trans :5056` row. Renamed the
  remaining `/eme-gir/sux` URL path to `/epsd2/sux` to match the
  current Flask route, and changed every "the web app" / "Flask web
  app" reference in the body copy to "the verification browser" so
  the framing carries through.

- **Compacted `CLAUDE.md` from 605 lines to ~210 lines** by extracting
  the deep technical reference material to a new
  [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md). CLAUDE.md now stays
  focused on what every agent needs every session: the four-layer repo
  overview, the daily-use commands table, the versioning + CHANGELOG
  upkeep policy (the most important rule), the Claude Code stdio
  wiring (including the critical "subprocess caches old code on import"
  gotcha), the TLS chain workaround, and the data-license summary.
  Sections moved verbatim to `docs/ARCHITECTURE.md`: reverse-
  engineered Oracc URL surface, Oracc JSON Open Data format parser
  reference, `glossary.sqlite` schema, local browser internals, the
  full MCP servers tool table, ETCSL build details, transport modes
  (stdio vs streamable-HTTP), OAuth 2.1 / Auth0 authorization,
  transport security / DNS-rebinding allowlist, reverse-proxy headers
  / `X-Forwarded-Proto`, Umami analytics two-property split,
  containerization (Dockerfile + compose + init.sh), logging,
  cuneiform rendering, attestation rendering, and corpus project-name
  conventions. CLAUDE.md gains a "Where to find deeper material"
  pointer block at the top listing `docs/ARCHITECTURE.md`,
  `LICENSE-DATA.md`, `CHANGELOG.md`, and `prompt/*_PROMPT.md`.
  Trade-off: agents now need one extra hop (open
  `docs/ARCHITECTURE.md`) when they want deep technical detail, but
  the routine read of CLAUDE.md at session start drops from ~28K
  tokens to ~9K tokens of memory budget.

### Added

- **New "Development & contribution" section on the landing page**
  (`templates/www.html`, `#development` anchor, positioned between
  Data sources & licenses and the footer). Introduces visitors to
  the open-source nature of the project, the MIT licensing of the
  code, and the paths for engagement. A 4-card grid covers Source
  (MIT, GitHub), Tech stack (Python 3.12+, Flask, FastMCP, SQLite,
  Docker), Self-host (one-line `docker compose up`), and Public
  deployment (small AWS Docker Swarm, Graviton arm64, free while
  infrastructure permits). Below the grid, a two-paragraph lede
  block covers "🤝 Get involved" (PRs, bug reports, feature
  requests, questions on GitHub Issues; explicit invitation to
  Sumerologists to flag scholarly issues in translations, sense
  ranking, attestations) and "💝 Sponsorship" (transparent about
  the public instance being a personal investment, framed as
  "sponsorship keeps the public surface free for everyone else"
  rather than as a request). Reuses the existing `.services` /
  `.service` card grid CSS for visual consistency with the
  Services section above; clickable cards become `<a>` with hover
  lift, info-only cards become `<div>` with default cursor. Each
  link / card click fires `data-umami-event` with one of seven
  distinct `data-umami-event-target` values (`github-source`,
  `self-host`, `github-issues`, `github-new-issue`, `mit-license`,
  `claude-md`, `changelog`) so analytics can show which
  contribution path visitors actually take.

### Changed

- **Consolidated the two `.prompt-reissue` callouts under each Path
  A and Path B prompt-box** (`templates/www.html`) into a single
  combined statement at the bottom of the "How to use" section.
  The new closing paragraph fuses three pieces of guidance into one
  place: (1) both bootstrap calls are idempotent, (2) after the
  handshake just ask in natural language and the loaded context
  picks which server to use, and (3) re-issue periodically when
  drift sets in — covering BOTH the Path A symptoms (skipping the
  `sense_count`/`sense_pct` ranking, omitting cited links) AND the
  Path B symptoms (Ummia persona voice flattening, scribal frame
  slipping, drills getting skipped). Removes ~20 lines of
  duplicated callout markup, drops the orphaned `.prompt-reissue`
  CSS class, and gives the message one canonical landing spot the
  reader encounters AFTER seeing both paths rather than two
  parallel asides nested mid-section.
- **Strengthened the CHANGELOG upkeep rule in `CLAUDE.md`** to
  cover EVERY source modification, not just "user-visible" changes.
  Previously the rule excluded pure refactors, comment polish, CI
  tooling, and test additions; now those each get their own
  appropriate subsection (`### Changed`, `### Documentation`,
  `### Fixed`). Closing line: "When in doubt, log it. The cost of
  an extra bullet is trivial; the cost of a missing one is
  invisible drift that bites at release time when nobody can
  reconstruct what changed."
- **Unified both bootstrap prompts on the landing page**
  (`templates/www.html`) to the glob-style
  `"use the start_here tool of all eme-gir-* mcp servers"` —
  replacing Path A's explicit four-server enumeration
  (`eme-gir-epsd2, eme-gir-etcsl, eme-gir-cdli, eme-gir-ogsl`) AND
  Path B's Ummia-only call (`eme-gir-ummia`). Shorter, easier to
  remember, and resilient to future server additions: any new
  `eme-gir-*` server gets bootstrapped automatically without
  having to update the landing page. The two paths still
  differentiate at the framing level — Path A's "Research &
  translation" eyebrow and follow-up examples orient the agent
  toward research workflows; Path B's "Guided instruction" eyebrow
  and lesson-curriculum follow-ups orient toward the Ummia teaching
  persona — but the bootstrap call itself is now identical, with
  the user's first follow-up query determining which workflow
  takes over. The `data-umami-event-path` attribute on each copy
  button still distinguishes `"research"` vs `"teaching"` for
  analytics, so we can still see which CTA visitors click.

## [0.2.1] — 2026-06-02

### Added

- **Copy buttons on the Path A and Path B bootstrap prompts**
  (`templates/www.html` landing page, "How to use" section). The two
  `<div class="prompt-box">` elements now carry a 32×32 copy button
  pinned to their top-right corner; clicking copies the bootstrap
  prompt string to the clipboard and flashes a checkmark confirmation
  for 1.4s. Reuses the existing `.copy-btn` styling and JS handler
  from the MCP endpoint URLs section, so the visitor sees consistent
  copy-button affordance everywhere on the page. Fires
  `data-umami-event="bootstrap-prompt-copy"` with
  `data-umami-event-path="research"` or `"teaching"` so we can see
  in analytics which path visitors actually adopt.
- **"Re-issue periodically" callouts on both bootstrap paths.**
  Amber-bordered note blocks under each prompt-box explain that long
  sessions cause context drift and that re-pasting the same prompt
  is idempotent and refreshes the per-server operating instructions.
  Path A's note focuses on attestation-first / `sense_pct` ranking
  drift; Path B's note focuses on the Ummia persona / scribal-voice
  drift in long teaching sessions. New `.prompt-reissue` CSS class
  styles the callout as a left-bordered amber strip with a 💡 lead.
- **Expandable verbatim citations in the licensing table.** Each
  License-column cell now wraps its short label (`CC BY-SA 3.0`,
  `Academic copyright`, `Mixed`) in a native HTML `<details>`
  element whose `<summary>` is the label and whose expanded body is
  the full canonical attribution string with project URLs and
  reuse conditions inlined as clickable links. Uses the native
  disclosure widget (no JavaScript), with custom CSS replacing the
  default ▸/▾ marker. Click-to-expand keeps the page compact while
  making the verbatim text one-click discoverable. Each expansion
  also fires `data-umami-event="license-expand"` so we can measure
  which license rows draw curiosity.

### Fixed

- **CDLI photo / lineart imagery was 100% suppressed across the
  catalogue** because `build_cdli_db.py` coerced the source CSV's
  `photo_up` and `lineart_up` columns through `_truthy()` — which
  recognizes only `'1'` / `'true'` / `'yes'` / `'y'` aliases. But
  those columns don't carry booleans; they carry **scan-metadata
  strings** like `'600ppi 20160630'` (photo uploaded at 600 DPI on
  2016-06-30) and `'150ppi 20160630'` (line art uploaded). Every
  non-empty value fell through to `0`, zeroing out the
  `has_photo` / `has_lineart` flags across all 353,283 rows, which
  in turn nulled out every `photo_url` / `lineart_url` field on
  every `CDLIArtifact` (because the URL ternary in
  `_build_cdli_artifact` checks the flags). Downstream agents
  reasonably concluded that "CDLI has no imagery in this snapshot",
  which was a fabricated artifact of our ingestion bug.
  Add a new `_has_scan()` helper in `build_cdli_db.py` that treats
  any non-empty value as a present asset (matches the CSV's actual
  semantics), and switch the `photo_up` / `lineart_up` call sites
  to use it instead of `_truthy()`. After re-ingest, the catalogue
  surfaces ~132K rows with `has_photo=1` (37%) and ~251K rows with
  `has_lineart=1` (71%) — putting cdli.earth's hosted imagery
  within reach of every cited tablet in `lookup_artifact`,
  `find_artifacts`, and the `see_examples` / `find_verb_form`
  enrichment splat.
- **Bump `INIT_VERSION` from `4` to `5`** in `init.sh` so the next
  deploy's init container detects the existing sentinel as stale,
  wipes `/app/data`, and rebuilds every SQLite index — most
  importantly `cdli.sqlite` — with the corrected `_has_scan`
  semantics. Inline comment documents the reason so the version
  bump is self-explanatory in `git log` and `git blame`. Total
  wipe-rebuild cost is ~10 min dominated by the glossary rebuild;
  the corpus zips on disk are reused (`download_corpus.py` is
  resume-safe).
- **Corrected `LICENSE-DATA.md` link on the landing page** —
  previously pointed at `/blob/main/LICENSE-DATA.md` which 404s
  because the repository's default branch is `root`, not `main`.
  Now points at `/blob/root/LICENSE-DATA.md`.

## [0.2.0] — 2026-06-02

### Changed (BREAKING)

- **Removed `has_photo` and `has_lineart` boolean fields from
  `CDLIArtifact`.** The image URL fields (`photo_url`,
  `photo_thumb_url`, `lineart_url`, `lineart_thumb_url`) already encoded
  availability — they're `null` when CDLI has no asset of that kind for
  the artifact, and a `https://cdli.earth/…` URL otherwise. Carrying a
  separate boolean meant agents had two sources of truth that could
  drift; now the URL's null-ness is the sole availability signal. Updated
  `prompt/CDLI_PROMPT.md` (and the `start_here()` bootstrap docstring)
  to teach the new rule: "non-null URL → render as Markdown link; null
  → omit from reply; never fabricate." Downstream clients reading
  `has_photo` / `has_lineart` will need to switch to
  `photo_url is not None` / `lineart_url is not None`. Also strips the
  same booleans from any tool that splats `CDLIArtifact` into a larger
  response (none currently do; the shared enrichment in
  `eme_gir/cdli.py` was already URL-only).

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

[Unreleased]: https://github.com/jenova-marie/eme-gir/compare/v0.2.1...HEAD
[0.2.1]: https://github.com/jenova-marie/eme-gir/releases/tag/v0.2.1
[0.2.0]: https://github.com/jenova-marie/eme-gir/releases/tag/v0.2.0
[0.1.0]: https://github.com/jenova-marie/eme-gir/releases/tag/v0.1.0
