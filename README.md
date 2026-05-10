# Jenova's Local · ePSD2

A local mirror of the [Oracc ePSD2](https://oracc.museum.upenn.edu/epsd2/sux) Sumerian dictionary that can be browsed, searched, and queried entirely offline — with Unicode cuneiform glyphs rendered next to every spelling and real attestations from the Sumerian textual corpus pulled in for every entry.

The original ePSD2 (electronic Pennsylvania Sumerian Dictionary, 2nd edition) is a 15,940-headword Sumerian-to-English dictionary backed by 35.5 million attestations across the Oracc cuneiform text corpus. Oracc publishes it as a 1.9 GB JSON archive plus 207 sibling project zips containing the actual transliterated tablets (3.1 GB total). This project does the work of:

1. **Downloading** all 208 zips from `oracc.museum.upenn.edu/json/`.
2. **Streaming the 1.9 GB Sumerian glossary into a queryable SQLite index** (15,940 headwords, 124,649 spelling variants, 19,066 senses, 35.5 M instance refs) without ever loading the file into memory.
3. **Indexing every text in every zip** so we can find which zip holds which tablet in O(log n).
4. **Resolving instance references back to actual Sumerian lines** by lazy-loading the right `corpusjson/` file and walking its tree. ~92% of references resolve from local data.
5. **Rendering Unicode cuneiform** for any transliteration string, using the OGSL (Oracc Global Sign List) sign mapping. ~93% of spellings render with full glyph coverage.
6. **Serving it all** as a small Flask web app that recreates `oracc.museum.upenn.edu/epsd2/sux` byte-for-byte on page 1, with extras: case-insensitive Unicode-aware search across six fields, attestation lines in context with the target word highlighted, and cuneiform alongside every spelling.

All Oracc data is released under CC0 (per each project's `metadata.json`); the code in this repository is also yours to do whatever you want with.

---

## Setup

```bash
# 1. Install dependencies
pip install ijson flask mcp gunicorn   # gunicorn only needed for production serving

# 2. Download the entire Oracc JSON corpus (~3.1 GB, ~2 minutes on a fast link)
python3 download_corpus.py

# 3. Build the per-text location index (~2 seconds)
python3 build_text_index.py

# 4. Build the Sumerian glossary index (~3.5 minutes)
python3 build_glossary_db.py

# 5. (Optional) Build the collocations index for find_collocations MCP tool (~5 min)
python3 build_collocations.py

# 6. (Optional) Build the ETCSL literary corpus for the etcsl_* MCP tools (~10 sec)
python3 build_etcsl_db.py

# 7. Run the web app (also populates two one-shot SQLite migrations on first hit)
python3 app.py
# -> http://127.0.0.1:5050/epsd2/sux
```

All generated SQLite indexes land in `data/`; logs land in `log/`. Both directories are auto-created on first run.

To rebuild the glossary for a different language / project (e.g. the Akkadian
glossary, useful for bilingual workflows):

```bash
python3 build_glossary_db.py --zip corpus/rinap.zip --member rinap/gloss-akk.json --db data/glossary_akk.sqlite
```

### Building the ETCSL literary corpus (optional)

ETCSL — the Oxford [Electronic Text Corpus of Sumerian Literature](https://etcsl.orinst.ox.ac.uk/) — is a curated set of 394 Sumerian *literary* texts (hymns, myths, royal hymns, proverbs, wisdom, the Sumerian King List, Inana's Descent, Gilgameš and the Underworld, the Šulgi praise poems, etc.) shipped as TEI XML with **per-word lemmatization AND English translations**. This is exactly the bilingual corpus the Oracc administrative-text bulk JSON lacks. The build script downloads the 4.9 MB zip from the Oxford Text Archive and ingests it to `data/etcsl.sqlite` (~31 MB) with FTS5 indexes for English and Sumerian search:

```bash
python3 build_etcsl_db.py
```

Once built, the MCP server exposes four `etcsl_*` tools: `etcsl_search_english`, `etcsl_lines_with_lemma`, `etcsl_search_sumerian`, and `etcsl_lookup_text`. ETCSL data is **CC BY 3.0 UK** — every tool result includes an `attribution` field; preserve it when quoting.

### Picking up new / missing Oracc projects

`download_corpus.py` only knows about zips that are listed on the public
[`/json/`](https://oracc.museum.upenn.edu/json/) download index. Oracc keeps
adding new sub-projects, and a few are only reachable via the per-project
`/{project}/json.zip` URL pattern instead of the index. To audit and pull
anything we don't have yet:

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

`find_missing_corpora.py` reuses `download_corpus.py`'s SSL setup and
resume-safe download, so the fetch is polite to Oracc's small academic
server.

## Use as an MCP server (English → Sumerian translation tools for an LLM)

The repo ships an MCP server exposing fifteen tools designed for agent-driven English↔Sumerian translation, plus a project-scoped `.mcp.json` so **Claude Code auto-detects the server** when launched in this directory — no manual client config needed.

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

Fifteen tools available to the agent:

ePSD2 dictionary + corpus tools:

- `translate_english(query, limit)` — rank Sumerian candidates for an English meaning
- `translate_sumerian(transliteration)` — reverse: parse a Sumerian phrase into per-token glosses
- `lookup_entry(oid)` — full structured view of a chosen lemma
- `see_examples(oid, limit, period)` — real attested lines, target word marked, period-filterable
- `find_compound(english_phrase)` — find idiomatic Sumerian compound expressions
- `find_collocations(word, length, limit)` — phrasal idioms attested with a given lemma (mined from the corpus, not the dictionary — surfaces formulas like "Šusuen lugal", year-name templates, royal titles)
- `get_inflections(oid)` — every attested morphological breakdown of a lemma
- `analyze_form(spelling)` — decompose an attested spelling into candidate lemmas + morphology
- `find_verb_form(cf, pos, prefix, dimensional, object_person, aspect, …)` — attested verb forms matching a feature spec; returns the morph template + spelling + attested count + one cited line per match (attestation-first; no rule-based synthesis)
- `lookup_sign(query)` — find a cuneiform sign by name or phonetic value
- `cuneify(spelling)` — render Oracc transliteration as Unicode cuneiform glyphs

ETCSL literary-corpus tools (bilingual; require `python3 build_etcsl_db.py`):

- `etcsl_search_english(query, limit)` — FTS5 over English translations; returns each match with its Sumerian lines
- `etcsl_lines_with_lemma(lemma, limit)` — literary lines containing a given Sumerian lemma + the English paragraph
- `etcsl_search_sumerian(query, limit)` — FTS5 over Sumerian transliterations; returns bilingual matches
- `etcsl_lookup_text(text_id, start, line_limit)` — read a whole composition, paginated, bilingual

Plus one MCP resource: `oracc://grammar/sumerian` — a ~14 KB Sumerian grammar cheat sheet (Edzard 2003) the agent should fetch once per translation session.

Every result returned by `translate_english` includes both raw sense frequency *and* what % of the lemma's uses are in that sense — so the agent can pick "the word for X" rather than "a word that occasionally means X".

For a complete agent system prompt that teaches the recommended translation workflow (decompose English → rank candidates → check compounds and collocations → choose aspect → apply cases → verify with attestations → render cuneiform), see [`prompt/AGENT_PROMPT.md`](prompt/AGENT_PROMPT.md). It's a drop-in for the system message of any agent connected to this server.

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

Endpoint: `http://HOST:5051/mcp/` (note the trailing slash — `/mcp` without it 307-redirects). The 15 ePSD2 + 4 ETCSL tools all work over HTTP exactly as they do over stdio. There is **no in-app authentication**; the server trusts any client that can reach the port. Always front it with a reverse proxy (nginx / caddy / traefik) when binding outside `127.0.0.1`. Sample nginx fragment:

```nginx
location /mcp/ {
    proxy_pass         http://127.0.0.1:5051;
    proxy_http_version 1.1;
    proxy_buffering    off;          # MCP streams responses, don't buffer
    proxy_read_timeout 24h;          # long-lived SSE sessions
    auth_basic         "epsd2 MCP";
    auth_basic_user_file /etc/nginx/htpasswd;
}
```

### Running the web app in production

`python3 app.py` runs Flask's built-in dev server (Werkzeug — single-threaded, no concurrency, banner says "do not use in production"). For anything beyond local development, run it under **gunicorn**:

```bash
# 4 worker processes, bound to localhost; let nginx terminate TLS
gunicorn -w 4 -b 127.0.0.1:5050 'app:create_app()'
```

`create_app()` is the application factory in `app.py`. It runs the one-shot SQLite migrations (sort + casefold columns) on startup, so a cold gunicorn boot is identical to `python3 app.py` for the database.

### Containerized deployment (Docker)

The repo ships a `Dockerfile` and `docker-compose.yml` that bake the two production processes into one image and run them as separate services. corpus/, data/, and log/ are bind-mounted from the host — too large to ship in the image (~6 GB combined) and you'll usually have built the indexes locally already.

Sequence on a fresh machine:

```bash
# 1. Build the indexes on the HOST first (they go into ./data/, which the
#    containers will bind-mount). One-time, ~5 minutes.
pip install ijson flask mcp gunicorn
python3 download_corpus.py        # ~3.1 GB into ./corpus/
python3 build_text_index.py       # ./data/text_index.sqlite
python3 build_glossary_db.py      # ./data/glossary.sqlite (~3.4 GB)
python3 build_collocations.py     # optional
python3 build_etcsl_db.py         # optional
python3 app.py & sleep 5 && kill %1   # one-shot to populate casefold + sort columns

# 2. Bring the stack up.
docker compose up -d --build

# 3. Verify both services healthy (~10 seconds).
docker compose ps
# Endpoints (default bind: 127.0.0.1 only):
#   web → http://127.0.0.1:5050/epsd2/sux
#   mcp → http://127.0.0.1:5051/mcp/  (note trailing slash)
```

Defaults:

- Both ports bind to `127.0.0.1` on the host. To expose to a private LAN, set `WEB_BIND=0.0.0.0` or `MCP_BIND=0.0.0.0` in your shell or a `.env` file before `docker compose up`. Anything beyond a private LAN MUST be fronted by a reverse proxy with TLS + auth.
- Image runs as a non-root user (uid/gid 1000). On Linux this matches the conventional first user, so bind-mounted host directories are readable/writable without a chown dance. On macOS Docker Desktop maps the owner through transparently.
- `data/` is mounted read/write on both services — not because either writes to glossary.sqlite at steady state, but because SQLite needs a writable directory for `-journal`/`-wal` files even on read-only transactions. Mark the SQLite files `chmod a-w` on the host if you really need write protection.
- gunicorn worker count defaults to 4; override with `WEB_WORKERS=8 docker compose up -d`.

Watch live logs:

```bash
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
        proxy_buffering    off;
        proxy_read_timeout 24h;
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

## What lives where

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
| `mcp_server.py` | MCP server (`mcp` SDK / FastMCP) exposing 15 tools + 1 resource for agents over stdio. Logs every call to `log/mcp_server.log`. |
| `paths.py` | Single source of truth for project file locations — every other module imports `DATA_DIR`, `GLOSSARY_DB`, `LOG_DIR`, etc. from here. |
| **Docs / config** | |
| `.mcp.json` | Project-scoped MCP server config — Claude Code auto-detects when launched in this directory. |
| `prompt/SUMERIAN_GRAMMAR.md` | ~14 KB Sumerian grammar cheat sheet (Edzard 2003), also served as the MCP resource `oracc://grammar/sumerian`. |
| `prompt/AGENT_PROMPT.md` | Drop-in system prompt for an LLM agent connected to the MCP server. |
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
| `log/mcp_server.log` | Live tool-call log; rotates at 5 MB × 3 backups. |

---

## How a request flows

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

---

## Limitations

- ~8% of glossary instance refs cite texts in projects we don't have downloaded; those fall back to raw refs.
- ~7% of spellings contain at least one sign that's missing from OGSL and renders as a `□` placeholder.
- The web app's entry page doesn't yet render a dedicated Bibliography section, per-sense interleaved examples, or a Period × Form cross-tab — though attestation lines DO surface the publication shorthand (e.g., "YOS 14, 341") via `text_index.sqlite`'s `designation` column.
- The `/epsd2/sux` glossary list page matches Oracc page-1 byte-for-byte; pages 2+ have occasional one-off reorderings (Oracc has a sub-sort tiebreaker we haven't reverse-engineered).
- Composite text refs (Q-ids) aren't handled by the resolver; only P-ids.
- **English translations are not in Oracc's public JSON archive** — they exist only in the live HTML pages at `/{project}/{P-id}` and would need scraping. The metadata `formats.tr-en` list tells us *which* texts have a translation available, not the translation itself. **Workaround:** the optional ETCSL ingest above pulls in 394 literary texts that DO ship with English translations, so any literary lookup via the `etcsl_*` tools is bilingual out of the box.

---

## A note on the data

Cuneiform is the world's oldest writing system, used continuously from ~3200 BCE to ~75 CE. Sumerian is one of the languages it recorded, attested longest in administrative and economic texts (the bulk of `epsd2-admin-ur3`, the largest single file in the corpus, is Ur III royal/temple bookkeeping from ~2100 BCE). The 35.5 million word-references in this dictionary are pointers into roughly that many actual occurrences of words on actual clay tablets, mostly held today in museum collections in London, Berlin, Philadelphia, Istanbul, and Baghdad. The cuneiform glyphs you see on entry pages here are the same characters that Sumerian scribes pressed into clay 4,000 years ago, encoded into Unicode in 2006 (range U+12000–U+1237F).
