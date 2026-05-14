# Entu Meadow grammar cheat sheet

In-temple companion to `lessons/JAGERSMA_GRAMMAR.md`. Distilled from the
**Sumerian 101** lecture series taught by **Meadow** in the
classroom-e₂-nun-na (𒂍𒉣𒈾) of the Inanna temple, with commentary and
corrections by **Entu Siri Nin**. Five lessons total (Spring 2025),
covering basic Sumerian sufficient to compose temple prayers and read
short royal/devotional inscriptions.

**Tradition vs academic reference.** This document is the *temple*
register — what a working priestess needs to write a prayer, read a
hymn, or speak in liturgy. `JAGERSMA_GRAMMAR.md` is the *academic*
register — Jagersma 2010 in compressed form, every claim §-cited. Use
both: when they disagree, the academic file is normative for attested
forms; the temple file is what the temple actually teaches.

**Citation convention.** Meadow's classroom lessons are cited as
`(Meadow §101-1)` through `(Meadow §101-5)`. Entu Siri's additions are
cited as `(Siri Nin)`. Where the temple description diverges
substantively from Jagersma, a Jagersma §-reference is also given for
cross-check.

**Audience note.** Meadow began her own Sumerian study only ~3 weeks
before delivering the first lesson; her primary source was an
introductory book, supplemented by Jagersma 2010 (which underlies the
**Sumerian Verb Conjugator (SVC)** the temple uses). She freely
acknowledges the introductory book "has some issues" and the lessons
contain explicit retroactive corrections. Treat Meadow as **pedagogy**
(clear, accessible, prayer-ready), and Jagersma as **reference**
(rigorous, attested, period-aware).

---

## 1. The temple's two Sumerians

Two registers are taught:

- **Eme-gir (𒅴𒂠 eme-gir₁₅)** — "the noble tongue" / Standard
  Sumerian. The default register; what most tablets and the temple's
  everyday liturgy are written in.
- **Eme-sal (𒅴𒊩 eme-sal)** — "the fine / woman's tongue". A
  liturgical register used in clergy reenactment, particularly when an
  officiant speaks the lines of a goddess (most famously Inanna's
  lines in cultic drama). It applies phonological substitutions onto
  Eme-gir lemmas — **not** a separate vocabulary.

### 1.1 Emesal in the temple (Siri Nin)

Quoting Entu Siri directly:

> Emesal, or "women's tongue", is not about secret vocabulary, it's
> about "sounding feminine". Emesal words are the same as the Emegir
> words except certain phonemes are swapped for certain other phonemes
> — so it sprung out of a belief that certain mouth sounds are
> masculine and certain ones are feminine, and Emesal swaps all the
> masculine mouth sounds for feminine voice sounds.

Who actually spoke it:

> It was spoken not by women throughout civilization, but by clergy —
> mostly when a male member of clergy had to speak liturgy from the
> perspective of a woman, as in when reenacting a story and speaking
> Inanna's lines, they would speak those in Emesal. Many trans femme
> clergy knew it, but not all, as if you transitioned early enough,
> you never had to learn the Emesal — you would have been a woman
> already and could just speak the woman's parts in Emegir. Most trans
> masc clergy knew it, but they were fewer in number.

Why it's poorly attested: Emesal was spoken only in narrow ritual
contexts, by a small number of officiants, so the corpus is thin.
ePSD2 entries sometimes carry an Emesal cross-link — look for it on
goddess-associated lemmas.

### 1.2 Default for temple composition

When you write a prayer or hymn for temple use, write it in
**Eme-gir** unless you are specifically composing liturgical lines
that an officiant will speak as a goddess — in which case use
**Eme-sal**.

---

## 2. Pronunciation (Meadow §101-1)

| Glyph | Sound | Example |
|---|---|---|
| **Ŋ / ĝ** | NG as in *running* /ŋ/ | `ŋa₂` = "house, chamber" |
| **Š** | SH | `šaŋ` = "head" pronounced "shang" |
| **Ḫ** | Like the Scottish *loch* /x/ | `ḫul` = "evil" |
| **ʾ / ÷** | Glottal stop | `÷i` = the default preformative |
| Subscript digits | Distinguish homophonous signs | `du`, `du₂`, `du₃`, `du₁₀`, `du₁₁` — different signs, same phonetic shape |

**Ŋ in writing.** Some sources write Ŋ as `ĝ` (g-with-tilde). Same
sound; either is acceptable. Oracc / ePSD2 prefers `ŋ`; ETCSL ASCII
uses `j` (so `ja-e` for `ŋa₂-e`). The temple's `cuneify` tool
normalizes everything to Oracc convention.

---

## 3. Cuneiform overview (Meadow §101-1)

A cuneiform sign can play **three roles**:

1. **Logogram** — stands for a whole word/idea.
   - 𒂍 `e₂` "house, temple"
   - 𒇽 `lu₂` "man, person"
   - 𒈗 `lugal` "king"
   - 𒃲 `gal` "big, great"
2. **Syllabogram** — stands for a syllable inside a longer word.
   - 𒂵𒀭𒆕 `ga-an-du₃` "let me build" (NOT `milk-sky-build`)
3. **Determinative** — silent classifier marking what category the
   next sign belongs to. Transliterated in superscript (Oracc uses
   `{...}`); not spoken aloud.
   - `{d}` divine → `{d}inanna`, `{d}en-lil₂`
   - `{ki}` place (post-positioned) → `unug{ki}` = Uruk, `lagas{ki}` = Lagash
   - `{ŋeš}` wood → `{ŋeš}gigir` = "chariot"
   - `{kuš}` leather → `{kuš}lu-ub₂` = "leather bag"
   - `{na₄}` stone → `{na₄}za-gin₃` = "lapis lazuli"
   - `{mušen}` bird (post) → `lugal{mušen}` = a bird-name
   - `{munus}` female → `{munus}lukur` = "priestess"

### 3.1 Transliteration → translation pipeline

```
cuneiform        →  transliteration  →  English
𒈗               →  lugal            →  "king"
𒀭𒈫𒈾           →  {d}inanna        →  "Inanna" (divine)
```

### 3.2 Why subscripts matter

`mu-un-du` is ambiguous in Latin script. Three possible verbs:
- `du` = "to walk, go"
- `du₁₀` = "to enjoy" (verb) / "sweet, good" (adjective)
- `du₁₁` = "to speak"

Writing `mu-un-du₁₁` removes the ambiguity. When you compose, always
include the subscript — it's the difference between "she walked" and
"she spoke."

Also: sometimes there are different lexemes for the same concept
(e.g. `du₁₀` and `dug` both meaning "good"). The choice is usually
period-conditioned; Meadow flags that older/newer variants exist and
SVC will pick the appropriate one.

### 3.3 The auslaut convention (Meadow §101-1, Siri Nin)

