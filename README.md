# Eme-gir 𒅴𒂠

**A Sumerian-language MCP tool server for LLM agents** — five Model
Context Protocol servers exposing the **electronic Pennsylvania
Sumerian Dictionary (ePSD2)**, the **Oracc cuneiform corpus**, the
Oxford **Electronic Text Corpus of Sumerian Literature (ETCSL)**, and
the **Cuneiform Digital Library Initiative (CDLI)** artifact catalogue
to language models over a uniform JSON-RPC interface. Built around an
**attestation-first** contract: every tool returns real forms from real
tablets with cited sources, so the agent's job is to *choose* among
attested options, not to confabulate plausible-looking morphology for a
sparsely-trained ergative-absolutive isolate.

The repository also ships a **local Flask web browser over the ePSD2
glossary** that recreates the canonical `oracc.museum.upenn.edu/epsd2`
pages byte-for-byte. It is provided strictly as a 1:1 *verification
surface* against the upstream — useful for diffing local parses against
the canonical site, browsing offline, and grounding the MCP tools'
outputs in a human-readable rendering. It is not a replacement for
Oracc. A known limitation: result sorting may differ from the canonical
site on pages 2+ of multi-page lists, because Oracc's exact sort
algorithm (including its sub-sort tiebreaker) is not known.

If you're a developer who wants their LLM agent to translate English
into actual Sumerian rather than plausible-looking nonsense; a
Sumerologist who wants to query 35 million attestations without
touching the network; or a digital humanist looking to bring
four-thousand-year-old clay tablets into a modern indexed pipeline —
this is for you.

---

## What this is

The University of Pennsylvania's **electronic Pennsylvania Sumerian Dictionary**, second edition (Eme-gir), is the standard modern lexical resource for Sumerian. It was published in 2017 by an international team led by Steve Tinney, and it integrates with the **Open Richly Annotated Cuneiform Corpus (Oracc)** — a federated archive of roughly 138,000 transliterated cuneiform texts from museum collections around the world. Alongside Oracc, the Oxford **Electronic Text Corpus of Sumerian Literature (ETCSL)** — 394 hand-lemmatized literary compositions (hymns, myths, royal hymns, proverbs, the Sumerian King List, Inana's Descent, Gilgameš and the Underworld, the Šulgi praise poems) shipped with English translations — supplies the bilingual half of the Sumerian textual record that Oracc itself doesn't yet publish in machine-readable form. The **CDLI** artifact catalogue (353K cuneiform-bearing objects) supplies the museum-side metadata.

Oracc publishes its data in two ways. The **live web interface** at `oracc.museum.upenn.edu/epsd2` serves richly hyperlinked HTML pages and is excellent for browsing one entry at a time. The **bulk JSON archive** at `/json/` (208 zipped per-project archives, ~3.1 GB total) mirrors the same content as machine-readable structures and is excellent for almost nothing in particular until you build infrastructure on top of it. ETCSL is similarly stranded: its 4.9 MB TEI XML bundle from the Oxford Text Archive is rigorously lemmatized and translated, but the format is academic-archival, not query-ready. *This project is the infrastructure that turns all of it into queryable, performant, agent-accessible Sumerian.*

### Primary surface — five MCP servers for LLM-agent queries

The main thing this project is. **Nineteen specialized translation + catalogue tools plus a teaching surface and two knowledge resources**, organized into **five MCP servers along clean data-source boundaries** so an LLM client can choose its exposure: connect to all five for the full agent workflow, or just the raw-data servers (ePSD2 + ETCSL + CDLI + OGSL) and let the model discover the translation pattern itself.

| Server | Tools | Default HTTP port |
|---|---:|---:|
| **eme-gir-epsd2** | 11 ePSD2 dictionary + corpus tools (translate_english, lookup_entry, find_verb_form, …) | 5052 |
| **eme-gir-etcsl** | 4 ETCSL literary corpus tools — every result bilingual | 5053 |
| **eme-gir-cdli** | 2 CDLI artifact catalogue tools (provenience, museum, image links) | 5054 |
| **eme-gir-ogsl** | 2 cuneiform sign rendering tools (cuneify, lookup_sign) — useful for Akkadian/Hittite too | 5055 |
| **eme-gir-ummia** | Ummia 𒌝𒈪𒀀 (master teacher) — Sumerian 101 five-lesson curriculum + dual-register grammar reference | 5058 |
| `mcp_server.py` (legacy all-in-one) | All 19 data tools + 2 resources, for backwards compat | 5051 |

