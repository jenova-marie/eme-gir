# Jagersma 2010 → Oracc/ePSD2 conventions

A Rosetta stone between Bram Jagersma's *A Descriptive Grammar of Sumerian*
(PhD dissertation, Universiteit Leiden, 2010, 776 pp, 31 chapters) and the
Oracc/ePSD2 transliteration conventions used in this repository. This file
is the source of truth for terminology, notation, and period labels used in
`JAGERSMA_NOTES.md` and the synthesized `SUMERIAN_GRAMMAR.md`.

---

## 1. Citation format

Every grammatical claim derived from Jagersma carries an inline section
citation: `(Jagersma §N.M)` or, in dense passages, `(§N.M)`. Page numbers
are used only for verbatim quotes or when a claim is figure/table-bound.

- `§7.3` = Chapter 7 (Cases), section 3 (Ergative case)
- `§15.2.2` = Chapter 15, §2.2 (Perfective inflection pattern)
- `(p. 743)` = appendix verb-slot diagram

Where Jagersma's claim contradicts an older grammar (Edzard, Thomsen,
Falkenstein) we cite Jagersma's reading; where Jagersma is silent or
hedges, the cheat sheet says so explicitly rather than glossing over it.

---

## 2. Period labels (Jagersma's century codes)

Jagersma's source references end with a century-BCE digit. Mapping:

| Code | Period (Jagersma) | Period (conventional) | Approx. dates |
|---|---|---|---|
| 26 | Fara | Early Dynastic IIIa (ED IIIa) | ~2600 BCE |
| 25 | Old Sumerian (early) | Early Dynastic IIIa late | ~2500 BCE |
| 24 | Old Sumerian (late) | Early Dynastic IIIb (ED IIIb) | ~2400 BCE |
| 23 | Old Akkadian (Sargonic) | Sargonic / Old Akkadian | ~2300 BCE |
| 22 | Gudea | Lagash II / Gudea dynasty | ~2200–2100 BCE |
| 21 | Ur III | Third Dynasty of Ur (Ur III) | ~2100–2000 BCE |

**"Old Sumerian"** (Jagersma) = **ED IIIa-IIIb** (conventional). This is
Jagersma's primary descriptive ground and **our new agent default period**.

**Provenance codes** in source references: A (Adab), D (Drehem), I (Isin),
L (Lagash), N (Nippur), U (Umma), Ur (Ur), ? (unknown).

### Mapping to the ePSD2 `periods.p` column

`see_examples(oid, period=…)` does a case-insensitive substring match
against `glossary.sqlite::periods.p`. Confirmed-good substrings:

