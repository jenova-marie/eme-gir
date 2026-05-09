# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this repo is

A workspace for **reverse-engineering and parsing the Oracc / ePSD2 (electronic Pennsylvania Sumerian Dictionary) corpus**. Oracc is "The Open Richly Annotated Cuneiform Corpus" hosted at `https://oracc.museum.upenn.edu`. This directory holds:

- `index.html`, `js/p4.js`, `js/p4cbd.js` — frontend files scraped from the live site, used to reverse-engineer the URL/API surface (jQuery is intentionally not vendored)
- `download_corpus.py` — pulls the full set of `.zip` archives from `https://oracc.museum.upenn.edu/json/` into `corpus/`
- `build_glossary_db.py` — streams a `gloss-{lang}.json` from inside its zip into a queryable SQLite index (`glossary.sqlite` by default). Uses ijson (yajl2_c backend) for constant-memory parsing.
- `app.py` + `templates/` — Flask app that recreates Oracc's `/epsd2/sux` glossary browser locally, rendering from `glossary.sqlite`. Reuses Oracc's CSS via absolute URLs.
- `corpus/` — 208 zip files (~3.1 GB), one per Oracc project; this is the bulk dataset
- `glossary.sqlite` — 3.4 GB indexed extract of `epsd2/gloss-sux.json` (15,940 headwords, 124,649 spellings, 37,659 period rows, 1,901 compound refs, 35.5 M instance refs); sub-10 ms point lookups. Rebuild with `python3 build_glossary_db.py`.
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

# Build the glossary SQLite index (defaults: corpus/epsd2.zip → epsd2/gloss-sux.json → glossary.sqlite)
python3 build_glossary_db.py
# Build for a different language / project
python3 build_glossary_db.py --zip corpus/rinap.zip --member rinap/gloss-akk.json --db rinap_akk.sqlite

# Query the glossary
sqlite3 -header -column glossary.sqlite "SELECT cf, gw, pos, icount FROM entries WHERE cf='lugal';"

# Run the local Oracc-style glossary browser
python3 app.py                # http://127.0.0.1:5050/epsd2/sux
python3 app.py --port 8000 --debug
```

Dependencies: `ijson` (`pip install ijson`) — uses the C backend (`yajl2_c`) automatically when available. Everything else is stdlib.

There are no tests, build, or lint steps — this is a data/scripts repo.

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

Templates use **Oracc's own CSS** by linking the absolute `https://oracc.museum.upenn.edu/css/p4.css` etc. — so the look matches without us hosting any styles. If you want to detach for offline use, mirror those CSS files into `static/` and update `templates/base.html`.

Known scope cutoffs (deliberate, for the MVP):

- No determinative superscripts on spellings yet (`ŋeš`, `kuš`, `na₄` etc. — they're in the JSON's form structure, just not captured by the parser).
- No textual attestation rendering yet — entry detail shows `word_ref` strings only. Resolving them needs the `corpusjson/{P-id}.json` files inside each project's zip; walk the `cdl` tree to the matching `ref`.
- No KWIC / sentence / line context-engine, no distribution profiles, no sign info.
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
