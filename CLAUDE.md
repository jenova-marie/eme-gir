# CLAUDE.md

Guidance for Claude Code agents working in this repository.

> **Where to find deeper material:**
>
> - [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) — schemas, parsers,
>   transport internals, OAuth, Umami split, containerization,
>   project-name conventions, all the deep technical reference
> - [`LICENSE-DATA.md`](LICENSE-DATA.md) — authoritative statement on
>   the three data-source licenses (Oracc CC BY-SA 3.0, ETCSL academic,
>   CDLI mixed)
> - [`CHANGELOG.md`](CHANGELOG.md) — release history; the
>   `[Unreleased]` section is where every commit must land an entry
>   (see "Versioning and CHANGELOG upkeep" below)
> - `prompt/*_PROMPT.md` — per-server bootstrap docs returned by
>   `start_here()` (ePSD2, ETCSL, CDLI, OGSL, Ummia)

## What this repo is

A workspace for **parsing the Oracc / Eme-gir (electronic Pennsylvania
Sumerian Dictionary) corpus and exposing it to LLM agents** for English
↔ Sumerian translation. Oracc is "The Open Richly Annotated Cuneiform
Corpus" hosted at `https://oracc.museum.upenn.edu`. Organized into four
layers:

**Layer 1 — top-level scripts.** Build pipeline + entry points at the
repo root:

- `download_corpus.py` — pulls 208 zip archives (~3.1 GB) from Oracc into `corpus/`
- `build_glossary_db.py`, `build_text_index.py`, `build_collocations.py`,
  `build_inflected_collocations.py`, `build_etcsl_db.py`, `build_cdli_db.py`
  — populate the SQLite indexes in `data/`
- `app.py` + `templates/` — Flask glossary browser (ePSD2 verification surface)
- `www_app.py` + `templates/www.html` — Flask landing page at eme-gir.org
- `mcp_server.py` — legacy all-in-one MCP server (back-compat; new
  deployments prefer per-domain servers below)

**Layer 2 — `servers/` (per-domain MCP entry points).** Each `__main__.py`
is a thin (~30-40 line) wrapper that registers its domain's tools:

- `servers/epsd2` (port 5052) — 11 ePSD2 dictionary + corpus tools
- `servers/etcsl` (port 5053) — 4 bilingual Oxford literary corpus tools
- `servers/cdli` (port 5054) — 2 CDLI artifact catalogue tools
- `servers/ogsl` (port 5055) — 2 cuneiform sign tools (`cuneify`, `lookup_sign`)
- `servers/ummia` (port 5058) — teaching surface (Sumerian 101 + dual-register grammar)

**Layer 3 — `eme_gir/` (shared Python package).** Imported by every entry
point and build script. Internal imports use relative form
(`from .paths import ...`); external use absolute (`from eme_gir.paths import ...`).

