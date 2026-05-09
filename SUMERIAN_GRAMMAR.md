# Sumerian grammar cheat sheet

Compact reference for composing Sumerian from English. Distilled from
Dietz Otto Edzard, *Sumerian Grammar* (Brill HdO Vol. 71, 2003) — the
standard reference for the language. Section numbers (e.g., §5.4.2) point
back to chapters in that volume for verification.

## 1. Transliteration conventions

- **Lowercase** = phonetic reading of a sign (`lugal` = the spoken word).
- **UPPERCASE** = sign name when no phonetic value is given (`LUGAL` is
  the cuneiform sign whose value is `lugal`, used as a logogram).
- **Hyphen** `-` joins signs that make up one Sumerian word: `lu₂-gal`.
- **Period** `.` separates parts of a compound grapheme: `AB.GAR`.
- **Braces** `{...}` mark **determinatives** — silent classifier signs
  written as superscript:
  - `{d}` = divine (Akk. *dingir*) before god names: `{d}lugal`
  - `{ŋeš}` = wood: `{ŋeš}gigir` (chariot)
  - `{kuš}` = leather: `{kuš}lu-ub₂` (leather bag)
  - `{na₄}` = stone: `{na₄}za-gin₃` (lapis lazuli)
  - `{mušen}` = bird (post-determinative): `lugal{mušen}` (an eagle)
  - `{id₂}` = river/canal name
  - `{ki}` = place name (post-determinative): `Unug{ki}` (Uruk)
- **Subscripts** distinguish homophones: `lu`, `lu₂`, `lu₃` are all spoken
  similarly but written with different signs.
- **Half-brackets** `⸢ ⸣` mark partly-damaged signs in publication; not
  used in translation output.
- **Square brackets** `[ ]` mark fully-broken signs; `[...]` is missing
  text.
- **Sumerian alphabetical order**: A, B, C, D, E, G, **Ŋ**, H, **Ḫ**, I,
  K, L, M, N, O, P, R, S, **Ṣ**, **Š**, T, **Ṭ**, U, W, X, Y, Z.

## 2. Word order

Sumerian is **SOV** (Subject – Object – Verb) and **ergative-absolutive**:

- The **absolutive** case (no suffix) marks the *subject of an intransitive
  verb* AND the *object of a transitive verb*.
- The **ergative** case (suffix `-e`) marks the *subject of a transitive
  verb*.

```
lugal-e e₂ mu-un-du₃           the king built a/the house
king-ERG  house  PFV-3SG.A-build
```

Adjectives **follow** the noun: `e₂ gibil` "new house", `udug ḫul` "evil
demon" (§6).

## 3. Noun phrase: case suffixes (§5.4)

Stack: `NOUN` + `(adjective)` + `(possessive)` + `(plural)` + `case`.
Possessive sits closer to the noun than case.

| # | Case | Suffix | Use | Example |
|---|---|---|---|---|
| 1 | **absolutive** | -Ø | object of trans, subject of intrans | `lugal` (king) |
| 2 | **ergative** | -e | subject of trans verb | `lugal-e` (king did…) |
| 3 | **genitive** | -ak (often spelled `-a(k)`, `-(k)`, or as final consonant of next word) | "of" — possessor follows possessed | `e₂ lugal-ak` (the king's house, "house of king") |
| 4 | **locative** | -a | "in, at" — non-person class only | `e₂-a` (in the house) |
| 5 | **dative** | -ra (-r after vowel) | "to, for" — person class | `lugal-ra` (to the king) |
| 6 | **comitative** | -da | "with" | `lugal-da` (with the king) |
| 7 | **ablative-instrumental** | -ta | "from, with (instrument)" — non-person | `e₂-ta` (from the house) |
| 8 | **terminative** | -še (writes `-šè`) | "to, towards" — both classes | `lugal-še₃` (to/towards the king) |
| 9 | **directive** | -e | "at, to (position next to)" — non-person | `e₂-e` (at the house) — collides with ergative -e |
| 10 | **equative** | -gin₇ (writes GIM) | "like, as" | `lugal-gin₇` (like a king) |

Note: Sumerian distinguishes **person class** (humans + named gods) from
**non-person class** (things, places, animals). Some cases are restricted
to one class.

### Possessive suffixes

Attach to the noun BEFORE case (rank order: `noun – possessive – case`).

| Person | Singular | Plural |
|---|---|---|
| 1st (my / our) | `-ŋu₁₀` | `-me` |
| 2nd (your) | `-zu` | `-zu-ne-ne` |
| 3rd person class (his/her) | `-(a)ni` | `-(a)ne-ne` |
| 3rd non-person class (its) | `-bi` | `-bi-ne` |

Examples: `e₂-ŋu₁₀` "my house", `ama-zu` "your mother", `dub-ba-ni` "his
tablet" (§9, §5.2).

When followed by genitive or locative, final vowel of possessive contracts:
`-ŋu₁₀ + -ak → -ŋa₂(k)`; `-zu + -ak → -za(k)`; `-bi + -a → -ba`.

### Plurality

Person class: add **`-(e)ne`** after possessive: `lugal-e-ne` "kings",
`dumu-ne-ne` "their children".

Non-person class: typically **collective** (`udu` already means "sheep" in
collective sense), or **reduplicate the adjective**: `e₂ gal-gal` "big
houses". Or use **-ḫi-a** "various" or **dedli** "individual" (§5.3).

## 4. Demonstratives (§7)

- **`-bi`** — anaphoric, "the (aforementioned)", "this/that one (just
  mentioned)" — also serves as 3sg non-person possessive
