# `eme-gir-epsd2` — Sumerian dictionary + corpus MCP server

You are connected to a local copy of the **electronic Pennsylvania
Sumerian Dictionary, 2nd edition** (Eme-gir / ePSD2) — the standard
modern lexical resource for Sumerian, prepared by Steve Tinney and
the Oracc team at the University of Pennsylvania. The data is licensed
**CC BY-SA 3.0 Unported** (the Oracc project-wide license; see
oracc.museum.upenn.edu/doc/about/licensing) — **attribution is required**
and the **ShareAlike clause propagates** to substantial reuses. Every
response from this server carries the canonical attribution string in
its `attribution` field; pass it through to the user verbatim. Loaded
into SQLite indexes from the Oracc bulk JSON archive. No network calls;
sub-50 ms point lookups.

**How to attribute (read this).** Every response also carries two short
fields built for exactly this purpose:
- `citation_short` — a one-line token (e.g. `ePSD2 (CC BY-SA 3.0)`).
  Reproduce it verbatim in a **Sources** section of your reply whenever you
  surface ANY field from a result — including numeric counts, spellings,
  and rendered glyphs, not only quoted prose.
- `presentation` — a point-of-use instruction describing how to attribute
  the result. Follow it.

`see_examples` and `find_verb_form` cited lines additionally carry a
pre-composed `display_markdown` block (the transliteration + the CDLI
artifact link + a dual ePSD2/CDLI citation, fused together) — when you
show a cited line, **relay its `display_markdown` verbatim** rather than
re-assembling it. The full verbatim license is also available as the MCP
resource **`license://oracc-epsd2`**, so the per-call `citation_short` can
stay short.

**Corpus shape:**

```
   15,940 lemmas        ← dictionary headwords
   19,066 senses        ← polysemous entries broken out per sense
  124,649 forms         ← attested spelling variants
   37,659 period rows   ← per-lemma temporal distribution
    1,901 compounds     ← multi-word cross-references
35,533,056 attestations  ← word-occurrences in 138K corpus texts
```

This is the **biggest** of the four data servers and the **primary**
surface for English ↔ Sumerian translation. The companion servers
specialize:

- **`eme-gir-ogsl`** — cuneiform sign rendering (`cuneify`, `lookup_sign`)
- **`eme-gir-cdli`** — artifact catalogue + image links (`lookup_artifact`, `find_artifacts`)
- **`eme-gir-etcsl`** — Oxford literary corpus (bilingual; traditional academic copyright with citation request, NOT a Creative Commons license)

This server **cross-references with CDLI automatically**: every
attested-line result from `see_examples` and `find_verb_form` carries
the cited tablet's CDLI URL + museum metadata splatted in as extra
fields, so the agent can offer click-through links to the actual
artifact without a separate `lookup_artifact` call.

---

## The attestation-first principle

**Sumerian morphology is too irregular to synthesize from rules.**
The right approach is to **retrieve attested forms** from the corpus,
not generate them. This server is built around that principle:

- ✅ Use `find_verb_form` / `get_inflections` to pull verb forms a
  Bronze Age scribe actually wrote.
- ✅ Use `find_collocations` / `find_phrase_pattern` to ground
  phrasings in real corpus n-grams.
- ✅ Use `see_examples` to cite primary-source lines.
- ❌ Don't compose a verb form like `mu-na-an-du₃-eš` from
  morpheme tables and hope it's grammatical — verify it's attested.

When the corpus doesn't attest a form you want, **find a closely-
related attested form and adapt it**, or honestly disclose to the
user that the form they asked for has no corpus precedent.

---

## The `sense_count` + `sense_pct` ranking

The single most important concept for using `translate_english`:

- **`sense_count`** = how many times this exact sense is attested in the corpus.
- **`sense_pct`** = what % of the lemma's TOTAL attestations are in this sense.
- **`entry_total`** = the lemma's total attestation count across all senses.

Use BOTH numbers together:

| sense_count | sense_pct | Interpretation |
|---|---|---|
| **High** | **~100%** | **"The word for X."** Single-meaning lemma; unambiguous choice. (`lugal [king]`: 49,818 / 100%.) |
| High | 50–99% | "A common meaning of this lemma, but it has others." Worth using; check `lookup_entry` for the other senses to make sure you're picking the right one. |
| High | <50% | "A non-dominant meaning of a polysemous lemma." Risky — when scribes wrote this lemma they usually meant something else. Consider alternatives. |
| **Low (1–10)** | **High (50–100%)** | Rare lemma, but unambiguous. Honest choice for a rare concept; flag the low attestation in your reply. |
| Low | Low (1–10%) | **Fringe metaphorical extension.** Almost never the right pick. (e.g. "horn" matches `a [arm]` at 0% sense_pct because "horn of the arm" exists as a fringe metaphor for "elbow.") |

The default ranking in `translate_english` is by `sense_count DESC`.
A high-count low-pct result will rank above a low-count high-pct
result — don't be fooled by raw count. Read both columns.

---

## English → Sumerian workflow

For each English content word:

```
1. translate_english(query)
   → rank candidates. Prefer high sense_count AND high sense_pct.
   → if top candidate has sense_pct < 80%, run lookup_entry to inspect
     the full sense distribution before committing.

2. lookup_entry(oid)  [verification, almost always required]
   → full sense list + top spellings (already cuneified) + period
     breakdown + compounds. Confirms you picked the right lemma.

3. find_compound(english_phrase)  [for phrases / verb-noun idioms]
   → Sumerian uses many fixed compounds where English uses syntax:
       "to bail water" → a bal       (multi-word cf)
       "palace" → egal               (orthographic compound, written e₂-gal)
       "scribe" → dubsar             (written dub-sar)
       "to look at" → igi—bar        (compound verb)
   → Prefer the compound over composing word-by-word when the corpus
     has one.

4. find_collocations(cf)  [phrasal patterns attested with this lemma]
   → year-name templates, royal title formulas, administrative idioms.
   → Mined from 2/3/4-grams of citation forms across all corpusjson.

5. find_phrase_pattern(pattern)  [structural template query]
   → "every transitive clause with this verb", "every ergative-marked
     noun + locative-marked noun + verb skeleton".
   → See "find_phrase_pattern slot grammar" section below.

6. find_verb_form(cf, pos=, prefix=, dimensional=, object_person=, aspect=)
   → for verbs: retrieve attested forms matching a feature spec.
     Returns morpheme template + spelling + count + one cited line.
   → Don't synthesize the verb form; retrieve it.

   OR

   get_inflections(oid)
   → for verbs: the FULL morphological landscape (every prefix chain,
     every base, every suffix combination, with counts). Use when you
     want the broader picture rather than a targeted feature spec.

7. see_examples(oid, period='Early Dynastic')
   → cite at least one real attested line in your reply. Each line
     comes with text_id (P-id), line label, transliteration, period,
     plus CDLI URLs + museum metadata splatted in.
```

**Default period when unspecified: ED (Early Dynastic, ~2900–2350
BCE)** — Jagersma's primary descriptive ground (Old Sumerian = ED
IIIa-IIIb). When the user specifies a period, use that filter
substring (see "Valid period filter strings" section below).

---

## Sumerian → English workflow

```
1. translate_sumerian(transliteration)
   → per-token glosses, whole-token-first tokenization.
   → Each token carries match_kind: "whole" (preferred) /
     "split_fallback" (lost the whole token, falling back to
     hyphen-split pieces) / "unmatched".
   → When you see "split_fallback", proceed to step 2 for that
     token — don't trust the per-piece glosses.

2. analyze_form(spelling)  [for any token that needs holistic decomposition]
   → returns candidate lemmas + the morphological role the spelling
     plays in each (base / form-sans / morph pattern).
   → Use when a token came back as split_fallback, or when you need
     to see the morphology template of an attested form.

3. parse_phrase(transliteration)  [for structural ambiguity]
   → case-aware chunking: each token classified by phrase role
     (subject_ergative, oblique_dative, comparison_equative,
     verb_head, …), plus a compact bracket skeleton:
       "[NP lugal-ERG] [NP e-ABS] [V du (mu-na-)]"
   → Reach for this when ambiguity matters (which noun does this
     case suffix attach to? is -gin₇ equative or attributive?).
   → NOT a full syntactic parser — it surfaces explicit role markers
     from morphology and lets you build the parse on top.

4. lookup_entry(oid)  [if a token's sense distribution is ambiguous]
   → see all senses + their attestation percentages to disambiguate.
```

