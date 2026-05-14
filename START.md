# Getting Started

Setup, build, run, and deploy instructions for **Jenova's Local · Eme-gir**. For the project overview, motivation, and historical context, see [README.md](README.md).

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

# (Optional) Build the CDLI artifact catalogue for lookup_artifact + find_artifacts
# (~30 sec; downloads 147 MB CSV from GitHub LFS, builds a 157 MB SQLite)
python3 build_cdli_db.py

# Run the web app once to populate the casefold + sort SQLite migrations
python3 app.py    # → http://127.0.0.1:5050/eme-gir/sux
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
python3 app.py                      # → http://127.0.0.1:5050/eme-gir/sux
python3 app.py --port 8000 --debug  # alternate port + Flask debug mode
```

`app.py` runs Flask's built-in development server (Werkzeug — single-threaded, no concurrency, banner says "do not use in production"). For production deployment, see [Running the web app under gunicorn](#running-the-web-app-under-gunicorn) below.

The web app routes:

- `GET /` → 302 redirect to `/eme-gir/sux`
- `GET /eme-gir/sux` — paginated glossary; query params `?page`, `?zoom={letter}`, `?q={search}`
- `GET /eme-gir/<oid>` — entry detail page with attestations, cuneiform, and period breakdown

---

## 3. Run as an MCP server (for LLM agents)

Two deployment modes:

1. **All-in-one** (legacy, simple): `mcp_server.py` registers all 21 tools and 2 resources in one process. Use this for quick local agent work where one MCP connection is enough.
2. **Five per-domain servers** (Phase 5, preferred for new deployments): each domain (ePSD2, ETCSL, CDLI, OGSL, Translator) runs as its own MCP server. Lets you scale/secure/version each independently, and — most importantly — lets an LLM client connect to just the **raw data servers** (ePSD2 + ETCSL + CDLI + OGSL) without the Translator's opinionated workflow guidance, so the model discovers the translation pattern itself rather than being told.

Both modes are configured in the repo's `.mcp.json` so **Claude Code auto-detects the servers** when launched in this directory — six entries total. Comment out the entries you don't want.

For other MCP clients (Claude Desktop, Cline, etc.), add the subset you want to the client's `mcpServers` config. Examples:

```json
{
  "mcpServers": {
    "eme-gir": {
      "type": "stdio",
      "command": "/absolute/path/to/python3-with-mcp-installed",
      "args": ["/absolute/path/to/this/repo/mcp_server.py"]
    },
    "eme-gir-epsd2": {
      "type": "stdio",
      "command": "/absolute/path/to/python3-with-mcp-installed",
      "args": ["-m", "servers.epsd2"],
      "cwd": "/absolute/path/to/this/repo"
    },
    "eme-gir-etcsl": {
      "type": "stdio",
      "command": "/absolute/path/to/python3-with-mcp-installed",
      "args": ["-m", "servers.etcsl"],
      "cwd": "/absolute/path/to/this/repo"
    },
    "eme-gir-cdli": {
      "type": "stdio",
      "command": "/absolute/path/to/python3-with-mcp-installed",
      "args": ["-m", "servers.cdli"],
      "cwd": "/absolute/path/to/this/repo"
    },
    "eme-gir-ogsl": {
      "type": "stdio",
      "command": "/absolute/path/to/python3-with-mcp-installed",
      "args": ["-m", "servers.ogsl"],
      "cwd": "/absolute/path/to/this/repo"
    },
    "eme-gir-translator": {
      "type": "stdio",
      "command": "/absolute/path/to/python3-with-mcp-installed",
      "args": ["-m", "servers.translator"],
      "cwd": "/absolute/path/to/this/repo"
    }
  }
}
```

> **Paths must be absolute** and the per-domain entries need `cwd` set so `python -m servers.<domain>` resolves the package. MCP clients spawn the server without sourcing your shell init, so a bare `python3` resolves to the system python (which may not have the `mcp` package). On macOS with asdf-managed Python, look up the canonical path with `readlink -f $(which python3)`.

### The nineteen tools

Tools are listed below by domain — which is also the post-Phase-5 per-server grouping. Each tool's enclosing server is shown in parentheses; the legacy `mcp_server.py` exposes all of them.

**Eme-gir dictionary + corpus tools** (server: `eme-gir-epsd2`):

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

**ETCSL literary-corpus tools** (server: `eme-gir-etcsl`; bilingual; require `python3 build_etcsl_db.py`):

- `etcsl_search_english(query, limit)` — FTS5 over English translations; returns each match with its Sumerian lines
- `etcsl_lines_with_lemma(lemma, limit)` — literary lines containing a given Sumerian lemma + the English paragraph
- `etcsl_search_sumerian(query, limit)` — FTS5 over Sumerian transliterations; returns bilingual matches
- `etcsl_lookup_text(text_id, start, line_limit)` — read a whole composition, paginated, bilingual

**CDLI artifact catalogue tools** (server: `eme-gir-cdli`; require `python3 build_cdli_db.py`):

- `lookup_artifact(p_id)` — full per-artifact metadata for one P-id: provenience (find spot), period, museum custody (collection + accession number), dimensions, citations, plus URLs to CDLI-hosted photographs and line drawings when available.
- `find_artifacts(provenience, period, museum_collection, genre, language, limit)` — filter the 353K-row catalogue. All filters are case-insensitive substring matches (`provenience='Drehem'` matches `'Drehem (mod. Puzriš-Dagan)'`); AND together when multiple supplied. Useful for "every Ur III tablet from Drehem in the British Museum" style questions.

`see_examples` and `find_verb_form` automatically splat the same CDLI image URLs + museum metadata onto every cited line they return when `cdli.sqlite` is built — so an agent calling `see_examples('o0033341')` for the lemma `lugal` gets each attested line with a clickable link to its CDLI photograph for free.

**Signs / cuneiform rendering tools** (server: `eme-gir-ogsl`; require `corpus/ogsl.zip` from the standard corpus download):

- `lookup_sign(query)` — find a cuneiform sign by name (`LUGAL`) or phonetic value (`lugal`); returns the Unicode glyph + all known phonetic readings.
- `cuneify(spelling)` — render Oracc transliteration as Unicode cuneiform glyphs. Handles braced determinatives, hyphen-joined sign sequences, sign-list dot-compounds, morphology tails.

**Translator / bootstrap surface** (server: `eme-gir-translator`; no data dependencies — markdown only):

Two MCP resources, both intended to be fetched once at session start so the agent self-bootstraps without operator-side prompt copy-paste:

- `oracc://prompt/agent` — the drop-in system prompt teaching the end-to-end workflow (also lives as the file [`prompt/AGENT_PROMPT.md`](prompt/AGENT_PROMPT.md)).
- `oracc://grammar/sumerian` — TWO grammar references concatenated (~80 KB): Jagersma 2010 academic + Meadow/Siri Nin temple companion. Lives as [`lessons/JAGERSMA_GRAMMAR.md`](lessons/JAGERSMA_GRAMMAR.md) + [`lessons/MEADOW_GRAMMAR.md`](lessons/MEADOW_GRAMMAR.md).