- **`-ne(n)`** — emphatic deictic, "this very one"

`lugal-bi` "this/that king", "the king (we just spoke of)".

## 5. Numerals (sexagesimal, §10)

| 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 | 10 |
|---|---|---|---|---|---|---|---|---|---|
| `dili` / `aš` | `min` | `eš₅` | `limmu` | `ia₂` | `aš₃` | `imin` (lex. `umun₅`) | `ussu` | `ilimmu` | `u` |

| 20 | 30 | 40 | 50 | 60 | 600 | 3,600 | 36,000 | 216,000 |
|---|---|---|---|---|---|---|---|---|
| `niš` | `ušu` | `nimin` | `ninnu` | `ŋeš` (`ŋeš₂`) | `ŋeš-u` | `šar₂` | `šar₂-u` | `šar₂-gal` |

Sumerian counts in 10s and 60s alternately; 60 is "one big unit" (`ŋeš`),
hence our hour and degree subdivisions. `3 600 = ŋeš × ŋeš = šar₂`.

Ordinals: number in the genitive + copula `-am₃`: `u₄ 2-kam` =
`u(d) min ak-am` "of day two" = "the second day".

## 6. The copula `-am₃` (suffix)

`PN dumu-am₃` "PN is a son". `lugal-bi-im` (after vowel `-am₃` → `-m`)
"this is its king". The copula attaches as a suffix to the predicate noun.

## 7. The verb (§12) — the heart of Sumerian

Every finite verb is built around a **base** (root), surrounded by a
prefix chain and suffix chain.

### 7.1 Aspect: ḫamṭu vs marû (§12.2)

Sumerian opposes two verbal stems:

- **ḫamṭu** ("quick") — perfective / completed action. Translates the
  Akkadian preterite *iprus*. Used in **conjugation pattern 2b** for
  transitives.
- **marû** ("slow") — imperfective / ongoing / future / habitual.
  Translates Akkadian *iparras*. Used in **pattern 2a** for transitives,
  and may take the suffix `-ed` for explicit future.

Most verbs have distinct stems; many are identical. Common patterns
(§12.4):

| Type | ḫamṭu | marû | Example |
|---|---|---|---|
| Identical | `gar` | `gar` | place |
| Reduplicating marû | `gar` | `gar-gar` | place (intensive) |
| Suppletive | `du` "go" | `ŋen` "go" | go |
| Vowel change | `du₃` "build" | `du₃` | build |
| Extended marû | `e₃` "go out" | `e₃-d` (with `-ed`) | go out |

### 7.2 Verb structure (§12.7, §12.8)

The full template, left to right:

```
[modal][conj.prefix][ventive][dimensional indicators][person]-ROOT-[suffixes]
```