All of them share the same `eme_gir/` Python package — same SQLite indexes, same OGSL sign renderer, same attestation resolver, same auth wiring — but each is an independent process you can run + scale + secure separately. Every operation is sub-50-millisecond, a local SQLite query, never a network round-trip. The servers are designed for English ↔ Sumerian translation grounded in **attestation**: instead of letting LLMs hallucinate plausible-sounding morphology, every tool returns *real* forms with cited tablet sources, and every cited tablet links straight to its CDLI photograph. ETCSL coverage means every literary lookup comes back **bilingual** — invaluable for grounding translations in canonical Sumerian literary style. The [MCP toolbox](#the-mcp-toolbox) section below walks through each tool and resource in detail.

### Additional feature — the ePSD2 verification browser

A small Flask web app that recreates the look and feel of `oracc.museum.upenn.edu/epsd2` page-by-page, byte-for-byte where possible. It is **strictly a verification surface**, not a replacement for the canonical site — cite Oracc, not this mirror. Two motivations:

- **1:1 comparison with the canonical site.** Because the local pages render from the same source data Oracc uses, you can diff a local entry against the canonical Oracc entry to validate the parsing pipeline and catch corpus drift. Page 1 of the glossary matches byte-for-byte; pages 2+ have occasional one-off reorderings due to a sub-sort tiebreaker we haven't fully reverse-engineered.
- **Human-readable grounding for MCP outputs.** When the MCP servers return a lemma `oid` or a citation, the verification browser is where you (or the user behind the agent) go to *see* the dictionary entry in its full hyperlinked, cuneiform-rendered context — the same context an Oracc reader would see, served offline, with extras the live site doesn't offer (case-insensitive Unicode-aware search, attestation lines shown in their original sentence context with the target word highlighted, cuneiform glyphs alongside every spelling).

### Underneath both: the data pipeline

To make those two surfaces possible, this project also:

- **Pulls down all 208 Oracc project zips and the ETCSL bulk XML** — no network trips during normal use, robust against the academic servers' occasional slowness or downtime, friendly to small bandwidth budgets.
- **Streams the 1.9 GB Sumerian glossary into a SQLite index** without ever holding the source file in memory. The index has normalized tables for headwords, spellings, senses, attestation references, periods, compound words, and morphological breakdowns — 35.5 million word-occurrences indexed for sub-10-millisecond point lookups.
- **Ingests the 394 ETCSL literary texts** into a separate SQLite with FTS5 indexes on Sumerian transliteration AND English translation, ~160K lemmatized words and ~5,600 translation paragraphs queryable in either direction.
- **Resolves every attestation reference back to the actual line on the actual clay tablet**, by lazy-loading the right per-text JSON file from inside its project zip and walking the document tree. About 92% of references resolve successfully from the local data; the remainder cite projects we haven't downloaded.
- **Renders Sumerian cuneiform script as Unicode** for any transliteration string, using the Oracc Global Sign List (OGSL). Roughly 93% of glossary spellings render with full glyph coverage; the rest are flagged with `□` placeholders so you always know what's missing.

The whole thing runs on a laptop. The full corpus is ~3.1 GB and the indexes another ~3.5 GB; given those, every MCP tool call and every verification-browser page render is a local SQLite query, typically under fifty milliseconds.

## What this enables

### For LLM applications

A serious bridge between modern AI agents and an ancient language with extremely sparse training data. Frontier LLMs have read enough Sumerian to half-remember the basics, but Sumerian is an agglutinative, ergative-absolutive isolate with idiosyncratic morphology that generative models routinely confabulate when asked to produce it. The MCP servers' design philosophy is **attestation-first**: instead of letting the agent synthesize plausible-looking morphology, every tool returns *real* forms attested in the corpus, ranked by frequency, with cited tablet sources. The agent's job is to choose; the corpus's job is to constrain.

The "[The MCP toolbox](#the-mcp-toolbox)" section below walks through each of the nineteen tools and the two knowledge resources — what they do, when an agent reaches for them, and why they exist.

### For Sumerologists and Assyriologists

A laptop-friendly version of the entire Eme-gir + Oracc dataset plus the ETCSL literary corpus, all responding in milliseconds, working completely offline, and giving you direct SQL access to every cross-referenceable structure — period attestations, compound formations, sign frequencies, collocational n-grams, bilingual line-by-line literary readings. Things the live web interface can't easily answer — *"give me every Ur III text where `lugal` appears within three words of the verb `du₃`"*, or *"show me every literary line where `inana` is the subject of a marû verb"* — become fifty-millisecond queries against denormalized SQLite. And because the verification browser's pages render from the same source data Oracc uses, you can diff a local entry against the canonical oracc.museum.upenn.edu page when you need to verify a parse.

### For digital humanists

A reference implementation of how to take a mature scholarly digital corpus and make it consumable by modern tooling — both machine (the five MCP servers) and human (the verification browser). The data model, schema, parsing strategies, and MCP tool design are all open and documented; the licensing means no friction for derivative work.

## The MCP toolbox

The toolbox is organized around the workflow of a working translator: bootstrap the language, find candidate words, ground them in real attestations, decompose unfamiliar forms, link to museum-hosted photographs of the cited tablets, render the result. Every tool returns structured data with **frequency statistics** so the agent can reason about what's *typical* in the corpus versus what's *fringe* — a critical signal when the same Sumerian word can plausibly mean three different things and the agent has to pick one.

Tools are grouped below by **data source**, which also matches the five-server split: ePSD2 dictionary tools, ETCSL literary tools, CDLI artifact tools, OGSL sign tools, and the Ummia teaching surface. An agent that connects to `eme-gir-epsd2 + eme-gir-etcsl + eme-gir-cdli + eme-gir-ogsl` gets the raw data surfaces with no opinionated workflow guidance attached; an agent that also connects to `eme-gir-ummia` receives the master-teacher persona, the Sumerian 101 five-lesson curriculum, and the dual-register grammar reference (Jagersma academic + Meadow temple companion) as bootstrap material. The legacy all-in-one `mcp_server.py` exposes everything in one process for backwards compatibility.

### Bootstrap: the knowledge resources

Both resources are designed to be fetched once at session start so the agent can self-bootstrap on first connection — no operator-side prompt copy-paste required.

- **`oracc://prompt/agent`** — a drop-in system prompt teaching the end-to-end workflow over these tools: how to decompose English into content words, when to reach for `find_compound` vs `find_collocations`, how to pick ḫamṭu vs marû aspect, the required output format (transliteration + cuneiform + interlinear gloss + lexical justification + cited attestation), the ETCSL attribution requirement, and a fully worked example. Pairs with the grammar reference below; the prompt teaches *how to use the tools*, the grammar teaches *what Sumerian is*.
- **`oracc://grammar/sumerian`** — TWO grammar references bundled (~80 KB combined). **First: the academic reference** (~40 KB) — a comprehensive Sumerian grammar cheat sheet distilled from Bram Jagersma, *A Descriptive Grammar of Sumerian* (PhD dissertation, Universiteit Leiden, 2010, 776 pp), the most comprehensive modern descriptive grammar of Sumerian. Covers transliteration conventions, phonology, the twelve enclitic cases with surface-ambiguity tables, gender/plural, pronouns/numerals/adjectives, the nine-slot finite-verb template, perfective vs imperfective inflection patterns, all preformatives (vocalic/modal/negative), dimensional prefixes (IO/OO/local/comitative/ablative/terminative), the ventive `{mu}` and middle `{ba}`, non-finite forms, copular clauses, and nominalization-based subordination. Every grammatical claim carries an inline Jagersma section number (e.g. `§7.3`) so the user can verify against the primary reference. **Second: the temple-register companion** (~48 KB) — Meadow's Sumerian 101 classroom-e₂-nun-na lessons plus Entu Siri Nin's commentary: prayer-ready pedagogy (the PNC mnemonic, the "pesky -a" three-tip heuristic, the Emesal liturgical register, worked temple-composition examples). Conflict-resolution policy: the academic part is normative for reading attested texts; the temple part is normative for composing new in-temple Sumerian. Default period for translation when unspecified is **ED (Early Dynastic, ~2900-2350 BCE)** — Jagersma's primary descriptive ground (Old Sumerian = ED IIIa-IIIb). Without this in working memory, the agent can't reason about why `lugal-ra` is dative or why `mu-na-du₃` and `bi₂-in-du₃` differ in person agreement.

**For clients that only surface tools and not MCP resources** (the majority of production MCP clients as of writing), the same two bodies of content are also exposed as ordinary tools — call **`start_here()`** to get the agent system prompt and **`get_grammar_reference()`** to get the grammar cheat sheet. The agent prompt's docstring is prefixed with "⭐ CALL THIS FIRST" so a tools-list scan naturally surfaces it as the entry point. Spec-complete clients should prefer the resource form (cheaper, no tool round-trip, semantically right); the tool wrappers are a compatibility shim.

### Translating English → Sumerian

The tools an agent reaches for when going from an English meaning to a real, attested Sumerian expression.

- **`translate_english(query)`** — the entry point. Returns Sumerian lemma candidates ranked by frequency, with two disambiguating numbers per candidate: `sense_count` (how often this lemma appears in the corpus overall) and `sense_pct` (what fraction of those occurrences carry this specific meaning). A high `sense_count` with a low `sense_pct` means *"this word occasionally has that meaning"* — almost never the right pick. Conversely, `lugal [king] N` with 49,818 attestations at 100% sense_pct is the unambiguous Sumerian word for *king*.
- **`find_compound(english_phrase)`** — Sumerian frequently uses fixed multi-word compounds where English would use a single verb or a syntactic construction. *To bail water* is `a bal`; *to build a temple* is `e₂ du₃`. The agent calls this **before** composing word-by-word, because if a compound exists for the user's intent, that's what scribes actually wrote.
- **`find_collocations(cf)`** — phrasal idioms attested with a given lemma. Mined from all 138,000 corpusjson texts as 2/3/4-grams of citation forms. Surfaces year-name templates, royal titles, administrative formulas. If the user wants a phrase containing `lugal`, this tells the agent which adjacent words actually appeared on real tablets next to *king* (and which combinations would sound invented to a native speaker).
- **`find_phrase_pattern(pattern)`** — structural-template query over the corpus n-gram index. Each slot's grammar is `TARGET[gw]:case` where `TARGET` is a literal cf (`"lugal"`), a POS code (`"N"`, `"V/t"`, `"RN"`, `"V*"` for any verb), or `"*"`; the optional `[gw]` constrains the sense (`"lugal[king]"` vs `"lugal[plant]"`); the optional `:case` constrains the case marker (`"N:ergative"`, `"N:locative"`, `"N:!ergative"` for negation). Returns attested n-grams matching positionally, ranked by frequency. Three layers of disambiguation in one tool:<br>**v1**: *"what general shape did scribes write?"* — `["RN","lugal"]` → year-name templates.<br>**v3 (sense)**: *"which homograph?"* — `["lugal[king]","N"]` separates from `["lugal[plant]","N"]`.<br>**v2 (case)**: *"with what grammatical role?"* — `["N:ergative","N","V*"]` surfaces transitive-clause skeletons. The reviewer's lapis-blue-sky discriminator: `["zagin","*"]` returns 61 attested attributive uses, `["zagin:equative","*"]` returns 0 — empirical evidence that "lapis-X" is the dominant reading. Routes to the case+sense aware `inflected_collocations.sqlite` (62 MB, ~106K rows) when available; falls back to the legacy cf-only index for v1 patterns when not.
- **`find_verb_form(cf, pos, prefix=…, dimensional=[…], object_person=…, aspect=…)`** — the heart of attestation-first translation. The agent specifies a grammatical feature spec (perfective vs imperfective, person/number agreement, dimensional case prefixes) and gets back the attested verb forms that match, ranked by frequency, each with its morpheme template plus one cited line from the corpus. The agent does not *synthesize* `mu-na-du₃` from grammar rules — it *retrieves* it from a tablet where a Bronze Age scribe actually wrote it.

### Translating Sumerian → English

The reverse direction — for when an agent encounters an attested phrase, or when the user wants to read primary text.

- **`translate_sumerian(transliteration)`** — parses a transliterated Sumerian phrase into per-token English glosses. Whole-token-first: splits the input only on whitespace, then tries the full hyphenated word as a form-spelling lookup (so `lu₂-gal` resolves cleanly as `lugal`, `mu-un-du₃` as the inflected form of `du₃`), falling back to per-piece splitting only when the whole token has no match. Each token additionally carries its detected case/possessive/plural suffix chain when present, so the agent gets the grammatical-role signal from the morphology itself.
- **`parse_phrase(transliteration)`** — case-aware grammatical pre-annotation. Beyond glossing, each token is classified by its syntactic role from the morphology — `subject_ergative`, `oblique_dative`, `comparison_equative`, `verb_head`, etc. — and the response includes a compact bracket skeleton like `[NP lugal-ERG] [NP e-ABS] [V du (mu-na-)]` plus heuristic notes flagging detected patterns (transitive clause, equative comparison) and any ambiguous suffixes the agent should resolve manually. Not a full syntactic parser; a morphology-driven anchor for the LLM's parse. Useful when structural ambiguity matters — e.g. is `za-gin₃-gin₇` "the lapis-blue (attributive) sky" or "the sky, lapis-like (equative)"? The presence of `-gin₇` makes the answer mechanical.
- **`analyze_form(spelling)`** — decomposes a single attested spelling into candidate lemmas plus their morphological role (base, prefix chain, suffix). The deepest single-word lookup; called by the agent when `parse_phrase`'s pre-annotation flags an ambiguous form that needs holistic analysis.
- **`lookup_sign(query)`** — maps cuneiform signs both directions: by sign name (`LUGAL` → 𒈗 with all phonetic readings) or by phonetic value (`lugal` → which sign carries that reading). Disambiguates polyphones.

### Grounding and verification

A translation isn't credible without citation. These tools let the agent show its work and confirm its choices.

- **`lookup_entry(oid)`** — the full structured view of a chosen lemma: every sense, the top spellings (with cuneiform glyphs), period attestations, compound expressions. The agent uses this to confirm a choice it made from `translate_english` is the right one before committing to a phrasing.
- **`get_inflections(oid)`** — every attested morphological breakdown of a lemma — every prefix chain, every base/suffix combination, with frequency counts. Larger and noisier than `find_verb_form`; used when the agent wants the broader landscape of *"what shapes can this verb take in the actual corpus."*
- **`see_examples(oid, limit, period)`** — real attested lines from real tablets, with the target word highlighted. Period-filterable: `period='Ur III'` (~2100 BCE), `'Old Babylonian'` (~1800 BCE), `'Neo-Sumerian'`, etc. — so the agent can match the user's intended historical register. Each line carries its publication shorthand (*YOS 14, 341*) and P-id, which the agent cites in its reply.

### Rendering

- **`cuneify(spelling)`** — the last step. Converts an Oracc transliteration string (`lugal-e e₂ mu-na-du₃`) into Unicode cuneiform glyphs (𒈗𒂊 𒂍 𒈬𒈾𒆕). Handles braced determinatives, hyphen-joined sign sequences, sign-list dot-compounds, and morphology tails. About 93% of glossary spellings render with full coverage; the rest flag missing signs with `□` placeholders so the agent can be honest about gaps rather than silently dropping them.

### Literary corpus (bilingual via ETCSL)

The four `etcsl_*` tools query the Oxford [Electronic Text Corpus of Sumerian Literature](https://etcsl.orinst.ox.ac.uk/) — 394 lemmatized literary compositions (hymns, myths, royal hymns, proverbs, the Sumerian King List, Inana's Descent, Gilgameš and the Underworld, Šulgi's praise poems) that ship with English translations alongside the Sumerian. Unlike the administrative bulk corpus, which is transliteration-only, every ETCSL hit comes back **bilingual** — invaluable for grounding translations in canonical literary style.

- **`etcsl_search_english(query)`** — concept-level FTS5 search over the Oxford translations. Try `'kingship'`, `'underworld'`, `'descend*'`, `'"divine power"'`. Returns each match with the English paragraph and the Sumerian lines it covers.
- **`etcsl_search_sumerian(query)`** — FTS5 over Sumerian transliteration in the literary corpus, returning bilingual matches. Hyphens are token separators, so quote multi-token spellings (`'lugal-bi'`).
- **`etcsl_lines_with_lemma(lemma)`** — grounds a specific Sumerian lemma in literary use. The agent uses this when the user asks *"how would a poet phrase this"* rather than *"how would an Ur III scribe record this."*
- **`etcsl_lookup_text(text_id, start, line_limit)`** — read a whole composition end-to-end, paginated, bilingual. Famous IDs: `c.1.4.1` (Inana's Descent), `c.1.8.1.4` (Gilgameš and the Underworld), `c.2.1.1` (Sumerian King List).

Every `etcsl_*` result carries an `attribution` field with the canonical citation: *Black, J.A., Cunningham, G., Robson, E., and Zólyomi, G., The Electronic Text Corpus of Sumerian Literature (etcsl.orinst.ox.ac.uk), Oxford 1998–2006. © The Authors.* ETCSL is **not** released under any Creative Commons license — the Oxford editors hold traditional academic copyright and the project's citation request is honored as a non-optional condition of reuse. The agent passes the attribution through to the user verbatim. See [`LICENSE-DATA.md`](LICENSE-DATA.md).

### Artifact catalogue (via CDLI)

The two CDLI-backed tools query the **Cuneiform Digital Library Initiative**'s artifact catalogue — 353,000 cuneiform-bearing objects indexed by P-id with their excavation provenience, period attribution, museum custody, dimensions, publication history, and the URLs to CDLI-hosted photographs and line drawings. The same catalogue is also splatted **automatically** onto every cited line returned by `see_examples` and `find_verb_form`, so an agent answering "show me an attested form" can offer "see the actual tablet" links to the user without any extra tool calls — `cdli_url`, `photo_url`, `lineart_url`, plus thumbnails and museum holding info ride along on every `AttestationLine`.

- **`lookup_artifact(p_id)`** — one P-id → one record. Upgrades a bare "P347156" citation into a proper "VS 24, 037 (VAT 16439, Berlin Vorderasiatisches Museum), Old Babylonian, from Babylon" reference. Returns provenience (with remarks and excavation field number), period (with refinement remarks), museum (collection + catalog number + accession number), dimensions, genre/subgenre, language, material, object type, publication history, and computed image URLs (`photo_url`, `lineart_url`, plus `photo_thumb_url` / `lineart_thumb_url` for inline display).
- **`find_artifacts(provenience=…, period=…, museum_collection=…, genre=…, language=…, has_photo=…, has_lineart=…, …)`** — filtered query over the 353K-row catalogue. For structural questions about the corpus: *"every Ur III tablet from Drehem held by the British Museum"*, *"all Lagash II votive inscriptions"*, *"every Sumerian literary fragment in the Yale Babylonian Collection that has a photograph"*. Useful when the user wants representative coverage rather than a single example.

Every artifact result carries the CDLI catalogue attribution. **CDLI is NOT CC0** despite being widely treated that way: the catalogue text is freely reusable with citation per CDLI's "fair academic practice" terms, and the imagery on cdli.earth is non-commercial only (image copyright rests variously with CDLI, photographers, and holding museums). We do **not** host any CDLI imagery — every `photo_url` and `lineart_url` we return points straight to cdli.earth, so image-licensing remains CDLI's domain. The `attribution` field on every response carries the canonical credit; pass it through. See [`LICENSE-DATA.md`](LICENSE-DATA.md) for the full statement.

For the recommended end-to-end agent workflow that stitches these tools together (decompose English → rank candidates → check compounds and collocations → choose aspect → apply cases → verify with attestations → render cuneiform), see [`prompt/AGENT_PROMPT.md`](prompt/AGENT_PROMPT.md) — a drop-in system prompt that teaches the workflow with worked examples. The same content is also served by the MCP server itself as `oracc://prompt/agent` so a connecting agent can self-bootstrap without operator-side configuration.

## Architecture at a glance

```
  ┌────────────────────────┐ ┌──────────────────────────┐ ┌──────────────────────────┐
  │ oracc.museum.upenn.edu │ │ etcsl.orinst.ox.ac.uk    │ │ cdli-gh @ githubuserc... │
  │  /json/  — 208 zips    │ │  TEI XML — bilingual     │ │  cdli_cat.csv (LFS)      │
  └─────────┬──────────────┘ └─────────┬────────────────┘ └─────────┬────────────────┘
            │ download_corpus.py       │ build_etcsl_db.py          │ build_cdli_db.py
            ▼                          ▼                            ▼
        corpus/*.zip               data/etcsl.sqlite            data/cdli.sqlite
            │
            │ streaming JSON parser (ijson, constant-memory)
            ▼
      data/glossary.sqlite + text_index.sqlite + collocations.sqlite + inflected_collocations.sqlite

  ═══════════════════════════════════════════════════════════════════════════════════
   eme_gir/  ←  shared Python package (paths, log, cuneify, text_resolver, cdli,
                models/, sumerian_morphology, server, auth0_verifier, umami_analytics)
              ↑                            ↑                           ↑
              │                            │                           │
  ┌───────────┴───────────┐   ┌────────────┴──────────┐   ┌────────────┴───────────┐
  │  Five MCP servers     │   │  ePSD2 verification   │   │  Legacy mcp_server.py  │
  │  (per-domain) — the   │   │  browser (Flask)      │   │  port 5051 — all 19    │
  │  primary surface      │   │  port 5050            │   │  data tools in one     │
  │                       │   │  • /epsd2/sux         │   │  process (back-compat) │
  │  eme-gir-epsd2 :5052  │   │  • entry pages        │   └────────────────────────┘
  │  eme-gir-etcsl :5053  │   │  • cuneiform render   │
  │  eme-gir-cdli  :5054  │   │  • period filtering   │
  │  eme-gir-ogsl  :5055  │   │  • 1:1 vs upstream    │
  │  eme-gir-ummia :5058  │   └───────────────────────┘
  │                       │
  │  stdio + HTTP, opt-in │
  │  Auth0 OAuth, DNS-    │
  │  rebinding allowlist  │
  └───────────────────────┘
```

The five per-domain MCP servers + the ePSD2 verification browser share the same `eme_gir/` Python package — same SQLite indexes, same OGSL renderer, same attestation resolver, same auth wiring. Each MCP server is a thin (~30-40 line) entry point under `servers/<domain>/__main__.py` that registers only its domain's tools. They can be started independently (`python -m servers.epsd2`), or deployed together via the included Docker stack (gunicorn for Flask, uvicorn for MCP, behind your reverse proxy of choice). A one-shot init container handles the multi-minute first-boot data setup so the running services keep tight startup windows. The HTTP MCP transport optionally validates Auth0-issued OAuth 2.1 bearer tokens (RS256 JWT, RFC 9728 discovery via `/.well-known/oauth-protected-resource`); off by default, opt-in via global `EME_GIR_REQUIRE_AUTH=1` for deployments that need in-app auth instead of relying on a reverse proxy.

## Data and attributions

> **TL;DR:** All four data sources have meaningful reuse conditions. None of them is unconditionally public-domain, despite being widely treated as such in casual reuse. See [`LICENSE-DATA.md`](LICENSE-DATA.md) for the full statement.

| Source | License | What we use |
|---|---|---|
| **Oracc / ePSD2** (Tinney, Robson, Veldhuis, et al., U Penn) | **CC BY-SA 3.0 Unported** — attribution required, ShareAlike propagates | Sumerian glossary; ~138K corpusjson texts |
| **OGSL** (Tinney, distributed via Oracc) | **CC BY-SA 3.0** (same as Oracc) | Cuneiform sign → Unicode mapping |
| **ETCSL** (Black, Cunningham, Robson, Zólyomi, et al., Oxford 1998–2006) | **NO Creative Commons license** — traditional academic copyright; citation request honored as a non-optional reuse condition | 394 lemmatized literary texts with English translations |
| **CDLI** (Cuneiform Digital Library Initiative, originally UCLA, now MPIWG Berlin / cdli.earth) | **Catalogue text** freely reusable with citation (CDLI's "fair academic practice" terms); **imagery non-commercial only** | 353K-row artifact catalogue. We do NOT host any imagery — all photo/lineart URLs link to cdli.earth |

Every MCP tool returns an `attribution` field containing the canonical citation for its server's data. **Pass it through to the user verbatim** — this is mandatory under all three license regimes (Oracc's CC BY-SA requires attribution, ETCSL's citation request is non-optional, CDLI's terms require citation for catalogue reuse).

**The CC BY-SA 3.0 ShareAlike consideration** for Oracc-derived bundles (`data/glossary.sqlite` and friends): the ShareAlike clause means substantial reuses of the data layer must propagate the CC BY-SA 3.0 license to their derivative. The code in this repo is MIT (see below), but the *data layer* built from Oracc carries the copyleft inheritance. If you redistribute this repo's `data/` directory or use it as the foundation of a downstream service, the data half of your project must remain CC BY-SA 3.0-compatible. [`LICENSE-DATA.md`](LICENSE-DATA.md) documents this and how it interacts with the MIT-licensed code.

## License

The **code** in this repository is released under the **MIT License** — see [`LICENSE`](LICENSE). Use it however you like, including commercially; the only requirement is that you carry the copyright notice forward in copies or substantial portions.

The **data** bundled or built by this code has separate, more restrictive terms — see [`LICENSE-DATA.md`](LICENSE-DATA.md). In particular: Oracc data (which forms the bulk of `data/glossary.sqlite`) is CC BY-SA 3.0 with a ShareAlike inheritance clause, and ETCSL data carries traditional academic copyright with a required Oxford citation. MIT applies to *the code*, not to the linguistic data the code processes.

## A note on the data itself

Cuneiform is the world's oldest writing system, used continuously from roughly 3200 BCE to roughly 75 CE — a span of more than three thousand years. Sumerian is one of the languages it recorded, attested longest in administrative and economic texts. The bulk of the largest single zip in the corpus (`eme-gir-admin-ur3`, 536 MB) is Ur III royal and temple bookkeeping from around 2100 BCE — the receipts, ration lists, work assignments, and animal counts of a Bronze Age bureaucracy.

The 35.5 million word-references in this dictionary are pointers into roughly that many actual occurrences of words on actual clay tablets, mostly held today in museum collections in London, Berlin, Philadelphia, Istanbul, and Baghdad. The cuneiform glyphs you see on entry pages here are the same characters that Sumerian scribes pressed into clay four millennia ago, encoded into Unicode in 2006 (block U+12000–U+1237F). When the MCP server's `cuneify` tool turns a transliteration like `lugal-e e₂ mu-na-du₃` into the glyphs 𒈗𒂊 𒂍 𒈬𒈾𒆕, you are looking at the same writing system that recorded the Code of Ur-Nammu, the Epic of Gilgameš, the praise poems of king Šulgi, the household accounts of Sumerian temples, and (in its later Akkadian and Hittite cuneiform descendants) the diplomatic correspondence of the Late Bronze Age.

This project doesn't add anything to that data; it just makes it easier to ask questions of it.

## Limitations

- About **8%** of glossary attestation references cite texts in projects we haven't downloaded; those fall back to raw reference strings on entry pages.
- About **7%** of spellings contain at least one sign missing from OGSL and render with `□` placeholders. Coverage will improve as OGSL grows.
- The verification browser's entry page doesn't yet render a dedicated bibliography section, per-sense interleaved examples, or a Period × Form cross-tabulation — though attestation lines do surface the publication shorthand (e.g. "YOS 14, 341") for any text with catalogue metadata.
- The `/epsd2/sux` glossary list page matches the live Oracc page 1 byte-for-byte; pages 2+ have occasional one-off reorderings (Oracc has a sub-sort tiebreaker we haven't fully reverse-engineered).
- Composite text references (Q-ids) aren't handled by the attestation resolver; only P-ids (physical objects).
- English translations of texts are not in Oracc's public JSON archive — they exist only in the live HTML pages and would need scraping. The optional ETCSL ingest pulls in 394 literary texts that DO ship with English translations, so any literary lookup via the `etcsl_*` MCP tools is bilingual out of the box, but the administrative bulk corpus remains transliteration-only.

## Getting started

For setup, build, and deployment instructions — including the Docker compose stack, MCP server configuration for various clients, and reverse-proxy recipes — see **[START.md](START.md)**.

For a complete LLM-agent system prompt that teaches the recommended translation workflow (decompose English → rank candidates → check compounds and collocations → choose aspect → apply cases → verify with attestations → render cuneiform), see [`prompt/AGENT_PROMPT.md`](prompt/AGENT_PROMPT.md). The MCP server also exposes it as the `oracc://prompt/agent` resource so a connecting agent can self-bootstrap.

For the Sumerian grammar cheat sheet that the MCP server also exposes as the `oracc://grammar/sumerian` resource, see [`lessons/JAGERSMA_GRAMMAR.md`](lessons/JAGERSMA_GRAMMAR.md).

For an in-depth reference aimed at AI coding assistants extending this project — schema documentation, the Oracc URL surface, the InCommon TLS gotcha, the cuneiform-rendering pipeline, the Docker layout — see [`CLAUDE.md`](CLAUDE.md).