- `paths.py` — single source of truth for project file locations
- `__init__.py` — `__version__` string (single source of truth; stamped onto
  MCP servers' `serverInfo.version` field by `eme_gir.server.make_server()`)
- `log.py` — `log_call` decorator (entry/exit timing + umami emission)
- `server.py` — `make_server()` factory + `run_server()` argparse loop;
  applies Auth0 + transport security from env vars
- `cuneify.py` — Oracc transliteration → Unicode cuneiform glyphs
- `text_resolver.py` — `word_ref` strings → actual transliteration lines
- `cdli.py` — shared CDLI enrichment splatted onto `AttestationLine`
- `sumerian_morphology.py` — suffix peeler + verbal-prefix detector
- `attribution.py` — single-source attribution strings, citation_short,
  presentation, license_banner()
- `auth0_verifier.py` — RS256 JWT verification (opt-in)
- `umami_analytics.py` — fire-and-forget tool-call telemetry
- `models/` — Pydantic response models per-domain
- `tools/` — tool function implementations per-domain

**Layer 4 — data + prompts.**

- `corpus/` — 208 zip files (~3.1 GB), one per Oracc project; the bulk dataset
- `data/` — generated SQLite indexes (created on first init):
  `glossary.sqlite` (~3.4 GB), `text_index.sqlite`, `collocations.sqlite`,
  `inflected_collocations.sqlite`, `etcsl.sqlite`, `cdli.sqlite`. Full
  schema in `docs/ARCHITECTURE.md`.
- `prompt/` — per-server bootstrap markdown returned by `start_here()`:
  `EPSD2_PROMPT.md`, `ETCSL_PROMPT.md`, `CDLI_PROMPT.md`, `OGSL_PROMPT.md`,
  `UMMIA_PROMPT.md`, `AGENT_PROMPT.md` (legacy). Plus
  `lessons/JAGERSMA_GRAMMAR.md` + `lessons/MEADOW_GRAMMAR.md` for the
  dual academic + temple grammar reference.
- `log/` — rotating per-server logs (5 MB × 3 backups)
- `.mcp.json` — project-scoped MCP server config (auto-detected by Claude Code)
- `.incommon_intermediate.pem` — cached TLS intermediate cert (see TLS gotcha below)

## Common commands

```bash
# Download or resume the entire corpus (idempotent; skips files already at the right size)
python3 download_corpus.py

# Tune parallelism (default 4; be polite — small academic server)
python3 download_corpus.py --workers 2

# Inspect a single project's contents without extracting
unzip -l corpus/eme-gir.zip
unzip -p corpus/eme-gir.zip eme-gir/metadata.json | python3 -m json.tool

# Build the glossary SQLite index
python3 build_glossary_db.py

# Build the text-location index across all 208 zips (needed for attestation rendering)
python3 build_text_index.py

# Build CDLI catalogue (~30s after a 147 MB download)
python3 build_cdli_db.py

# Build ETCSL literary corpus (~10s after a 4.9 MB download)
python3 build_etcsl_db.py

# Build collocations indexes (~5 min for the unigram + n-gram index;
#   ~30 min for the case+sense-aware inflected variant)
python3 build_collocations.py
python3 build_inflected_collocations.py

# Query the glossary
sqlite3 -header -column data/glossary.sqlite "SELECT cf, gw, pos, icount FROM entries WHERE cf='lugal';"

# Run the local Oracc-style browser
python3 app.py                # http://127.0.0.1:5050/eme-gir/sux
python3 app.py --port 8000 --debug

# Run the landing page
python3 www_app.py            # http://127.0.0.1:5057/
python3 www_app.py --port 5057 --debug

# Run an MCP server over stdio (Claude Code / Claude Desktop)
python3 -m servers.epsd2
python3 -m servers.cdli
python3 -m servers.ummia
# (or the legacy all-in-one)
python3 mcp_server.py

# Run over HTTP (streamable-http transport)
python3 -m servers.epsd2 --transport http --host 127.0.0.1 --port 5052

# Bring up the full stack in containers
docker compose up -d --build
docker compose logs -f mcp-epsd2

# Production WSGI for the Flask apps (gunicorn picks up create_app() factory)
gunicorn -w 4 -b 127.0.0.1:5050 'app:create_app()'
gunicorn -w 2 -b 127.0.0.1:5057 'www_app:create_app()'
```

Dependencies (`pip install -r requirements.txt`): `ijson` (yajl2_c backend
for constant-memory JSON streaming), `flask`, `mcp` (the MCP SDK; HTTP
transport pulls `uvicorn` + `starlette` transitively), `gunicorn`,
`httpx`, `pyjwt[crypto]` (only loaded when `EME_GIR_REQUIRE_AUTH=1`).
Everything else stdlib.

There are no tests, build, or lint steps — this is a data/scripts repo.

**Log convention:** when capturing build-script output, tee to `log/`:

```bash
python3 build_glossary_db.py 2>&1 | tee log/build_glossary.log
python3 build_cdli_db.py 2>&1 | tee log/build_cdli.log
```

`*.log` is gitignored anywhere.

## Versioning and CHANGELOG upkeep

The project follows [Semantic Versioning](https://semver.org/) with a
single source of truth at [`eme_gir/__init__.py`](eme_gir/__init__.py)'s
`__version__` string. That value is read by
`eme_gir.server.make_server()` and stamped onto every MCP server's
`serverInfo.version` field on the `initialize` handshake (verifiable
via the `mcp.client.streamable_http` SDK or by checking the startup
banner: `eme-gir-epsd2 v0.2.1 MCP server starting ...`).

[`CHANGELOG.md`](CHANGELOG.md) at the repo root tracks every
modification to the source tree in
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/) format.
**Every commit that modifies any source file (Python, HTML/Jinja
templates, CSS, JS, YAML, Caddyfile, shell, Dockerfile, init.sh, the
prompt markdown files, CLAUDE.md itself, etc.) must update the
`## [Unreleased]` section in the same commit** — this is non-negotiable.
Treat the changelog the way a senior maintainer treats a release notes
file: if the diff touched a file under version control, the change
deserves a bullet.

### What counts (must changelog)

- New MCP tools, new tool parameters, new response fields, new MCP resources
- Breaking changes to tool signatures or response shapes (Pydantic model edits)
- New environment variables (`EME_GIR_*`), new ports, new container services
- Bug fixes that change observable behavior
- New build scripts, new data sources, new SQLite schemas
- Web app / www landing page features users will notice
- Auth / transport-security changes
- Refactors (file moves, internal renames, package reorganization) — log under `### Changed`
- Comment / docstring polish that clarifies non-obvious behavior — log under `### Documentation`
- CI/CD tooling that affects what gets built or deployed — log under `### Changed` or `### Fixed`
- CLAUDE.md / README.md / prompt/*.md edits — log under `### Documentation`
- Style-only edits to user-facing surfaces (CSS, landing-page copy polish) — log under `### Changed`
- The release commit itself (always under a new `## [X.Y.Z]` heading per the release procedure below)

### Very narrow exclusions (still preferred to log under `### Documentation`)

- Pure whitespace / formatter-only changes with zero semantic content
- Auto-generated lockfile bumps from `pip freeze` that don't change any installed version
- Removal of dead code that was already commented out

When in doubt, log it. The cost of an extra bullet is trivial; the cost
of a missing one is invisible drift that bites at release time when
nobody can reconstruct what changed.

### How to update the changelog

For ongoing development:

1. Add a bullet to the appropriate subsection (`### Added`, `### Changed`, `### Fixed`, `### Deprecated`, `### Removed`, `### Security`, `### Documentation`, `### Privacy`) under the existing `## [Unreleased]` heading.
2. Phrase the entry in the imperative-or-past-tense form Keep a Changelog uses — e.g. *"Add pagination to translate_english"*, *"Restore ePSD2 footer to normal document flow"*.
3. Reference the affected MCP tool / file / surface explicitly so a future reader can locate the change without a `git blame`.

When cutting a release:

1. Bump `__version__` in `eme_gir/__init__.py` per semver semantics.
2. Move every `## [Unreleased]` bullet under a new `## [X.Y.Z] — YYYY-MM-DD` heading directly below `## [Unreleased]` (the empty Unreleased section stays).
3. Update the bottom-of-file reference links so `[Unreleased]` compares from the new tag and a new `[X.Y.Z]` link points at the GitHub release page.
4. Commit with `🔖 release: v$VERSION`.
5. Tag the commit: `git tag -a v$VERSION -m "v$VERSION — <one-line summary>"`.
6. Push both the commit AND the tag: `git push origin prod && git push origin v$VERSION` (or `git push --tags`).

### Pre-1.0 caveat

While `__version__ < 1.0.0`, MINOR bumps (`0.1 → 0.2`) may break MCP tool signatures or response shapes; this is intentional during the iteration phase. PATCH bumps (`0.1.0 → 0.1.1`) are always backwards compatible. Once `1.0.0` ships, semver becomes binding — MAJOR bumps signal breaking changes.

## Wiring into Claude Code / Claude Desktop

The repo ships `.mcp.json` for project-scoped auto-detection. **Both
paths must be absolute** because Claude Code spawns MCP servers without
sourcing the user's shell init — a bare `python3` resolves to
`/usr/bin/python3` which doesn't have the `mcp` package, and the server
dies before responding to `initialize` (looks like "MCP server is down"):

```json
{
  "mcpServers": {
    "eme-gir-epsd2": {
      "type": "stdio",
      "command": "<absolute path to a python that has the `mcp` package>",
      "args": ["-m", "servers.epsd2"],
      "cwd": "<absolute path to this repo>"
    }
  }
}
```

On the author's macOS+asdf setup that resolves to e.g.
`/Users/<you>/.asdf/installs/python/3.12.11/bin/python3` and
`/Users/<you>/projects/<...>/eme-gir`. For a different machine, get the
python path with `readlink -f $(which python3)` after confirming
`python3 -c 'import mcp'` succeeds. The committed `.mcp.json` at the
repo root currently hardcodes the author's paths — clone-and-go users
will need to edit it to match their own machine.

**Critical gotcha on stdio subprocesses:** Python imports modules once
at process startup. If you make code changes mid-session, the running
stdio subprocess keeps serving the OLD code from when it spawned — disk
updates don't propagate. After any edit to `servers/*` or `eme_gir/*`,
either disconnect/reconnect the MCP server via the `/mcp` slash command
in Claude Code or restart the whole session.

## TLS gotcha — important for any HTTPS code

`oracc.museum.upenn.edu` serves a valid cert from "InCommon RSA Server CA 2"
but **omits the intermediate from its TLS chain**. As a result:

- `curl` works (macOS/Linux libcurl does AIA chasing)
- Python `urllib`/`requests` and Claude Code's `WebFetch` **fail** with
  `unable to get local issuer certificate`

`download_corpus.py` solves this by fetching the intermediate from
`http://crt.sectigo.com/InCommonRSAServerCA2.crt` (URL is in the leaf
cert's AIA extension), caching it as `.incommon_intermediate.pem`, and
merging it into the SSL context alongside `certifi`. Reuse this pattern
in any new Python that talks to Oracc — don't disable verification.

## Data licenses

See [`LICENSE-DATA.md`](LICENSE-DATA.md) for the authoritative
statement. Summary:

- **Oracc / ePSD2 / OGSL** — **CC BY-SA 3.0 Unported** (per Oracc's project-wide license). Attribution required; ShareAlike propagates to substantial reuses.
- **ETCSL (Oxford)** — **No Creative Commons license.** Traditional academic copyright (© Black, Cunningham, Robson, Zólyomi 1998–2006); the project has only ever published a citation request, not a redistribution grant.
- **CDLI catalogue text** — freely reusable with citation per CDLI's "fair academic practice" terms; **imagery** on cdli.earth is non-commercial only.
- **Code in this repo** — MIT (separate from the data layer; see `LICENSE`).
