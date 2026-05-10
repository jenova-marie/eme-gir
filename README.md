# Jenova's Local · ePSD2

A complete offline mirror, web browser, and AI-agent interface for the **electronic Pennsylvania Sumerian Dictionary** and the larger **Oracc cuneiform corpus** — the canonical scholarly resources for the world's oldest written language.

If you're a Sumerologist who wants to query 35 million attestations without touching the network; a developer who wants their LLM agent to translate English into actual Sumerian rather than plausible-looking nonsense; or a digital humanist looking to bring four-thousand-year-old clay tablets into a modern indexed pipeline — this is for you.

---

## What this is

The University of Pennsylvania's **electronic Pennsylvania Sumerian Dictionary**, second edition (ePSD2), is the standard modern lexical resource for Sumerian. It was published in 2017 by an international team led by Steve Tinney, and it integrates with the **Open Richly Annotated Cuneiform Corpus (Oracc)** — a federated archive of roughly 138,000 transliterated cuneiform texts from museum collections around the world.

Oracc publishes its data in two ways. The **live web interface** at `oracc.museum.upenn.edu/epsd2` serves richly hyperlinked HTML pages, and is excellent for browsing one entry at a time. The **bulk JSON archive** at `/json/` (208 zipped per-project archives, ~3.1 GB total) mirrors the same content as machine-readable structures, and is excellent for almost nothing in particular until you build infrastructure on top of it. *This project is that infrastructure.*

Specifically, Jenova's Local · ePSD2:

- **Pulls down all 208 Oracc project zips** and keeps them locally — no network trips during normal use, robust against the academic server's occasional slowness or downtime, friendly to a small server with limited bandwidth.
- **Streams the 1.9 GB Sumerian glossary into a SQLite index** without ever holding the source file in memory. The index has normalized tables for headwords, spellings, senses, attestation references, periods, compound words, and morphological breakdowns — 35.5 million word-occurrences indexed for sub-10-millisecond point lookups.
- **Resolves every attestation reference back to the actual line on the actual clay tablet**, by lazy-loading the right per-text JSON file from inside its project zip and walking the document tree. About 92% of references resolve successfully from the local data; the remainder cite projects we haven't downloaded.
- **Renders Sumerian cuneiform script as Unicode** for any transliteration string, using the Oracc Global Sign List (OGSL). Roughly 93% of glossary spellings render with full glyph coverage; the rest are flagged with `□` placeholders so you always know what's missing.
- **Serves it all as a small Flask web app** that recreates the look and feel of the live oracc.museum.upenn.edu/epsd2/sux page, with extras the live site doesn't offer: case-insensitive Unicode-aware search across six fields, attestation lines shown in their original sentence context with the target word highlighted, and cuneiform alongside every spelling.
- **Exposes the same data to LLM agents over the Model Context Protocol (MCP)** with fifteen specialized tools designed to support English ↔ Sumerian translation grounded in the real attested usage of the language. This is the part most directly aimed at AI applications.

The whole thing runs on a laptop. The full corpus is ~3.1 GB and the indexes another ~3.5 GB; given those, every operation in the web app and every MCP tool call is a local SQLite query, typically under fifty milliseconds.

## What this enables

### For Sumerologists and Assyriologists

A laptop-friendly version of the entire ePSD2 + Oracc dataset that responds in milliseconds, works completely offline, and gives you direct SQL access to every cross-referenceable structure in the data — period attestations, compound formations, sign frequencies, collocational n-grams. Things the live web interface can't easily answer — *"give me every Ur III text where `lugal` appears within three words of the verb `du₃`"* — become fifty-millisecond queries against a single denormalized SQLite database.

### For LLM applications

A serious bridge between modern AI agents and an ancient language with extremely sparse training data. Frontier LLMs have read enough Sumerian to half-remember the basics, but Sumerian is an agglutinative, ergative-absolutive isolate with idiosyncratic morphology that generative models routinely confabulate when asked to produce it. The MCP server's design philosophy is **attestation-first**: instead of letting the agent synthesize plausible-looking morphology, every tool returns *real* forms attested in the corpus, ranked by frequency, with cited tablet sources. The agent's job is to choose; the corpus's job is to constrain.