Plus two MCP tool wrappers for tools-only clients that don't surface resources:

- `start_here()` — returns the agent prompt body
- `get_grammar_reference()` — returns the dual-register grammar as a structured response (`academic`, `temple`, `combined`, `temple_available` fields)

Every result returned by `translate_english` includes both raw sense frequency *and* what % of the lemma's uses are in that sense — so the agent can pick "the word for X" rather than "a word that occasionally means X".

For the underlying drop-in agent system prompt as a standalone file (useful when configuring MCP clients that don't auto-fetch resources), see [`prompt/AGENT_PROMPT.md`](prompt/AGENT_PROMPT.md).

### Watching the servers live

Every tool call is logged to a per-server file under `log/` (rotating, 5 MB × 3 backups), with arguments, duration, and a one-line result summary. Log file names:

| Server | Log file |
|---|---|
| Legacy all-in-one | `log/mcp_server.log` |
| ePSD2 | `log/eme-gir-epsd2.log` |
| ETCSL | `log/eme-gir-etcsl.log` |
| CDLI | `log/eme-gir-cdli.log` |
| Signs | `log/eme-gir-ogsl.log` |
| Translator | `log/eme-gir-translator.log` |

Tail one or all while chatting with the agent:

```bash
tail -F log/mcp_server.log              # legacy only
tail -F log/eme-gir-*.log               # all 5 per-domain servers
tail -F log/*.log                       # everything
```

Errors get full tracebacks. The startup banner reports the loaded DB sizes so you can confirm the right files are mounted.

### Running over HTTP (for remote agents, Docker, or non-stdio clients)

Every server can also speak the MCP **streamable-HTTP** transport — useful when the consumer can't (or shouldn't) launch the server as a subprocess: web-hosted agents, multi-tenant deployments, sidecar containers, etc. Suite-wide port allocation:

| Server | HTTP command | Default port |
|---|---|---:|
| Legacy all-in-one | `python3 mcp_server.py --transport http` | 5051 |
| ePSD2 | `python -m servers.epsd2 --transport http` | 5052 |
| ETCSL | `python -m servers.etcsl --transport http` | 5053 |
| CDLI | `python -m servers.cdli --transport http` | 5054 |
| Signs | `python -m servers.ogsl --transport http` | 5055 |
| Translator | `python -m servers.translator --transport http` | 5056 |

(The Flask web app uses 5050.) Each server takes the same `--host` / `--port` overrides — bind to `0.0.0.0` behind a reverse proxy on a private network.

Endpoint pattern: `http://HOST:PORT/mcp/` (note the trailing slash — `/mcp` without it 307-redirects). Tools work over HTTP exactly as they do over stdio. By default there is **no in-app authentication**; the server trusts any client that can reach the port. Always front it with a reverse proxy (nginx / caddy / traefik) when binding outside `127.0.0.1`. To enforce in-app auth instead (or in addition), see the next section — auth env vars apply to ALL servers uniformly via the shared `eme_gir.server` boilerplate.

### Adding Auth0 OAuth (optional, HTTP transport only)

The HTTP transport supports OAuth 2.1 bearer-token auth with **Auth0** as the identity provider. When enabled, every request to `/mcp/` is gated on a valid Auth0-issued RS256 JWT in the `Authorization: Bearer ...` header. The server runs as a **Resource Server** (RS) only — Auth0 issues the tokens; we just validate them.

This is **opt-in** via env var. Stdio transport never authenticates regardless (per the MCP spec, stdio uses environment-based credentials).

#### One-time Auth0 setup

1. In the Auth0 dashboard, create an **API**:
   - Name: anything descriptive, e.g. `eme-gir-mcp`
   - Identifier (audience): a stable URL representing your server, e.g. `https://eme-gir.example.com`. Doesn't have to resolve — Auth0 just uses it as an opaque string in the `aud` JWT claim.
   - Signing algorithm: **RS256** (the default)
2. On the API's "Permissions" tab, add a scope: `mcp:access` (description: "Access the eme-gir MCP server"). All 19 tools sit behind this single scope; finer-grained scopes can be added later if needed.
3. Either grab a long-lived test token from the API's "Test" tab (good for local development), or create a Machine-to-Machine application authorized to call this API and use the `client_credentials` grant.

#### Server-side env vars

When `EME_GIR_REQUIRE_AUTH=1`:

| Var | Required | Example | What it does |
|---|---|---|---|
| `EME_GIR_REQUIRE_AUTH` | yes | `1` | Toggles auth on. Anything other than `1` keeps the legacy unauthenticated behavior. |
| `EME_GIR_AUTH0_TENANT_URL` | yes | `https://my-tenant.auth0.com` | Base URL of your Auth0 tenant (no trailing slash). The verifier fetches `${TENANT}/.well-known/jwks.json` to validate signatures. |
| `EME_GIR_AUTH0_AUDIENCE` | yes | `https://eme-gir.example.com` | Must match the API identifier you set in step 1. Tokens with a different `aud` are rejected (RFC 8707 audience binding — prevents tokens for one server from being replayed against another). |
| `EME_GIR_AUTH0_RESOURCE_SERVER_URL` | yes | `https://eme-gir.example.com` | The **public-facing** URL of THIS server, used in the RFC 9728 Protected Resource Metadata served at `/.well-known/oauth-protected-resource`. Differs from `--host`/`--port` when behind a reverse proxy. |
| `EME_GIR_AUTH0_REQUIRED_SCOPE` | no | `mcp:access` | A scope that must be present in the token's `scope` claim. Defaults to `mcp:access`; set to empty string to allow any valid Auth0 token. |

#### Local invocation

```bash
EME_GIR_REQUIRE_AUTH=1 \
EME_GIR_AUTH0_TENANT_URL=https://my-tenant.auth0.com \
EME_GIR_AUTH0_AUDIENCE=https://eme-gir.example.com \
EME_GIR_AUTH0_RESOURCE_SERVER_URL=https://eme-gir.example.com \
python3 mcp_server.py --transport http --host 0.0.0.0 --port 5051
```

The startup banner will confirm the mode: `auth=ENABLED (Auth0 issuer=..., audience=..., required_scopes=['mcp:access'])`.

