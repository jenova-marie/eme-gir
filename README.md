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

To rebuild the glossary for a different language / project (e.g. the Akkadian
glossary, useful for bilingual workflows):

```bash
python3 build_glossary_db.py --zip corpus/rinap.zip --member rinap/gloss-akk.json --db glossary_akk.sqlite
```

## Use as an MCP server (English → Sumerian translation tools for an LLM)

The repo also ships an MCP server exposing five tools designed for agent-driven English-to-Sumerian translation. Add to your Claude Desktop / Claude Code MCP config:

```json
{
  "mcpServers": {
    "epsd2": {
      "type": "stdio",
      "command": "python3",
      "args": ["/path/to/this/repo/mcp_server.py"]
    }
  }
}
```

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

---

## What lives where

| | |
|---|---|
| `download_corpus.py` | Stdlib-only batch downloader; resume-safe; auto-fetches the InCommon TLS intermediate that Oracc's server omits. |
| `build_glossary_db.py` | ijson-streaming parser. Builds `glossary.sqlite` with normalized tables for entries, forms, norms, senses, signature occurrences, periods, compounds, and instances. |
| `build_text_index.py` | Scans every `corpus/*.zip` for `corpusjson/P*.json` files, builds `text_index.sqlite` mapping `(project, text_id) -> (zip, member)`. |
| `text_resolver.py` | Lazy lookup + LRU cache that turns a glossary `word_ref` (e.g. `epsd2/admin/ur3:P113959.10.3`) into the actual Sumerian line, with the target word marked. |
| `cuneify.py` | Loads OGSL on first use, exposes a Jinja `cuneify` filter. Tokenizes Oracc transliteration (determinatives, hyphen-joiners, compound graphemes, morphology tails) and renders Unicode cuneiform. |
| `app.py` + `templates/` | Flask app. Routes: `/epsd2/sux` (paginated glossary with letter zoom + search), `/epsd2/<oid>` (entry detail). |
| `mcp_server.py` | MCP server (`mcp` SDK / FastMCP) exposing 10 tools + 1 resource for agents over stdio. |
| `build_collocations.py` | Mines 2/3/4-gram phrasal collocations from every corpusjson text → `collocations.sqlite`. |
| `text_resolver.py` | Lazy lookup + LRU cache that turns a glossary `word_ref` into an attested Sumerian line. |
| `cuneify.py` | OGSL-backed transliteration → Unicode cuneiform converter; Jinja filter and stand-alone. |
| `SUMERIAN_GRAMMAR.md` | ~14 KB Sumerian grammar cheat sheet (Edzard 2003) shipped both as a file and as an MCP resource. |
| `text_index.sqlite` | Generated. `(project, text_id) → (zip, member, period, designation)` for ~140K texts. |
| `collocations.sqlite` | Generated. ~178K phrasal n-grams of citation forms mined from the corpus. |
| `static/img/jenova.png` | Header avatar / favicon. |
| `corpus/` | Generated. 208 `.zip` files (~3.1 GB). Gitignored. |
| `glossary.sqlite` | Generated. ~3.4 GB indexed extract of the Sumerian glossary. Gitignored. |
| `text_index.sqlite` | Generated. ~6 MB index of 139,455 `(project, text_id)` pairs. Gitignored. |
| `CLAUDE.md` | Detailed reference for AI coding assistants and humans alike — schema docs, the Oracc URL surface, the TLS gotcha, and project-prefix glossary. |

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
       │       ├─> text_index.sqlite: lookup (project, text_id)
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
- No Bibliography section, no per-sense interleaved examples, no period × form cross-tab — Oracc shows these on the entry page; we don't yet.
- The `/epsd2/sux` glossary list page matches Oracc page-1 byte-for-byte; pages 2+ have occasional one-off reorderings (Oracc has a sub-sort tiebreaker we haven't reverse-engineered).
- Composite text refs (Q-ids) aren't handled by the resolver; only P-ids.
- No English translations pulled from sibling `tr-en/` files yet.

---

## A note on the data

Cuneiform is the world's oldest writing system, used continuously from ~3200 BCE to ~75 CE. Sumerian is one of the languages it recorded, attested longest in administrative and economic texts (the bulk of `epsd2-admin-ur3`, the largest single file in the corpus, is Ur III royal/temple bookkeeping from ~2100 BCE). The 35.5 million word-references in this dictionary are pointers into roughly that many actual occurrences of words on actual clay tablets, mostly held today in museum collections in London, Berlin, Philadelphia, Istanbul, and Baghdad. The cuneiform glyphs you see on entry pages here are the same characters that Sumerian scribes pressed into clay 4,000 years ago, encoded into Unicode in 2006 (range U+12000–U+1237F).
