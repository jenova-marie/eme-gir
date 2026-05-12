# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this repo is

A workspace for **parsing the Oracc / ePSD2 (electronic Pennsylvania Sumerian Dictionary) corpus and exposing it to LLM agents** for English ↔ Sumerian translation. Oracc is "The Open Richly Annotated Cuneiform Corpus" hosted at `https://oracc.museum.upenn.edu`. This directory holds:

- `download_corpus.py` — pulls the full set of `.zip` archives from `https://oracc.museum.upenn.edu/json/` into `corpus/`
- `build_glossary_db.py` — streams a `gloss-{lang}.json` from inside its zip into a queryable SQLite index (`glossary.sqlite` by default). Uses ijson (yajl2_c backend) for constant-memory parsing.
- `app.py` + `templates/` — Flask app that recreates Oracc's `/epsd2/sux` glossary browser locally, rendering from `glossary.sqlite`. Reuses Oracc's CSS via absolute URLs. Branded as "Jenova's Local · ePSD2" with `static/img/jenova.png`.
- `text_resolver.py` — resolves glossary `word_ref` strings (e.g. `epsd2/admin/ur3:P113959.10.3`) into the actual line of Sumerian text by lazy-loading the right `corpusjson/{P-id}.json` from inside its zip. LRU-cached per-text.
- `cuneify.py` — converts Oracc transliteration (`{d}lugal`, `lu₂-gal`, `peš₁₀-peš₁₀-e\l`) into Unicode cuneiform glyphs (𒀭𒈗, 𒇽𒃲, 𒁁𒁁𒂊). Loads the OGSL sign list from `corpus/ogsl.zip` once at import; exposed as a Jinja `cuneify` filter. ~93% of glossary spellings render with full glyph coverage.
- `mcp_server.py` — MCP (Model Context Protocol) server exposing the corpus to LLM agents over stdio. **Twenty-one** tools live in `tools/list`: nineteen translation/catalogue tools + two bootstrap-resource wrappers. The nineteen are: thirteen over the ePSD2 dictionary + corpus (`translate_english`, `translate_sumerian`, `parse_phrase`, `lookup_entry`, `see_examples`, `find_compound`, `find_collocations`, `find_phrase_pattern`, `get_inflections`, `analyze_form`, `find_verb_form`, `lookup_sign`, `cuneify`) + four over the ETCSL literary corpus (`etcsl_search_english`, `etcsl_lines_with_lemma`, `etcsl_search_sumerian`, `etcsl_lookup_text` — bilingual because ETCSL ships English translations) + two over the CDLI artifact catalogue (`lookup_artifact`, `find_artifacts` — provenience, museum custody, and CDLI-hosted photo / lineart links). `see_examples` and `find_verb_form` also splat in CDLI image URLs and museum metadata onto every cited line when the catalogue is built. `parse_phrase` is the case-aware grammatical pre-annotator: it peels suffixes, classifies tokens by phrase role (subject_ergative, oblique_dative, comparison_equative, verb_head, …), and emits a compact bracket skeleton — not a true syntactic parser, but enough morphology-driven anchor points for the LLM to do the final parse. The two bootstrap wrappers — `start_here()` and `get_grammar_reference()` — return the same content as the two MCP resources (`oracc://prompt/agent`, `oracc://grammar/sumerian`) but via the universally-supported tools surface, since many production MCP clients today don't wire up `resources/list`/`resources/read`. `start_here()` leads its docstring with "⭐ CALL THIS FIRST" so a tools-list scan naturally surfaces it as the entry point. Spec-complete clients should prefer the resource form (cheaper, no tool round-trip, semantically primary). Designed for English↔Sumerian translation workflows; every candidate carries `sense_count` + `sense_pct` so the agent can distinguish "the word for X" from "X is a fringe meaning of this word".
- `build_etcsl_db.py` — downloads the [ETCSL](https://etcsl.orinst.ox.ac.uk/) bulk zip (4.9 MB) from the Oxford Text Archive into `data/etcsl.zip`, parses 394 TEI XML literary texts (with a hand-built entity-expansion table for ~80 ETCSL-specific entity refs that stdlib xml.etree refuses), normalizes ETCSL's ASCII transliteration (`j→ŋ`, `c→š`, digit subscripts) to ePSD2/Oracc convention, ingests into `data/etcsl.sqlite` (~31 MB) with FTS5 indexes on Sumerian transliteration AND English translations. Powers the four `etcsl_*` MCP tools.
- `build_cdli_db.py` — downloads the [CDLI](https://cdli.earth) bulk catalogue (`cdli_cat.csv`, ~147 MB) from the cdli-gh GitHub mirror via media.githubusercontent.com (LFS-direct, no `git lfs` install needed), parses 353K artifact rows × 64 columns into `data/cdli.sqlite` (~157 MB) keeping a curated subset of ~25 columns we actually use (designation, period, provenience, museum, dimensions, image-availability flags). Powers the `lookup_artifact` + `find_artifacts` MCP tools AND the photo/lineart URL enrichment that gets splatted onto every cited line by `see_examples` / `find_verb_form`. CDLI catalogue is CC0; we host no images — all image URLs point straight to cdli.earth.
- `build_collocations.py` — walks every corpusjson text in `corpus/`, extracts 2/3/4-grams of citation forms within each line, stores counts in `collocations.sqlite`. ~138K texts → ~178K collocations kept (default `--min-count 3`).
- `build_text_index.py` — scans every project zip in `corpus/` for `*/corpusjson/P*.json` files and builds `text_index.sqlite`, a `(project, text_id) → (zip_path, member_path)` map. Takes ~2 s for the full 208 zips.
- `paths.py` — single source of truth for project file locations (DATA_DIR, LOG_DIR, GLOSSARY_DB, etc.). Every other module imports its canonical paths from here.
- `corpus/` — 208 zip files (~3.1 GB), one per Oracc project; this is the bulk dataset
- `data/` — generated SQLite indexes live here (auto-created on first run via `paths.py`):
  - `data/glossary.sqlite` — 3.4 GB indexed extract of `epsd2/gloss-sux.json` (15,940 headwords, 124,649 spellings, 37,659 period rows, 1,901 compound refs, 35.5 M instance refs); sub-10 ms point lookups. Rebuild with `python3 build_glossary_db.py`.
  - `data/text_index.sqlite` — ~10 MB index of 139,455 `(project, text_id, period, designation)` rows across all corpus zips, enabling instant text→zip lookup AND period filtering on attestations. 85% of texts have period metadata pulled from each project's `catalogue.json`. Rebuild with `python3 build_text_index.py`.
  - `data/collocations.sqlite` — ~22 MB index of 178K phrasal collocations (2/3/4-grams of citation forms) mined from ~138K corpusjson texts, with min count 3. Plus 62K unigram counts. Rebuild with `python3 build_collocations.py`.
  - `data/inflected_collocations.sqlite` — ~62 MB index of ~106K case+sense-aware n-grams (cf, gw, pos, case per slot) mined from the same ~138K corpusjson texts, filtered to Sumerian-only (`f.lang` starts with `sux`). Uses the same suffix peeler as `parse_phrase` to detect the outermost case marker on each lemma's visible spelling. Powers v2/v3 syntax (`lugal[king]:ergative`, `N:locative`, etc.) in `find_phrase_pattern`. Built in ~5 min. Rebuild with `python3 build_inflected_collocations.py`.
  - `data/glossary_akk.sqlite` — ~114 MB Akkadian glossary built from `corpus/rinap.zip::rinap/gloss-akk.json` (3,651 Akkadian entries, 1.18 M instance refs). Built via `python3 build_glossary_db.py --zip corpus/rinap.zip --member rinap/gloss-akk.json --db data/glossary_akk.sqlite`. Not the default DB the MCP server reads; available for bilingual workflows when wired in.
  - `data/etcsl.sqlite` — ~31 MB ETCSL literary corpus: 394 texts, 34,229 lines, 159,963 lemmatized words, 5,608 translation paragraphs. FTS5 indexes on `lines.transliteration` (Sumerian) and `paragraphs.translation` (English). Schema is keyed by `lines.line_id` (globally unique within a text, e.g. `c141.1` or `c24216.B.5`) — NOT `line_n` — because 168 of the 394 texts have multi-section line numbering that restarts at 1 per section. `lines.ord` (1..N sequential within text) drives stable paging in `etcsl_lookup_text`; `lines.line_label` (`"1"` or `"A.5"`) is the human-readable display string. Build via `python3 build_etcsl_db.py`. Build script auto-downloads `data/etcsl.zip` from `ota.bodleian.ox.ac.uk` (cached, idempotent).
  - `data/etcsl.zip` — ~4.9 MB cached source download.
  - `data/cdli.sqlite` — ~157 MB CDLI artifact catalogue: 353,283 artifacts × ~25 curated columns (designation, period, provenience, museum, dimensions, image-availability flags). Indexes on period, provenience, museum_collection, genre, language. Powers `lookup_artifact` + `find_artifacts` AND the photo/lineart URL enrichment on `see_examples` / `find_verb_form`. Build via `python3 build_cdli_db.py`. Source: cdli-gh/data on GitHub via media.githubusercontent.com (LFS-direct, no `git lfs` install needed). Last meaningful data update was Aug 2022 — stale but acceptable since catalogue facts (provenience, museum custody, period) don't change after accessioning.
  - `data/cdli_cat.csv` — ~147 MB cached source CSV (downloaded from cdli-gh/data; rebuild script reuses if present).
- `log/` — generated server logs live here.
- `prompt/` — checked-in prompt + reference material for LLM agents:
  - `prompt/SUMERIAN_GRAMMAR.md` — ~30 KB comprehensive Sumerian grammar cheat sheet distilled from Jagersma 2010 (Bram Jagersma, *A Descriptive Grammar of Sumerian*, PhD dissertation, Universiteit Leiden, 2010, 776 pp). Every grammatical claim carries an inline Jagersma §-citation for verification. Covers phonology, the twelve enclitic cases (with surface-ambiguity tables), the nine-slot finite-verb template, perfective/imperfective inflection patterns, all preformatives, dimensional prefixes, non-finite forms, copular clauses, and nominalization-based subordination. Default period for translation when unspecified is **ED (Early Dynastic, ~2900-2350 BCE)** — Jagersma's primary descriptive ground (Old Sumerian = ED IIIa-IIIb). Shipped both as a file AND as the MCP resource `oracc://grammar/sumerian` so an agent can fetch it once per session. Companion audit-trail files: `prompt/JAGERSMA_CONVENTIONS.md` (Jagersma → Oracc notation map; period labels; citation format) and `prompt/JAGERSMA_NOTES.md` (per-chapter structured digest of the 31-chapter source, ~17K words, every claim cited).
  - `prompt/AGENT_PROMPT.md` — drop-in system prompt that teaches an LLM agent how to use the MCP server's tools end-to-end (10-step English→Sumerian workflow + reverse direction + worked example). Distinct from SUMERIAN_GRAMMAR.md: the prompt teaches HOW to use the tools, the grammar teaches WHAT Sumerian is. Shipped both as a file AND as the MCP resource `oracc://prompt/agent` so an agent can self-bootstrap on first connection without operator-side configuration.
- `README.md` — top-level project README aimed at humans cloning the repo.
- `.mcp.json` — project-scoped MCP server config so Claude Code auto-detects the server when launched in this directory. **Uses absolute paths** because Claude Code spawns MCP server processes without sourcing the user's shell init, so a bare `python3` resolves to `/usr/bin/python3` (no `mcp` package). See "MCP server" section.
- `log/mcp_server.log` — generated. Live tool-call log written by the server's `_log_call` decorator (rotating, 5 MB × 3 backups). Tail with `tail -F log/mcp_server.log` to watch agent activity in real time.
- `static/img/jenova.png` — header avatar (128×128, 24 KB) and favicon
- `.incommon_intermediate.pem` — cached TLS intermediate cert (see "TLS gotcha" below); do not delete

**Data license:** All Oracc JSON data is released under **CC0** (per each project's `metadata.json`). No attribution required, but customary.

## Common commands

```bash
# Download or resume the entire corpus (idempotent; skips files already at the right size)
python3 download_corpus.py

# Just print URLs without downloading
python3 download_corpus.py --list-only

# Tune parallelism (default 4; be polite — small academic server)
python3 download_corpus.py --workers 2

# Inspect a single project's contents without extracting
unzip -l corpus/epsd2.zip
unzip -p corpus/epsd2.zip epsd2/metadata.json | python3 -m json.tool

# Build the glossary SQLite index (defaults: corpus/epsd2.zip → epsd2/gloss-sux.json → data/glossary.sqlite)
python3 build_glossary_db.py
# Build for a different language / project
python3 build_glossary_db.py --zip corpus/rinap.zip --member rinap/gloss-akk.json --db data/glossary_akk.sqlite

# Build the text-location index across all 208 zips (needed for attestation rendering)
python3 build_text_index.py

# Query the glossary
sqlite3 -header -column data/glossary.sqlite "SELECT cf, gw, pos, icount FROM entries WHERE cf='lugal';"

# Run the local Oracc-style glossary browser
python3 app.py                # http://127.0.0.1:5050/epsd2/sux
python3 app.py --port 8000 --debug

# Run the MCP server over stdio (default; for Claude Desktop / Code MCP config)
python3 mcp_server.py

# Or over HTTP (streamable-http transport) for remote agents, Docker, etc.
# Endpoint: http://HOST:PORT/mcp/  (note trailing slash)
# No in-app auth — bind to 127.0.0.1 for local-only, or 0.0.0.0 behind a
# reverse proxy that handles TLS + access control.
python3 mcp_server.py --transport http --host 127.0.0.1 --port 5051

# Run the Flask web app under a production WSGI server (vs `python3 app.py`
# which uses the single-threaded Werkzeug dev server). create_app is the
# Flask application factory; gunicorn picks it up via the call form.
gunicorn -w 4 -b 127.0.0.1:5050 'app:create_app()'

# Bring up both services in containers (image gets built on first invocation;
# corpus/, data/, log/ are bind-mounted from the host — see Dockerfile and
# docker-compose.yml). First-boot order matters: the web service runs the
# casefold/sort migrations, and the mcp service depends on its healthcheck.
docker compose up -d --build
docker compose logs -f mcp
```

Dependencies (`pip install ijson flask mcp gunicorn`):
- `ijson` — constant-memory streaming JSON parser. Uses the `yajl2_c` backend automatically when available; required by `build_glossary_db.py`, `build_text_index.py`, `download_corpus.py`.
- `flask` — required by `app.py` (the local glossary browser).
- `mcp` — required by `mcp_server.py` (the MCP server). The `--transport http` mode pulls in `uvicorn` + `starlette` transitively (already deps of `mcp[server]`).
- `gunicorn` — production WSGI server for the Flask app. Optional for development (use `python3 app.py` for autoreload + Werkzeug); required for any deployment beyond localhost.
- Everything else is stdlib.

There are no tests, build, or lint steps — this is a data/scripts repo.

**Log convention:** when capturing build script output, write to `log/`:

```bash
python3 build_glossary_db.py 2>&1 | tee log/build_glossary.log
python3 build_text_index.py  2>&1 | tee log/text_index_build.log
python3 build_collocations.py 2>&1 | tee log/collocations_build.log
python3 download_corpus.py   2>&1 | tee log/corpus_download.log
```

The MCP server writes its own log to `log/mcp_server.log` automatically; build scripts only log to disk if you `tee` them. `*.log` is gitignored anywhere.

## The reverse-engineered Oracc URL surface

Source: `js/p4.js` and `js/p4cbd.js`. The server renders **HTML**, not JSON, on these endpoints — but the markup uses stable hooks (`class="cf"` citation form, `class="gw"` guide word/English gloss, `class="sux"` Sumerian, `class="sense"`, `class="wr"` writing, `class="summary-headword"`) and `data-oid` IDs (e.g., `o0023086`). CORS is open (`access-control-allow-origin: *`).

Modern routes (the live ones):

| Purpose | Pattern | Example |
|---|---|---|
| Glossary landing | `/{proj}/{lang}` | `/epsd2/sux` |
| Search | `/{proj}/{lang}?q={term}` | `/epsd2/sux?q=lugal` |
| Article (entry) | `/{proj}/{oid}` | `/epsd2/o0023086` |
| Page navigation | `/{proj}/{lang}?page=N&zoom=A` | `/epsd2/sux?zoom=Š&page=2` |
| Distribution profile | `/{proj}/{lang}?xis={instance}` | usage stats per period/genre |
| Sign info | `/{proj}/ogsl/brief/{id}.html` | cuneiform sign details |
| Sources / score | `/{proj}/{oid}?sources` or `?score` | textual attestations |

The legacy `/cgi-bin/oracc?...` and `/cgi-bin/oraccget?...` routes referenced in `p4cbd.js` are mostly **dead** (return 4-byte empty responses). Use the modern URL routes above for HTML scraping, or — preferred — work from the bulk JSON in `corpus/`.

## Oracc JSON Open Data format (parser reference)

Authoritative source: `https://oracc.museum.upenn.edu/doc/opendata/json/index.html`. Every Oracc JSON file is a single object with a `"type"` member (and a `"project"` member for project data).

### Zip layout

Each project zip contains a single top-level directory matching the project name (e.g., `epsd2/…`, `rinap/…`). Standard files inside:

- `metadata.json` — project config, license, witnesses (composites), and a `"formats"` map listing which texts have `atf`, `lem`, `tr-en`, `xtf`
- `catalogue.json` — per-text bibliographic catalogue keyed by text ID; always provides at least one of `id_text`/`id_composite`, plus `designation`, `period`, `provenience`
- `corpus.json` — manifest of text editions in `corpusjson/` (only present for text-edition projects)
- `corpusjson/P{nnnnnn}.json` — one file per text edition (see "cdl tree" below)
- `gloss-{lang}.json` — glossary, one per language (e.g., `gloss-sux.json`, `gloss-akk.json`)
- `index-{name}.json` — search-engine index exports: `index-cat`, `index-lem`, `index-{lang}`, `index-txt`, `index-tra`, `index-qpn`
- `sortcodes.json` — sort-order maps
- `{proj}-portal.json`, `{proj}-sl.json` — project-specific extras
- `cat.geojson` — geographic data when present (e.g., RINAP)

`manifest.json` is mentioned in the spec but **only served live** — it is not packed into the zips.

### Project type quirks

`metadata.json` → `config.project-type` distinguishes shapes:

- **`superglo`** (e.g., epsd2): primarily a glossary; the heavy file is `gloss-sux.json` (~1.9 GB for epsd2). May lack `corpusjson/`.
- Text-edition projects (e.g., rinap): include `corpusjson/` plus `gloss-*.json` glossaries built from those texts.

### Text editions: the "cdl" tree (`type: "cdl"`)

XCL = "XML Chunks and Lemmas". The tree has three primary node types under `cdl` arrays:

- **`c`** — chunk: text, sentence, clause, phrase, etc. Has `id`, `type`, `subtype?`, `label?`, and a nested `cdl` array.
- **`d`** — discontinuity: `line-start`, `tablet`, `obverse`, `reverse`, `punct`, damage markers. Has `ref`, `n?`, `label?`, `subtype?`.
- **`l`** — lemma: a lemmatized word. Key fields:
  - `frag` — the visible transliteration fragment (with brackets, half-brackets, etc.)
  - `id` — lemma ID
  - `ref` — `{textid}.{lineN}.{wordN}` reference
  - `inst` — citation form (`cf[gw]POS`)
  - `sig` — full signature string (see below)
  - `f` — feature object: `lang`, `form`, `cf` (citation form), `gw` (guide word), `sense`, `norm` (normalization), `pos`, `epos` (extended POS)

The **`sig` string** has the shape `@{project}%{lang}:{form}={cf}[{gw}//{sense}]{pos}'{epos}${norm}`. To save space, parsed signatures are deduplicated into a top-level `sigs` object in the corpus JSON, keyed by the sig string.

To reconstruct text: walk the `cdl` tree depth-first and concatenate `text` properties on `d` and `l` nodes (with sensible joiners — `gdl_delim` on `d` nodes provides spacing).

### Glossaries: `gloss-{lang}.json` (`type: "glossary"`)

Top-level fields: `type`, `project`, `lang`, `entries[]`, `instances{}`.

Each entry in `entries[]`:

- `headword` — `cf[gw]POS` form, e.g., `qēmu[flour]N`
- `id`, `cf`, `gw`, `pos`
- `icount` (instance count), `ipct` (percentage), `xis` (reference into `instances{}`)
- `forms[]` — spelling variants, each with `n` (the spelling), `icount`, `ipct`, `xis`
- `norms[]` — normalizations
- `senses[]` — distinct senses, each with their own `forms`/`norms`/`sigs`
- `sigs[]` — full signature occurrences

The top-level `instances{}` map keys (e.g., `akk.r0019b`) to lists of word references like `"rimanum:P405162.3.2"` — use these to jump back into `corpusjson/` files. Project prefix is always present because projects can cite each other's texts.

### Indexes: `index-{name}.json` (`type: "index"`)

`{ type: "index", project, name, keys: [{key, count, instances: [...]}] }`. Keys are normalized (accents → numeric indices, English uses a stemmer). For `txt`/`lem`/`tra` index types, instances are word IDs — display them via `https://oracc.museum.upenn.edu/{PROJECT}/{INSTANCE_ID}/html`.

### Top-level (server-side, not in zips)

`projects.json` (`type: "projects"`, simple list) and `projectlist.json` (`type: "projectlist"`, with blurbs/abbreviations) — both retrievable from the server root.

## glossary.sqlite schema

Built by `build_glossary_db.py`. All `icount`/`ipct` fields are integers (cast from the JSON's stringified numbers). Indexes are deferred until after bulk insert and built at the end for ~3× faster ingest.

| Table | Rows (epsd2 sux) | Columns | Notes |
|---|---|---|---|
| `meta` | 11 | `key, value` | source path, byte count, row counts, ingested_at, sort_version |
| `entries` | 15,940 | `id PK, headword, cf, gw, pos, icount, ipct, xis, [letter, sort_key]` | one row per headword. `headword` is the full `cf[gw]POS` string. `letter`/`sort_key` are added by `app.py` on first run for Sumerian-correct alphabetical ordering (Ŋ between G and H, separators before letters, `.` after letters). Indexed on `cf`, `gw`, `pos`, `xis`, `letter`, `sort_key`. |
| `forms` | 124,649 | `id PK, entry_id, n, icount, ipct, xis` | spelling variants. `n` is the orthography (e.g. `lugal-e`). Indexed on `entry_id`, `n`, `xis`. |
| `norms` | 75,217 | `id PK, entry_id, n, icount, ipct, xis` | normalizations. Indexed on `entry_id`, `n`. |
| `senses` | 19,066 | `id PK, entry_id, n, mng, pos, icount, ipct, xis` | distinct senses for polysemous entries. `mng` is the meaning gloss. Indexed on `entry_id`, `mng`. |
| `sense_sigs` | 366,760 | `id PK, sense_id, sig, icount, ipct, xis` | full Oracc signature occurrences (`@proj%lang:form=cf[gw//sense]pos'epos$norm`). Indexed on `sense_id`, `sig`. |
| `periods` | 37,659 | `entry_id, ord, p, icount, ipct, xis, PK(entry_id, ord) WITHOUT ROWID` | per-period attestation counts (e.g., "Ur III: 9816, Old Babylonian: …"). `ord` preserves Oracc's display order. Indexed on `p`. |
| `compounds` | 1,901 | `entry_id, xcpd, eref, PK(entry_id, xcpd) WITHOUT ROWID` | "see-compounds" cross-references — e.g. *a* [ARM] → *a aŋ* [COMMAND], *a bad* [SPREAD], etc. `eref` points at the compound entry's `id`. Indexed on `eref`. |
| `morphology` | 248,176 | `cbd_id PK, entry_id, kind, n, icount, ipct, xis WITHOUT ROWID` | per-entry morphological breakdown. `kind` ∈ {`base`, `morph`, `morph2`, `stem`, `prefix`, `form-sans`}. `n` is the morpheme pattern (`~` marks the base position in `morph` patterns; `mu.na:~` = prefix chain `mu.na` + base; `~,bi.a` = base + 3sg.nonp poss + locative). For epsd2/sux: 120K form-sans, 75K morphs, 38K bases, 15K prefixes; stem and morph2 empty. Indexed on `(entry_id, kind)`, `(kind, n)`, `xis`, and `(kind, n_cf)` for case-insensitive lookups. |
| `instances` | 35,533,056 | `xis, word_ref, PK(xis,word_ref) WITHOUT ROWID` | the `xis → [{project}:{textid}.{line}.{word}]` map flattened into rows. Indexed on `word_ref` for reverse lookups. |

Common queries:

```sql
-- All spellings of "lugal" (king), most-attested first
SELECT f.n, f.icount FROM entries e JOIN forms f ON f.entry_id=e.id
WHERE e.cf='lugal' AND e.gw='king' ORDER BY f.icount DESC;

-- All texts where a specific word instance appears
SELECT word_ref FROM instances WHERE xis = (
  SELECT xis FROM entries WHERE cf='lugal' AND gw='king'
);

-- Reverse lookup: which lemma does this attestation belong to?
SELECT e.cf, e.gw FROM instances i
JOIN entries e ON e.xis = i.xis
WHERE i.word_ref = 'epsd2:P012345.10.3';
```

To map `word_ref` (`{project}:{P-id}.{line}.{word}`) back to the actual transliteration, look up the corresponding `corpusjson/{P-id}.json` inside the project zip and walk the `cdl` tree to the matching `ref`.

## Local Oracc-style browser (`app.py`)

Recreates `https://oracc.museum.upenn.edu/epsd2/sux` from the local SQLite. **Page 1 OIDs match the live site exactly**; pages 2+ match closely with occasional one-off reorderings (Oracc has a sub-sort tiebreaker we haven't reverse-engineered yet — likely an entry-level sortcode field we don't capture). All of `corpus/` and the live site remain CC0.

Routes:

- `GET /` → 302 to `/epsd2/sux`
- `GET /epsd2/sux` — paginated glossary; query params `?page`, `?zoom={letter}`, `?q={search}`
- `GET /epsd2/<oid>` — entry detail page

Sumerian alphabetical sorting is implemented in `sort_key()` in `app.py`. Bumping `SORT_VERSION` triggers a one-shot re-population of the `letter` and `sort_key` columns on the next startup. Search-helper substitutions (`j→ŋ`, `sz→š`, `s,→ṣ`, `t,→ṭ`, digits → subscripts, `'→ʾ`) are applied to the `?q=` param in `normalize_query()`.

`app.py` also owns the casefold migration (`ensure_casefold_columns()`, gated on `CASEFOLD_VERSION`): adds `_cf` mirror columns to `entries.cf`, `entries.gw`, `senses.mng`, `forms.n`, `norms.n`, `compounds.xcpd`, and `morphology.n` for fast Unicode-aware case-insensitive search, plus an `idx_morphology_kind_n_cf` index that the MCP server's `analyze_form` and `translate_sumerian` rely on. Bumping `CASEFOLD_VERSION` re-runs the migration. Both migrations are idempotent and run on `python3 app.py` startup; the MCP server checks for `casefold_version` in `meta` and bails with a hint if absent.

Templates use **Oracc's own CSS** by linking the absolute `https://oracc.museum.upenn.edu/css/p4.css` etc. — so the look matches without us hosting any styles. If you want to detach for offline use, mirror those CSS files into `static/` and update `templates/base.html`.

## MCP server (`mcp_server.py`)

Exposes the corpus to LLM agents via the Model Context Protocol over stdio. Built with `mcp` Python SDK's `FastMCP`. Bias: every tool that returns lemma candidates returns BOTH `sense_count` (raw frequency of *this sense*) and `sense_pct` (what % of the entry's total uses are this sense), so the agent can rank "the word for X" above "X is a fringe meaning of this word" — see the discussion in CLAUDE history.

Tools:

| Tool | Purpose |
|---|---|
| `translate_english(query, limit)` | Rank Sumerian candidates for an English word. Hits both entry guide-words and per-sense meanings. Sorted by `sense.icount DESC`. |
| `translate_sumerian(transliteration, limit_per_token)` | Reverse-direction lookup: parse a Sumerian phrase into per-token English glosses. **Whole-token-first**: splits the input only on whitespace, then tries the whole hyphenated word as a forms+form-sans+bases lookup (so `lu₂-gal` resolves cleanly as `lugal`, `mu-un-du₃` as the inflected `du₃`, `dili-bad` as `dilibad`); only falls back to hyphen-splitting when the whole-token lookup yields zero candidates. Each token also carries detected case/possessive/plural suffix chain when present (the Option 3 enhancement) — same suffix table used by `parse_phrase`. `match_kind` field signals `"whole"` vs `"split_fallback"` vs `"unmatched"`. |
| `parse_phrase(transliteration)` | Case-aware grammatical pre-annotation. Goes beyond `translate_sumerian` glossing by classifying each token's phrase role via the morphology (`subject_ergative`, `oblique_dative`, `comparison_equative`, `verb_head`, …), returning a compact bracket skeleton (`[NP lugal-ERG] [NP e-ABS] [V du (mu-na-)]`), and emitting heuristic notes (e.g. transitive-clause detection, ambiguous-suffix warnings for `-e`/`-a`/`-bi`). NOT a true syntactic parser — it surfaces the grammatical role markers explicitly encoded in the morphology and lets the agent build the final parse. The agent should call this when structural ambiguity matters; for plain word-by-word lookup `translate_sumerian` is lighter. Verb-form detection uses the prefix chain (mu-, ba-, bi₂-, …) and skips nominal suffix-peeling when triggered. |
| `lookup_entry(oid)` | Full structured view: senses, top spellings (with cuneiform glyphs), periods, compounds. |
| `see_examples(oid, limit, period)` | Real attested lines via `text_resolver`, target word marked. Supports period filter (substring, case-insensitive — "babylonian" matches Old AND Middle Babylonian) — pre-fetches matching text IDs from `text_index.sqlite` to avoid resolving irrelevant texts. |
| `find_compound(english_phrase)` | Find idiomatic Sumerian compound expressions for an English phrase. |
| `find_collocations(word, length, limit)` | Find multi-word phrasal idioms attested with a given lemma. Reads `collocations.sqlite`. The index is keyed by **citation form (cf)**, NOT by spelling — but the tool auto-resolves common misses: if `word='e₂'` (a spelling) returns zero, it looks up `e₂` in `forms.n_cf`/`morphology.n_cf`, picks the most-attested matching cf (`e`), and retries. Result includes `resolved_from` when this happened. |
| `find_phrase_pattern(pattern, limit)` | Structural-template query over the corpus collocation index. Each slot's grammar is `TARGET ('[' gw ']')? (':' case)?` where TARGET ∈ {literal cf, POS code, POS family glob `V*`, or `*` for any cf}. The optional `[gw]` constrains the sense (homograph disambiguation, v3); the optional `:case` constrains the detected outermost case suffix (v2). Both gw and case accept `!`-prefix for negation. Routing: prefers `data/inflected_collocations.sqlite` (the case+sense aware build, ~62 MB / 106K rows) when available; falls back to `data/collocations.sqlite` for v1 patterns when the inflected DB is absent; returns ErrorResponse with a build-hint when v2/v3 syntax is used and the inflected DB is missing. Rows are pre-keyed by full distinct `(cf, gw, pos, case)` tuples in the inflected table, so homograph + case variants surface as separate rows (e.g. `lugal[king]-ERG` vs `lugal[king]-` are distinct hits). Slot-parser is in `_parse_slot()`; the two query backends are `_find_phrase_pattern_inflected()` and `_find_phrase_pattern_legacy()`. Both validate length 2-4 (the index only holds 2/3/4-grams). |
| `get_inflections(oid, min_count=2, limit_per_kind=25)` | Show attested morphological breakdowns. Defaults filter the long tail of count<2 noise and cap each kind bucket at 25 to keep results scannable in an MCP context. Pass `min_count=0, limit_per_kind=0` for the full firehose (e.g. `lugal` has 132 form-sans rows total). Result includes `truncated` dict telling the caller when more data exists. |
| `analyze_form(spelling, limit)` | Decompose a Sumerian spelling into candidate lemmas + their morphological role. Indexed lookup against `forms.n_cf` + `morphology.n_cf` (kind in base/form-sans/morph). |
| `find_verb_form(cf, pos, prefix=…, dimensional=[…], object_person=…, polarity=…, aspect=…, suffix_a=…, reduplicated=…, with_example=True)` | Attestation-first verb-form retrieval. Translates a grammatical-feature spec into a slot-aware filter over `morphology` rows for the given `(cf, pos)` entry, ranks by `icount`, and (by default) returns one cited line per match via `text_resolver`. Slot model: `[nu] . [conj-prefix=mu/ba/i/bi/ga/ha] . [dim slots=na(dat)/ni(loc)/da(com)/ta(abl)/ši(term)/e(loc2)] . [obj-agreement=n(3sg.h)/b(3sg.nh)/neš(3pl.h)/ʔ(1sg)] : [base] ; [suffixes incl. nominalizer -a, marû -e/-ed/-en/-eš]`. `prefix='imp'` matches the bare base. Filtering is done in Python after pulling the entry's morph rows so slot tokens (`n` ≠ `na` ≠ `ne`) are matched exactly — GLOB alone is too greedy. Aspect is a SUFFIX HEURISTIC; verbs with stem alternation (e.g. ŋen/du-du for "go") are stored as separate entries and must be queried by cf separately. Returns `verified_in_forms=True` when the mechanically-synthesized spelling happens to match a `forms.n` row exactly; not all do (Sumerian phonology fills in vowels — `mu.n:~` surfaces as `mu-un-du₃` not `mu-n-du₃`), but the morph row's `count` is authoritative regardless. |
| `lookup_sign(query)` | Look up a cuneiform sign by name ("LUGAL") or phonetic value ("lugal"). Returns the Unicode glyph, sign name, all phonetic readings. |
| `cuneify(spelling)` | Render Oracc transliteration as Unicode cuneiform glyphs. |
| `etcsl_search_english(query, limit)` | FTS5 over ETCSL English translations. Each hit returns the English paragraph PLUS the Sumerian lines (`line` is the display label like `"1"` or `"A.5"`) it covers. Bilingual. |
| `etcsl_lines_with_lemma(lemma, limit)` | Find literary lines containing a given Sumerian lemma (cf), each with the English translation paragraph that line belongs to. Joins on `(text_id, line_id)`. |
| `etcsl_search_sumerian(query, limit)` | FTS5 over Sumerian transliteration in ETCSL. Returns each match with its English paragraph. Hyphens are token separators (`unicode61`); quote multi-token spellings (`'lugal-bi'`). |
| `etcsl_lookup_text(text_id, start, line_limit)` | Read a whole composition. `start` is a 1-based `ord` (NOT a line label — multi-section texts like `c.2.4.2.16` would otherwise have ambiguous line numbers). Result includes `next_start` for paging through long works. Lines are grouped into bilingual blocks by paragraph. |
| `start_here()` | Resource-blind-client wrapper: returns the agent system prompt (same content as the `oracc://prompt/agent` resource). Docstring leads with "⭐ CALL THIS FIRST" so tools-only clients naturally surface it as the entry point on first connection. |
| `get_grammar_reference()` | Resource-blind-client wrapper: returns the Sumerian grammar cheat sheet (same content as the `oracc://grammar/sumerian` resource). Called after `start_here()` per the agent prompt's bootstrap instructions. |

Sanity-checks `glossary.sqlite` and `text_index.sqlite` exist on startup; bails with a hint if not. Also requires the `app.py` casefold migration to have run (checks `meta.casefold_version`). Run order from cold: `download_corpus.py` → `build_text_index.py` → `build_glossary_db.py` → `build_collocations.py` (optional, only needed for `find_collocations` tool) → `build_etcsl_db.py` (optional, only needed for the four `etcsl_*` tools) → `python3 app.py` (once, to populate casefold + sort columns) → `python3 mcp_server.py`.

The `find_collocations` tool degrades gracefully (returns an error structure) if `collocations.sqlite` is absent. The four `etcsl_*` tools raise `FileNotFoundError` if `etcsl.sqlite` is absent (caught and returned to the agent as an error result). All other tools work without either optional DB.

### ETCSL literary corpus (`build_etcsl_db.py` + the four `etcsl_*` tools)

ETCSL (the Oxford [Electronic Text Corpus of Sumerian Literature](https://etcsl.orinst.ox.ac.uk/), Black et al. 1998-2006, **CC BY 3.0 UK**) is a curated set of 394 Sumerian literary texts (hymns, myths, royal hymns, proverbs, wisdom, the King List, Inana's Descent, Gilgameš, Šulgi praise poems) shipped as TEI XML with **per-word lemmatization AND English translations**. This fills the bilingual gap in the Oracc bulk JSON, which ships only transliteration. Every `etcsl_*` tool result includes an `attribution` field (`ETCSL_ATTRIBUTION` constant in `mcp_server.py`) — preserve it when quoting.

Schema design (`data/etcsl.sqlite`):
- `texts` — one row per composition: `text_id`, `title`, `has_translation`.
- `lines` — `(text_id, line_id)` is the unique key; `line_id` is globally unique within a text (e.g. `c141.1` or `c24216.B.5`). Flat `(text_id, line_n)` won't work because **168 of the 394 texts have multi-section line IDs** that restart numbering at 1 per section — using `(text_id, line_n)` as PK silently dropped Sections B/C in early dev. `ord` (1..N sequential within text) drives stable paging; `line_label` (`"1"` / `"A.5"`) is for display.
- `words` — `(text_id, line_id, word_pos)` PK. Per-word lemmatization (`form`, `lemma`, `pos`, `label`, `type`).
- `paragraphs` — translation paragraphs with `line_range` like `"1-3"` or `"B.1-B.5"`.
- FTS5 indexes: `lines_fts` on `transliteration`, `paragraphs_fts` on `translation`. Both are content-rowid-backed (NOT `WITHOUT ROWID` because FTS5 requires a real rowid to track its content).

Build details:
- TEI XML uses ~80 ETCSL-specific entity refs (`&d;` for the divine determinative, `&jic;` for `{ŋeš}`, `&damb;`/`&dame;` for half-brackets, `&suppb;`/`&suppe;` for editorial brackets, etc.). Stdlib `xml.etree` rejects undeclared entities, so `build_etcsl_db.py` regex-substitutes them on the raw XML before parsing.
- Bracket entities map to **Unicode characters** (`⸢⸣⟨⟩`), NOT ASCII (`[]<>`), because some entities appear inside XML attribute values and `<corr sic="...[en-ki]...">` would corrupt the markup.
- Transliteration is normalized from ETCSL's ASCII convention to ePSD2/Oracc Unicode in `normalize_translit()`: `j → ŋ`, `c → š`, ASCII digits in subscript context → Unicode subscripts. This means the same `lemma` value works as a key in both ETCSL words and ePSD2 entries.
- The build is idempotent: re-running drops and rebuilds the SQLite. Skips download if `data/etcsl.zip` already exists.

### Transport modes (stdio vs streamable-HTTP)

`mcp_server.py` accepts `--transport {stdio,http}` (default `stdio`). HTTP mode mounts the server's `streamable_http_app` at `/mcp/` (FastMCP's default `streamable_http_path`) on `--host` (default `127.0.0.1`) and `--port` (default `5051`, sitting one above the Flask app's `5050`). Both transports wrap the IDENTICAL set of FastMCP-decorated tool functions — there's no tool-level branching by transport. The HTTP server is uvicorn under the hood (FastMCP carries it transitively) and is production-ready as a process. By default there is **no in-app authentication** — front it with nginx/caddy/traefik for TLS + access control when binding outside `127.0.0.1`. Port-bound endpoint URLs are normalized with the trailing slash: `http://HOST:5051/mcp/` (a request to `/mcp` returns 307 to `/mcp/`).

The committed `.mcp.json` only describes the stdio launch (Claude Code spawns it as a subprocess). HTTP mode is for everyone else: Docker sidecars, web-hosted agents, multi-tenant deployments. Confirmed compatible with the `mcp` Python SDK's `streamablehttp_client` — initialize / list_tools / call_tool all work identically over HTTP and stdio.

### OAuth 2.1 / Auth0 authorization (`auth0_verifier.py`)

Optional bearer-token auth on the HTTP transport, opt-in via `EPSD2_REQUIRE_AUTH=1`. FastMCP's resource-server-only mode is the architectural fit: we implement `mcp.server.auth.provider.TokenVerifier` (single async method `verify_token(token: str) -> AccessToken | None`), pass it plus an `AuthSettings` to the FastMCP constructor, and FastMCP wires the rest:
- `BearerAuthBackend` extracts `Authorization: Bearer ...` from incoming requests
- `RequireAuthMiddleware` rejects unauthenticated requests with 401 + `WWW-Authenticate: Bearer error="invalid_token", error_description="...", resource_metadata="..."`
- RFC 9728 Protected Resource Metadata is auto-served at `/.well-known/oauth-protected-resource` listing the configured Auth0 tenant as the `authorization_servers` entry and `mcp:access` as `scopes_supported`

`auth0_verifier.py` is thin (~80 lines): uses `pyjwt[crypto]`'s `PyJWKClient` (built-in JWKS LRU cache, 10-min TTL) to fetch Auth0's signing keys; validates RS256 signature + `aud` + `iss` (with trailing slash, per Auth0 convention) + `exp`/`iat` + required scope. The sync `get_signing_key_from_jwt` call is wrapped in `asyncio.to_thread` so JWKS cache misses don't block the asyncio event loop.

Env-var contract (consulted at module load by `_build_auth_kwargs()` in `mcp_server.py`):
- `EPSD2_REQUIRE_AUTH` — `"1"` enables, anything else disables (default: disabled)
- `EPSD2_AUTH0_TENANT_URL` — `https://my-tenant.auth0.com` (no trailing slash)
- `EPSD2_AUTH0_AUDIENCE` — Auth0 API identifier, e.g. `https://epsd2.example.com`
- `EPSD2_AUTH0_RESOURCE_SERVER_URL` — public-facing URL of THIS server (used in RFC 9728 metadata; differs from `--host`/`--port` when behind a proxy)
- `EPSD2_AUTH0_REQUIRED_SCOPE` — defaults to `mcp:access`; set to empty string to allow any valid Auth0 token

Stdio transport never enforces auth (per MCP spec stdio uses env-based credentials, not OAuth). If you set `EPSD2_REQUIRE_AUTH=1` but launch with `--transport stdio`, the verifier is constructed but sits idle, and the startup banner emits a WARN making this explicit. Verified end-to-end (2026-05-10): unauthenticated POST returns 401 with the correct `WWW-Authenticate` header; the official `mcp.client.streamable_http` client gets rejected on `initialize`; `/.well-known/oauth-protected-resource` returns the right JSON. A live valid-token test requires a real Auth0 tenant.

Auth wiring uses `AnyHttpUrl` (from pydantic) for the `issuer_url` and `resource_server_url` fields per `AuthSettings` schema. `pyjwt[crypto]` is in `requirements.txt`; the `[crypto]` extra pulls in `cryptography` for RS256 signature verification. Imports are LAZY in `_build_auth_kwargs()` so the no-auth path doesn't pay the import cost and stdio dev environments without pyjwt installed don't fail to start.

### Transport security / DNS-rebinding allowlist (`_build_transport_security_kwargs`)

The MCP SDK's streamable-http transport ships `enable_dns_rebinding_protection=True` by default with an empty allowlist that effectively only accepts `Host: localhost` / `127.0.0.1` (with port wildcards) — see `mcp.server.transport_security.TransportSecuritySettings`. Behind a reverse proxy that passes the public Host header through, every request returns **`421 Misdirected Request: Invalid Host header`**. Symptom looks like a routing/Caddy bug; root cause is SDK middleware refusing the Host. Operators must opt in via three EPSD2 env vars:

- `EPSD2_ALLOWED_HOSTS` — comma-separated public hostnames the proxy will use. `localhost`, `localhost:*`, `127.0.0.1`, `127.0.0.1:*`, `::1`, `[::1]:*` are auto-added so in-container `curl --fail http://localhost:5051/...` healthchecks keep working (curl sends `Host: localhost:5051` with the port suffix — bare `localhost` doesn't match).
- `EPSD2_ALLOWED_ORIGINS` — comma-separated `Origin` headers for browser MCP clients. No auto-additions; stricter than allowed_hosts.
- `EPSD2_DISABLE_DNS_REBINDING_PROTECTION` — truthy escape hatch. Banner emits a WARNING when on. Only safe when the proxy enforces Host validation upstream.

When none of the three is set, FastMCP falls through to its own auto-default (localhost-only with port wildcards). When ANY is set, `_build_transport_security_kwargs()` constructs an explicit `TransportSecuritySettings` and we override the auto-default. Startup banner reports `transport_security=ENABLED (allowed_hosts=..., allowed_origins=...)` or `transport_security=DISABLED` so the operative state is visible. Verified end-to-end with `Host: <allowed>` → 200, `Host: <not-allowed>` → 421, with-port localhost healthcheck pattern → 200.

### Containerization (`Dockerfile` + `docker-compose.yml` + `init.sh`)

The repo ships a `python:3.12.11-slim`-based image and a **three-service** compose file:

1. **`init`** — one-shot. Runs `/app/init.sh`, exits 0 when done. Web + mcp declare `depends_on: init: condition: service_completed_successfully`, so they don't start until init exits. On a fresh host this can take 5-15 minutes (downloading 3.1 GB of zips, building a 3.4 GB glossary SQLite, etc.); on subsequent starts it fast-paths via the sentinel in ~50 ms.
2. **`web`** — gunicorn + Flask on `:5050`. Worker count via `${WEB_WORKERS:-4}`.
3. **`mcp`** — `mcp_server.py --transport http` on `:5051`.

Same image for all three services; only the `command:` differs.

`init.sh` trust model: the sentinel `/app/data/.initialized` is the SOLE source of truth for "data/ is consistent with the current code." Sentinel missing OR version-stale → `find /app/data -mindepth 1 -delete` → rebuild from scratch. corpus/ is never wiped because `download_corpus.py` is resume-safe. Steps performed (in order, each gated by env vars where optional):
1. `download_corpus.py` (skipped if `corpus/epsd2.zip` exists — proxy for "corpus directory is populated"; the script is itself resume-safe)
2. `build_text_index.py` (~2 s)
3. `build_glossary_db.py` (~3.5 min, the dominant cost)
4. `build_collocations.py` (~5 min, gated by `EPSD2_BUILD_COLLOCATIONS=1`)
5. `build_etcsl_db.py` (~10 s, gated by `EPSD2_BUILD_ETCSL=1`)
6. Pre-warm Flask sort + casefold migrations on `glossary.sqlite` so the MCP server's startup check (which reads `meta.casefold_version`) passes immediately when mcp boots in parallel with web (otherwise mcp would race gunicorn's first worker for the migration lock).

Bumping `INIT_VERSION` in init.sh forces a wipe + rebuild on the next start. Pre-built host data can be reused by manually writing `echo "init_version=2" > data/.initialized` BEFORE `docker compose up`.

Build-time gotchas already accounted for in the Dockerfile:
- `WORKDIR /app` makes the dir root-owned even after `COPY --chown` chowns the contents — gunicorn (running as `epsd2`) needs to write `/app/.gunicorn` for its control file. Fix: explicit `chown epsd2:epsd2 /app` after the COPY.
- `libyajl2` system package — `ijson`'s C backend depends on it; without it ijson silently falls back to its pure-python parser (~10x slower).
- `chmod +x /app/init.sh` after the COPY (host file perms aren't always preserved by `COPY --chown`).
- Non-root uid/gid 1000 matches the conventional first user on Linux hosts so bind mounts work without permission shuffling.

Runtime gotchas in `docker-compose.yml`:
- `data/` mount is RW for the `mcp` service even though MCP only does SELECTs — SQLite needs to create `-journal`/`-wal` files in the same directory as the DB even for read-only transactions. `:ro` mount → `sqlite3.OperationalError: unable to open database file` on first tool call.
- `init` is the dependency target for both web and mcp. Web no longer depends on mcp's casefold migration ordering (init pre-warms it); both servers start in parallel after init.
- Healthchecks use `curl --fail` against `/` (302) and `/mcp/` (307) respectively; both 3xx counts as success. `start_period: 15s` is enough — the long setup work is in the init service, not in either server.
- Ports default to `127.0.0.1:PORT:PORT` — set `WEB_BIND=0.0.0.0` / `MCP_BIND=0.0.0.0` env vars to expose to the LAN. Anything beyond a private LAN must be fronted with a TLS-terminating proxy.

### Logging

Every tool call goes through a `_log_call` decorator that emits `→ tool(args)` / `← tool (Nms) → summary` lines to BOTH stderr AND a rotating `log/mcp_server.log` (5 MB × 3 backups). The file handler is essential because Claude Code captures only client-side events in its `~/Library/Caches/claude-cli-nodejs/.../mcp-logs-epsd2/*.jsonl` — the server's stderr is otherwise discarded. Tail with `tail -F log/mcp_server.log` while chatting with the agent. Errors get full tracebacks via `log.exception`. The startup banner logs DB sizes so you can confirm the right files are loaded.

### Wiring into Claude Code / Claude Desktop

The repo ships `.mcp.json` for project-scoped auto-detection. **Both paths must be absolute** because Claude Code spawns MCP servers without sourcing the user's shell init — a bare `python3` resolves to `/usr/bin/python3` which doesn't have the `mcp` package, and the server dies before responding to `initialize` (looks like "MCP server is down"):

```json
{
  "mcpServers": {
    "epsd2": {
      "type": "stdio",
      "command": "<absolute path to a python that has the `mcp` package>",
      "args": ["<absolute path to this repo>/mcp_server.py"]
    }
  }
}
```

On the author's macOS+asdf setup that resolves to e.g. `/Users/<you>/.asdf/installs/python/3.12.11/bin/python3` and `/Users/<you>/projects/<...>/epsd2/mcp_server.py`. For a different machine, get the python path with `readlink -f $(which python3)` after confirming `python3 -c 'import mcp'` succeeds. The committed `.mcp.json` at the repo root currently hardcodes the author's paths — clone-and-go users will need to edit it to match their own machine.

## Cuneiform rendering (`cuneify.py`)

Templates use `{{ spelling | cuneify }}` to convert transliteration into Unicode cuneiform glyphs. The font stack is `'Noto Sans Cuneiform','Akkadian',serif` — most modern macOS/Linux systems already have a Cuneiform-capable font installed; the OS falls back automatically.

Tokenization handles:

- Hyphen-joined sign sequences: `lu₂-gal` → 𒇽𒃲
- Sign-list dot-compounds: `AB.GAR`
- Braced determinatives, pre and post: `{d}lugal` → 𒀭𒈗, `lugal{mušen}` → 𒈗𒄷
- Multi-word spellings split on whitespace: `gu₃ mu-un-de₂`
- Morphology tails after backslash: `peš₁₀-peš₁₀-e\l` → keeps only the part before `\`
- Compound graphemes with parens: `muₓ(|KA×GAN₂@t|)` → uses the inner `|...|` form

The OGSL lookup is built lazily via `@functools.lru_cache(maxsize=1)` on `_load_lookup()`, indexes both phonetic values (lowercase, e.g. `lugal`) and sign names (uppercase, e.g. `LUGAL`), and prefers the first sign for ambiguous values (5.5% of cases). Unknown signs render as `□` (PLACEHOLDER constant).

Coverage: 92.9% of the 124,649 forms in `glossary.sqlite` render with no `□` placeholders. Throughput is ~200K forms/sec, so cuneify is essentially free per page render.

## Attestation rendering (`text_resolver.py`)

Entry detail pages show real Sumerian transliteration with the target word highlighted, pulled live from `corpusjson/{P-id}.json` inside the right project zip via a two-stage lookup:

1. `parse_word_ref("epsd2/admin/ur3:P113959.10.3")` → `(project, text_id, line_n, word_n)`
2. `_lookup(project, text_id)` queries `text_index.sqlite` → `(zip_path, member_path)`
3. `_load_corpusjson(...)` opens the zip, parses JSON, depth-first walks the `cdl` tree
4. Collects all `l`/`d` nodes whose `ref` starts with `{text_id}.{line_n}.` → those are the words on this line, in order
5. Marks the word whose `ref == target_ref` as `is_target=True`

Caching: `_load_corpusjson` is `@lru_cache(maxsize=512)`. Corpus texts are typically small (a few KB to a few hundred KB), so 512 cached parses ≈ a few hundred MB of RAM. Page-render latency stays at ~37 ms for warm-cache hits.

`resolve_many(refs, limit=N)` deduplicates by `(project, text_id, line_n)`, so a word that appears 100x in the same line shows up once. The entry route over-fetches (500 raw refs) and lets the resolver pick up to 20 unique lines.

Failure modes (all handled silently — return `None`):

- Text not in any local zip (~8% of glossary refs cite projects we don't have)
- Empty / malformed corpusjson file (`json.JSONDecodeError`, `BadZipFile`, `KeyError`)
- Stale ref pointing at a line/word that no longer exists in the current corpus

When *all* attestations fail to resolve, the entry page falls back to showing a small sample of raw `word_ref` strings.

Known scope cutoffs (deliberate, for the MVP):

- No determinative superscripts on spellings yet (`ŋeš`, `kuš`, `na₄` etc. — they're in the JSON's form structure, just not captured by the parser).
- Composite-text refs (Q-ids) not handled by the resolver regex; only P-ids.
- No KWIC / sentence / line context-engine, no distribution profiles.
- **English translations not in JSON archive** — the Oracc public JSON open data does NOT ship English translations; they exist only in the live HTML at `/{proj}/{P-id}` (look for `class="t1 xtr"` / `class="tr"` markers). To get translations we'd have to scrape + cache. The metadata.json `formats.tr-en` list tells us *which* texts have a translation available, not the translation itself.
- Bibliography is partially surfaced: `see_examples` returns `designation` (e.g., "YOS 14, 341") per line via `text_index.sqlite`, but the web app's entry page doesn't yet render a dedicated Bibliography section.
- No Period × Form cross-tab on entry pages.
- The 7.1% of spellings whose signs are missing from OGSL render with `□` placeholders.
- The tiny page-2/3 ordering discrepancies vs Oracc.

## TLS gotcha (important for any HTTPS code)

`oracc.museum.upenn.edu` serves a valid cert from "InCommon RSA Server CA 2" but **omits the intermediate from its TLS chain**. As a result:

- `curl` works (macOS/Linux libcurl does AIA chasing)
- Python `urllib`/`requests` and Claude Code's `WebFetch` **fail** with `unable to get local issuer certificate`

`download_corpus.py` solves this by fetching the intermediate from `http://crt.sectigo.com/InCommonRSAServerCA2.crt` (URL is in the leaf cert's AIA extension), caching it as `.incommon_intermediate.pem`, and merging it into the SSL context alongside `certifi`. Reuse this pattern in any new Python that talks to Oracc — don't disable verification.

## Useful project-name conventions

Inside `corpus/`, file prefixes group related projects:

- `epsd2*` — Sumerian dictionary (the core dataset); the biggest is `epsd2-admin-ur3.zip` (Ur III administrative texts, 536 MB)
- `rinap*`, `riao`, `ribo`, `etcsri`, `armep` — royal inscriptions (Neo-Assyrian / Assyria / Babylonia / Sumerian / Achaemenid)
- `saao*`, `atae-*` — letters and archives (State Archives of Assyria; Archive of Texts of the Ancient East, sub-projected by city)
- `dcclt`, `ogsl`, `osl` — lexical lists and sign lists (the Mesopotamians' own dictionaries + the cuneiform glyph catalog)
- `amgg` — Ancient Mesopotamian Gods and Goddesses (encyclopedia)
- `ccpo`, `cmawro`, `blms`, `adsd*`, `dccmt` — commentaries, anti-witchcraft, liver omens, astronomical diaries, mathematical texts
- `aemw-amarna*`, `aemw-ugarit` — Late Bronze Age Western corpora (Amarna letters, Ugarit)
- `cdli`, `xcat`, `qcat`, `ecut`, `epsd2-catalogue` — catalogues / cross-project metadata