#### Docker invocation

The compose file already declares the env vars with empty defaults. Set them via `.env` file or shell:

```bash
EME_GIR_REQUIRE_AUTH=1 \
EME_GIR_AUTH0_TENANT_URL=https://my-tenant.auth0.com \
EME_GIR_AUTH0_AUDIENCE=https://eme-gir.example.com \
EME_GIR_AUTH0_RESOURCE_SERVER_URL=https://eme-gir.example.com \
docker compose up -d
```

Or persist them in a `.env` file alongside `docker-compose.yml`:

```env
EME_GIR_REQUIRE_AUTH=1
EME_GIR_AUTH0_TENANT_URL=https://my-tenant.auth0.com
EME_GIR_AUTH0_AUDIENCE=https://eme-gir.example.com
EME_GIR_AUTH0_RESOURCE_SERVER_URL=https://eme-gir.example.com
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
- **Reverse-proxy auth.** Run the MCP server with `EME_GIR_REQUIRE_AUTH=0` and let your reverse proxy (nginx / caddy / Auth0's own proxy) inject `Authorization` headers based on whatever auth the proxy enforces (basic auth, Auth0 SSO, mTLS).
- **Wait for native client OAuth.** The MCP spec mandates the discovery dance via Protected Resource Metadata; clients will eventually catch up. Once they do, no server-side change is needed — our server already serves the right metadata.

### Allowing the public hostname through DNS-rebinding protection (REQUIRED behind a reverse proxy)

The MCP Python SDK ships with **DNS-rebinding protection ON by default**, with an allowlist that only accepts `Host: localhost` or `Host: 127.0.0.1` (with port wildcards). When you put the HTTP transport behind a reverse proxy (Caddy / nginx / traefik) and the proxy passes the public hostname through to uvicorn unchanged, every request gets rejected with **`421 Misdirected Request: Invalid Host header`** — looks like a misconfiguration but is actually the SDK's middleware refusing an unallowlisted Host. Production deployments MUST opt in to their own hostname.

Three env vars:

| Var | Required | Example | What it does |
|---|---|---|---|
| `EME_GIR_ALLOWED_HOSTS` | yes (when behind a proxy) | `eme-gir.intra.example.net,eme-gir.example.com` | Comma-separated list of public hostnames the proxy serves the MCP server under. `localhost` / `127.0.0.1` / `::1` (with and without port suffixes) are added automatically so in-container healthchecks keep working — only list the public hostnames here. |
| `EME_GIR_ALLOWED_ORIGINS` | only for browser clients | `https://archive.example.org` | Comma-separated list of `Origin` headers accepted on cross-origin requests. Stricter than allowed_hosts: no auto-additions. Skip this if no browser MCP client will hit the endpoint. |
| `EME_GIR_DISABLE_DNS_REBINDING_PROTECTION` | escape hatch | `1` | Disables the check entirely. Only safe when your reverse proxy enforces Host validation upstream. The startup banner emits a WARNING when this is on. |

Example for a Caddy/nginx deployment:

```env
EME_GIR_ALLOWED_HOSTS=eme-gir.intra.example.net
EME_GIR_ALLOWED_ORIGINS=https://archive.example.org
```

Or in docker compose env:

```bash
EME_GIR_ALLOWED_HOSTS=eme-gir.intra.example.net docker compose up -d
```

The startup banner will confirm what got applied:

```
auth=ENABLED (Auth0 issuer=...)
transport_security=ENABLED (allowed_hosts=['eme-gir.intra.example.net','localhost','localhost:*','127.0.0.1','127.0.0.1:*','::1','[::1]:*'], allowed_origins=[...])
```