This includes a verb-form lookup that accepts grammatical features (perfective vs imperfective, person/number agreement, dimensional case prefixes, polarity) and returns matching attested forms with their morphological decompositions; a phrasal-collocation index built from all 138,000 corpusjson texts; bilingual search over the Oxford [Electronic Text Corpus of Sumerian Literature](https://etcsl.orinst.ox.ac.uk/) — 394 hymns, myths, royal compositions, and proverbs with English translations; a complete reverse-direction (Sumerian → English) parsing pipeline that handles cuneiform sign disambiguation; and a Sumerian grammar cheat sheet served as an MCP resource so the agent can pull it once per session into its working context.

### For digital humanists

A reference implementation of how to take a mature scholarly digital corpus and make it consumable by modern tooling — both human (the web app) and machine (the MCP server). The data model, schema, parsing strategies, and MCP tool design are all open and documented; the licensing means no friction for derivative work.

## Architecture at a glance

```
┌────────────────────────┐      ┌──────────────────────────┐
│ oracc.museum.upenn.edu │      │ etcsl.orinst.ox.ac.uk    │
│  /json/                │      │  (Oxford literary corpus) │
│  — 208 project zips    │      │  — TEI XML, bilingual    │
└─────────┬──────────────┘      └────────┬─────────────────┘
          │ download_corpus.py            │ build_etcsl_db.py
          ▼                               ▼
      corpus/*.zip                  data/etcsl.sqlite
          │
          │ streaming JSON parser (ijson, constant-memory)
          ▼
      data/glossary.sqlite     data/text_index.sqlite     data/collocations.sqlite
       (3.4 GB · 35.5 M         (10 MB · text → zip          (22 MB · phrasal n-grams
        attestation refs)         lookup + period meta)        of citation forms)
          │
          ▼
      ┌──────────────────────┐         ┌─────────────────────────────────┐
      │ Flask web app        │         │ MCP server (FastMCP)             │
      │  • /epsd2/sux        │         │  • stdio transport (Claude Code, │
      │  • entry pages       │         │    local agents)                 │
      │  • cuneiform render  │         │  • streamable-HTTP transport     │
      │  • period filtering  │         │    (remote agents, Docker)       │
      │                      │         │  • 15 tools + 1 grammar resource │
      └──────────────────────┘         └─────────────────────────────────┘
```

Both servers can run as standalone Python processes, or be deployed together via an included Docker stack (gunicorn for Flask, uvicorn for MCP, behind your reverse proxy of choice). A one-shot init container handles the multi-minute first-boot data setup so the running services keep tight startup windows.

## Data and attributions

| Source | License | What we use |
|---|---|---|
| **Oracc / ePSD2** (Tinney, Robson, Veldhuis, et al.) | **CC0** | Sumerian glossary; ~138K corpusjson texts; OGSL sign list |
| **ETCSL** (Black, Cunningham, Robson, Zólyomi, et al., Oxford 1998–2006) | **CC BY 3.0 UK** | 394 lemmatized literary texts with English translations |
| **OGSL** (Tinney) | CC0, distributed inside Oracc | Cuneiform sign → Unicode mapping |

The Oracc and OGSL data is dedicated to the public domain (CC0) and so requires no attribution, but cite it anyway — it represents decades of meticulous scholarship by an international team. The ETCSL license formally requires attribution; every MCP tool that returns ETCSL data carries an `attribution` field with the canonical citation string for downstream propagation.

## License

The code in this repository is released under the **MIT License** — see [`LICENSE`](LICENSE). Use it however you like, including commercially; the only requirement is that you carry the copyright notice forward in copies or substantial portions. The license applies to *the code*, not to the underlying linguistic data, which is governed separately by Oracc / ePSD2 (CC0) and ETCSL (CC BY 3.0 UK) as documented in the table above.

## A note on the data itself

Cuneiform is the world's oldest writing system, used continuously from roughly 3200 BCE to roughly 75 CE — a span of more than three thousand years. Sumerian is one of the languages it recorded, attested longest in administrative and economic texts. The bulk of the largest single zip in the corpus (`epsd2-admin-ur3`, 536 MB) is Ur III royal and temple bookkeeping from around 2100 BCE — the receipts, ration lists, work assignments, and animal counts of a Bronze Age bureaucracy.

The 35.5 million word-references in this dictionary are pointers into roughly that many actual occurrences of words on actual clay tablets, mostly held today in museum collections in London, Berlin, Philadelphia, Istanbul, and Baghdad. The cuneiform glyphs you see on entry pages here are the same characters that Sumerian scribes pressed into clay four millennia ago, encoded into Unicode in 2006 (block U+12000–U+1237F). When the MCP server's `cuneify` tool turns a transliteration like `lugal-e e₂ mu-na-du₃` into the glyphs 𒈗𒂊 𒂍 𒈬𒈾𒆕, you are looking at the same writing system that recorded the Code of Ur-Nammu, the Epic of Gilgameš, the praise poems of king Šulgi, the household accounts of Sumerian temples, and (in its later Akkadian and Hittite cuneiform descendants) the diplomatic correspondence of the Late Bronze Age.

This project doesn't add anything to that data; it just makes it easier to ask questions of it.

## Limitations

- About **8%** of glossary attestation references cite texts in projects we haven't downloaded; those fall back to raw reference strings on entry pages.
- About **7%** of spellings contain at least one sign missing from OGSL and render with `□` placeholders. Coverage will improve as OGSL grows.
- The web app's entry page doesn't yet render a dedicated bibliography section, per-sense interleaved examples, or a Period × Form cross-tabulation — though attestation lines do surface the publication shorthand (e.g. "YOS 14, 341") for any text with catalogue metadata.
- The `/epsd2/sux` glossary list page matches the live Oracc page 1 byte-for-byte; pages 2+ have occasional one-off reorderings (Oracc has a sub-sort tiebreaker we haven't fully reverse-engineered).
- Composite text references (Q-ids) aren't handled by the attestation resolver; only P-ids (physical objects).
- English translations of texts are not in Oracc's public JSON archive — they exist only in the live HTML pages and would need scraping. The optional ETCSL ingest pulls in 394 literary texts that DO ship with English translations, so any literary lookup via the `etcsl_*` MCP tools is bilingual out of the box, but the administrative bulk corpus remains transliteration-only.

## Getting started

For setup, build, and deployment instructions — including the Docker compose stack, MCP server configuration for various clients, and reverse-proxy recipes — see **[START.md](START.md)**.

For a complete LLM-agent system prompt that teaches the recommended translation workflow (decompose English → rank candidates → check compounds and collocations → choose aspect → apply cases → verify with attestations → render cuneiform), see [`prompt/AGENT_PROMPT.md`](prompt/AGENT_PROMPT.md).

For the Sumerian grammar cheat sheet that the MCP server also exposes as the `oracc://grammar/sumerian` resource, see [`prompt/SUMERIAN_GRAMMAR.md`](prompt/SUMERIAN_GRAMMAR.md).

For an in-depth reference aimed at AI coding assistants extending this project — schema documentation, the Oracc URL surface, the InCommon TLS gotcha, the cuneiform-rendering pipeline, the Docker layout — see [`CLAUDE.md`](CLAUDE.md).
