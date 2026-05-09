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
pip install ijson flask mcp

# 2. Download the entire Oracc JSON corpus (~3.1 GB, ~2 minutes on a fast link)
python3 download_corpus.py

# 3. Build the per-text location index (~2 seconds)
python3 build_text_index.py

# 4. Build the Sumerian glossary index (~3.5 minutes)
python3 build_glossary_db.py

# 5. (Optional) Build the collocations index for find_collocations MCP tool (~5 min)
python3 build_collocations.py

# 6. Run the web app (also populates two one-shot SQLite migrations on first hit)
python3 app.py
# -> http://127.0.0.1:5050/epsd2/sux
```

All generated SQLite indexes land in `data/`; logs land in `log/`. Both directories are auto-created on first run.

To rebuild the glossary for a different language / project (e.g. the Akkadian
glossary, useful for bilingual workflows):

```bash
python3 build_glossary_db.py --zip corpus/rinap.zip --member rinap/gloss-akk.json --db data/glossary_akk.sqlite
```

## Use as an MCP server (English → Sumerian translation tools for an LLM)

The repo ships an MCP server exposing ten tools designed for agent-driven English↔Sumerian translation, plus a project-scoped `.mcp.json` so **Claude Code auto-detects the server** when launched in this directory — no manual client config needed.

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

Ten tools available to the agent:

- `translate_english(query, limit)` — rank Sumerian candidates for an English meaning
- `translate_sumerian(transliteration)` — reverse: parse a Sumerian phrase into per-token glosses
- `lookup_entry(oid)` — full structured view of a chosen lemma
- `see_examples(oid, limit, period)` — real attested lines, target word marked, period-filterable
- `find_compound(english_phrase)` — find idiomatic Sumerian compound expressions
- `find_collocations(word, length, limit)` — phrasal idioms attested with a given lemma (mined from the corpus, not the dictionary — surfaces formulas like "Šusuen lugal", year-name templates, royal titles)
- `get_inflections(oid)` — every attested morphological breakdown of a lemma
- `analyze_form(spelling)` — decompose an attested spelling into candidate lemmas + morphology
- `lookup_sign(query)` — find a cuneiform sign by name or phonetic value
- `cuneify(spelling)` — render Oracc transliteration as Unicode cuneiform glyphs

Plus one MCP resource: `oracc://grammar/sumerian` — a ~14 KB Sumerian grammar cheat sheet (Edzard 2003) the agent should fetch once per translation session.

Every result returned by `translate_english` includes both raw sense frequency *and* what % of the lemma's uses are in that sense — so the agent can pick "the word for X" rather than "a word that occasionally means X".

For a complete agent system prompt that teaches the recommended translation workflow (decompose English → rank candidates → check compounds and collocations → choose aspect → apply cases → verify with attestations → render cuneiform), see [`prompt/AGENT_PROMPT.md`](prompt/AGENT_PROMPT.md). It's a drop-in for the system message of any agent connected to this server.

### Watching the server live

Every tool call is logged to `log/mcp_server.log` (rotating, 5 MB × 3 backups), with arguments, duration, and a one-line result summary. Tail it while chatting with the agent:

```bash
tail -F log/mcp_server.log
```

Errors get full tracebacks. The startup banner reports loaded DB sizes so you can confirm the right files are mounted.

---

## What lives where

| | |
|---|---|
| **Code** | |
| `download_corpus.py` | Stdlib-only batch downloader; resume-safe; auto-fetches the InCommon TLS intermediate that Oracc's server omits. |
| `build_glossary_db.py` | ijson-streaming parser. Builds `glossary.sqlite` with normalized tables for entries, forms, norms, senses, signature occurrences, periods, compounds, morphology, and instances. |
| `build_text_index.py` | Scans every `corpus/*.zip` for `corpusjson/P*.json` and per-text catalogue metadata, builds `text_index.sqlite`. |
| `build_collocations.py` | Mines 2/3/4-gram phrasal collocations from every corpusjson text → `collocations.sqlite`. |
| `text_resolver.py` | Lazy lookup + LRU cache that turns a glossary `word_ref` (e.g. `epsd2/admin/ur3:P113959.10.3`) into the actual Sumerian line, with the target word marked. |
| `cuneify.py` | OGSL-backed transliteration → Unicode cuneiform converter. Loaded on first use; exposed as a Jinja filter to the web app and as the `cuneify` MCP tool. |
| `app.py` + `templates/` | Flask app. Routes: `/epsd2/sux` (paginated glossary with letter zoom + search), `/epsd2/<oid>` (entry detail). Also runs the one-shot `_cf` casefold + Sumerian-sort migrations on first startup. |
| `mcp_server.py` | MCP server (`mcp` SDK / FastMCP) exposing 10 tools + 1 resource for agents over stdio. Logs every call to `log/mcp_server.log`. |
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
- **English translations are not in Oracc's public JSON archive** — they exist only in the live HTML pages at `/{project}/{P-id}` and would need scraping. The metadata `formats.tr-en` list tells us *which* texts have a translation available, not the translation itself.

---

## A note on the data

Cuneiform is the world's oldest writing system, used continuously from ~3200 BCE to ~75 CE. Sumerian is one of the languages it recorded, attested longest in administrative and economic texts (the bulk of `epsd2-admin-ur3`, the largest single file in the corpus, is Ur III royal/temple bookkeeping from ~2100 BCE). The 35.5 million word-references in this dictionary are pointers into roughly that many actual occurrences of words on actual clay tablets, mostly held today in museum collections in London, Berlin, Philadelphia, Istanbul, and Baghdad. The cuneiform glyphs you see on entry pages here are the same characters that Sumerian scribes pressed into clay 4,000 years ago, encoded into Unicode in 2006 (range U+12000–U+1237F).