If you see `transport_security=default (SDK accepts Host: localhost / 127.0.0.1 only ...)` and you're behind a proxy, that's the cause of any 421 errors — set `EME_GIR_ALLOWED_HOSTS` and restart.

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
#   web → http://127.0.0.1:5050/eme-gir/sux
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
- Skip optional builds: `EME_GIR_BUILD_COLLOCATIONS=0 EME_GIR_BUILD_ETCSL=0 docker compose up -d` (their MCP tools degrade gracefully or error if absent).

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
    server_name eme-gir.example.org;
    # ssl_certificate ...

    location /mcp/ {
        proxy_pass         http://127.0.0.1:5051;
        proxy_http_version 1.1;
        proxy_buffering    off;          # MCP streams responses, don't buffer
        proxy_read_timeout 24h;          # long-lived SSE sessions
        auth_basic         "eme-gir MCP";
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

The repo is organized into four layers post-Phase-5:

| | |
|---|---|
| **Top-level build pipeline + entry points** | |
| `download_corpus.py` | Stdlib-only batch downloader; resume-safe; auto-fetches the InCommon TLS intermediate that Oracc's server omits. |
| `find_missing_corpora.py` | Audit tool: HEAD-probes every project in Oracc's `projects.json` against `corpus/`, lists what's reachable but missing. `--fetch` flag downloads them (with zip-validity check). |
| `build_glossary_db.py` | ijson-streaming parser. Builds `glossary.sqlite` with normalized tables for entries, forms, norms, senses, signature occurrences, periods, compounds, morphology, and instances. |
| `build_text_index.py` | Scans every `corpus/*.zip` for `corpusjson/P*.json` and per-text catalogue metadata, builds `text_index.sqlite`. |
| `build_collocations.py` | Mines 2/3/4-gram phrasal collocations from every corpusjson text → `collocations.sqlite`. |
| `build_inflected_collocations.py` | Case+sense-aware n-grams → `inflected_collocations.sqlite`. Powers `find_phrase_pattern` v2/v3 syntax. |
| `build_etcsl_db.py` | Downloads ETCSL bulk zip (4.9 MB), parses 394 TEI XML texts (custom entity-expansion table), normalizes to Oracc Unicode, ingests to `etcsl.sqlite` with FTS5 indexes. Powers the `etcsl_*` tools. |
| `build_cdli_db.py` | Downloads the CDLI catalogue CSV (~147 MB) from the cdli-gh GitHub mirror, parses 353K rows into `cdli.sqlite`. Powers `lookup_artifact` + `find_artifacts` + the AttestationLine enrichment in `see_examples`/`find_verb_form`. |
| `app.py` + `templates/` | Flask app. Routes: `/eme-gir/sux` (paginated glossary with letter zoom + search), `/eme-gir/<oid>` (entry detail). Also runs the one-shot `_cf` casefold + Sumerian-sort migrations on first startup. |
| `mcp_server.py` | **Legacy all-in-one** MCP server. Registers all 21 tools and 2 resources in one process. Kept for backwards compat; new deployments should prefer `servers/<domain>`. Logs to `log/mcp_server.log`. |
| `init.sh` | One-shot data initialization script for the Docker `init` service. Downloads corpus + builds indexes if the `data/.initialized` sentinel is missing. |
| **`servers/` — per-domain MCP entry points (Phase 5)** | |
| `servers/epsd2/__main__.py` | 11 ePSD2 dictionary + corpus tools, HTTP port 5052. `python -m servers.epsd2`. |
| `servers/etcsl/__main__.py` | 4 ETCSL literary corpus tools (bilingual), HTTP port 5053. |
| `servers/cdli/__main__.py` | 2 CDLI artifact catalogue tools, HTTP port 5054. |
| `servers/ogsl/__main__.py` | 2 cuneiform sign rendering tools, HTTP port 5055. |
| `servers/translator/__main__.py` | Bootstrap surface (2 resources + 2 tool wrappers, no data tools), HTTP port 5056. |
| **`eme_gir/` — shared Python package (Phases 1-4)** | |
| `eme_gir/paths.py` | Single source of truth for project file locations — every module imports `DATA_DIR`, `GLOSSARY_DB`, `LOG_DIR`, etc. from here. |
| `eme_gir/log.py` | `init_logging(server_name)` + `log_call` decorator. Per-server log files written to `log/<server_name>.log`. |
| `eme_gir/server.py` | Shared server boilerplate: `make_server(name, instructions)` (auth + transport-security wiring) and `run_server(mcp, log, default_port, required_dbs)` (argparse + startup banner). |
| `eme_gir/cuneify.py` | OGSL-backed transliteration → Unicode cuneiform. Loaded on first use; exposed as a Jinja filter to the web app and as the `cuneify` MCP tool. |
| `eme_gir/text_resolver.py` | Lazy lookup + LRU cache that turns a glossary `word_ref` into the actual Sumerian line. |
| `eme_gir/cdli.py` | Shared CDLI helpers (connect + enrichment). Used cross-domain by ePSD2's `see_examples`/`find_verb_form`. |
| `eme_gir/sumerian_morphology.py` | Suffix peeler + verbal-prefix detector. Shared by `parse_phrase`, `translate_sumerian`, `build_inflected_collocations.py`. |
| `eme_gir/auth0_verifier.py` | Optional Auth0 RS256 JWT verification for HTTP-transport bearer-token auth. |
| `eme_gir/umami_analytics.py` | Fire-and-forget tool-call telemetry. Opt-in via env vars. |
| `eme_gir/models/{common,epsd2,etcsl,cdli,signs,translator}.py` | Pydantic response models per-domain. `models/__init__.py` re-exports everything for backwards compat. |
| `eme_gir/tools/{epsd2,etcsl,cdli,signs,translator}.py` | Tool function implementations per-domain. Plain Python functions decorated with `@log_call`; entry points register them via `mcp.tool(annotations=READ_ONLY_ANNOTATIONS)(fn)`. |
| **Docs / config** | |
| `.mcp.json` | Project-scoped MCP server config — 6 entries (legacy + 5 per-domain). Claude Code auto-detects when launched in this directory. |
| `Dockerfile` + `docker-compose.yml` | Container stack: `python:3.12.11-slim` base, three services (init, web, mcp). |
| `requirements.txt` | Python deps (ijson, flask, mcp, gunicorn). |
| `lessons/JAGERSMA_GRAMMAR.md` | ~40 KB Jagersma-2010-based academic grammar reference. Cite as `(Jagersma §N.M)`. |
| `lessons/MEADOW_GRAMMAR.md` | ~48 KB temple-register grammar companion (Meadow's Sumerian 101 lessons + Siri Nin's commentary). Cite as `(Meadow §101-N)` or `(Siri Nin)`. Combined with JAGERSMA_GRAMMAR.md (~80 KB) by `get_grammar_reference()` and the `oracc://grammar/sumerian` resource. |
| `prompt/AGENT_PROMPT.md` | Drop-in system prompt for an LLM agent connected to the MCP servers. Also served as the `oracc://prompt/agent` resource by the Translator server. |
| `CLAUDE.md` | Detailed reference for AI coding assistants — schema docs, the Oracc URL surface, the TLS gotcha, project-prefix glossary, the 5-server architecture. |
| `static/img/jenova.png` | Header avatar / favicon. |
| **Generated artifacts (gitignored)** | |
| `corpus/` | 208 `.zip` files (~3.1 GB), one per Oracc project. |
| `data/glossary.sqlite` | ~3.4 GB indexed extract of the Sumerian glossary (15,940 entries, 35.5 M attestations, 248 K morphology rows). |
| `data/glossary_akk.sqlite` | ~114 MB Akkadian glossary built from `corpus/rinap.zip` for bilingual workflows (optional). |
| `data/text_index.sqlite` | ~10 MB index of 139,455 `(project, text_id, period, designation)` rows. |
| `data/collocations.sqlite` | ~22 MB index of ~178K phrasal n-grams of citation forms mined from the corpus. |
| `data/inflected_collocations.sqlite` | ~62 MB case+sense-aware n-grams. Powers `find_phrase_pattern` v2/v3. |
| `data/etcsl.sqlite` | ~31 MB ETCSL literary corpus (394 texts, 34,229 lines) with FTS5 on Sumerian + English. |
| `data/etcsl.zip` | ~4.9 MB cached Oxford Text Archive ETCSL bulk zip. |
| `data/cdli.sqlite` | ~157 MB CDLI artifact catalogue (353K artifacts × ~25 curated columns). |
| `data/cdli_cat.csv` | ~147 MB cached CDLI source CSV. |
| `data/.initialized` | Per-host runtime sentinel written by `init.sh` after a successful Docker first-boot init. |
| `log/*.log` | Live tool-call logs (one per running MCP server). Each rotates at 5 MB × 3 backups. |

---

## Appendix: how a request flows

```
GET /eme-gir/o0033341 (lugal)
       │
       ├─> SQLite: load entry + forms + norms + senses + sense_sigs
       │            + periods + compounds + 500 instance refs
       │
       ├─> text_resolver.resolve_many(refs, limit=20)
       │       │
       │       ├─> parse_word_ref('eme-gir:P347156.34.5')
       │       ├─> data/text_index.sqlite: lookup (project, text_id)
       │       ├─> open corpus/eme-gir.zip, parse corpusjson/P347156.json
       │       ├─> walk cdl tree, collect words on line 34
       │       └─> mark target word, dedupe by (text, line)
       │       (cached LRU 512 entries)
       │
       ├─> cuneify(form.n) for every spelling           [Jinja filter]
       │
       └─> render templates/entry.html
```