| Slot | Examples | Meaning |
|---|---|---|
| Modal | `ḫe₂-` (precative "may"), `na-` (negative imperative "do not"), `ga-` (cohortative "let me"), `bara-` (negative affirmative), `nu-` (indicative negation) | mood / negation |
| Conj. prefix | `i-` / `e-`, `mu-`, `ba-`, `bi₂-`, `al-`, `(a)l-` | basic finiteness; `mu-` often = ventive (toward speaker), `ba-` often = away/locative |
| Ventive | `-m-` (in `mu-`, `mma-`, `mta-` etc.) | action toward speaker (1st person) |
| Dimensional indicators | `-ši-` (terminative), `-ta-` (ablative), `-da-` (comitative), `-na-` (dative), `-ni-`/`-bi-` (locative) | echo case suffixes on nouns; "to him", "from it", "with you" etc. |
| Person/class | `-n-` (3sg person), `-b-` (3sg non-person), `-e-` (2sg) | pronoun before root |
| ROOT | `du₃`, `gar`, `du`, `ak`… | verb stem (ḫamṭu or marû) |
| Suffixes | `-en` (1sg), `-en` (2sg), `-Ø` (3sg), `-enden` (1pl), `-enzen` (2pl), `-eš` (3pl), `-e` (3sg ergative agreement marû), `-ed` (future) | person agreement + tense/aspect |

### 7.3 Conjugation patterns (§12.7)

**Pattern 1 — intransitive / passive** (subject in absolutive):

| Person | ḫamṭu | marû |
|---|---|---|
| 1sg | `(prefix)-ROOT-en` | `(prefix)-ROOT-en` |
| 2sg | `(prefix)-ROOT-en` | `(prefix)-ROOT-en` |
| 3sg | `(prefix)-ROOT` | `(prefix)-ROOT-e` |
| 3pl | `(prefix)-ROOT-eš` | `(prefix)-ROOT-ene` |

**Pattern 2a — transitive marû** (agent ergative, prefix `-n-` for 3sg
person):

```
mu-na-ab-šum₂-mu = "he is giving it to him"
   |  |  |  ROOT-e
   |  |  └─ -b- (3sg non-person object)
   |  └─ -na- (dative "to him")
   └─ mu- (conj. prefix, ventive)
```

**Pattern 2b — transitive ḫamṭu** (the most common form for past actions):

```
lugal-e e₂ mu-un-du₃ = "the king built the/a house"
                |
                └─ mu-n-du₃: prefix "mu-" + 3sg person agent "-n-" + ROOT du₃
```

### 7.4 Imperative (§12.13)

Just the bare ḫamṭu base: `gen` "go!", `du₃` "build!"
With prefix chain attached as suffix instead: `gar-mu-na-ab` "give it to
him!" (lit. "place-it-to-him").

### 7.5 Reduplication (§12.5–§12.6)

Reduplicating the base expresses **plurality** of subject/object,
**intensification**, or in marû the imperfective itself:
`gi₄` "return" → `gi₄-gi₄` "keep returning / many return".

## 8. Compound verbs (§12.15)

Sumerian forms many "verbs" as **noun + verb** lexical units. Treat as a
single compound: the noun part stays in absolutive and the verbal part
takes all the morphology. Examples:

| Compound | Literal | Idiomatic |
|---|---|---|
| `a bal` | water + pour | to bail water / pour out water |
| `a bad` | arms + spread | to spread the arms |
| `a de₂` | water + pour | to irrigate (by flooding) |
| `e₂ du₃` | house + build | to build a temple/house |
| `gu₃ de₂` | voice + pour | to call out, cry out |
| `inim … pad` | word + utter | to swear an oath |
| `lugal kura` | king + presence | in the presence of the king |
| `mu lugalak pad` | name + king-of + utter | to swear by the king's name |
| `šu ti(g)` | hand + approach | to receive |
| `šu lugal` | hand + king | royal authority/quality |

Always check the glossary's `find_compound` tool for fixed expressions
before composing word-by-word — Sumerian frequently uses these instead of
verb derivation.

## 9. Pronouns (§9)

### Personal (independent — used for emphasis)

| | Singular | Plural |
|---|---|---|
| 1st | `ŋa₂-e` (I) | `me-en-de₃` (we) |
| 2nd | `za-e` (you) | `me-en-zen` (you pl.) |
| 3rd person | `e-ne`, `a-ne` (he/she) | `e-ne-ne` (they) |

Most pronominal reference is encoded in **suffixes** (possessive on nouns,
agreement markers on verbs). Independent pronouns are reserved for
emphasis or as topics.

### Demonstrative

`ur₅` "this" (rare, mostly literary). The clitic `-bi` does most
demonstrative work.

### Interrogative

- `aba` "who?" (person class)
- `ana` "what?" (non-person class)
- `me-a`, `me-še` "where? whither?"
- `me-na` "when?"

