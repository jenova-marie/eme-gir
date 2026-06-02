# Architecture & technical reference

Deep technical documentation for the eme-gir codebase. The top-level
[`CLAUDE.md`](../CLAUDE.md) carries the high-level orientation and the
policies every agent must follow; this file is the reference manual you
consult when you need to know *how* a particular subsystem works.

Contents:

1. [The reverse-engineered Oracc URL surface](#the-reverse-engineered-oracc-url-surface)
2. [Oracc JSON Open Data format (parser reference)](#oracc-json-open-data-format-parser-reference)
3. [`glossary.sqlite` schema](#glossarysqlite-schema)
4. [Local Oracc-style browser (`app.py`)](#local-oracc-style-browser-apppy)
5. [MCP servers (`mcp_server.py` + `servers/`)](#mcp-servers-mcp_serverpy--servers)
6. [ETCSL literary corpus](#etcsl-literary-corpus)
7. [Transport modes (stdio vs streamable-HTTP)](#transport-modes-stdio-vs-streamable-http)
8. [OAuth 2.1 / Auth0 authorization](#oauth-21--auth0-authorization)
9. [Transport security / DNS-rebinding allowlist](#transport-security--dns-rebinding-allowlist)
10. [Reverse-proxy headers / `X-Forwarded-Proto`](#reverse-proxy-headers--x-forwarded-proto)
11. [Umami analytics — two-property split](#umami-analytics--two-property-split)
12. [Containerization](#containerization)
13. [Logging](#logging)
14. [Cuneiform rendering](#cuneiform-rendering)
15. [Attestation rendering](#attestation-rendering)
16. [Project-name conventions](#project-name-conventions)

## The reverse-engineered Oracc URL surface

Source: `js/p4.js` and `js/p4cbd.js`. The server renders **HTML**, not JSON, on these endpoints — but the markup uses stable hooks (`class="cf"` citation form, `class="gw"` guide word/English gloss, `class="sux"` Sumerian, `class="sense"`, `class="wr"` writing, `class="summary-headword"`) and `data-oid` IDs (e.g., `o0023086`). CORS is open (`access-control-allow-origin: *`).

Modern routes (the live ones):

| Purpose | Pattern | Example |
|---|---|---|
| Glossary landing | `/{proj}/{lang}` | `/eme-gir/sux` |
| Search | `/{proj}/{lang}?q={term}` | `/eme-gir/sux?q=lugal` |
| Article (entry) | `/{proj}/{oid}` | `/eme-gir/o0023086` |
| Page navigation | `/{proj}/{lang}?page=N&zoom=A` | `/eme-gir/sux?zoom=Š&page=2` |
| Distribution profile | `/{proj}/{lang}?xis={instance}` | usage stats per period/genre |
| Sign info | `/{proj}/ogsl/brief/{id}.html` | cuneiform sign details |
| Sources / score | `/{proj}/{oid}?sources` or `?score` | textual attestations |

The legacy `/cgi-bin/oracc?...` and `/cgi-bin/oraccget?...` routes referenced in `p4cbd.js` are mostly **dead** (return 4-byte empty responses). Use the modern URL routes above for HTML scraping, or — preferred — work from the bulk JSON in `corpus/`.

## Oracc JSON Open Data format (parser reference)

Authoritative source: `https://oracc.museum.upenn.edu/doc/opendata/json/index.html`. Every Oracc JSON file is a single object with a `"type"` member (and a `"project"` member for project data).

### Zip layout

Each project zip contains a single top-level directory matching the project name (e.g., `eme-gir/…`, `rinap/…`). Standard files inside:

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

- **`superglo`** (e.g., eme-gir): primarily a glossary; the heavy file is `gloss-sux.json` (~1.9 GB for eme-gir). May lack `corpusjson/`.
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

## `glossary.sqlite` schema

Built by `build_glossary_db.py`. All `icount`/`ipct` fields are integers (cast from the JSON's stringified numbers). Indexes are deferred until after bulk insert and built at the end for ~3× faster ingest.

| Table | Rows (eme-gir sux) | Columns | Notes |
|---|---|---|---|
| `meta` | 11 | `key, value` | source path, byte count, row counts, ingested_at, sort_version |
| `entries` | 15,940 | `id PK, headword, cf, gw, pos, icount, ipct, xis, [letter, sort_key]` | one row per headword. `headword` is the full `cf[gw]POS` string. `letter`/`sort_key` are added by `app.py` on first run for Sumerian-correct alphabetical ordering (Ŋ between G and H, separators before letters, `.` after letters). Indexed on `cf`, `gw`, `pos`, `xis`, `letter`, `sort_key`. |
| `forms` | 124,649 | `id PK, entry_id, n, icount, ipct, xis` | spelling variants. `n` is the orthography (e.g. `lugal-e`). Indexed on `entry_id`, `n`, `xis`. |
| `norms` | 75,217 | `id PK, entry_id, n, icount, ipct, xis` | normalizations. Indexed on `entry_id`, `n`. |
| `senses` | 19,066 | `id PK, entry_id, n, mng, pos, icount, ipct, xis` | distinct senses for polysemous entries. `mng` is the meaning gloss. Indexed on `entry_id`, `mng`. |
| `sense_sigs` | 366,760 | `id PK, sense_id, sig, icount, ipct, xis` | full Oracc signature occurrences (`@proj%lang:form=cf[gw//sense]pos'epos$norm`). Indexed on `sense_id`, `sig`. |
| `periods` | 37,659 | `entry_id, ord, p, icount, ipct, xis, PK(entry_id, ord) WITHOUT ROWID` | per-period attestation counts (e.g., "Ur III: 9816, Old Babylonian: …"). `ord` preserves Oracc's display order. Indexed on `p`. |
| `compounds` | 1,901 | `entry_id, xcpd, eref, PK(entry_id, xcpd) WITHOUT ROWID` | "see-compounds" cross-references — e.g. *a* [ARM] → *a aŋ* [COMMAND], *a bad* [SPREAD], etc. `eref` points at the compound entry's `id`. Indexed on `eref`. |
| `morphology` | 248,176 | `cbd_id PK, entry_id, kind, n, icount, ipct, xis WITHOUT ROWID` | per-entry morphological breakdown. `kind` ∈ {`base`, `morph`, `morph2`, `stem`, `prefix`, `form-sans`}. `n` is the morpheme pattern (`~` marks the base position in `morph` patterns; `mu.na:~` = prefix chain `mu.na` + base; `~,bi.a` = base + 3sg.nonp poss + locative). For eme-gir/sux: 120K form-sans, 75K morphs, 38K bases, 15K prefixes; stem and morph2 empty. Indexed on `(entry_id, kind)`, `(kind, n)`, `xis`, and `(kind, n_cf)` for case-insensitive lookups. |
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
WHERE i.word_ref = 'eme-gir:P012345.10.3';
```

To map `word_ref` (`{project}:{P-id}.{line}.{word}`) back to the actual transliteration, look up the corresponding `corpusjson/{P-id}.json` inside the project zip and walk the `cdl` tree to the matching `ref`.

## Local Oracc-style browser (`app.py`)

Recreates `https://oracc.museum.upenn.edu/eme-gir/sux` from the local SQLite. **Page 1 OIDs match the live site exactly**; pages 2+ match closely with occasional one-off reorderings (Oracc has a sub-sort tiebreaker we haven't reverse-engineered yet — likely an entry-level sortcode field we don't capture). All of `corpus/` and the live site are governed by Oracc's CC BY-SA 3.0 license (attribution + ShareAlike).

Routes:

- `GET /` → 302 to `/eme-gir/sux`
- `GET /eme-gir/sux` — paginated glossary; query params `?page`, `?zoom={letter}`, `?q={search}`
- `GET /eme-gir/<oid>` — entry detail page

Sumerian alphabetical sorting is implemented in `sort_key()` in `app.py`. Bumping `SORT_VERSION` triggers a one-shot re-population of the `letter` and `sort_key` columns on the next startup. Search-helper substitutions (`j→ŋ`, `sz→š`, `s,→ṣ`, `t,→ṭ`, digits → subscripts, `'→ʾ`) are applied to the `?q=` param in `normalize_query()`.

`app.py` also owns the casefold migration (`ensure_casefold_columns()`, gated on `CASEFOLD_VERSION`): adds `_cf` mirror columns to `entries.cf`, `entries.gw`, `senses.mng`, `forms.n`, `norms.n`, `compounds.xcpd`, and `morphology.n` for fast Unicode-aware case-insensitive search, plus an `idx_morphology_kind_n_cf` index that the MCP server's `analyze_form` and `translate_sumerian` rely on. Bumping `CASEFOLD_VERSION` re-runs the migration. Both migrations are idempotent and run on `python3 app.py` startup; the MCP server checks for `casefold_version` in `meta` and bails with a hint if absent.

Templates use **Oracc's own CSS** by linking the absolute `https://oracc.museum.upenn.edu/css/p4.css` etc. — so the look matches without us hosting any styles. If you want to detach for offline use, mirror those CSS files into `static/` and update `templates/base.html`.

## MCP servers (`mcp_server.py` + `servers/`)

Exposes the corpus to LLM agents via the Model Context Protocol. Built with the `mcp` Python SDK's `FastMCP`.

**Six MCP servers in total** post-Phase-5:

| Server | Entry point | Tools | Default HTTP port | Required data |
|---|---|---:|---:|---|
| `eme-gir` (legacy all-in-one) | `python3 mcp_server.py` | 21 | 5051 | all of glossary, text_index, etcsl, cdli, ogsl |
| `eme-gir-epsd2` | `python -m servers.epsd2` | 11 | 5052 | `data/glossary.sqlite` + `data/text_index.sqlite` |
| `eme-gir-etcsl` | `python -m servers.etcsl` | 4 | 5053 | `data/etcsl.sqlite` |
| `eme-gir-cdli` | `python -m servers.cdli` | 2 | 5054 | `data/cdli.sqlite` |
| `eme-gir-ogsl` | `python -m servers.ogsl` | 2 | 5055 | `corpus/ogsl.zip` |
| `eme-gir-translator` | `python -m servers.translator` | 2 + 2 resources | 5056 | none — markdown only |

The five per-domain servers share the `eme_gir/` package (paths, log, cuneify, text_resolver, cdli, sumerian_morphology, auth0_verifier, umami_analytics) + the `eme_gir/models/{domain}.py` Pydantic response models + the `eme_gir/tools/{domain}.py` tool implementations. Each `servers/<domain>/__main__.py` is a thin (~30-40 line) wrapper that imports tools, calls `eme_gir.server.make_server(name, instructions)` (which applies Auth0 + transport-security from env vars), registers the domain's tools via `mcp.tool(annotations=READ_ONLY_ANNOTATIONS)(fn)`, and calls `eme_gir.server.run_server(mcp, log, default_port, required_dbs=...)` which handles argparse + startup banner + transport selection.

The Translator server is special: **no data tools**. It exposes only the bootstrap resources (`oracc://prompt/agent`, `oracc://grammar/sumerian`) and the two tool wrappers around them (`start_here`, `get_grammar_reference`). An agent that connects to Translator + the four data servers gets opinionated workflow guidance; an agent that connects to just the four data servers (skipping Translator) is expected to discover the workflow on its own — the architectural pivot that motivated the per-domain split in the first place.

**Tool bias preserved across all servers**: every tool that returns lemma candidates returns BOTH `sense_count` (raw frequency of *this sense*) and `sense_pct` (what % of the entry's total uses are this sense), so the agent can rank "the word for X" above "X is a fringe meaning of this word".

Tools:

| Tool | Purpose |
|---|---|
| `translate_english(query, limit, offset)` | Rank Sumerian candidates for an English word. Hits both entry guide-words and per-sense meanings. Sorted by `sense.icount DESC`. Paginated. |
| `translate_sumerian(transliteration, limit_per_token)` | Reverse-direction lookup: parse a Sumerian phrase into per-token English glosses. Whole-token-first: splits the input only on whitespace, then tries the whole hyphenated word; only falls back to hyphen-splitting when the whole-token lookup yields zero candidates. Each token also carries detected case/possessive/plural suffix chain when present. `match_kind` field signals `"whole"` / `"split_fallback"` / `"unmatched"`. |
| `parse_phrase(transliteration)` | Case-aware grammatical pre-annotation. Classifies each token's phrase role via the morphology (`subject_ergative`, `oblique_dative`, …), returns a compact bracket skeleton (`[NP lugal-ERG] [NP e-ABS] [V du (mu-na-)]`), emits heuristic notes (transitive-clause detection, ambiguous-suffix warnings for `-e`/`-a`/`-bi`). Not a true syntactic parser — it surfaces grammatical role markers explicitly encoded in the morphology and lets the agent build the final parse. Verb-form detection uses the prefix chain (mu-, ba-, bi₂-, …) and skips nominal suffix-peeling when triggered. |
| `lookup_entry(oid)` | Full structured view: senses, top spellings (with cuneiform glyphs), periods, compounds. |
| `see_examples(oid, limit, period)` | Real attested lines via `text_resolver`, target word marked. Supports period filter (substring, case-insensitive — "babylonian" matches Old AND Middle Babylonian) — pre-fetches matching text IDs from `text_index.sqlite` to avoid resolving irrelevant texts. |
| `find_compound(english_phrase, limit)` | Find idiomatic Sumerian compound expressions for an English phrase. |
| `find_collocations(word, length, limit, offset)` | Multi-word phrasal idioms attested with a given lemma. Reads `collocations.sqlite`. The index is keyed by **citation form (cf)**, NOT by spelling — but the tool auto-resolves common misses: if `word='e₂'` (a spelling) returns zero, it looks up `e₂` in `forms.n_cf`/`morphology.n_cf`, picks the most-attested matching cf (`e`), and retries. Result includes `resolved_from` when this happened. Paginated. |
| `find_phrase_pattern(pattern, limit, offset)` | Structural-template query over the corpus collocation index. Each slot: `TARGET ('[' gw ']')? (':' case)?` where TARGET ∈ {literal cf, POS code, POS family glob `V*`, or `*`}. Both `gw` and `case` accept `!`-prefix for negation. Routing: prefers `data/inflected_collocations.sqlite` (case+sense aware) when available; falls back to `data/collocations.sqlite` for v1 patterns; returns ErrorResponse with a build hint when v2/v3 syntax is used and the inflected DB is missing. Paginated. |
| `get_inflections(oid, min_count=2, limit_per_kind=25)` | Show attested morphological breakdowns. Defaults filter the long tail of count<2 noise and cap each kind bucket at 25 to keep results scannable. Pass `min_count=0, limit_per_kind=0` for the full firehose. Result includes `truncated` dict telling the caller when more data exists. |
| `analyze_form(spelling, limit, offset)` | Decompose a Sumerian spelling into candidate lemmas + their morphological role. Indexed lookup against `forms.n_cf` + `morphology.n_cf` (kind in base/form-sans/morph). Paginated. |
| `find_verb_form(cf, pos, prefix=…, dimensional=[…], object_person=…, polarity=…, aspect=…, suffix_a=…, reduplicated=…, with_example=True)` | Attestation-first verb-form retrieval. Translates a grammatical-feature spec into a slot-aware filter over `morphology` rows for the given `(cf, pos)` entry, ranks by `icount`, and (by default) returns one cited line per match via `text_resolver`. Aspect is a SUFFIX HEURISTIC; verbs with stem alternation (e.g. ŋen/du-du for "go") are stored as separate entries and must be queried by cf separately. |
| `lookup_sign(query)` | Look up a cuneiform sign by name ("LUGAL") or phonetic value ("lugal"). Returns the Unicode glyph, sign name, all phonetic readings. |
| `cuneify(spelling)` | Render Oracc transliteration as Unicode cuneiform glyphs. |
| `etcsl_search_english(query, limit, offset)` | FTS5 over ETCSL English translations. Each hit returns the English paragraph PLUS the Sumerian lines it covers. Bilingual. Paginated. |
| `etcsl_lines_with_lemma(lemma, limit, offset)` | Find literary lines containing a given Sumerian lemma (cf), each with the English translation paragraph that line belongs to. Joins on `(text_id, line_id)`. Paginated. |
| `etcsl_search_sumerian(query, limit, offset)` | FTS5 over Sumerian transliteration in ETCSL. Returns each match with its English paragraph. Hyphens are token separators (`unicode61`); quote multi-token spellings (`'lugal-bi'`). Paginated. |
| `etcsl_lookup_text(text_id, start, line_limit)` | Read a whole composition. `start` is a 1-based `ord` (NOT a line label — multi-section texts like `c.2.4.2.16` would otherwise have ambiguous line numbers). Result includes `next_start` for paging through long works. Lines are grouped into bilingual blocks by paragraph. |
| `lookup_artifact(p_id)` | One P-id → full CDLI catalogue record (provenience, period, museum, dimensions, image URLs). |
| `find_artifacts(provenience=…, period=…, museum_collection=…, genre=…, language=…, subgenre=…, limit, offset)` | Filtered query over the 353K-row CDLI catalogue. All filters substring-matched, ANDed. Paginated. |
| `start_here()` | Returns the per-server bootstrap doc from `prompt/*_PROMPT.md`. Docstring leads with "⭐ CALL THIS FIRST" so a tools-list scan naturally surfaces it as the entry point on first connection. |
| `get_grammar_reference()` | Returns the dual Jagersma + Meadow Sumerian grammar reference (~80 KB combined). Ummia server only. |

Sanity-checks `glossary.sqlite` and `text_index.sqlite` exist on startup; bails with a hint if not. Also requires the `app.py` casefold migration to have run (checks `meta.casefold_version`). Run order from cold: `download_corpus.py` → `build_text_index.py` → `build_glossary_db.py` → `build_collocations.py` (optional, only needed for `find_collocations` tool) → `build_etcsl_db.py` (optional, only needed for the four `etcsl_*` tools) → `python3 app.py` (once, to populate casefold + sort columns) → `python3 mcp_server.py`.

The `find_collocations` tool degrades gracefully (returns an error structure) if `collocations.sqlite` is absent. The four `etcsl_*` tools raise `FileNotFoundError` if `etcsl.sqlite` is absent (caught and returned to the agent as an error result). All other tools work without either optional DB.

## ETCSL literary corpus

ETCSL (the Oxford [Electronic Text Corpus of Sumerian Literature](https://etcsl.orinst.ox.ac.uk/), Black et al. 1998–2006, **traditional academic copyright with citation request — NOT a Creative Commons license**; see [`LICENSE-DATA.md`](../LICENSE-DATA.md)) is a curated set of 394 Sumerian literary texts (hymns, myths, royal hymns, proverbs, wisdom, the King List, Inana's Descent, Gilgameš, Šulgi praise poems) shipped as TEI XML with **per-word lemmatization AND English translations**. This fills the bilingual gap in the Oracc bulk JSON. Every `etcsl_*` tool result includes an `attribution` field — preserve it when quoting.

Schema design (`data/etcsl.sqlite`):

- `texts` — one row per composition: `text_id`, `title`, `has_translation`.
- `lines` — `(text_id, line_id)` is the unique key; `line_id` is globally unique within a text (e.g. `c141.1` or `c24216.B.5`). Flat `(text_id, line_n)` won't work because **168 of the 394 texts have multi-section line IDs** that restart numbering at 1 per section. `ord` (1..N sequential within text) drives stable paging; `line_label` (`"1"` / `"A.5"`) is for display.
- `words` — `(text_id, line_id, word_pos)` PK. Per-word lemmatization (`form`, `lemma`, `pos`, `label`, `type`).
- `paragraphs` — translation paragraphs with `line_range` like `"1-3"` or `"B.1-B.5"`.
- FTS5 indexes: `lines_fts` on `transliteration`, `paragraphs_fts` on `translation`. Both are content-rowid-backed.

Build details:

- TEI XML uses ~80 ETCSL-specific entity refs (`&d;` for the divine determinative, `&jic;` for `{ŋeš}`, `&damb;`/`&dame;` for half-brackets, etc.). Stdlib `xml.etree` rejects undeclared entities, so `build_etcsl_db.py` regex-substitutes them on the raw XML before parsing.
- Bracket entities map to **Unicode characters** (`⸢⸣⟨⟩`), NOT ASCII (`[]<>`), because some entities appear inside XML attribute values.
- Transliteration is normalized from ETCSL's ASCII convention to Eme-gir/Oracc Unicode in `normalize_translit()`: `j → ŋ`, `c → š`, ASCII digits in subscript context → Unicode subscripts.
- The build is idempotent: re-running drops and rebuilds the SQLite. Skips download if `data/etcsl.zip` already exists.

## Transport modes (stdio vs streamable-HTTP)

`mcp_server.py` accepts `--transport {stdio,http}` (default `stdio`). HTTP mode mounts the server's `streamable_http_app` at `/mcp/` (FastMCP's default `streamable_http_path`) on `--host` (default `127.0.0.1`) and `--port` (default `5051`). Both transports wrap the IDENTICAL set of FastMCP-decorated tool functions — there's no tool-level branching by transport. The HTTP server is uvicorn under the hood (FastMCP carries it transitively) and is production-ready as a process. By default there is **no in-app authentication** — front it with nginx/caddy/traefik for TLS + access control when binding outside `127.0.0.1`. Port-bound endpoint URLs are normalized with the trailing slash: `http://HOST:5051/mcp/` (a request to `/mcp` returns 307 to `/mcp/`).

The committed `.mcp.json` only describes the stdio launch (Claude Code spawns it as a subprocess). HTTP mode is for everyone else: Docker sidecars, web-hosted agents, multi-tenant deployments. Confirmed compatible with the `mcp` Python SDK's `streamablehttp_client` — initialize / list_tools / call_tool all work identically over HTTP and stdio.

## OAuth 2.1 / Auth0 authorization

`eme_gir/auth0_verifier.py`. Optional bearer-token auth on the HTTP transport, opt-in via `EME_GIR_REQUIRE_AUTH=1`. FastMCP's resource-server-only mode is the architectural fit: we implement `mcp.server.auth.provider.TokenVerifier` (single async method `verify_token(token: str) -> AccessToken | None`), pass it plus an `AuthSettings` to the FastMCP constructor, and FastMCP wires the rest:

- `BearerAuthBackend` extracts `Authorization: Bearer ...` from incoming requests
- `RequireAuthMiddleware` rejects unauthenticated requests with 401 + `WWW-Authenticate: Bearer error="invalid_token", error_description="...", resource_metadata="..."`
- RFC 9728 Protected Resource Metadata is auto-served at `/.well-known/oauth-protected-resource` listing the configured Auth0 tenant as the `authorization_servers` entry and `mcp:access` as `scopes_supported`

`eme_gir/auth0_verifier.py` is thin (~80 lines): uses `pyjwt[crypto]`'s `PyJWKClient` (built-in JWKS LRU cache, 10-min TTL) to fetch Auth0's signing keys; validates RS256 signature + `aud` + `iss` (with trailing slash, per Auth0 convention) + `exp`/`iat` + required scope. The sync `get_signing_key_from_jwt` call is wrapped in `asyncio.to_thread` so JWKS cache misses don't block the asyncio event loop.

Env-var contract (consulted at module load by `_build_auth_kwargs()` in `eme_gir/server.py`):

- `EME_GIR_REQUIRE_AUTH` — `"1"` enables, anything else disables (default: disabled)
- `EME_GIR_AUTH0_TENANT_URL` — `https://my-tenant.auth0.com` (no trailing slash)
- `EME_GIR_AUTH0_AUDIENCE` — Auth0 API identifier, e.g. `https://eme-gir.example.com`
- `EME_GIR_AUTH0_RESOURCE_SERVER_URL` — public-facing URL of THIS server (used in RFC 9728 metadata; differs from `--host`/`--port` when behind a proxy)
- `EME_GIR_AUTH0_REQUIRED_SCOPE` — defaults to `mcp:access`; set to empty string to allow any valid Auth0 token

Stdio transport never enforces auth (per MCP spec stdio uses env-based credentials, not OAuth). If you set `EME_GIR_REQUIRE_AUTH=1` but launch with `--transport stdio`, the verifier is constructed but sits idle, and the startup banner emits a WARN making this explicit.

Auth wiring uses `AnyHttpUrl` (from pydantic) for the `issuer_url` and `resource_server_url` fields per `AuthSettings` schema. `pyjwt[crypto]` is in `requirements.txt`; the `[crypto]` extra pulls in `cryptography` for RS256 signature verification. Imports are LAZY in `_build_auth_kwargs()` so the no-auth path doesn't pay the import cost.

## Transport security / DNS-rebinding allowlist

`eme_gir.server._build_transport_security_kwargs`. The MCP SDK's streamable-http transport ships `enable_dns_rebinding_protection=True` by default with an empty allowlist that effectively only accepts `Host: localhost` / `127.0.0.1` (with port wildcards). Behind a reverse proxy that passes the public Host header through, every request returns **`421 Misdirected Request: Invalid Host header`**. Symptom looks like a routing/Caddy bug; root cause is SDK middleware refusing the Host. Operators must opt in via three env vars:

- `EME_GIR_ALLOWED_HOSTS` — comma-separated public hostnames the proxy will use. `localhost`, `localhost:*`, `127.0.0.1`, `127.0.0.1:*`, `::1`, `[::1]:*` are auto-added so in-container `curl --fail http://localhost:5051/...` healthchecks keep working.
- `EME_GIR_ALLOWED_ORIGINS` — comma-separated `Origin` headers for browser MCP clients. No auto-additions; stricter than allowed_hosts.
- `EME_GIR_DISABLE_DNS_REBINDING_PROTECTION` — truthy escape hatch. Banner emits a WARNING when on. Only safe when the proxy enforces Host validation upstream.

When none of the three is set, FastMCP falls through to its own auto-default (localhost-only with port wildcards). When ANY is set, `_build_transport_security_kwargs()` constructs an explicit `TransportSecuritySettings` and we override the auto-default. Startup banner reports `transport_security=ENABLED (allowed_hosts=..., allowed_origins=...)` or `transport_security=DISABLED` so the operative state is visible.

## Reverse-proxy headers / `X-Forwarded-Proto`

`eme_gir.server._trust_proxy_enabled` + `_run_uvicorn_with_proxy_headers`. A second sibling-bug of the DNS-rebinding gotcha: when an HTTPS-terminating proxy (Caddy/nginx) forwards plain HTTP to the upstream, Starlette generates `/mcp/` → `/mcp` redirects with the **scheme it sees on the wire** (plain `http://`), not the scheme the external client used (`https://`). uvicorn 0.38 defaults `proxy_headers=True` but `forwarded_allow_ips=None`, which collapses to `"127.0.0.1"` only — Caddy proxying from the Docker bridge IP (or any non-127.0.0.1 source) gets ignored, so `X-Forwarded-Proto: https` is silently dropped. Not blocking — clients that hit `/mcp` (no trailing slash) work fine — but it bites any client that follows redirects or normalizes onto the trailing-slash form.

Operator opt-in:

- `EME_GIR_TRUST_PROXY` — truthy → run uvicorn ourselves (via `mcp.streamable_http_app()`) with `proxy_headers=True, forwarded_allow_ips="*"` so the upstream honors `X-Forwarded-Proto` / `X-Forwarded-For` regardless of source IP. Default off; flip to `1` in the host `.env` for Caddy-fronted production deploys. Only safe when the reverse proxy itself sets the `X-Forwarded-*` headers (Caddy does so by default).

When OFF (default), the HTTP launch path is the unchanged `mcp.run(transport="streamable-http")` call — FastMCP's hardcoded uvicorn config applies, so behavior is bit-identical to pre-fix. When ON, `_run_uvicorn_with_proxy_headers()` mirrors what `FastMCP.run_streamable_http_async()` does (same host/port/log_level pulled from `mcp.settings`) but adds the two proxy-trust knobs uvicorn won't expose otherwise. Startup banner reports `trust_proxy=ENABLED (forwarded_allow_ips=*)` or `trust_proxy=disabled`. Verify by curling `/mcp/` with `X-Forwarded-Proto: https` and a public `Host:` header — the 307's `Location:` should preserve `https://`.

## Umami analytics — two-property split

The project tracks two distinct surfaces in Umami: **MCP server tool calls** (server-side, Python) and **website clicks/pageviews** (browser-side, embedded in templates). These are SEPARATE Umami properties with SEPARATE website-ID UUIDs so the dashboards stay clean — agent telemetry on one chart, visitor behavior on another.

Env-var contract:

| Var | Purpose | Where it's read |
|---|---|---|
| `EME_GIR_UMAMI_URL` | base URL of the self-hosted Umami instance, e.g. `https://umami.recoverysky.app` | both surfaces (shared) |
| `EME_GIR_UMAMI_MCP_ID` | UUID of the MCP property | `umami_analytics.init_from_env()` in MCP servers |
| `EME_GIR_UMAMI_WEBSITE_ID` | UUID of the website property | `app.py` + `www_app.py` → injected into templates as `UMAMI_WEBSITE_ID` Jinja var |
| `EME_GIR_UMAMI_API_KEY` | optional API key (most self-hosted Umami instances don't need one) | MCP-side only (browser-side embeds use the public `/script.js` endpoint) |
| `EME_GIR_UMAMI_HOSTNAME` | per-service identifier (`eme-gir-epsd2`, `eme-gir-www`, etc.) reported with each MCP event | overridden per-service in `docker-compose.yml` |

Server-side (MCP): `eme_gir/log.py:log_call` decorates every tool function and emits one Umami event per call with `name=tool_function_name, data={duration_ms, outcome, arg_keys, result_count, error_kind?}`. **The privacy boundary is deliberate**: tool names, arg-key names, latency, and result counts go to Umami; tool ARGUMENT VALUES, query strings, result content, IPs, session IDs, and Auth0 client identifiers do NOT. A user's `translate_english("homophobia")` query must NEVER show up in the analytics dashboard — only the fact that `translate_english` was called once with one arg key.

Browser-side (Web/WWW): `app.py:create_app()` and `www_app.py:create_app()` read `EME_GIR_UMAMI_URL` + `EME_GIR_UMAMI_WEBSITE_ID` and expose them as Jinja template variables. `templates/base.html` (ePSD2 verification browser) and `templates/www.html` (landing page) each gate a `<script defer src="$URL/script.js" data-website-id="$WEBSITE_ID">` tag on both variables being non-empty. Click events ride along via `data-umami-event="..."` and `data-umami-event-*="..."` attributes on `<a>` and `<button>` elements.

Backwards-compat: if `EME_GIR_UMAMI_MCP_ID` is unset but `EME_GIR_UMAMI_WEBSITE_ID` is set, the MCP-side `init_from_env()` falls back to the website ID and logs a deprecation warning. This keeps single-property pre-split deployments working until the operator migrates.

Disabling: leave any of `EME_GIR_UMAMI_URL`, `EME_GIR_UMAMI_MCP_ID`, or `EME_GIR_UMAMI_WEBSITE_ID` unset and that surface stays silent — MCP server logs "analytics=disabled"; the browser templates emit no `<script>` tag.

## Containerization

`Dockerfile` + `docker-compose.yml` + `init.sh`. The repo ships a `python:3.12.11-slim`-based image and an eight-service compose stack:

1. **`init`** — one-shot. Runs `/app/init.sh`, exits 0 when done. Web + mcp declare `depends_on: init: condition: service_completed_successfully`, so they don't start until init exits. On a fresh host this can take 5-15 minutes (downloading 3.1 GB of zips, building a 3.4 GB glossary SQLite, etc.); on subsequent starts it fast-paths via the sentinel in ~50 ms.
2. **`web`** — gunicorn + Flask on `:5050`. Worker count via `${WEB_WORKERS:-4}`.
3. **`www`** — gunicorn + Flask landing page on `:5057`.
4. **`mcp`** (legacy all-in-one) + four per-domain MCP services + Ummia. All share the same image; only `command:` differs.

`init.sh` trust model: the sentinel `/app/data/.initialized` is the SOLE source of truth for "data/ is consistent with the current code." Sentinel missing OR version-stale → `find /app/data -mindepth 1 -delete` → rebuild from scratch. corpus/ is never wiped because `download_corpus.py` is resume-safe. Steps performed (in order, each gated by env vars where optional):

1. `download_corpus.py` (skipped if `corpus/eme-gir.zip` exists — proxy for "corpus directory is populated"; the script is itself resume-safe)
2. `build_text_index.py` (~2 s)
3. `build_glossary_db.py` (~3.5 min, the dominant cost)
4. `build_collocations.py` (~5 min, gated by `EME_GIR_BUILD_COLLOCATIONS=1`)
5. `build_etcsl_db.py` (~10 s, gated by `EME_GIR_BUILD_ETCSL=1`)
6. `build_cdli_db.py` (~30 s, gated by `EME_GIR_BUILD_CDLI=1`)
7. Pre-warm Flask sort + casefold migrations on `glossary.sqlite` so the MCP server's startup check (which reads `meta.casefold_version`) passes immediately when mcp boots in parallel with web.

Bumping `INIT_VERSION` in init.sh forces a wipe + rebuild on the next start. Pre-built host data can be reused by manually writing `echo "init_version=N" > data/.initialized` BEFORE `docker compose up`.

Build-time gotchas already accounted for in the Dockerfile:

- `WORKDIR /app` makes the dir root-owned even after `COPY --chown` chowns the contents — gunicorn (running as `eme-gir`) needs to write `/app/.gunicorn` for its control file. Fix: explicit `chown eme-gir:eme-gir /app` after the COPY.
- `libyajl2` system package — `ijson`'s C backend depends on it; without it ijson silently falls back to its pure-python parser (~10x slower).
- `chmod +x /app/init.sh` after the COPY (host file perms aren't always preserved by `COPY --chown`).
- Non-root uid/gid 1000 matches the conventional first user on Linux hosts so bind mounts work without permission shuffling.

Runtime gotchas in `docker-compose.yml`:

- `data/` mount is RW for the `mcp` service even though MCP only does SELECTs — SQLite needs to create `-journal`/`-wal` files in the same directory as the DB even for read-only transactions. `:ro` mount → `sqlite3.OperationalError: unable to open database file` on first tool call.
- `init` is the dependency target for both web and mcp. Web no longer depends on mcp's casefold migration ordering (init pre-warms it); both servers start in parallel after init.
- Healthchecks use `curl --fail` against `/` (302) and `/mcp/` (307) respectively; both 3xx counts as success. `start_period: 15s` is enough — the long setup work is in the init service, not in either server.
- Ports default to `127.0.0.1:PORT:PORT` — set `WEB_BIND=0.0.0.0` / `MCP_BIND=0.0.0.0` env vars to expose to the LAN. Anything beyond a private LAN must be fronted with a TLS-terminating proxy.

## Logging

Every tool call goes through the `log_call` decorator (in `eme_gir/log.py`) that emits `→ tool(args)` / `← tool (Nms) → summary` lines to BOTH stderr AND a rotating per-server log file in `log/` (5 MB × 3 backups). The file handler is essential because Claude Code captures only client-side events in its `~/Library/Caches/claude-cli-nodejs/.../mcp-logs-eme-gir/*.jsonl` — the server's stderr is otherwise discarded. Tail with `tail -F log/eme-gir-*.log` while chatting with the agent. Errors get full tracebacks via `log.exception`. The startup banner logs DB sizes so you can confirm the right files are loaded.

## Cuneiform rendering

`eme_gir/cuneify.py`. Templates use `{{ spelling | cuneify }}` to convert transliteration into Unicode cuneiform glyphs. The font stack is `'Noto Sans Cuneiform','Akkadian',serif` — most modern macOS/Linux systems already have a Cuneiform-capable font installed; the OS falls back automatically.

Tokenization handles:

- Hyphen-joined sign sequences: `lu₂-gal` → 𒇽𒃲
- Sign-list dot-compounds: `AB.GAR`
- Braced determinatives, pre and post: `{d}lugal` → 𒀭𒈗, `lugal{mušen}` → 𒈗𒄷
- Multi-word spellings split on whitespace: `gu₃ mu-un-de₂`
- Morphology tails after backslash: `peš₁₀-peš₁₀-e\l` → keeps only the part before `\`
- Compound graphemes with parens: `muₓ(|KA×GAN₂@t|)` → uses the inner `|...|` form

The OGSL lookup is built lazily via `@functools.lru_cache(maxsize=1)` on `_load_lookup()`, indexes both phonetic values (lowercase, e.g. `lugal`) and sign names (uppercase, e.g. `LUGAL`), and prefers the first sign for ambiguous values (5.5% of cases). Unknown signs render as `□` (PLACEHOLDER constant).

Coverage: 92.9% of the 124,649 forms in `glossary.sqlite` render with no `□` placeholders. Throughput is ~200K forms/sec, so cuneify is essentially free per page render.

## Attestation rendering

`eme_gir/text_resolver.py`. Entry detail pages show real Sumerian transliteration with the target word highlighted, pulled live from `corpusjson/{P-id}.json` inside the right project zip via a two-stage lookup:

1. `parse_word_ref("eme-gir/admin/ur3:P113959.10.3")` → `(project, text_id, line_n, word_n)`
2. `_lookup(project, text_id)` queries `text_index.sqlite` → `(zip_path, member_path)`
3. `_load_corpusjson(...)` opens the zip, parses JSON, depth-first walks the `cdl` tree
4. Collects all `l`/`d` nodes whose `ref` starts with `{text_id}.{line_n}.` → those are the words on this line, in order
5. Marks the word whose `ref == target_ref` as `is_target=True`

Caching: `_load_corpusjson` is `@lru_cache(maxsize=16)` (bounded tight because Ur III administrative outliers can be tens of MB raw → hundreds of MB resident in Python objects, and maxsize=512 was OOM-killing gunicorn workers). Page-render latency stays at ~37 ms for warm-cache hits.

`resolve_many(refs, limit=N)` deduplicates by `(project, text_id, line_n)`, so a word that appears 100x in the same line shows up once. The entry route over-fetches (150 raw refs) and lets the resolver pick up to 20 unique lines.

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

## Project-name conventions

Inside `corpus/`, file prefixes group related projects:

- `eme-gir*` — Sumerian dictionary (the core dataset); the biggest is `eme-gir-admin-ur3.zip` (Ur III administrative texts, 536 MB)
- `rinap*`, `riao`, `ribo`, `etcsri`, `armep` — royal inscriptions (Neo-Assyrian / Assyria / Babylonia / Sumerian / Achaemenid)
- `saao*`, `atae-*` — letters and archives (State Archives of Assyria; Archive of Texts of the Ancient East, sub-projected by city)
- `dcclt`, `ogsl`, `osl` — lexical lists and sign lists (the Mesopotamians' own dictionaries + the cuneiform glyph catalog)
- `amgg` — Ancient Mesopotamian Gods and Goddesses (encyclopedia)
- `ccpo`, `cmawro`, `blms`, `adsd*`, `dccmt` — commentaries, anti-witchcraft, liver omens, astronomical diaries, mathematical texts
- `aemw-amarna*`, `aemw-ugarit` — Late Bronze Age Western corpora (Amarna letters, Ugarit)
- `cdli`, `xcat`, `qcat`, `ecut`, `eme-gir-catalogue` — catalogues / cross-project metadata