| Default | ePSD2 column value(s) | Use for `period=` arg |
|---|---|---|
| ED (Jagersma's default) | "Early Dynastic IIIa", "Early Dynastic IIIb", "Early Dynastic" | `"Early Dynastic"` (matches both IIIa+IIIb) |
| Ur III | "Ur III" | `"Ur III"` |
| Old Babylonian | "Old Babylonian", "Middle Babylonian" | `"Babylonian"` (matches both — note this is BROAD) |
| Old Akkadian | "Old Akkadian" | `"Old Akkadian"` |
| Lagash II / Gudea | "Lagash II" | `"Lagash II"` |
| Fara | "Early Dynastic IIIa" (Fara is treated as ED IIIa) | not separately filterable; use ED |

The verification phase (`JAGERSMA_VERIFICATION.md`) confirms these
substrings return hits on the live `glossary.sqlite`.

---

## 3. Transliteration: Jagersma → Oracc/ePSD2

Jagersma uses a linguistic transliteration system; Oracc uses the
"standard" Sumerological one with subscript number disambiguation. The
cheat sheet always uses **Oracc/ePSD2 convention** so examples
round-trip through our existing `cuneify` tool. Jagersma's originals
are preserved in `JAGERSMA_NOTES.md` for verification.

### 3.1. Sign-script distinctions

| Jagersma | Oracc | Notes |
|---|---|---|
| **bold** (logograms) | plain (no styling) | Oracc plain text doesn't distinguish; the convention disappears |
| ***bold italic*** (phonograms) | plain | as above |
| Superscript determinatives (`ᵈinanna`) | `{d}inanna`, `inanna{d}` | Oracc uses braces; Jagersma uses Unicode superscripts |
| Numeric subscripts (`du₁₁`, `gi₇`) | `du₁₁`, `gi₇` | Same convention. Oracc uses Unicode subscript digits in modern files; ASCII digits acceptable for query input |
| Accent disambiguation (`dú` = TU, `dù` = GAG) | `du₂`, `du₃` | Oracc preferred form: replace accents with subscripts. Accent forms still legal but normalized away by `cuneify`. |

### 3.2. Special phoneme letters

| Jagersma | Oracc/ePSD2 | Phoneme |
|---|---|---|
| `ḫ` (sometimes typeset `h~`) | `ḫ` (the actual character) or `h` in legacy contexts | velar/uvular fricative /x/ |
| `ĝ` | `ŋ` (Unicode 014B) | velar nasal /ŋ/. ETCSL legacy uses `j`; both `j` and `ĝ` legacy forms normalize to `ŋ` |
| `ř` | `r` | Jagersma's special r-grapheme (a contextually distinct r, possibly /tʃ/-like or rhotic+coronal). Oracc does not distinguish — both surface as `r`. Document the loss in notes. |
| `š` | `š` | same |
| `ṣ` | `ṣ` (Oracc) / `s,` (ASCII input) | same |
| `ṭ` | `ṭ` / `t,` | same |
| `÷` | `ʾ` or unwritten | Jagersma's glottal-stop symbol (aleph). Used in lexical forms like `{÷u}`, `{÷i}`, `{÷a}` (vocalic prefixes) and the nominalizer `{÷a}`. In Oracc spelling the glottal stop is usually unwritten; sometimes `ʾ` (Unicode 02BE). Treat all Jagersma `÷X` morphemes as Oracc bare-vowel morphemes (`u`, `i`, `a`, etc.). |

### 3.3. Bracket notation in Jagersma's morphemic analysis

| Jagersma symbol | Meaning | Cheat sheet convention |
|---|---|---|
| `{...}` | basic/lexical form of a morpheme (e.g. `{mu}`, `{÷a}`) | Preserve as-is. The cheat sheet talks ABOUT morphemes with braces; surface forms are bare. |
| `/.../` | phonological representation | Use sparingly; only when contrasting with spelling |
| `[...]` | phonetic representation | Almost never needed; spelling is closer to phonology than phonetics |
| `Ø` | zero morpheme | Preserve. Important for the inflection patterns. |
| `-` | morpheme boundary (affix–affix or affix–stem) | Same |
| `=` | clitic boundary | Same |
| `.` | period in multi-element gloss (`be.there`, `lapis.lazuli`) | Same |
| `( )` | dropped/elided vowel in basic form, e.g. `n(i)` = /n/ surfacing from /ni/ | Preserve in interlinear analyses; drop in surface examples |
| `/` (in gloss line) | alternative glosses for one morpheme (`3N.S/DO`) | Same |

### 3.4. Worked example of normalization

Jagersma's example (§11.4.2, ex. 14):

```
(14) ᵈen-líl-ra ᵈšul-ge-re kaš dé-a
     en.líl=ra šul.ge.r=e kaš =Ø dé -Ø -÷a =÷a
     Enlil =DAT Shulgi =ERG beer=ABS pour-NFIN-NOM=LOC
     'when Shulgi poured beer for Enlil' (OIP 115:433 3; D; 21)
```

Oracc-normalized cheat-sheet form:

```
{d}en-lil₂-ra {d}šul-ge-re kaš de₂-a
en.lil₂ = ra   šul.ge.r = e   kaš = Ø   de₂ - Ø - a = a
Enlil    DAT   Shulgi    ERG  beer ABS  pour NFIN NOM LOC
```

Transformations applied:
- `ᵈ` (superscript) → `{d}` (Oracc determinative)
- `líl` → `lil₂` (accent → numeric subscript)
- `dé` → `de₂` (accent → numeric subscript)
- `÷a` → `a` (glottal stop unwritten)
- The case/role gloss line and translation are kept verbatim.

The Sumerian line round-trips through `cuneify`: `{d}en-lil₂-ra` →
𒀭𒂗𒆤𒊏 etc.

---

## 4. Grammatical terminology

Jagersma deliberately reforms several traditional Sumerological terms. The
cheat sheet follows Jagersma's terminology, with a brief note on the older
term where confusion is likely.

### 4.1. Aspect labels (Jagersma §15.1, §1.3.1)

| Older term | Jagersma | This repo |
|---|---|---|
| preterite, ḫamṭu (ḫamtu) | **perfective** | perfective |
| present-future, marû | **imperfective** | imperfective |

Glossing convention: **perfective forms are NOT explicitly glossed** (treated
as the unmarked default); **imperfective forms are always tagged `IPFV`**
(Jagersma §1.3.2). The cheat sheet follows this — if you see no aspect
tag, the form is perfective.

NB: Jagersma stresses (§15.1) that "perfective" and "imperfective" here do
NOT pattern like Slavic perfective/imperfective. Sumerian perfective covers
states, timeless truths, and completed actions; imperfective covers
uncompleted actions. The labels are conventional.

### 4.2. Case vs. verbal-prefix terminology (Jagersma §1.3.1, §11.6)

Older grammars (Falkenstein, Edzard, Thomsen) use case names ('dative',
'locative') for verbal prefixes too. Jagersma separates them strictly:

| Older "dative case + dative prefix" | Jagersma |
|---|---|
| Dative case (NP marker) | **dative case** (only for human indirect objects, §7.5) |
| Dative-prefix (verb) | **indirect-object prefix** (§11.4.4, ch. 17) |
| "Directive" case (NP marker, non-human IO) | **directive case** (§7.6) |
| Locative case (NP marker `=÷a`) | **locative case** (§7.8) |
| Locative case (NP marker `=ne`) | **locative₂ case** (LOC2 in glosses, §7.9) |
| "Locative" prefix on verb | **local prefix** {ni}, {e} (§16.2, §20) |
| Comitative case | **comitative case** (§7.7) |
| Comitative-prefix | **comitative prefix** {da} (§19) — same name, but distinct from the case |

The cheat sheet labels NP markers with the case name; labels verbal
prefixes with the prefix's lexical form `{...}` plus its functional role
(indirect-object, oblique-object, local, comitative, ablative,
terminative).

### 4.3. Verbal slots — Jagersma's labels (Appendix p. 743)

Left to right in the finite verb:

| Slot # | Jagersma label | Contents | Cheat sheet shorthand |
|---|---|---|---|
| 1 | Preformatives — proclitics | `nu`, `ḫa` | NEG, MOD |
| 1' | Preformatives — prefixes | `÷i`, `÷a`, `÷u`, `na(n)`, `ga`, `bara`, `ši`, `na` | VP (vocalic prefix) / MOD / NEG |
| 2 | Prefix `{nga}` | `nga` | — |
| 3 | Ventive prefix | `mu`, `ma` | VENT |
| 4 | Prefix `{ba}` | `ba` | MM (middle marker) |
| 5 | Initial person-prefixes | `÷`, `e`, `n`, `b`, `mē`, `enē`, `nnē` | IPP — agrees with IO/OO |
| 6a | Indirect-object marker (in dimensional prefix block) | `(a)`, `(ra)` | IO marker |
| 6b | Dimensional prefix `{da}`, `{ta}`, `{ši}` | `da`, `ta`, `ši` | COM-pfx, ABL-pfx, TERM-pfx |
| 6c | Local prefixes | `ni`, `e` | LOC-pfx, LOC2-pfx |
| 7 | Final person-prefixes (FPP) | `÷`, `e`, `n`, `b` | FPP — agrees with A in perfective, with DO in imperfective |
| 8 | **STEM** | the verb root | — |
| 9 | Imperfective suffix | `ed` | IPFV |
| 10 | Person suffixes Set A | `en`, `en`, `Ø`, `enden`, `enzen`, `eš` | PS-A — perfective S/DO |
| 11 | Person suffixes Set B | `en`, `en`, `e`, `enē` | PS-B — imperfective A |
| 12 | Nominalizing suffix | `÷a` | NOM |

(Diagram caveat: elements from the same box/column cannot co-occur in one
verbal form. Exception: preformatives `{nu}` and `{ḫa}` can co-occur with
`{÷i}` (and perhaps `{÷a}`). Appendix p. 743.)

Mapping to our `find_verb_form` parameters:
- `prefix=` (mu/ba/i/bi/ga/ha) maps to slots 1', 3, 4 collapsed (the agent
  composes "conjugation prefix")