---

## Valid period filter strings for `see_examples`

The `period` argument is a **case-insensitive substring** matched
against the `period` column in `text_index.sqlite`. Below are the
top period strings as they literally appear in the index. Each row
shows the substring → what it matches.

| substring → | matches | rows |
|---|---|---:|
| `"Ur III"` | `Ur III` | 81,511 |
| `"Neo-Assyrian"` | `Neo-Assyrian` | 13,250 |
| `"Old Babylonian"` | `Old Babylonian` | 9,536 |
| `"Old Akkadian"` | `Old Akkadian` | 5,785 |
| `"Early Dynastic IIIb"` | `Early Dynastic IIIb` | 3,938 |
| `"Neo-Babylonian"` | `Neo-Babylonian` | 3,606 |
| `"Middle Babylonian"` | `Middle Babylonian` | 3,023 |
| `"Middle Assyrian"` | `Middle Assyrian` | 2,654 |
| `"Uruk III"` | `Uruk III` | 1,366 |
| `"Achaemenid"` | `Achaemenid` | 1,112 |
| `"Lagash II"` | `Lagash II` | 943 |
| `"Lagaš II"` | `Lagaš II` (š variant) | 257 |
| `"Early Dynastic IIIa"` | `Early Dynastic IIIa` | 885 |
| `"Hellenistic"` | `Hellenistic` | 799 |
| `"First Millennium"` | `First Millennium` | 529 |
| `"ED IIIa"` | `ED IIIa` (CDLI-style short form) | 348 |
| `"Early Dynastic"` | `Early Dynastic` (catch-all + the IIIa/IIIb full names) | 343 + matches |
| `"Seleucid"` | `Seleucid` | 236 |
| `"Old Assyrian"` | `Old Assyrian` | 159 |

**Substring-matching gotchas:**

- `"Early Dynastic"` catches the catch-all rows AND the full IIIa/IIIb forms (343 + 885 + 3,938 = 5,166 total) — broadest catch-all for ED.
- `"Babylonian"` catches Old Babylonian, Middle Babylonian, Neo-Babylonian (16,165 combined).
- `"Lagash"` catches `Lagash II` only (943); does NOT catch `Lagaš II` (š variant) — they're separate strings. Use `"Lagaš"` for the š form, or just query both separately.
- `"Assyrian"` catches all four Assyrian periods (Old / Middle / Neo / etc.).

About **14% of texts** in the index have no period metadata — those
are excluded from any period-filtered query, so `total_matches` will
be lower than the unfiltered total even when the filter is broad.

---

## `find_phrase_pattern` slot grammar

The pattern is a 2-4 element list. Each slot uses the grammar:

```
slot = TARGET ('[' gw ']')? (':' case)?
```

Where:

- **`TARGET`** is one of:
  - A literal citation form: `"lugal"`, `"e"`, `"du"`, `"inana"`
  - A POS code: `"N"`, `"V/t"`, `"V/i"`, `"AJ"`, `"RN"`, `"DN"`, `"GN"`, …
  - A POS family glob: `"V*"` (any verb)
  - `"*"` — any cf, any POS
- **`[gw]`** optionally constrains the sense (homograph disambiguation): `"lugal[king]"` filters to the king-sense `lugal`, excluding `lugal[plant]`. Prefix `!` to negate: `"lugal[!king]"`.
- **`:case`** optionally constrains the case marker: `"N:ergative"`, `"N:locative"`, `"N:dative"`, `"N:terminative"`, `"N:comitative"`, `"N:ablative_instrumental"`, `"N:equative"`, `"N:genitive"`, `"N:directive"`. Prefix `!` to negate: `"N:!ergative"`. **`null`** means zero-marked (no overt suffix; absolutive).

**Worked patterns:**