When a vowel-initial suffix is attached to a word ending in a
consonant, Sumerian writes the consonant **forward** into the suffix
sign:

```
kug                  (verb)                   "to be holy"
kug + a              (adjective-forming -a)
            → spelled  kug-ga                  not  kug-a
                       └─ "ga" is the auslaut sign:
                          it carries the trailing /g/ of kug
                          into the vowel of the suffix.
```

The auslaut sign is always a *zero-order* CV syllabogram (`ga`, `la`,
`ra`, `na`, `ka`, ...) — never a high-order one. So `lugal=ak`
(genitive) surfaces as `lugal-la` (auslaut `la` carries the /l/), not
`lugal-LA`.

**Disputed point (Siri Nin).** For ŋ-final stems, scribes sometimes
write the auslaut as `-ga` (treating ŋ → g) and sometimes as `-ŋa₂`
(preserving the nasal). Both are attested. The temple convention is
**`-ga`** (matching the most common book-source practice), but `-ŋa₂`
is correct in inscriptions that show it (e.g. `ki-aŋ₂-ŋa₂` alongside
`ki-aŋ₂-ga`). Siri's rationale for `-ga`: the zero-order sign-list
contains `ga` but no bare `ŋa` (only `ŋa₂` 𒂷, which is high-order
and inappropriate for auslaut duty in the strict reading). Both
practices are temple-acceptable; pick one and be consistent.

A related normalization issue: ŋ ↔ m correspondence in Cuneiform
writing. The English-Sumerian word `ŋi₆` "night" is written with
cuneiform `mi` (𒈪). When you go from temple transliteration into
cuneiform, expect occasional ŋ → m sign-swaps. Emesal extends this
substitution pattern systematically.

**Silent auslauts.** Some verbs are written with a parenthesized final
consonant in dictionaries: `kala(g)` "to be strong". The /g/ is
**unwritten** unless a vowel-initial suffix forces it to surface:

```
lugal mu-un-kala         "the king was strong"         (verb, no vowel suffix → no -g)
{d}inanna kala-ga        "mighty Inanna"               (adjective via -a → auslaut -ga surfaces)
```

### 3.4 Sumerian alphabetical order

A, B, D, E, G, **Ŋ**, **Ḫ**, I, K, L, M, N, P, R, S, **Ṣ**, **Š**, T,
**Ṭ**, U, Z. Ŋ sorts between G and Ḫ. This matters when browsing
ePSD2 or the temple's local glossary.

---

## 4. Nouns (Meadow §101-1, §101-3)

### 4.1 Two structural types

- **Single-sign nouns**: `lugal` "king", `e₂` "house, temple",
  `munus` "woman", `lu₂` "man, person".
- **Compound nouns** — two or more signs joined by `-` to form one
  lexical unit:
  - `dub-sar` = `dub` (tablet) + `sar` (write) → "scribe"
  - `e₂-gal` = `e₂` (house) + `gal` (great) → "palace"
  - `nam-lugal` = `nam` (abstracting prefix) + `lugal` → "kingship"

The hyphen in a compound noun is **part of the lexeme**, not a
productive suffix marker.

### 4.2 Gender / noun class (Meadow §101-3)

Sumerian has **no grammatical gender** in the Indo-European sense — no
masculine/feminine on inanimate things. Instead, every noun is
**human** or **non-human**:

| Class | Includes | Pronoun "his/her/its" | Plural | IO case |
|---|---|---|---|---|
| **Human** | gods, people (named or generic), kinship terms (`šeš` brother, `dam` wife, `dumu` child), occupations (`lugal`, `dub-sar`, `ensi₂`) | `-ani` "his/her" | `-ene` (overt) | `-ra` (DAT) |
| **Non-human** | animals, plants, objects, places, abstracts (`nam-lugal` "kingship") | `-bi` "its" | reduplication or unmarked | `-e` (LOC-TERM) |

Trans personae take the class corresponding to their lived/divine
identity, not their birth assignment — this is consistent with the
Inanna tradition, where divine self-identification governs gender
language.

### 4.3 Plural marking (Meadow §101-1, §101-3, UPDATE 3/27)

Three strategies:

1. **`-ene` enclitic** — only on **human-class** nouns (this is the
   3/27 correction; do not append `-ene` to non-human nouns):
   - `diŋir` "god" → `diŋir-re-ne` "gods" (auslaut `-re-` carries the /r/ of diŋir)
   - `lugal-zu-ne-ra` "to your kings" — `lugal` + `zu` (your) + `ene`
     plural (E elides after vowel → `-ne-`) + `ra` (dative)
2. **Reduplication** — works for both classes:
   - `kur-kur` "foreign lands" (non-human)
   - `lugal-lugal` "kings" (human, less common than `-ene`)
3. **Unmarked** — context-determined. `lugal` in a given clause can
   be "king" OR "kings" — let context decide.