- `dimensional=[…]` maps to slot 6 (the dimensional prefixes block)
- `object_person=` maps to slot 5 (initial person-prefix)
- `polarity=` maps to slot 1 (preformative `{nu}`)
- `aspect=` is a suffix heuristic (slot 9 + slot 10 vs slot 11)
- `suffix_a=` maps to slot 12 (`{÷a}` nominalizer)

### 4.4. Case names — Jagersma's twelve

Per the Dutch summary (p. 746) Sumerian has **twelve cases**. From the
abbreviations table (p. xvii) and §7:

| # | Case | Jagersma marker | Glose | Primary use |
|---|---|---|---|---|
| 1 | absolutive | Ø | ABS | direct object; intransitive subject |
| 2 | ergative | `=e` | ERG | transitive subject |
| 3 | genitive | `=ak` | GEN | possessor |
| 4 | dative | `=ra` | DAT | human indirect object |
| 5 | directive | `=e` | DIR | non-human indirect/oblique object |
| 6 | locative | `=÷a` (= `=a`) | LOC | "in, on" |
| 7 | locative₂ | `=ne` | LOC2 | rare alternative locative |
| 8 | comitative | `=da` | COM | "with" |
| 9 | terminative | `=še` | TERM | "to, toward" |
| 10 | ablative | `=ta` | ABL | "from" |
| 11 | equative | `=gen` (or `=gin₇`) | EQU | "like" |
| 12 | adverbiative | `=eš` | ADV | manner |