| pattern | what it finds |
|---|---|
| `["RN", "lugal"]` | year-name templates: royal-name + king |
| `["lugal[king]", "N"]` | king + any noun — co-occurring pairs |
| `["lugal[king]:ergative", "N", "V*"]` | "the king(-erg) verbs a/the X" — transitive clauses with king as agent |
| `["N:ergative", "N:locative", "V*"]` | full transitive-clause skeletons with a locative complement |
| `["e[house]:absolutive", "du[build]"]` | "house (object) + build" — the temple-building idiom |
| `["zagin:equative", "*"]` | lapis-comparative phrases (`zagin = lapis lazuli`) — the prompt's documented test case; returns 0 because lapis was never used as an equative comparison in attested literature, so this is a useful diagnostic of how a true-zero result looks |

**Routing:** when the case+sense aware
`data/inflected_collocations.sqlite` is present (~62 MB index of
~106K case-aware n-grams), the tool uses it for v2 (`:case`) and v3
(`[gw]`) syntax. When that DB is absent, only v1 (cf + POS + `*`
patterns) work; v2/v3 returns a structured error with build hint.

Results are 2/3/4-grams attested in the corpus, ranked by frequency.

---

## Common POS codes

Sumerian dictionary lemmas carry these POS codes:

| code | meaning | count |
|---|---|---:|
| `N` | noun (common) | 7,830 |
| `DN` | divine name (deity) | 2,879 |
| `PN` | personal name | 1,342 |
| `V/t` | transitive verb | 1,058 |
| `TN` | temple name | 486 |
| `V/i` | intransitive verb | 434 |
| `SN` | sign name | 379 |
| `RN` | royal name | 331 |
| `GN` | geographic name | 302 |
| `AJ` | adjective | 267 |
| `WN` | watercourse / well name | 183 |
| `MN` | month name | 121 |
| `ON` | occupation/title name | 90 |
| `NU` | numeral | 60 |
| `CN` | canal name | 48 |

The `V*` family glob in `find_phrase_pattern` covers both `V/t` and `V/i`.

---

## Cross-server: CDLI enrichment on attested lines

When `see_examples` or `find_verb_form` returns an `AttestationLine`,
the line is auto-enriched with CDLI artifact metadata if the
catalogue knows the cited P-id. The extra fields:

```
cdli_url            ← CDLI artifact page (always populated when CDLI knows the P-id)
photo_url, photo_thumb_url     ← when CDLI has a photograph
lineart_url, lineart_thumb_url ← when CDLI has a line drawing
museum_collection, museum_no   ← current custody
```

**Render these as Markdown hyperlinks** in your reply when the
artifact informed the answer (same rendering rule as
`eme-gir-cdli`):

```
[P347156](https://cdli.earth/artifacts/347156) obv. 3 — *e₂ mu-na-du₃*
"he built the temple for him". Provenience: Lagaš (Tello).
Collection: Musée du Louvre, AO 22934.
[photo](…) · [lineart](…)
```

Render every populated URL as a clickable link. When an image URL
is `null`, omit it from the reply — don't say "no photo available".

---

## Output format for translation replies

For each translation, return:

1. **Sumerian transliteration** — your answer
2. **Cuneiform** — call `eme-gir-ogsl`'s `cuneify(spelling)` to render
3. **Morpheme gloss** — interlinear style:
   ```
   lugal-e   e₂        mu-un-du₃
   king-ERG  house-ABS  PFX-3SG.A-build
   ```
4. **Lexical justification** — one bullet per content word naming
   the chosen lemma, sense, and frequency stats:
   ```
   lugal [king] N — 49,818× (100% sense)
   e₂ [house] N — 20,279× (99% sense "house"; "temple" is 1% fringe)
   du₃ [build] V/t — 12,539× (98% sense)
   ```
5. **Cited attestation** — at least one P-id + line label showing
   the chosen lemma or collocation in real use, rendered as a
   clickable CDLI link (see "Cross-server: CDLI enrichment" above).
6. **Caveats** — period mismatch, low sense_pct, missing sign, etc.

---

## Common workflows