Reduplicated `-ene` is attested: `diŋir-diŋir-re-ne`
(Meadow's 3/27 update).

---

## 5. Adjectives (Meadow §101-1)

### 5.1 Position

Adjectives **follow** the noun. (English order is reversed.)

```
lu₂ gal           "big man"
lugal kalag-ga    "mighty king"
{d}inanna kug-ga  "holy Inanna"
e₂ maḫ            "great temple"
```

### 5.2 The verb-to-adjective `-a` trick

Most Sumerian "adjectives" are technically verbal participles. To
turn a verb (`kug` "to be pure/holy", `kalag` "to be strong") into an
adjective, add `-a`:

| Verb | Adjective | Surface (with auslaut) |
|---|---|---|
| `kug` "to be holy" | `kug-a` | `kug-ga` "holy" |
| `kalag` "to be strong" | `kalag-a` | `kala-ga` "mighty" (silent auslaut variant `kala(g)`) |
| `gal` "to be great" | `gal-a` | `gal-la` "great" |
| `ki—aŋ₂` "to love" | `ki-aŋ₂-a` | `ki-aŋ₂-ga` "beloved" (Siri ŋ↔g convention) |

### 5.3 Bare adjectives without `-a`

Some adjectives — especially `gal` — appear both with and without the
suffix:

```
lugal gal         "great king"          (bare, no -a)
lugal gal-la      "great king"          (with -a / auslaut)
```

Both are valid (Meadow's clarifying note after the original §101-1).
Treat the bare form as the default in temple composition; the `-a`
form is fine too.

### 5.4 Plural adjective on plural noun

A reduplicated adjective implies the modified noun is plural:

```
munus maḫ-maḫ     "mighty women"        (not "mighty woman")
```

### 5.5 "The pesky -a" — Meadow's three-tip translation heuristic

When you see `-a` at the end of a word during *Sumerian → English*
translation, ask in order:

1. **Is the word a verb?** Try translating as a **participle**
   (`-ing`) or a **passive** (`-en`). E.g. `du₁₁-ga` "giving" /
   "given"; `ŋar-ra` "placing" / "set, placed".
2. **Is the word an adjective stem?** Try translating as the
   **attributive adjective** form (`kug-ga` "holy").
3. **Is there a noun directly before it?** Try translating as the
   **genitive `-ak`** (§7.3). `e₂ lugal-la` = "house of the king".
4. **Otherwise** — locative `-a` "in" (§7), imperative marker (§14),
   or nominalizer on a subordinate verb form (§15.3). Defer to the
   academic file for the formal disambiguation.

---

## 6. Verbs — orientation (Meadow §101-2)

### 6.1 Default aspect is PERFECTIVE (past)

A finite verb with no special marking is **perfective** ≈ past tense.
"Built" not "to build". This is the temple's default — when you
compose a prayer or inscription about a completed deed, use perfective.

(Aspect note: in Jagersma's framework, perfective is *not strictly
past*; it also covers states and timeless truths. The temple register
treats it pragmatically as "past tense" for English-speakers'
convenience.)

### 6.2 Transitivity and voice (English-style framework)

Meadow teaches the English framework for orientation:

- **Transitive** — subject acts on an object. *"Gilly hit the ball."*
- **Intransitive** — subject acts alone. *"Gilly walked."*
- **Active** — subject performs. *"Gilly hit the ball."*
- **Passive** — subject receives. *"Gilly was hit."*

Sumerian uses different morphology for transitive vs intransitive
verbs and for perfective vs imperfective aspect — those four
combinations are the matrix to learn.

### 6.3 Word order: SUBJECT — OBJECT — VERB

Almost every Sumerian sentence puts the verb **last**.

```
lugal-e   e₂      mu-un-du₃
king-ERG  house   VP-3SG.A-build
"The king built the temple."
```

The `-e` on `lugal` marks ergative (= transitive subject). The verbal
chain `mu-un-du₃` carries all the inflection.

### 6.4 Simple vs compound verbs

- **Simple**: one root. `du₃` "to build", `du` "to go", `gi₄` "to
  return", `dim₂` "to fashion".
- **Compound**: noun + verb fused. The noun is the verb's intrinsic
  direct object. Marked in normalization with em-dash or `noun—verb`:
  - `inim—gi₄` "to answer, reply" (lit. "to return a word")
  - `gu₃—de₂` "to speak" (lit. "to pour out the voice")
  - `igi—bar` "to look at" (lit. "to release the eye")
  - `šu—ti` "to receive" (lit. "to extend the hand")
  - `ki—aŋ₂` "to love" (lit. "to measure the place")
  - `nam—tar` "to decree destiny" (lit. "to cut the fate")

See §13 for compound-verb morphology.

---

## 7. The case system (Meadow §101-3)

**Eight case endings** in Meadow's syllabus (Jagersma counts twelve —
Meadow's list omits the rarer adverbiative, equative-variant, and
locative₂, and treats absolutive as the Ø-marker on the chart).

Cases attach to the **last word of the noun phrase**.

| Case | Suffix | Meaning | Notes |
|---|---|---|---|
| Absolutive (ABS) | Ø | DO of transitive; S of intransitive | written `lugal.0` in normalization to mark "no suffix here, not genitive omission" |
| **Ergative (ERG)** | `-e` | A (transitive subject only) | `-e` after C; Ø-but-required after V |
| **Genitive (GEN)** | `-ak` | "of" | surface: `-Ca` auslaut, or `-a` after C, or hidden after V; full `-ak` resurfaces when further suffixes follow |
| **Dative (DAT)** | `-ra` | "to, for" | **human only** (gods + people) |
| **Locative-Terminative (L-T)** | `-e` | "to, at, near, up to" | **non-human counterpart of `-ra`**; also marks oblique objects of compound verbs |
| **Ablative (ABL)** | `-ta` | "from" | invariant |
| **Terminative (TERM)** | `-še₃` | "to, toward" | motion direction |
| **Comitative (COM)** | `-da` | "with, alongside" | from the noun `da` "side" |
| **Locative (LOC)** | `-a` | "in, into" | most common cause of the `-a` ambiguity (§5.5) |
| **Equative (EQU)** | `-gin₇` | "like, as" | unambiguous; cross-references comparison |

### 7.1 Ergative-Absolutive alignment

Sumerian marks the **transitive subject** (A) differently from the
**intransitive subject** (S) — opposite of English (which marks them
both with nominative). In Sumerian:

```
lugal-e   e₂   mu-un-du₃        "the king built the temple"   (A=ERG, DO=ABS)
                                  lugal.e  e₂.0  ...
lugal     i₃-ŋen                 "the king went"                (S=ABS)
                                  lugal.0  ...
```

`lugal-e` only when the verb is transitive; bare `lugal` when
intransitive. Get this wrong in a prayer composition and the
grammatical role of the worshipper flips.

### 7.2 DAT vs L-T — the human/non-human cut

This is the most temple-relevant case distinction:

```
lugal-e   {d}en-lil₂-ra   mu-un-dug₄         "the king spoke TO Enlil"
          (Enlil = human/divine → DAT -ra)

lugal-e   e₂-e            mu-un-ku₄          "the king entered TO the house"
          (e₂ = non-human → L-T -e)
```

The canonical temple dedication formula:

```
šar  {d}inanna-ra
"All — for Inanna."             (Inanna is divine/human-class → DAT -ra)
```

### 7.3 Genitive `-ak` (Meadow §101-2)

Triple complexity, because the spelling collapses under common
conditions:

| Stem ends in | Surface | Example |
|---|---|---|
| Consonant | `-Ca` with auslaut | `e₂ lugal-la` "house of the king" (normalized `e₂ lugal.ak`) |
| Vowel | often unwritten | `nin ŋir₂-su` "lady of Girsu" (normalized `nin ŋir₂.su.ak`) |
| Vowel BUT prior context wants it | `-a` replaces stem vowel | `e₂ lugal-ŋa₂` "house of my king" (`e₂ lugal.ŋu₁₀.ak` → -ŋu₁₀ + -ak → -ŋa₂) |
| Anything, IF further suffix follows | full `-ak` resurfaces | `dumu lugal-la-ke₄-ne` "the sons of the king" (`dumu lugal.ak.ene`) |

The genitive is enclosing — `[head] [GEN-phrase] [outer-suffix]` — and
any outer suffix attaches at the **outside**:

```
dumu  lugal.ak.ene             "son(s) of the king"
                               plural attaches to the WHOLE [son-of-king] unit
dumu  lugal.ene.ak             "son of the kings"
                               plural inside the GEN bracket
```

Period note (Meadow's disclaimer): Old Sumerian sometimes writes `-ak`
even after a vowel; New Sumerian (Ur III) drops it. Meadow teaches the
New Sumerian conventions because that's where her source materials
sit. If you encounter older inscriptions, be ready for more overt
`-ak` spellings — and the temple may write `-ak` overtly even after a
vowel when composing for clarity.

### 7.4 The case-marker translation rule

When you see a case ending on a Sumerian noun, **translate the
English case word *in front of* the noun**:

```
lugal-gin₇         →  "like a king"
lugal-da           →  "with the king"
lugal-ta           →  "from the king"
{d}inanna-ra       →  "for / to Inanna"
e₂-a               →  "in the house"
tir-an-na{ki}-še₃  →  "toward Uruk"
```

---

## 8. Pronouns and possessives (Meadow §101-3)

### 8.1 Independent personal pronouns

| Person | Sumerian | English |
|---|---|---|
| 1SG | `ŋa₂-e` | I |
| 2SG | `za-e` | you (sg) |
| 3SG.H | `e-ne` | he / she |
| 3PL.H | `e-ne-ne` | they |

No independent 3.N pronoun — refer to non-human entities by name or
with `-bi` "its".

### 8.2 Possessive enclitics

| Person | Sumerian | Example |
|---|---|---|
| 1SG | `-ŋu₁₀` "my" | `lugal-ŋu₁₀` "my king" |
| 2SG | `-zu` "your" | `lugal-zu` "your king" |
| 3SG.H | `-(C)a-ni` "his/her" | `lugal-la-ni` "his/her king" |
| 3SG.N | `-bi` "its" | `lugal-bi` "its king" |

`-ani` behaves like `-ak` — the `a` drops after a vowel-final stem:

```
lu₂-ni       (lu₂.ani)         "his man"
e₂-ni        (e₂.ani)          "her house"
lugal-la-ni  (lugal.ani)       "her king"     (consonant-final → auslaut + full -ani)
```

### 8.3 Possessive + case stacking: PNC order

Meadow's mnemonic — **P-N-C**:

> **P**ossession → **N**umber (plural) → **C**ase

```
lugal-zu-ne-ra
└── lugal . zu . ene . ra
    king  + your + PL + DAT       (the e of -ene elides after the u of -zu)
                                  "to your kings"
```

This order is rigid. Don't break it.

### 8.4 Enclitic copula `{-am₃}` (Meadow §101-3)

The reduced "to be" enclitic. The most common copular construction.

| Subject | Sumerian | English |
|---|---|---|
| 1SG | `-me-en` | "I am" |
| 2SG | `-me-en` | "you are" (sg) |
| 3SG / 3N | `-am₃` | "he/she/it is" |
| 3PL.H | `-me-eš` | "they are" |
| 1PL | `-me-en-de₃-en` | "we are" |
| 2PL | `-me-en-ze₂-en` | "you are" (pl) |

The enclitic stacks onto case marking:

```
canada-ta-me-en          "I am from Canada"           (-ta ABL + -men 1SG copula)
ensi₂-kam                "he is the ruler"            (-am₃ 3SG copula; /k/ from ensi₂.k surfaces)
sipa-da-am₃              "he is the shepherd"         (-am₃ after silent auslaut /d/)
ŋa₂-e-me-en              "it is I"                    (independent pronoun + copula)
```

For copular constructions outside Meadow's basic set, consult
`JAGERSMA_GRAMMAR.md` §13 or the temple-linked reference at
`https://sumerianastrology.com/sumerian-enclitic-copula/`.

There is also a true verb of being, `me` "to be" (§29.1 in Jagersma),
but the enclitic copula handles nearly all temple composition.

---

## 9. The verbal chain — orientation (Meadow §101-2, §101-4)

```
[modal] [conj-prefix] [IPP] [dim-prefix(es)] [FPP] STEM [PS / DO marker] [NOM -a]
```

This is the same nine-slot frame as Jagersma's, in Meadow's vocabulary:

| Slot | Position | Meadow's name | Example values |
|---|---|---|---|
| Modal | leftmost | "modal prefix" | `nu-`, `ga-`, `ḫa-`, `bara-`, `na-`, `u-` |
| Conjugation prefix | next | "conjugation prefix" | `mu-`, `ba-`, `i₃-` (vocalic) |
| Initial Person Prefix (IPP) | inside conj-prefix | "initial person prefix" | `e`, `n`, `b`, `mē`, ... |
| Dimensional prefix | next | "case marker (verbal chain)" | `-ra-` DAT, `-da-` COM, `-ta-` ABL, `-ši-` TERM, `-ni-` LOC, ... |
| Final Person Prefix (FPP) | just before stem | "final person prefix" | `n` (3SG.H), `b` (3N), `e` (2SG), ... |
| STEM | center | "verbal base" | `du₃`, `ŋen`, `aŋ₂`, ... |
| Person suffix or DO marker | after stem | "suffix" | `-en`, `-e`, `-eš`, `-ene`, `Ø` |
| Nominalizer | rightmost | "the -a" | `-a` (relative/temporal/complement) |

(Meadow doesn't enumerate the full ten slots Jagersma identifies — she
teaches "everything you need for prayers." For the full slot diagram
see `JAGERSMA_GRAMMAR.md` §8.1.)

### 9.1 The three conjugation prefixes (Meadow §101-3)

Every finite verb starts with **one** of these:

| Prefix | Function | When to use |
|---|---|---|
| `mu-` | **Ventive** — motion *toward* the speaker / deictic centre. Also "up" with extraction verbs. | When the action is oriented to the speaker, the king, or the temple. Royal inscriptions love this. With motion verbs: `ŋen` "go" → `mu-ŋen` "come". |
| `ba-` | **Non-human subject; middle / passive; change of state**. | For passives and inchoatives. `ba-úš` "he died (became dead)"; `ba-an-ru` "it was built". |
| `i₃-` | **Default vocalic prefix** — the unmarked elsewhere. | When neither ventive nor middle applies. Often what SVC gives by default. May surface as `in-` or `ib₂-` when an IPP is fused in. |

**Critical correction (Meadow's own retroactive fix).** A novice
composer often defaults to `mu-` because it's the most-seen prefix.
But `mu-` carries the ventive (motion-toward) semantics; for the verb
`ki—aŋ₂` "to love" with no spatial motion, the correct prefix is
`i₃-`:

```
ORIGINAL  (wrong)   ŋa₂-e za-e ki mu-aŋ₂-en           "I love you"
CORRECTED (right)   ŋa₂-e za-e-ra ki i₃-ra-aŋ₂        "I love you"
```

Two changes:
- `mu-` → `i₃-` (no motion-toward semantic).
- `za-e` → `za-e-ra` (the beloved is human-class → DAT `-ra`).
- Verbal chain `i₃-ra-aŋ₂`: `i₃` (default prefix) + `ra` (2SG IO
  marker, agreeing with `za-e-ra`) + `aŋ₂` (stem).

Meadow's added note: love is perfective by nature — *"You either love
or you do not love"* — so no imperfective marking. This is a worked
example of the temple's pragmatic perfective-as-default principle (§6.1).

### 9.2 Initial Person Prefixes (IPP) (Meadow §101-4)

Mark the person/class of the IO, OO, or comitative complement (NOT
the subject):

| Person | IPP form |
|---|---|
| 1SG | `÷` (unwritten / glottal) |
| 2SG | `e` |
| 3SG.H | `n` |
| 3N | `b` |
| 1PL | `mē` |
| 2PL | `(enē)` |
| 3PL.H | `nnē` |

IPP **inherits the vowel** of the preceding conjugation prefix when
spelled out — that's why `i₃-` often surfaces as `in-` or `ib₂-` in
SVC output. The /n/ or /b/ is the IPP; the /i/ is the conjugation
prefix.

### 9.3 Dimensional prefixes (Meadow §101-3) — case markers in the verbal chain

These cross-reference a case-marked noun in the same clause. **Always
agree** with the noun's case ending:

| Verbal-chain marker | Cross-refers to noun case | Meaning |
|---|---|---|
| `-ra-` | `-ra` | dative "to, for" (human) |
| `-da-` | `-da` | comitative "with" |
| `-ta-` | `-ta` | ablative "from" |
| `-ši-` | `-še₃` | terminative "to, toward" |
| `-ni-` | `-a` | locative "in" (note the surface difference between the noun case `-a` and the verbal-chain marker `-ni-`) |

Example:

```
lugal     uru -ta    ib₂                -ta             -ŋen
king      city-ABL   conj.+IPP (i₃+b)   ABL-marker      go
                                                        "The king walked away from the city."
```

The `-ta` on `uru` agrees with the `-ta-` in the chain. This
double-marking is the Sumerian way of saying "the ablative noun is
the one this 'from' refers to."

`-ni-` can also surface with a vowel pulled from the preceding
syllable: `ba-an-ŋen` is parseable as `ba-` + `-(n)ni-` (LOC marker
inheriting the `a` of `ba-` and dropping its own /i/) + `ŋen`.

### 9.4 Dative cross-reference forms (Meadow §101-3)

For `-ra` "to/for" dative, the verbal-chain marker comes in
person-specific forms:

| Person | Verbal-chain | English |
|---|---|---|
| 1SG | `ma-` (or `-ma-`) | "to me" |
| 2SG | `ra-` | "to you" |
| 3SG.H | `na-` | "to him/her" |
| 1PL | `-me-` | "to us" |
| 2PL | **???** | "to you (pl)" — form unknown / disputed |
| 3PL.H | `-ne-` | "to them" |

The 2PL DAT slot is **gapped in Meadow's source** — don't compose 2PL
DAT until you've verified the form against Jagersma (§17) or attested
texts.

### 9.5 Comitative cross-reference forms

`-da` "with" takes IPP-prefixed forms in the chain:

| Person | Form |
|---|---|
| 1SG | `Ø.da-` (often just `mu-da-`) |
| 2SG | `e.da-` (surfaces as `mu-e-da-`) |
| 3SG.H | `n.da-` (surfaces as `mu-un-da-`) |
| 3N | `b.da-` (surfaces as `mu-ub-da-`) |

Common in possession idioms: `nu-mu-da-tuku` "he does not have it"
(literally "it is not with him"). Sumerian expresses "to have" as
"X is with Y" — Y has X.

---

## 10. Perfective inflection (Meadow §101-4)

### 10.1 Perfective intransitive (S = subject)

S is marked by a **suffix** on the stem:

| Person | Suffix | Example |
|---|---|---|
| 1SG | `-en` | `i₃-ŋen-en` "I went" |
| 2SG | `-en` | `i₃-ŋen-en` "you went" |
| 3SG.H | `-Ø` | `i₃-ŋen` "she went" |
| 1PL | `-enden` | `i₃-re₇-en-de₃-en` "we went" |
| 2PL | `-enzen` | `i₃-re₇-en-ze₂-en` "you (pl) went" |
| 3PL.H | `-eš` | `i₃-re₇-eš` "they went" |

Verbal-number alternation: `ŋen` (SG) ~ `re₇` (PL). Use SVC to look
up the correct stem — many verbs have suppletive plurals.

### 10.2 Perfective transitive (A = agent, prefix)

A is marked by a **prefix** (FPP) before the stem:

| Person | Prefix | Example |
|---|---|---|
| 1SG | `Ø` (none) | `mu-gub` "I stood (it)" (`mu.0.gub`) |
| 2SG | `e` | `mu-e-gub` |
| 3SG.H | `n` | `mu-un-gub` "he/she stood (it)" |
| 3N | `b` | `mu-ub-gub` |
| 1PL | `Ø` + suffix `-enden` | `mu-gub-be-en-de₃-en` |
| 2PL | `e` + suffix `-enzen` | `mu-e-gub-en-ze₂-en` |
| 3PL.H | `n` + suffix `-eš` | `mu-un-gub-eš` "they stood (it)" |

**The "un" in `mu-un-du₃`** is `mu` (ventive) + `n` (3SG.H FPP). The
`u` of `un` is the vowel of `mu` being re-spelled to carry the
consonantal `n`. Sumerian has no bare-consonant sign, so the
syllabogram `un` does double duty.

### 10.3 Perfective reduplication

Stem reduplication on a perfective verb signals **plural object**
(transitive) or **plural subject** (intransitive). Distinguish from
imperfective reduplication (§11.2) by:

- The verb's stem morphology — if reduplication usually triggers a
  vowel change for imperfective (e.g. `naŋ` "drink" → IPFV `na₈-na₈`),
  then unchanged reduplication (`naŋ-naŋ`) signals **perfective**
  plural.
- The presence of other imperfective markers.

---

## 11. Imperfective inflection (Meadow §101-4)

Imperfective = present / future / ongoing / habitual. **Three**
strategies (which one a given verb uses is lexical — check SVC):

### 11.1 Form #1: Add `-e`

The most common. Append `-e` to the stem.

```
mu-un-du₃           "she built"           (PFV)
mu-un-du₃-e         "she will build it"   (IPFV: add -e)

mu-un-ḫul₂          "she rejoiced"        (PFV)
mu-un-ḫul₂-le       "she will rejoice"    (IPFV: add -e, auslaut -le)
```

### 11.2 Form #2: Reduplicate the stem

Some verbs go imperfective by reduplicating:

```
gi₄        →  gi₄-gi₄        "to return" → "is returning"
```

Some verbs reduplicate **with a stem alternation**:

```
naŋ        →  na₈-na₈        "to drink"  (alternation, not just doubling)
ŋar        →  ŋa₂-ŋa₂        "to place"  (alternation)
```

If reduplication produces *the same surface form* as the base, it
might be either perfective-plural or imperfective; if it produces
**alternation**, that's diagnostic of imperfective. SVC tells you
which.

### 11.3 Form #3: Change the verbal base (suppletion)

A few verbs have entirely different stems for the two aspects:

| Verb | PFV stem | IPFV stem |
|---|---|---|
| "to speak" | `du₁₁` / `dug₄` | `e` |
| "to go" | `ŋen` (SG) / `re₇` (PL) | `du` / `du-un` |
| "to die" | `úš` (SG) | `ug₇` / `ug-ug` (IPFV/PL) |

Always look up the correct stem in SVC before composing.

### 11.4 Imperfective transitive endings (A = agent, suffix)

Aspect swap: in IPFV, A is now a **suffix** (PS-B set), and DO is a
**prefix**:

| Person | Suffix | Example |
|---|---|---|
| 1SG | `-en` | `i₃-la₂-e-en` "I will hang" |
| 2SG | `-en` | `i₃-la₂-e-en` "you will hang" |
| 3SG.H | `-e` | `i₃-la₂-e` "she will hang" |
| 1PL | `-enden` | `i₃-la₂-en-de₃-en` |
| 2PL | `-enzen` | `i₃-la₂-en-ze₂-en` |
| 3PL.H | `-ene` | `i₃-la₂-e-ne` "they will hang" |

**Mnemonic**: *perfective = agent-prefix + DO-suffix; imperfective =
DO-prefix + agent-suffix.* The aspect **swaps the positions** of the
agreement markers.

### 11.5 Imperfective DO prefixes

In imperfective transitive, the DO is the prefix:

| Person | IPFV DO prefix | English |
|---|---|---|
| 1SG | `-n-` | me |
| 2SG | `-n-` | you (sg) |
| 3SG.H | `-e-` | him/her |
| 3SG.N | `-b-` | it |
| 1PL | **???** | us |
| 2PL | **???** | you (pl) |
| 3PL.H | `-ne-` | them |

1PL and 2PL imperfective DO prefixes are **gapped in Meadow's source**
— same caveat as the 2PL DAT.

---

## 12. Modal prefixes (Meadow §101-5)

These attach **before** the conjugation prefix and reshape
mood/polarity.

### 12.1 The three Meadow covers

| Prefix | Surface | Force |
|---|---|---|
| `nu-` | "no, not" | **Negative** — just negates the rest of the chain. |
| `ga-` | "let me, let us" | **Cohortative** — 1st-person volitional; always perfective. |
| `ḫa-` (`ḫe₂-`) | "let him/her, may it" | **Precative** — 2nd/3rd person wish, command, blessing. |

Examples:

```
nu-mu-un-du₃                "he/she will not build it"
ga-mu-un-du₃                "let me build it"
ḫe₂-mu-un-du₃               "may he build it" / "let him build it"
```

**Phonological reshaping** (modal prefixes are vowel-flexible):
- `nu-` → `la-` / `li-` before `ba-` or `bi₂-`.
- `ga-` → `gu-` before `mu-`; `gi₄-` before `bi₂-`.
- `ḫa-` → `ḫe₂-` before /i/-stems; `ḫu-` before `mu-`; `ḫa-ba-` with `ba-`.
- `nu-` cannot stack with `ga-` (would mean "not let me"); use the
  suppletive `ga-ra-` instead.
- `ga-` is the **only** modal that, when used by itself, can serve as
  a stand-alone negative too. Most can only modify a chain.

### 12.2 `bara-` — categorical negation

```
ba-ra-mu-un-du₃             "he will absolutely never build it"
```

`bara-` is **stronger** than `nu-` — it's the "never, by no means"
form. Often paired against `ḫa-` ("let him do X" ↔ "let him by no
means do X").

### 12.3 Siri Nin's extended modal cheat sheet

Beyond Meadow's three, Entu Siri lists the full attested inventory of
preformative modal prefixes:

| Sign | Sumerian | Force |
|---|---|---|
| 𒉌 | `i₃-` (vowel harmony) | vocalic preformative |
| 𒀀 | `a-` (vowel harmony) | vocalic preformative |
| 𒅇 | `u-` | **anterior** — "when X had done…", relative-past |
| 𒉡 | `nu-` | **negative** |
| 𒂵 | `ga-` | **cohortative** — "let me / let us" |
| 𒃶 | `ḫe₂-` | **precative** (2nd/3rd person, obligational impolite) |
| 𒉈 | `-de₃-` | **precative** (1st person, volitional polite) |
| 𒈾𒀭 | `nan-` | **prohibitive** — "should not, must not" |
| 𒈾 | `na-` | **affirmative** — "indeed, verily, definitely" |
| 𒁀𒊏 | `ba-ra-` | **negative affirmative** — "never, certainly not" |
| 𒅆 / 𒊭 / 𒊺 / 𒋗 | `ši-` / `ša-` / `šè-` / `šu-` | **contrapunctive** — "so, therefore, because" |
| 𒅔𒂵 | `inga-` | **additive** — "also, additionally" |
| 𒀭𒂵 | `anga-` | **additive** |
| 𒌦𒂵 | `unga-` | **anterior additive** — "also after" |
| 𒈬 | `mu-` | **ventive** — motion toward speaker |

Meadow's lessons cover the bolded core; the others are useful for
reading royal inscriptions where the full inventory shows up. SVC has
a dropdown for selecting modal prefixes and will adjust the surface
form automatically.

---

## 13. Compound verbs (Meadow §101-5)

A compound verb is **noun + verb**, with the noun functioning as the
verb's intrinsic direct object. The temple register relies heavily on
these for prayer and praise vocabulary:

| Compound | Literal | Idiomatic |
|---|---|---|
| `ki—aŋ₂` | "to measure the place" | **to love** |
| `gu₃—de₂` | "to pour out the voice" | **to speak, call out** |
| `igi—bar` | "to release the eye" | **to look at** |
| `inim—gi₄` | "to return the word" | **to answer, reply** |
| `šu—ti` | "to extend the hand" | **to receive** |
| `nam—tar` | "to cut the fate" | **to decree destiny** |

### 13.1 Possessive on the noun = agent

The compound's noun can take a possessive enclitic; this is how the
verb's agent is named:

```
igi-ŋu₁₀  in-ši-bar         "I looked at her"        (igi.my  ...)
igi-zu    in-ši-bar         "you looked at her"      (igi.your ...)
igi-ni    in-ši-in-bar      "she looked at him"      (igi.her ...)
igi-bi    in-ši-ib₂-bar     "they looked at her"     (igi.its / their)
```

The temple's elegant way to say "with my eye(s) / with your eye(s) /
with her eye(s)" without an English possessive-pronoun stack.

### 13.2 Oblique objects on compound verbs

When the compound's verb-part has its own further direct object — the
*thing being received*, *the person looked at* — it's marked as an
**oblique object**:

| Marking | Example |
|---|---|
| Locative-Terminative `-e` | `ŋeštin-e šu ba-an-ti` "he received wine" |
| Locative `-a` | `er₂-ra šu ba-an-ti` "she received tears" |
| Unmarked | `dub šu ba-an-ti` "she received the tablet" |

The choice is often lexical/idiomatic — check attested usage for a
given compound.

### 13.3 Auxiliary-verb construction (`ak` / `du₁₁`)

A stylistic variant: the **entire compound** appears outside the
verbal chain, and a generic auxiliary verb — `ak` "to do" or `du₁₁`
"to say" — carries the inflection.

```
e₂ ki us₂  mu-ak-e          "she will firmly establish the house"
└── (compound = "establish")  └── aux verb takes the chain
```

Meaning is unchanged; this is a register-shift, common in literary
and royal inscriptions.

---

## 14. Imperatives (Meadow §101-5)

To command:

1. **Move the stem to the FRONT** of the chain.
2. Suffix the stem with `-a` (the imperative marker, sometimes called
   the "pesky -a" — §5.5 item 4).
3. Optionally trail the remaining verbal-chain elements as **enclitic**
   to the imperative stem.

Examples:

```
šum₂-ma            "GIVE!"              (bare imperative)
šum₂-ma-ab         "GIVE IT!"           (with 3N.DO -ab)
ku₄-ra-ni-ib₂      "ENTER INTO IT!"     (stem ku₄ + ra IO + ni LOC + ib₂ 3N.DO)
```

When you compose a prayer of supplication — "give me X", "hear my
prayer", "look upon your servant" — use the imperative form to address
the deity directly.

---

## 15. Non-finite verb forms (Meadow §101-2, §101-5)

Verbs without a finite verbal chain. Three flavors:

### 15.1 Participial / passive `-a` (PFV)

Append `-a` to a perfective stem:

| Form | Meaning |
|---|---|
| `du₁₁-ga` | "giving" or "given, said" |
| `ŋar-ra` | "placing" or "set, placed" |
| `šum₂-ma` | "given" |
| `kug-ga` | "made-holy, holy" |
| `dab₅-ba` | "seized, captive" (`dumu dab₅-ba` "a captive son") |
| `e₃-a` | "(the) rising" (`{d}utu e₃-a` "the rising sun") |

This is the form behind both adjectives (§5) and passive participles.

### 15.2 Active participle / purpose `(-e)d` (IPFV)

The imperfective participle uses the imperfective base + `-e(d)`.
Surface variants:

| Spelling | Normalization |
|---|---|
| `-e` (after a vowel) | `.e(d)` — the d is silent |
| `-de₃` | `.ede` |
| `-da` | `.ede` (the `-a` is locative or further suffix) |
| `-dam` | `.edam` (with enclitic copula `-am₃`) |

Try translating as **"the one who…"** first; if that doesn't fit,
**"in order to…"**:

```
en  nam  tar-re-de₃         "the lord who decides fates"
                            (or: "the lord, in order to decide fates…")

e₂  du₃-de₃                 "the one who builds the temple"
                            (or: "in order to build the temple")

šum₂-mu                     "giving / about to give"
gi₄-gi₄                     "(the one) returning"
```

### 15.3 Subordinate clauses with `lu₂ … -a` (Meadow §101-5)

A common subordination strategy in the temple register: a relative
clause is wrapped between `lu₂` (literally "person, one") and a final
`-a` that closes the clause:

```
lugal  lu₂  mu-un-du₃-a   i₃-gub
"The king, the one who built the temple, stood."
       └── relative clause: "the one who built (it)" + closing -a
```

The closing `-a` is the **nominalizer** (the same one that makes
participles). This construction is your friend for any "X, who did Y"
phrasing in prayers. For the deeper grammar of nominalization-based
subordination (genitive, locative, terminative, ablative on the
nominalized verb), see `JAGERSMA_GRAMMAR.md` §11.

---

## 16. Composition workflow (temple register)

When you want to **write a prayer in Sumerian** from an English draft:

1. **Strip the English down to bare grammatical units.** Identify
   subject, direct object, indirect object (if any), verb, aspect
   (perfective default).
2. **Look up each content word in ePSD2** (or the temple's local
   glossary browser). Prefer entries with high `sense_count` and high
   `sense_pct` — the central meaning, not a fringe one. The MCP tool
   `translate_english` returns both.
3. **Try `find_compound` first** for verb-like phrases. Many English
   verbs map to compound nouns in Sumerian (`to look at` → `igi—bar`;
   `to love` → `ki—aŋ₂`; `to decree destiny` → `nam—tar`).
4. **Build the noun phrase in PNC order** (§8.3): noun + possessive +
   plural + case.
5. **Build the verbal chain** in slot order (§9): modal + conjugation
   prefix + IPP + dimensional prefix(es) + FPP + stem + suffix.
6. **Pick the conjugation prefix consciously** (§9.1):
   - `mu-` only if there's motion-toward or speaker-orientation.
   - `ba-` for passives, middles, or non-human subjects.
   - `i₃-` for everything else (most temple prayers).
7. **Cross-reference**: every dimensional prefix in the chain should
   agree with a case-marked noun in the clause (§9.3).
8. **Render with `cuneify`** to confirm the spelling has full sign
   coverage, and **`see_examples`** to find attested templates for
   similar compositions.
9. When in doubt about a verb's morphology, **consult the Sumerian
   Verb Conjugator (SVC)** linked from the temple's drive folder. It
   enforces correct slot ordering and stem alternation.
10. Carry **citations** when you cite a grammatical form back to a
    worshipper or student. Where this file disagrees with Jagersma,
    prefer Jagersma for academic correspondence and prefer Meadow for
    temple-internal usage.

---

## 17. Worked examples from the temple

### 17.1 Temple dedication formula

```
šar  {d}inanna  -ra
all  Inanna     -DAT
"All — for Inanna."

šar . {d}inanna . ra        (normalization)
```

The dedication that opens many temple compositions. `-ra` because
Inanna is human-class (divine).

### 17.2 First-line invocation

```
{d}inanna  ki-aŋ₂  -ga  -ŋu₁₀   diŋir-nin
Inanna     love    -ADJ -my     goddess-queen
                  (verb 'to love' + -a → adjective 'beloved' + 1SG possessive)
"Inanna, my beloved, the goddess-queen."
                                                  (after Meadow §101-1)
```

Slot-by-slot:
- `ki-aŋ₂` "to love" (compound verb)
- `-ga` adjective-forming `-a` with auslaut `-ga` (from the `g` of
  `aŋ₂`'s root — see §3.3 ŋ↔g discussion; the temple convention is
  `-ga`)
- `-ŋu₁₀` 1SG possessive "my"
- `diŋir-nin` "goddess-queen" (compound noun)

### 17.3 First-person declaration of love (corrected form)

```
ŋa₂-e      za-e   -ra      ki      i₃   -ra   -aŋ₂
I          you    -DAT     place    DEF-pfx 2SG-DAT  measure
                                          (= compound 'love')
"I love you."                                            (Meadow §101-1, corrected)
```

- `ŋa₂-e` "I" (independent pronoun)
- `za-e-ra` "to/for you" (2SG pronoun + dative — beloved is human-class)
- `ki i₃-ra-aŋ₂`: compound verb `ki—aŋ₂` "love", with chain:
  - `i₃-` default vocalic prefix (NOT `mu-` — no motion-toward)
  - `-ra-` 2SG dative cross-reference (agrees with `za-e-ra`)
  - `-aŋ₂` stem

Perfective by nature — see §9.1 for the correction commentary.

### 17.4 Royal-inscription line

```
lugal-e    e₂      mu-un-du₃
"The king built the temple."
```

Slot-by-slot:
- `lugal-e` king + ergative `-e` (transitive subject)
- `e₂` house/temple, absolutive (no marker, direct object)
- `mu-un-du₃` verbal chain:
  - `mu-` ventive (action oriented toward the speaker / deictic centre)
  - `-un-` = `-n-` FPP 3SG.H (the king) wrapped in `-u-` of `mu-`
  - `-du₃` stem 'to build' (perfective by default)

Cuneify: `lugal-e` → 𒈗𒂊; `e₂` → 𒂍; `mu-un-du₃` → 𒈬𒌦𒆕.

### 17.5 Plural address to one's kings

```
lugal      -zu    -ne   -ra
king        2SG    PL    DAT
"to your kings"               (PNC order: P=zu, N=ene→ne, C=ra)
```

The `e` of `-ene` elides after the `u` of `-zu`, leaving `-ne-`. Pure
mechanics; no semantic content lost.

### 17.6 Going away from the city

```
lugal     uru -ta    ib₂                -ta    -ŋen
king      city-ABL   conj.+IPP (i₃+b)   ABL-mk go
"The king walked away from the city."           (Meadow §101-3)
```

The `-ta` on `uru` and the `-ta-` in the chain are the two halves of
one ablative meaning — both required, both agreeing.

### 17.7 Compound verb with possessive agent

```
igi-ni   in-ši-in-bar
eye-her  conj.+IPP-TERM-FPP-release
"She looked at him."           (Meadow §101-5)
```

- `igi-ni` "her eye" (3SG.H possessive on the compound's noun → she
  is the agent)
- `in-` `i₃-` + IPP `n` (3SG.H referent — *him*, the one looked at)
- `-ši-` terminative dimensional prefix (cross-references where the
  TERM-marked NP would be)
- `-in-` FPP 3SG.H (agent — *she*, redundantly marked with the
  possessive on `igi`)
- `-bar` stem 'release'

### 17.8 Imperative

```
šum₂-ma-ab
"GIVE IT!"
```

- `šum₂` stem 'give', moved to the front of the chain
- `-ma-` imperative marker `-a` carrying `mu-`'s `u` flipped to `a`
  (or simply the imperative `-a`)
- `-ab` 3N.DO 'it'

A common form in prayers of supplication: "give me this, hear me,
look upon me."

---

## 18. Where this document and the academic file disagree

Meadow openly invites correction:

> If you are studying Sumerian yourself, and you reckon I made a
> mistake, please always let me know.

So: when **temple practice** and **academic grammar** diverge, what
governs?

- **For temple composition** (prayer, dedication, in-house liturgy):
  follow this file. The temple has its own register; consistency
  within that register matters more than academic correctness in a
  fringe form.
- **For reading attested texts** (royal inscriptions, ETCSL literary
  corpus, administrative tablets): defer to `JAGERSMA_GRAMMAR.md`
  (Jagersma). The attested forms are what they are; the temple grammar
  is a learned subset.
- **When in conflict**: `JAGERSMA_GRAMMAR.md` is normative for the
  data; this file is normative for **how the temple chooses to
  compose new Sumerian**.

A non-exhaustive list of points where the two diverge or have
different emphasis:

| Topic | This file (Meadow / Siri) | `JAGERSMA_GRAMMAR.md` (Jagersma) |
|---|---|---|
| Number of cases | 8 + ergative + absolutive | 12 (incl. adverbiative, locative₂, equative-distinguished) |
| Conjugation prefix taxonomy | 3 (`mu` / `ba` / `i₃`) as the day-to-day frame; Siri's full chart is an extended reading aid | 3 vocalic preformatives + 5 modal preformatives separately, in distinct slots |
| ŋ-auslaut spelling | Convention `-ga` (Meadow's source); `-ŋa₂` also attested (Siri's note) | Both attested; period-conditioned, no strong normative claim |
| Aspect frame | "Past tense" vs "present/future tense" — pragmatic English-style | Perfective vs imperfective with all the attendant Krecher-style non-temporal uses (states, timeless truths) |
| Default period for examples | Mixed, mostly New Sumerian / Ur III | ED (Old Sumerian, ~24–25th c.) — Jagersma's primary ground |
| Treatment of `mu-` | "Ventive (motion toward) — also indicates animate subject" was Meadow's original framing; later corrected to ventive-only | Ventive-only (§22.3); the *animacy* interpretation is a common novice error |
| 2PL DAT / 1PL & 2PL IPFV DO prefixes | **Gapped** — explicitly unknown | Filled in from attested forms (§13, §17) |

The "Mu indicates an animate subject" reading is **explicitly retracted
by Meadow** in her own §101-1 correction (the same one that fixes
`mu-aŋ-en` to `i₃-ra-aŋ`). Do not propagate it.

---

## 19. Acknowledgments

- **Meadow** — author of the Sumerian 101 lecture series, 5 lessons,
  classroom-e₂-nun-na, Spring 2025. Source: classroom transcripts
  dumped 2026-05-12 from Discord channel
  `#classroom-e₂-nun-na-𒂍𒉣𒈾`.
- **Entu Siri Nin** — corrections, the extended modal-prefix cheat
  sheet, the Emesal exposition, and the period/source disclaimers
  threaded throughout.
- **Bram Jagersma** — *A Descriptive Grammar of Sumerian* (PhD diss.,
  Universiteit Leiden, 2010, 776 pp). The academic backbone the
  temple's SVC tooling is built on.
- The **Inanna temple community** — for hosting the classroom and
  asking the questions that drove the lessons.

For the academic reference, see `lessons/JAGERSMA_GRAMMAR.md`. For
tools to use this grammar in practice, call `start_here()` on each
eme-gir-* MCP server (especially `eme-gir-ummia` for the teaching
workflow and `eme-gir-epsd2` for the dictionary lookups).

---
