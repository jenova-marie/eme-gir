# Getting Started

Setup, build, run, and deploy instructions for **Jenova's Local · ePSD2**. For the project overview, motivation, and historical context, see [README.md](README.md).

There are three rough layers, and you can stop wherever fits your need:

1. **Build the local indexes** — download the Oracc corpus, build the SQLite indexes. Required for everything else. ~5–15 minutes one-time, ~3.5 GB on disk.
2. **Browse interactively** — run the Flask web app for the human-facing glossary browser at `http://127.0.0.1:5050`.
3. **Wire up an LLM agent** — run the MCP server (over stdio for Claude Code / Claude Desktop, or over HTTP for remote agents and Docker deployments).

For production deployment with TLS, auth, and a reverse proxy, see the [Containerized deployment](#containerized-deployment-docker) and [Reverse proxy](#putting-both-behind-one-reverse-proxy) sections at the bottom.

---

## 1. Build the local indexes

```bash
# Install dependencies (gunicorn is only needed for production serving)
pip install ijson flask mcp gunicorn

# Download the entire Oracc JSON corpus (~3.1 GB, ~2 minutes on a fast link)
python3 download_corpus.py

# Build the per-text location index (~2 seconds)
python3 build_text_index.py

# Build the Sumerian glossary index (~3.5 minutes)
python3 build_glossary_db.py

# (Optional) Build the collocations index for the find_collocations MCP tool (~5 min)
python3 build_collocations.py

# (Optional) Build the ETCSL literary corpus for the etcsl_* MCP tools (~10 sec)
python3 build_etcsl_db.py

# Run the web app once to populate the casefold + sort SQLite migrations
python3 app.py    # → http://127.0.0.1:5050/epsd2/sux
```

All generated SQLite indexes land in `data/`; logs land in `log/`. Both directories are auto-created on first run.

To rebuild the glossary for a different language / project (e.g. the Akkadian glossary, useful for bilingual workflows):

```bash
python3 build_glossary_db.py \
  --zip corpus/rinap.zip \
  --member rinap/gloss-akk.json \
  --db data/glossary_akk.sqlite
```

### Building the ETCSL literary corpus (optional)

ETCSL — the Oxford [Electronic Text Corpus of Sumerian Literature](https://etcsl.orinst.ox.ac.uk/) — is a curated set of 394 Sumerian *literary* texts (hymns, myths, royal hymns, proverbs, wisdom, the Sumerian King List, Inana's Descent, Gilgameš and the Underworld, the Šulgi praise poems, etc.) shipped as TEI XML with **per-word lemmatization AND English translations**. This is exactly the bilingual corpus the Oracc administrative-text bulk JSON lacks. The build script downloads the 4.9 MB zip from the Oxford Text Archive and ingests it to `data/etcsl.sqlite` (~31 MB) with FTS5 indexes for English and Sumerian search:

```bash
python3 build_etcsl_db.py
```

Once built, the MCP server exposes four `etcsl_*` tools: `etcsl_search_english`, `etcsl_lines_with_lemma`, `etcsl_search_sumerian`, and `etcsl_lookup_text`. ETCSL data is **CC BY 3.0 UK** — every tool result includes an `attribution` field; preserve it when quoting.

### Picking up new / missing Oracc projects

`download_corpus.py` only knows about zips that are listed on the public [`/json/`](https://oracc.museum.upenn.edu/json/) download index. Oracc keeps adding new sub-projects, and a few are only reachable via the per-project `/{project}/json.zip` URL pattern instead of the index. To audit and pull anything we don't have yet:

```bash
# Just probe — list anything reachable on Oracc that's not in corpus/.
python3 find_missing_corpora.py

# Probe + download any reachable-but-missing zips, with zip-validity check
# (Oracc occasionally returns a 200 + HTML error page when a project's
# archive isn't built yet; bogus responses are detected and discarded).
python3 find_missing_corpora.py --fetch

# Optional: write a structured JSON report alongside the human one.
python3 find_missing_corpora.py --json data/missing_corpora.json
```

After fetching new zips, rebuild the indexes so they pick up the new content:

```bash
python3 build_text_index.py
python3 build_collocations.py    # only if you use the find_collocations MCP tool
```

`find_missing_corpora.py` reuses `download_corpus.py`'s SSL setup and resume-safe download, so the fetch is polite to Oracc's small academic server.

---

## 2. Run the web browser

```bash
python3 app.py                      # → http://127.0.0.1:5050/epsd2/sux
python3 app.py --port 8000 --debug  # alternate port + Flask debug mode
```

`app.py` runs Flask's built-in development server (Werkzeug — single-threaded, no concurrency, banner says "do not use in production"). For production deployment, see [Running the web app under gunicorn](#running-the-web-app-under-gunicorn) below.

The web app routes:

- `GET /` → 302 redirect to `/epsd2/sux`
- `GET /epsd2/sux` — paginated glossary; query params `?page`, `?zoom={letter}`, `?q={search}`
- `GET /epsd2/<oid>` — entry detail page with attestations, cuneiform, and period breakdown

---

## 3. Run as an MCP server (for LLM agents)

The repo ships an MCP server exposing seventeen tools designed for agent-driven English ↔ Sumerian translation, plus a project-scoped `.mcp.json` so **Claude Code auto-detects the server** when launched in this directory — no manual client config needed.

For other MCP clients (Claude Desktop, Cline, etc.), add this to the client's `mcpServers` config:

```json
{
  "mcpServers": {
    "epsd2": {
      "type": "stdio",
      "command": "/absolute/path/to/python3-with-mcp-installed",
      "args": ["/absolute/path/to/this/repo/mcp_server.py"]
    }
  }
}
```

> **Both paths must be absolute.** MCP clients spawn the server without sourcing your shell init, so a bare `python3` resolves to the system python (which may not have the `mcp` package). On macOS with asdf-managed Python, look up the canonical path with `readlink -f $(which python3)`.

### The seventeen tools

**ePSD2 dictionary + corpus tools:**

- `translate_english(query, limit)` — rank Sumerian candidates for an English meaning
- `translate_sumerian(transliteration)` — reverse direction: parse a Sumerian phrase into per-token glosses; surfaces detected case/possessive/plural suffixes on each token
- `parse_phrase(transliteration)` — case-aware grammatical pre-annotation; per-token phrase-role labels (ergative, dative, equative, verb_head, …), compact bracket skeleton, ambiguous-suffix warnings. Reach for this when structural ambiguity matters.
- `lookup_entry(oid)` — full structured view of a chosen lemma
- `see_examples(oid, limit, period)` — real attested lines, target word marked, period-filterable
- `find_compound(english_phrase)` — find idiomatic Sumerian compound expressions
- `find_collocations(word, length, limit)` — phrasal idioms attested with a given lemma (mined from the corpus, not the dictionary — surfaces formulas like "Šusuen lugal", year-name templates, royal titles)
- `find_phrase_pattern(pattern, limit)` — structural-template query over the corpus n-gram index. Each slot is `TARGET[gw]:case` where TARGET is a literal cf / POS code / POS family glob (`V*`) / `*`; optional `[gw]` constrains the sense (homograph disambiguation); optional `:case` constrains the case marker (`ergative`, `dative`, `locative`, `equative`, …, with `!` prefix for negation). E.g. `["RN","lugal"]` (year-name templates), `["lugal[king]:ergative","N"]` (king-as-agent + object), `["N:ergative","N","V*"]` (transitive-clause skeletons). Routes to `inflected_collocations.sqlite` when available, else falls back to `collocations.sqlite` for v1 patterns.
- `get_inflections(oid)` — every attested morphological breakdown of a lemma
- `analyze_form(spelling)` — decompose an attested spelling into candidate lemmas + morphology
- `find_verb_form(cf, pos, prefix, dimensional, object_person, aspect, …)` — attested verb forms matching a feature spec; returns the morph template + spelling + attested count + one cited line per match (attestation-first; no rule-based synthesis)
- `lookup_sign(query)` — find a cuneiform sign by name or phonetic value
- `cuneify(spelling)` — render Oracc transliteration as Unicode cuneiform glyphs

**ETCSL literary-corpus tools** (bilingual; require `python3 build_etcsl_db.py`):

- `etcsl_search_english(query, limit)` — FTS5 over English translations; returns each match with its Sumerian lines
- `etcsl_lines_with_lemma(lemma, limit)` — literary lines containing a given Sumerian lemma + the English paragraph
- `etcsl_search_sumerian(query, limit)` — FTS5 over Sumerian transliterations; returns bilingual matches
- `etcsl_lookup_text(text_id, start, line_limit)` — read a whole composition, paginated, bilingual

Plus two MCP resources, both intended to be fetched once at session start so the agent self-bootstraps without operator-side prompt copy-paste:

- `oracc://prompt/agent` — the drop-in system prompt teaching the end-to-end workflow over these tools (also lives as the file [`prompt/AGENT_PROMPT.md`](prompt/AGENT_PROMPT.md)).
- `oracc://grammar/sumerian` — a ~14 KB Sumerian grammar cheat sheet distilled from Edzard 2003 (also lives as the file [`prompt/SUMERIAN_GRAMMAR.md`](prompt/SUMERIAN_GRAMMAR.md)).

Every result returned by `translate_english` includes both raw sense frequency *and* what % of the lemma's uses are in that sense — so the agent can pick "the word for X" rather than "a word that occasionally means X".

For the underlying drop-in agent system prompt as a standalone file (useful when configuring MCP clients that don't auto-fetch resources), see [`prompt/AGENT_PROMPT.md`](prompt/AGENT_PROMPT.md).

### Watching the server live

Every tool call is logged to `log/mcp_server.log` (rotating, 5 MB × 3 backups), with arguments, duration, and a one-line result summary. Tail it while chatting with the agent:

```bash
tail -F log/mcp_server.log
```

Errors get full tracebacks. The startup banner reports loaded DB sizes so you can confirm the right files are mounted.

### Running over HTTP (for remote agents, Docker, or non-stdio clients)

The same `mcp_server.py` script also speaks the MCP **streamable-HTTP** transport — useful when the consumer can't (or shouldn't) launch the server as a subprocess: web-hosted agents, multi-tenant deployments, sidecar containers, etc.

```bash
# Local-only (default bind = 127.0.0.1, default port = 5051)
python3 mcp_server.py --transport http

# Behind a reverse proxy on a private network
python3 mcp_server.py --transport http --host 0.0.0.0 --port 5051
```

Endpoint: `http://HOST:5051/mcp/` (note the trailing slash — `/mcp` without it 307-redirects). All 19 tools (the 17 translation tools plus the two `start_here` / `get_grammar_reference` resource-wrapper tools) work over HTTP exactly as they do over stdio. By default there is **no in-app authentication**; the server trusts any client that can reach the port. Always front it with a reverse proxy (nginx / caddy / traefik) when binding outside `127.0.0.1`. To enforce in-app auth instead (or in addition), see the next section.

### Adding Auth0 OAuth (optional, HTTP transport only)

The HTTP transport supports OAuth 2.1 bearer-token auth with **Auth0** as the identity provider. When enabled, every request to `/mcp/` is gated on a valid Auth0-issued RS256 JWT in the `Authorization: Bearer ...` header. The server runs as a **Resource Server** (RS) only — Auth0 issues the tokens; we just validate them.

This is **opt-in** via env var. Stdio transport never authenticates regardless (per the MCP spec, stdio uses environment-based credentials).

#### One-time Auth0 setup

1. In the Auth0 dashboard, create an **API**:
   - Name: anything descriptive, e.g. `epsd2-mcp`
   - Identifier (audience): a stable URL representing your server, e.g. `https://epsd2.example.com`. Doesn't have to resolve — Auth0 just uses it as an opaque string in the `aud` JWT claim.
   - Signing algorithm: **RS256** (the default)
2. On the API's "Permissions" tab, add a scope: `mcp:access` (description: "Access the epsd2 MCP server"). All 19 tools sit behind this single scope; finer-grained scopes can be added later if needed.
3. Either grab a long-lived test token from the API's "Test" tab (good for local development), or create a Machine-to-Machine application authorized to call this API and use the `client_credentials` grant.

#### Server-side env vars

When `EPSD2_REQUIRE_AUTH=1`:

| Var | Required | Example | What it does |
|---|---|---|---|
| `EPSD2_REQUIRE_AUTH` | yes | `1` | Toggles auth on. Anything other than `1` keeps the legacy unauthenticated behavior. |
| `EPSD2_AUTH0_TENANT_URL` | yes | `https://my-tenant.auth0.com` | Base URL of your Auth0 tenant (no trailing slash). The verifier fetches `${TENANT}/.well-known/jwks.json` to validate signatures. |
| `EPSD2_AUTH0_AUDIENCE` | yes | `https://epsd2.example.com` | Must match the API identifier you set in step 1. Tokens with a different `aud` are rejected (RFC 8707 audience binding — prevents tokens for one server from being replayed against another). |
| `EPSD2_AUTH0_RESOURCE_SERVER_URL` | yes | `https://epsd2.example.com` | The **public-facing** URL of THIS server, used in the RFC 9728 Protected Resource Metadata served at `/.well-known/oauth-protected-resource`. Differs from `--host`/`--port` when behind a reverse proxy. |
| `EPSD2_AUTH0_REQUIRED_SCOPE` | no | `mcp:access` | A scope that must be present in the token's `scope` claim. Defaults to `mcp:access`; set to empty string to allow any valid Auth0 token. |

#### Local invocation

```bash
EPSD2_REQUIRE_AUTH=1 \
EPSD2_AUTH0_TENANT_URL=https://my-tenant.auth0.com \
EPSD2_AUTH0_AUDIENCE=https://epsd2.example.com \
EPSD2_AUTH0_RESOURCE_SERVER_URL=https://epsd2.example.com \
python3 mcp_server.py --transport http --host 0.0.0.0 --port 5051
```

The startup banner will confirm the mode: `auth=ENABLED (Auth0 issuer=..., audience=..., required_scopes=['mcp:access'])`.

#### Docker invocation

The compose file already declares the env vars with empty defaults. Set them via `.env` file or shell:

```bash
EPSD2_REQUIRE_AUTH=1 \
EPSD2_AUTH0_TENANT_URL=https://my-tenant.auth0.com \
EPSD2_AUTH0_AUDIENCE=https://epsd2.example.com \
EPSD2_AUTH0_RESOURCE_SERVER_URL=https://epsd2.example.com \
docker compose up -d
```

Or persist them in a `.env` file alongside `docker-compose.yml`:

```env
EPSD2_REQUIRE_AUTH=1
EPSD2_AUTH0_TENANT_URL=https://my-tenant.auth0.com
EPSD2_AUTH0_AUDIENCE=https://epsd2.example.com
EPSD2_AUTH0_RESOURCE_SERVER_URL=https://epsd2.example.com
```

#### Verifying

```bash
# Unauthenticated request — expect 401 with WWW-Authenticate header
# pointing at the Protected Resource Metadata.
curl -i -X POST http://127.0.0.1:5051/mcp -L \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -d '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{}}'

# Discovery endpoint — should return JSON listing your Auth0 tenant
# as the authorization_servers entry.
curl http://127.0.0.1:5051/.well-known/oauth-protected-resource

# Authenticated request — replace $TOKEN with an Auth0-issued JWT.
# Expect 200 + the normal initialize response.
curl -X POST http://127.0.0.1:5051/mcp -L \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -d '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"c","version":"1"}}}'
```

#### Client-side notes

As of this writing, **MCP clients (Claude Desktop, Claude Code) do not yet ship native OAuth/PKCE flow handling.** Practical paths today:

- **Static long-lived test tokens.** Auth0's API "Test" tab generates tokens valid for hours — paste into your MCP client config as a static `Authorization: Bearer ...` header. Fine for development and for trusted single-user deployments.
- **Reverse-proxy auth.** Run the MCP server with `EPSD2_REQUIRE_AUTH=0` and let your reverse proxy (nginx / caddy / Auth0's own proxy) inject `Authorization` headers based on whatever auth the proxy enforces (basic auth, Auth0 SSO, mTLS).
- **Wait for native client OAuth.** The MCP spec mandates the discovery dance via Protected Resource Metadata; clients will eventually catch up. Once they do, no server-side change is needed — our server already serves the right metadata.

### Allowing the public hostname through DNS-rebinding protection (REQUIRED behind a reverse proxy)

The MCP Python SDK ships with **DNS-rebinding protection ON by default**, with an allowlist that only accepts `Host: localhost` or `Host: 127.0.0.1` (with port wildcards). When you put the HTTP transport behind a reverse proxy (Caddy / nginx / traefik) and the proxy passes the public hostname through to uvicorn unchanged, every request gets rejected with **`421 Misdirected Request: Invalid Host header`** — looks like a misconfiguration but is actually the SDK's middleware refusing an unallowlisted Host. Production deployments MUST opt in to their own hostname.

Three env vars:

| Var | Required | Example | What it does |
|---|---|---|---|
| `EPSD2_ALLOWED_HOSTS` | yes (when behind a proxy) | `epsd2.intra.example.net,epsd2.example.com` | Comma-separated list of public hostnames the proxy serves the MCP server under. `localhost` / `127.0.0.1` / `::1` (with and without port suffixes) are added automatically so in-container healthchecks keep working — only list the public hostnames here. |
| `EPSD2_ALLOWED_ORIGINS` | only for browser clients | `https://archive.example.org` | Comma-separated list of `Origin` headers accepted on cross-origin requests. Stricter than allowed_hosts: no auto-additions. Skip this if no browser MCP client will hit the endpoint. |
| `EPSD2_DISABLE_DNS_REBINDING_PROTECTION` | escape hatch | `1` | Disables the check entirely. Only safe when your reverse proxy enforces Host validation upstream. The startup banner emits a WARNING when this is on. |

Example for a Caddy/nginx deployment:

```env
EPSD2_ALLOWED_HOSTS=epsd2.intra.example.net
EPSD2_ALLOWED_ORIGINS=https://archive.example.org
```

Or in docker compose env:

```bash
EPSD2_ALLOWED_HOSTS=epsd2.intra.example.net docker compose up -d
```

The startup banner will confirm what got applied:

```
auth=ENABLED (Auth0 issuer=...)
transport_security=ENABLED (allowed_hosts=['epsd2.intra.example.net','localhost','localhost:*','127.0.0.1','127.0.0.1:*','::1','[::1]:*'], allowed_origins=[...])
```

If you see `transport_security=default (SDK accepts Host: localhost / 127.0.0.1 only ...)` and you're behind a proxy, that's the cause of any 421 errors — set `EPSD2_ALLOWED_HOSTS` and restart.

---

## 4. Production deployment

### Running the web app under gunicorn

For anything beyond local development, run Flask under **gunicorn**:

```bash
# 4 worker processes, bound to localhost; let nginx terminate TLS
gunicorn -w 4 -b 127.0.0.1:5050 'app:create_app()'
```

`create_app()` is the application factory in `app.py`. It runs the one-shot SQLite migrations (sort + casefold columns) on startup, so a cold gunicorn boot is identical to `python3 app.py` for the database.

### Containerized deployment (Docker)

The repo ships a `Dockerfile` and `docker-compose.yml` that run the production stack as **three services**: a one-shot `init` that downloads + builds everything on first boot, then `web` (gunicorn + Flask) and `mcp` (FastMCP HTTP) which start in parallel after init exits 0. corpus/, data/, and log/ are bind-mounted from the host — too large to ship in the image (~6 GB combined).

**Cold start (no host-side prep required):**

```bash
docker compose up -d --build

# init does the heavy lifting (5-15 minutes on a fresh host):
docker compose logs -f init
# After init exits, web + mcp start in parallel and reach healthy in ~6 s.

# Endpoints (default bind: 127.0.0.1 only):
#   web → http://127.0.0.1:5050/epsd2/sux
#   mcp → http://127.0.0.1:5051/mcp/  (note trailing slash)
docker compose ps
```

**Reusing pre-built indexes from the host** (skips the multi-minute init):

```bash
# Build everything on the host first (steps from §1 above)
python3 download_corpus.py
python3 build_text_index.py
python3 build_glossary_db.py
python3 build_collocations.py     # optional
python3 build_etcsl_db.py         # optional
python3 app.py & sleep 5 && kill %1   # one-shot for casefold + sort migrations

# Then drop the sentinel so the init service trusts your data:
echo "init_version=2" > data/.initialized

docker compose up -d --build
# init fast-paths in <1 s; web + mcp healthy ~6 s later.
```

**Trust model.** The sentinel file `data/.initialized` is the single source of truth for "data is consistent with the current code." If missing or version-stale, `init` considers everything in `data/` defunct and **wipes it** before rebuilding (corpus/ is left intact — `download_corpus.py` is resume-safe). To force a re-init: `rm data/.initialized && docker compose up -d` (the init container will re-run on the next start).

**Defaults & overrides:**

- Both ports bind to `127.0.0.1` on the host. Override per-service: `WEB_BIND=0.0.0.0 MCP_BIND=0.0.0.0 docker compose up -d`. Anything beyond a private LAN MUST be fronted by a reverse proxy with TLS + auth.
- Image runs as a non-root user (uid/gid 1000); matches conventional Linux first-user so bind mounts work without a chown dance. macOS Docker Desktop maps owners through transparently.
- `data/` is mounted read/write on web and mcp — not because either writes glossary.sqlite at steady state, but because SQLite needs a writable directory for `-journal`/`-wal` files even on read-only transactions. Mark the SQLite files `chmod a-w` on the host if you really need write protection.
- gunicorn worker count defaults to 4; override with `WEB_WORKERS=8 docker compose up -d`.
- Skip optional builds: `EPSD2_BUILD_COLLOCATIONS=0 EPSD2_BUILD_ETCSL=0 docker compose up -d` (their MCP tools degrade gracefully or error if absent).

Watch live logs:

```bash
docker compose logs -f init  # init progress (only meaningful on first boot)
docker compose logs -f web   # Flask access + gunicorn lifecycle
docker compose logs -f mcp   # MCP startup banner + uvicorn requests
# (Tool-call timing lines also stream into ./log/mcp_server.log on the
# host because the log dir is bind-mounted.)
```

### Putting both behind one reverse proxy

A typical production layout serves the web UI at the root and HTTP MCP at `/mcp/`:

```nginx
server {
    listen 443 ssl;
    server_name epsd2.example.org;
    # ssl_certificate ...

    location /mcp/ {
        proxy_pass         http://127.0.0.1:5051;
        proxy_http_version 1.1;
        proxy_buffering    off;          # MCP streams responses, don't buffer
        proxy_read_timeout 24h;          # long-lived SSE sessions
        auth_basic         "epsd2 MCP";
        auth_basic_user_file /etc/nginx/htpasswd;
    }

    location / {
        proxy_pass         http://127.0.0.1:5050;
        proxy_set_header   Host $host;
        proxy_set_header   X-Forwarded-For $remote_addr;
        proxy_set_header   X-Forwarded-Proto $scheme;
    }
}
```

Two backend processes (`gunicorn` for Flask, `python3 mcp_server.py --transport http` for FastMCP), one public surface, TLS + auth handled centrally by the proxy. Keep `python3 app.py` for development — Werkzeug's autoreload is too useful to lose locally.

---

## Appendix: file inventory

| | |
|---|---|
| **Code** | |
| `download_corpus.py` | Stdlib-only batch downloader; resume-safe; auto-fetches the InCommon TLS intermediate that Oracc's server omits. |
| `find_missing_corpora.py` | Audit tool: HEAD-probes every project in Oracc's `projects.json` against `corpus/`, lists what's reachable but missing. `--fetch` flag downloads them (with zip-validity check). |
| `build_glossary_db.py` | ijson-streaming parser. Builds `glossary.sqlite` with normalized tables for entries, forms, norms, senses, signature occurrences, periods, compounds, morphology, and instances. |
| `build_text_index.py` | Scans every `corpus/*.zip` for `corpusjson/P*.json` and per-text catalogue metadata, builds `text_index.sqlite`. |
| `build_collocations.py` | Mines 2/3/4-gram phrasal collocations from every corpusjson text → `collocations.sqlite`. |
| `build_etcsl_db.py` | Downloads the ETCSL bulk zip (4.9 MB) from the Oxford Text Archive, parses 394 TEI XML literary texts (with a hand-built entity-expansion table for ~80 ETCSL-specific entity refs), normalizes ETCSL's ASCII transliteration to ePSD2/Oracc Unicode, ingests to `etcsl.sqlite` with FTS5 indexes. Powers the `etcsl_*` MCP tools. |
| `text_resolver.py` | Lazy lookup + LRU cache that turns a glossary `word_ref` (e.g. `epsd2/admin/ur3:P113959.10.3`) into the actual Sumerian line, with the target word marked. |
| `cuneify.py` | OGSL-backed transliteration → Unicode cuneiform converter. Loaded on first use; exposed as a Jinja filter to the web app and as the `cuneify` MCP tool. |
| `app.py` + `templates/` | Flask app. Routes: `/epsd2/sux` (paginated glossary with letter zoom + search), `/epsd2/<oid>` (entry detail). Also runs the one-shot `_cf` casefold + Sumerian-sort migrations on first startup. |
| `mcp_server.py` | MCP server (`mcp` SDK / FastMCP) exposing 17 translation tools + 2 bootstrap tool wrappers + 2 resources (`oracc://prompt/agent`, `oracc://grammar/sumerian`) for agents over stdio or streamable-HTTP. Logs every call to `log/mcp_server.log`. |
| `paths.py` | Single source of truth for project file locations — every other module imports `DATA_DIR`, `GLOSSARY_DB`, `LOG_DIR`, etc. from here. |
| `init.sh` | One-shot data initialization script for the Docker `init` service. Downloads corpus + builds indexes if the `data/.initialized` sentinel is missing. |
| **Docs / config** | |
| `.mcp.json` | Project-scoped MCP server config — Claude Code auto-detects when launched in this directory. |
| `Dockerfile` + `docker-compose.yml` | Container stack: `python:3.12.11-slim` base, three services (init, web, mcp). |
| `requirements.txt` | Python deps (ijson, flask, mcp, gunicorn). |
| `prompt/SUMERIAN_GRAMMAR.md` | ~14 KB Sumerian grammar cheat sheet (Edzard 2003), also served as the MCP resource `oracc://grammar/sumerian`. |
| `prompt/AGENT_PROMPT.md` | Drop-in system prompt for an LLM agent connected to the MCP server. Also served as the MCP resource `oracc://prompt/agent`. |
| `CLAUDE.md` | Detailed reference for AI coding assistants — schema docs, the Oracc URL surface, the TLS gotcha, and project-prefix glossary. |
| `static/img/jenova.png` | Header avatar / favicon. |
| **Generated artifacts (gitignored)** | |
| `corpus/` | 208 `.zip` files (~3.1 GB), one per Oracc project. |
| `data/glossary.sqlite` | ~3.4 GB indexed extract of the Sumerian glossary (15,940 entries, 35.5 M attestations, 248 K morphology rows). |
| `data/glossary_akk.sqlite` | ~114 MB Akkadian glossary built from `corpus/rinap.zip` for bilingual workflows (optional). |
| `data/text_index.sqlite` | ~10 MB index of 139,455 `(project, text_id, period, designation)` rows. |
| `data/collocations.sqlite` | ~22 MB index of ~178 K phrasal n-grams of citation forms mined from the corpus. |
| `data/etcsl.sqlite` | ~31 MB ETCSL literary corpus (394 texts, 34,229 lines, 159,963 words, 5,608 translation paragraphs) with FTS5 indexes on Sumerian and English. |
| `data/etcsl.zip` | ~4.9 MB cached download of the Oxford Text Archive ETCSL bulk zip; rebuilds skip re-downloading if present. |
| `data/.initialized` | Per-host runtime sentinel written by `init.sh` after a successful Docker first-boot init. |
| `log/mcp_server.log` | Live tool-call log; rotates at 5 MB × 3 backups. |

---

## Appendix: how a request flows

```
GET /epsd2/o0033341 (lugal)
       │
       ├─> SQLite: load entry + forms + norms + senses + sense_sigs
       │            + periods + compounds + 500 instance refs
       │
       ├─> text_resolver.resolve_many(refs, limit=20)
       │       │
       │       ├─> parse_word_ref('epsd2:P347156.34.5')
       │       ├─> data/text_index.sqlite: lookup (project, text_id)
       │       ├─> open corpus/epsd2.zip, parse corpusjson/P347156.json
       │       ├─> walk cdl tree, collect words on line 34
       │       └─> mark target word, dedupe by (text, line)
       │       (cached LRU 512 entries)
       │
       ├─> cuneify(form.n) for every spelling           [Jinja filter]
       │
       └─> render templates/entry.html
```