NB: The "directive" case marker (`=e`) is homophonous with the ergative
(`=e`). Resolving the ambiguity is one of the load-bearing problems for
`parse_phrase`; chapter 7 (specifically §7.3 vs §7.6) is the
disambiguation source.

### 4.5. Other terminological choices (Jagersma §1.3.1)

| Older | Jagersma |
|---|---|
| pronominal element / infix | (final) **person-prefix** / **person-suffix** |
| conjugation prefix | **preformative** (Jagersma collapses the older "modal", "negative", "vocalic" prefix labels under preformative) |
| {mu-} | **ventive prefix** (§22) |
| Participle | **participle** (used as label of convenience for non-finite forms; Jagersma flags this as imperfect — they're verbal nouns as much as verbal adjectives, §28.1) |
| "Locative-terminative" | abolished — split into **directive** (NP case, §7.6) and **local prefix** (verb, §20) |
| Oblique object | restricted to a specific clausal role (§18.1) — not "any object that isn't direct or indirect" |

---

## 5. Conventions for the cheat sheet's worked examples

Each worked example in `SUMERIAN_GRAMMAR.md` carries:

1. **Sumerian line** (Oracc convention, plain ASCII-with-Unicode-subscripts)
2. **Morphemic analysis** (Jagersma-style basic-form with `=` and `-`)
3. **Glose line** (Jagersma's gloss tags)
4. **Translation** (English)
5. **Source citation** (`SOURCE; PROVENIENCE; CENTURY`, copied verbatim from Jagersma)
6. **Cuneiform line** (`cuneify`-rendered glyphs — only when the example was selected to demo cuneify-round-trip in §19 Worked Examples; not on every example)
7. **Jagersma §-citation** (`Jagersma §N.M`)

---

## 6. Out of scope for the cheat sheet's notation map

- **Vowel length** — Jagersma's section on V-signs (§2.5) and his
  treatment of long vowels are described but the cheat sheet does NOT
  introduce vowel-length distinctions in transliteration. Oracc doesn't
  mark length and we follow Oracc.
- **`ř` distinction** — Jagersma's `ř` (a contextually distinct r) is
  flattened to `r` in our examples. Notes file preserves the original.
- **Tone** — Sumerian probably had pitch accent (§3.7); we do not mark it.
- **Bold/italic typography for word vs sound signs** — visible in
  Jagersma's printed examples, absent in Oracc plain text and absent in
  our cheat sheet.