### Indefinite

`name` "any/no" — `lu₂ name` "anyone", `niŋ₂ name` "anything", with a
negative verb yields "no one / nothing".

## 10. Conjunctions / subjunctions (§14)

Sumerian originally lacked a word for "and" — usually expressed by
juxtaposition. Most subordinate clauses are formed by **nominalizing the
verb** (suffix `-a` on the finite verb) and adding a case particle:

- `nominalized verb + -ta` = "after / when (perfective)"
- `nominalized verb + -gin₇` = "as soon as / like"

| Conjunction | Use |
|---|---|
| `u₃` (Akkadian loan) | "and" — coordinates clauses or names |
| `u₄-da` | "if" (lit. "in the day-of") |
| `tukum-bi` | "if" (Akkadian loan; introduces conditional) |
| `en-na` | "until / as long as" |
| `mu` | "because" |
| `igi-zu` (`igi-inzu`) | "as if" (introduces hypothetical comparison) |

Negation: `nu-` prefixed to verb, or `na-` (prohibitive: "do not!").

## 11. Period notes for word choice

| Period | Approx. dates | Translation flavor |
|---|---|---|
| Early Dynastic (ED I–IIIb) | 2900–2350 BCE | Archaic; very early lexicon, many royal inscriptions |
| Old Akkadian | 2350–2150 BCE | Classical Sumerian still vernacular; brief decline |
| Lagash II | 2150–2100 BCE | Gudea's reign; literary peak (cylinders A & B) |
| **Ur III** | 2100–2000 BCE | Standard "classical" Sumerian; vast administrative corpus; *the default register for translation* |
| Old Babylonian | 1900–1600 BCE | Sumerian as dead literary language; more bilinguals; scribal-school refinements |
| Middle/Neo Babylonian, Hellenistic | 1500 BCE onward | Liturgical/scholarly use; archaizing |

When the agent is unsure, default to **Ur III orthography and
vocabulary** — it has by far the most attestations in our corpus and is
the period most likely to give a reader what they expect from "Sumerian".

## 12. Translation workflow (suggested for an LLM agent)

1. **Identify content words**: nouns, verbs, key modifiers in the English
   source. Skip articles ("the", "a") — Sumerian has none.
2. For each, call `translate_english(word)` and pick the candidate with
   the highest `sense_count` *and* a `sense_pct` close to 100. Prefer
   single-word lemmas when available.
3. For phrases and verb-noun expressions, call `find_compound(phrase)`
   first — Sumerian often has a fixed expression where English uses a
   syntactic phrase.
4. Choose **ḫamṭu** (perfective) for past completed actions; **marû** for
   present, future, habitual, or ongoing actions.
5. Order: `subject(-erg if transitive) object(-Ø) verb-with-prefixes`.
6. Add case suffixes to oblique nouns (dative `-ra`, locative `-a`,
   comitative `-da`, etc.) and **mirror them in the verbal prefix chain**
   (`-na-`, `-ni-`, `-da-` etc.).
7. Build the verb: prefix chain + person markers + ROOT + suffixes.
8. Call `cuneify(transliteration)` to render the final composition in
   Unicode cuneiform glyphs.
9. Optionally call `see_examples` on a key lemma to verify the chosen
   collocation is attested in real texts (cite the P-id in the
   translation footnote).

## 13. A worked example

English: **"the king built a temple"**

```
1. king          -> translate_english("king")    -> lugal (49,818x, 100%)
2. temple        -> translate_english("temple")  -> e₂  (top sense "house/temple")
3. built         -> translate_english("build")   -> du₃ (Ur III dominant verb)
4. compound?     -> find_compound("build temple")-> e₂ du₃ confirmed as collocation
5. structure (SOV, ergative on subject, perfective ḫamṭu):
     SUBJECT-ERG  OBJECT-ABS  VERB-with-prefixes
     lugal-e      e₂-Ø        mu-un-du₃
                                |  |  └─ ḫamṭu base "build"
                                |  └─ -n- = 3sg person agent
                                └─ mu- = conj. prefix (often ventive)
6. cuneify("lugal-e e₂ mu-un-du₃") -> 𒈗𒂊 𒂍 𒈬𒌦𒆕
```

Reading: *lugal-ERG temple-ABS PFX-3SG.A-build* → "The king built the
temple."