### 1. Translate an English sentence to Sumerian
```
English: "the king built the temple"

translate_english("king")         → lugal [king] N, 49818×, 100% sense  ✓
translate_english("build")        → du [build] V/t, 12539×, 98%         ✓
translate_english("temple")       → top hits are sadug/šabra/saŋŋa
                                    (temple offerings/admins);
                                    e [house/temple] is 4th but is the
                                    actual word for "temple"
                                    → use e₂ with the "temple" sense

find_compound("build temple")     → e du, e duʾa — the idiomatic compound
                                    is "e₂ du₃" (separately, not joined)

find_verb_form(cf="du", pos="V/t", aspect="hamtu", object_person="3sg.h",
               dimensional=["dat"])
  → mu-na-du₃ pattern (ventive + 3sg.h.dat + 3sg.h.subj + build)

cuneify("lugal-e e₂ mu-na-du₃")   → 𒈗𒂊 𒂍 𒈬𒈾𒆕

see_examples(o0026033, period="Lagash II")  # du[build] in Gudea period
  → cite a real Gudea-cylinder line as evidence
```

### 2. Read an attested Sumerian line
```
"lugal-e e₂ mu-na-du₃" (you see this in a corpus result)

translate_sumerian("lugal-e e₂ mu-na-du₃")
  → per-token glosses, suffix peeling

parse_phrase("lugal-e e₂ mu-na-du₃")
  → "[NP lugal-ERG] [NP e-ABS] [V du (mu-na-)]"
  → "ergative subject + absolutive object + transitive verb"
```

### 3. Find rare attested verb forms
```
You want the negative perfective of "to enter" with 3sg.h subject.

translate_english("enter")        → ku₄ [enter] V/t

find_verb_form(cf="ku₄", pos="V/t",
               polarity="neg",
               object_person="3sg.h",
               aspect="hamtu")
  → attested forms ranked by count; each with morph template + cited line
```

### 4. Disambiguate a polysemous lemma
```
You see "gu" in a text. Which gu?

translate_sumerian("gu-am₃")
  → returns lemma candidates with entry_total counts

analyze_form("gu-am₃")
  → which entry's morphology this spelling matches
  → distinguishes "gu [eat] V/t" from "gu [thread] N" etc.

lookup_entry(<the winning oid>)
  → confirm by sense distribution + period attestation
```

### 5. Structural query: "what gets eaten?"
```
find_phrase_pattern(["N:absolutive", "gu[eat]"], limit=20)
→ every attested noun-as-direct-object of the verb gu[eat]
→ ranked by frequency: barley, sheep, oxen, etc.
→ check the result tokens' gw fields for sense disambiguation
```

---

## Quick reference — key response shapes

### `translate_english` results
```
oid, cf, gw, pos, sense, sense_count, sense_pct, entry_total
```

### `lookup_entry` results
```
oid, cf, gw, pos, headword, total_count
senses[]      ← {id, meaning, pos, count, pct}
spellings[]   ← {spelling, count, pct, cuneiform} — already rendered
periods[]     ← {period, count, pct}
compounds[]   ← {compound (cf), oid} — cross-references
```

### `find_verb_form` matches
```
morph              ← morpheme template ("mu.na.n:~")
spelling           ← attested or synthesized spelling
synthesized_spelling
verified_in_forms  ← True iff the synthesized form matches forms.n exactly
count              ← attestation count for this morph row
share_pct          ← share of the verb's total attestations
forms_table_count  ← can be null (when the synthesized form doesn't
                     exactly match a forms-table row, common because
                     Sumerian phonology fills in vowels the morph
                     tokens don't carry)
cuneiform          ← rendered glyphs
example            ← one cited corpus line (AttestationLine, with
                     CDLI enrichment)
```

### `AttestationLine` (from `see_examples`, `find_verb_form.example`)
```
text_id, project, line_label, designation, period, transliteration
target, target_position           ← the target word + its position in the line
cdli_url                          ← always populated (use it)
photo_url, photo_thumb_url        ← populated when CDLI has the asset
lineart_url, lineart_thumb_url    ← populated when CDLI has the asset
museum_collection, museum_no      ← current custody
```
