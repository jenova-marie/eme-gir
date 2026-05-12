# Sumerian grammar cheat sheet

Comprehensive reference for English ↔ Sumerian translation. Distilled
from **Bram Jagersma, *A Descriptive Grammar of Sumerian*** (PhD
dissertation, Universiteit Leiden, 2010, 776 pp). Section numbers in
the form `(Jagersma §N.M)` point back to Jagersma 2010 for verification.

**Scope.** Jagersma describes Sumerian as documented in third-millennium
texts (~2500–2000 BCE). Within that, **Old Sumerian (= Early Dynastic
IIIa–IIIb, 24–25th centuries BCE)** is the primary descriptive ground,
because earlier texts spell too few morphemes and later texts (Old
Babylonian onward) are by non-native scribes. **This document treats ED
as the default register.** Variants for Lagash II, Ur III, and Old
Babylonian Sumerian are noted as period sidebars where they differ.

**Size note.** This reference is ~30 KB and assumes a model with a
large context window. If you only need a quick orientation, start with
§4 (case system) and §8 (verbal slots).

**Conventions used.** Oracc / ePSD2 transliteration throughout
(subscript digits for sign-value disambiguation; `ŋ` for /ŋ/; `ḫ` for
/x/; determinatives in braces like `{d}inanna`). See
`prompt/JAGERSMA_CONVENTIONS.md` for the full notation map between
Jagersma's linguistic transliteration and Oracc.

---

## 1. Periods and dialect

| Period | Centuries BCE | Conventional name | Jagersma's name |
|---|---|---|---|
| Fara | 26th | Early Dynastic IIIa | Fara |
| Old Sumerian (early) | 25th | Early Dynastic IIIa late | Old Sumerian |
| Old Sumerian (late) | 24th | Early Dynastic IIIb | Old Sumerian |
| Old Akkadian | 23rd | Sargonic | Old Akkadian |
| Gudea | 22nd | Lagash II | Gudea |
| Ur III | 21st | Third Dynasty of Ur | Ur III |
| Old Babylonian | 19th–17th | post-vernacular | OB Sumerian |

Two dialect areas (Jagersma §1.2.3):
- **Southern**: Lagaš, Umma, Ur — the bulk of the descriptive corpus.
- **Northern**: Nippur, Adab, points north — diverges in the use of
  the vocalic preformative {÷a}, which becomes a passive marker in
  the Northern dialect (§24.5).

**Default period for translation, when unspecified: ED (Early Dynastic,
~2900–2350 BCE).** This is Jagersma's primary descriptive ground.

---

## 2. Transliteration conventions (Oracc, normalized from Jagersma)

- **Lowercase** = phonetic reading of a sign (`lugal` = the spoken word).
- **UPPERCASE** = sign name when no phonetic value is given (`LUGAL` is
  the cuneiform sign whose value is `lugal`, used as a logogram).
- **Hyphen** `-` joins signs that make up one Sumerian word: `lu₂-gal`.
- **Period** `.` separates parts of a compound grapheme: `AB.GAR`.
- **Braces** `{...}` mark **determinatives** (silent classifier signs):
  - `{d}` divine — before god names: `{d}inanna`, `{d}en-lil₂`
  - `{ki}` place — after place names: `unug{ki}`, `lagas{ki}`
  - `{ŋeš}` wood — before wooden objects: `{ŋeš}gigir` 'chariot'
  - `{kuš}` leather — `{kuš}lu-ub₂` 'leather bag'
  - `{na₄}` stone — `{na₄}za-gin₃` 'lapis lazuli'
  - `{mušen}` bird (post-determinative) — `lugal{mušen}` 'a bird-name'
  - `{munus}` female — `{munus}lukur` 'priestess'
- **Subscripts** distinguish homophones (different signs, same phonetic
  shape): `lu`, `lu₂`, `lu₃`, …; `du`, `du₂`, `du₃`, `du₁₁`, …
- **`ŋ`** = velar nasal /ŋ/ (Jagersma's `ĝ`; ETCSL `j`). Oracc preferred.
- **`ḫ`** = velar/uvular fricative /x/ (Jagersma typesets `h~`).
- **`š`**, **`ṣ`**, **`ṭ`** = palatal fricative, emphatic /s/, emphatic /t/.
- **Sumerian alphabetical order**: A, B, D, E, G, **Ŋ**, **Ḫ**, I, K, L,
  M, N, P, R, S, **Ṣ**, **Š**, T, **Ṭ**, U, Z. (Ŋ sorts between G and Ḫ.)

The transliteration here always uses **subscript digits** for sign
disambiguation. Legacy accent forms (`dú` for `du₂`, `dù` for `du₃`)
are equivalent but normalized away by Oracc tooling.

---

## 3. Phonology essentials (Jagersma ch. 3)

Useful for **suffix peeling** and ambiguity resolution.

### 3.1 Consonant inventory (Jagersma §3.1)

| Series | Bilabial | Coronal | Velar | Glottal |
|---|---|---|---|---|
| Voiceless aspirated stops (§3.2.2) | /p/ | /t/ | /k/ | — |
| Plain voiceless stops (§3.2.3) | /b/ | /d/ | /g/ | /÷/ glottal stop |
| Affricates (§3.3) | — | /z/, /ř/ | — | — |
| Fricatives (§3.4) | — | /s/, /š/ | /ḫ/ | /h/ |
| Nasals (§3.5) | /m/ | /n/ | /ŋ/ | — |
| Liquids / glide | — | /l/, /r/ | /j/ | — |

### 3.2 Vowels (Jagersma §3.9)

Four short: /a, e, i, u/. Four long: /ā, ē, ī, ū/ (independent phonemes
per spelling pair `da` vs `da-a`, §3.1, §3.9.2).

### 3.3 Crucial sound rules for parsing

- **Syllable-final aspirated stops are usually lost** (Jagersma §3.2.2).
  This affects `ak` 'make' (genitive marker `{ak}`, verb stem `ak`),
  `lu₅.k` 'live', `ka.k` 'mouth', `ensi₂.k` 'ruler'. The final /k/ is
  visible only when followed by a vowel (`ensi₂-ke₄` = `ensi₂.k=e`).
- **`{ak}` genitive** has surface forms `=ak`, `=a`, or completely
  unwritten depending on context (Jagersma §7.2.1–7.2.2). By Ur III
  the syllable-final /k/ is gone; in Old Sumerian it was reduced to
  /h/.
- **`{ta}` ablative-prefix** intervocalic /t/ → /r/ in Gudea+ texts
  (Jagersma §19.3.1): `ba-ta-zal` ~ `ba-ra-zal` 'it passed by'. This
  is phonological, not a different morpheme.
- **/r/ ≈ /d/** word-finally → scribal confusion between dative `{ra}`
  and comitative `{da}` after a vowel; the LANGUAGE doesn't substitute
  them, the SCRIBES do (Jagersma §7.11.1).
- **Old Sumerian vowel harmony** (Jagersma §3.9.3): in Old Sumerian
  the vocalic prefix surfaces as /e/ when followed by a syllable with
  /e/. Disappears by Ur III — a dating signature.
- **Syllable structure is strictly CV(C)** (Jagersma §3.10). No cluster
  syllables.
- **Stress on the final syllable of the phonological word**
  (Jagersma §3.11). Drives word-initial vowel elision in long words:
  `eden=ak` → `dè-na` 'of the plain'.

---

## 4. The case system (Jagersma ch. 7)

Sumerian has **twelve enclitic cases**. Each marker attaches to the
**last word of the noun phrase**. When NPs nest, markers stack on the
phrase-final word.

### 4.1 Inventory

| Case | Marker | Surface | Glose | Primary use |
|---|---|---|---|---|
| Absolutive | Ø | (nothing) | ABS | DO of transitive; S of intransitive (§7.4) |
| Ergative | `{e}` | `-e` after C; Ø after V | ERG | A (transitive subject) (§7.3) |
| Genitive | `{ak}` | `-ak`, `-a`, or hidden | GEN | possessor, "of" (§7.2) |
| Dative | `{ra}` | `-ra` after C, `-r` after V | DAT | HUMAN indirect object (§7.5) |
| Directive | `{e}` | `-e` after C, Ø after V | DIR | NON-HUMAN IO; oblique target (§7.6) |
| Locative | `{÷a}` | `-a` | LOC | "in, on" (§7.7) |
| Locative₂ | `{ne}` | `-ne` | LOC2 | rare alternative locative (§7.7.2) |
| Terminative | `{še}` | `-še` after C, `-š` after V | TERM | "to(ward), for, because of" (§7.8) |
| Adverbiative | `{eš}` | `-eš` | ADV | "in the manner of" (§7.9) |
| Ablative | `{ta}` | `-ta` | ABL | "from, out of" (§7.10) |
| Comitative | `{da}` | `-da` after C, `-d` after V | COM | "with" (§7.11) |
| Equative | `{gen}` | `-gen` / `-gin₇` | EQU | "like, as" (§7.12) |

### 4.2 Ergative-absolutive alignment (§11.4.3)

Sumerian **case marking is fully ergative**: the transitive subject
(A) is in the ergative; the intransitive subject (S) and the direct
object (DO) are both in the absolutive (Ø).

```
gu₃-de₂-a-Ø     ĝen     →  Gudea went           (Gudea=ABS  + intransitive verb)
gu₃-de₂-a-e     e₂      mu-řú  →  Gudea built the house    (Gudea=ERG + DO=ABS + V)
```

### 4.3 Surface ambiguity table (load-bearing for `parse_phrase`)

| Surface ending | Possible cases | Resolution heuristic |
|---|---|---|
| `-e` after C | ERG, DIR | Check the verb's coreferent prefix: ERG ↔ final person-prefix; DIR ↔ oblique-object prefix or local `{e}` prefix (Jagersma §7.3, §7.6) |
| Ø after V | ERG, DIR | Same as above; also could be ABS — fall back on clause role |
| `-a` | LOC, GEN (post-Ur III after /k/ loss), NOM (verb suffix `{÷a}`) | NP-internal context: is it post-verbal stem (NOM)? after a noun (LOC or GEN)? In a stacked NP-final position (GEN)? |
| `-ne` | LOC2 (rare), plural `{enē}` (after vowel) | If the noun is human, prefer plural; otherwise LOC2 |
| `-še` | TERM only | unambiguous |
| `-ta` | ABL only | unambiguous |
| `-da` | COM only | (scribes sometimes write `=ra` for `=da` after vowel — Jagersma §7.11.1) |
| `-gin₇` / `-gen` | EQU only | unambiguous |

### 4.4 Detailed case notes

**Genitive `{ak}` (§7.2).** The /k/ of `{ak}` is only written before a
vowel. Otherwise it's reduced. By Ur III the marker is just `=a` before
a consonant (Jagersma §7.2.1). Double and triple genitives are common
when NPs nest:

```
[mu [ensi₂.k [ĝir-su{ki}=ak]=ak]=še]
'because of (lit. "for the name of") the governor of Girsu'
mu  ensi₂  ĝir-su{ki}-ka-še        # surface form
                                   # (Jagersma §7.1 ex. 1; D; 21)
```

**Ergative `{e}` vs Directive `{e}`.** These are homophonous after a
consonant. Disambiguate by:
1. The clause's transitivity (ERG only with transitive verbs).
2. The verbal coreference: ERG co-occurs with a FINAL person-prefix
   marking the A; DIR co-occurs with an OBLIQUE-OBJECT prefix (ch. 18)
   or the local prefix `{e}` 'on' (§20.3).
3. Semantics (target/recipient vs agent).

**Dative `{ra}` vs Directive `{e}`.** A clean human/non-human split:
- `{d}en-lil₂-ra` 'to Enlil' (human → DAT) — corefers with IO-prefix `{nna}`.
- `e₂-e` 'to the house' (non-human → DIR) — corefers with OO-prefix `{nni}` or local `{e}`.

**Locative `{÷a}`.** Spelled simply `-a`. Coreferent with the local
prefix `{ni}` in the verb (§20.2). Distinguish from genitive `-a` and
the nominalizer `-a` by NP-internal vs verb-internal position.

**Terminative `{še}` vs Adverbiative `{eš}`.** Both are translatable
"for/as" in some contexts but morphologically distinct: `-še` after
consonant ("for X, toward X"); `-eš` invariant ("in the manner of X").

**Comitative `{da}` vs Ablative `{ta}`.** Both have invariant `-da` /
`-ta` forms. `{da}` 'with' corefers with the comitative verbal prefix
`{da}` and is heavily used in possession constructions ("X is with Y" =
"Y has X").

### 4.5 Possessor and case stacking

Order on NP: `[noun] [adjective] [genitive NP] [possessive] [demonstrative] [plural-{enē}] [case marker]`

Examples:
```
lugal kalag-ga             'the strong king'
e₂ lugal-la-na             'in the house of his king'   (e₂ lugal=ak=ane=÷a)
dumu-ne-ne-er              'to their children'          (dumu=anēnē=ra)
ud₅ sipa-da-ke₄-ne         'of the goat shepherds'      (ud₅ sipa.d=enē=ak=e — §7.2.1 ex. 8)
```

---

## 5. Noun phrase structure (Jagersma ch. 5–6)

### 5.1 Genders (Jagersma §6.2)

Two genders:
- **Human**: humans + deities (including divine objects)
- **Non-human**: everything else

The gender of the noun controls:
- Choice of plural marking
- Choice of pronoun (3SG.H vs 3N)
- Choice of case marker for IO (DAT for human, DIR for non-human)
- Choice of verbal person prefix (`{n}` vs `{b}` for 3SG)

### 5.2 Plural

- **Human plural**: enclitic `{enē}`, surface `-(e)-ne`. Position:
  between possessive and case.
- **Non-human plural**: NO plural marker. Expressed by reduplication
  of the noun (`kur-kur` 'foreign lands'), by quantifiers, or left
  contextually understood.

### 5.3 Modifiers

- **Adjectives** follow the noun (Jagersma §10.4.1): `lugal kalag-ga`
  'strong king'. (Historical shift toward N-Adj order may be Akkadian
  contact, §10.4.1.)
- **Genitive NPs** follow the head: `e₂ lugal=ak` 'house of the king' →
  surface `e₂ lugal-la`.
- **Possessive enclitics** between noun and plural/case.
- **Demonstratives**: `{be}` 'this/that' is an enclitic; `ne-en`
  'this' and `ur₅` 'that' are independent (Jagersma §8.4).

### 5.4 Compound nouns (Jagersma §6.5)

- **N + N**: `e₂-maš` 'sheepfold' (lit. 'house-goat'); `ki-šár` 'horizon'
- **N + Adj**: `lugal-zid` 'true king'
- **Coordinative**: `an-ki` 'heaven and earth'
- **N + participle**: highly productive — `lugal-zi-il-la` 'the
  raising king', `dumu dab₅-ba` 'a captive son' (lit. 'taken son')

### 5.5 Proper names

Sumerian names are often clauses: `ur-{d}namma` 'Servant-of-Namma',
`lugal-an-da` 'King-with-An'. They still inflect:
`lugal-an-da-ke₄` 'King-Anda did X'.

---

## 6. Pronouns (Jagersma ch. 8)

### 6.1 Independent personal pronouns (§8.2)

Used for emphasis; uncommon in flowing text.

| Person | Form |
|---|---|
| 1SG | `ĝa₂-e` / `ĝe₂₆` |
| 2SG | `ze₂` |
| 3SG.H | `e-ne` |
| 1PL | `me-en-de₃-en` |
| 2PL | `me-en-ze₂-en` |
| 3PL.H | `e-ne-ne` |

There is **no independent 3N pronoun** — context or the demonstrative
`{be}` fills the role.

### 6.2 Possessive enclitics (§8.3)

| Person | Singular | Plural |
|---|---|---|
| 1 | `-ĝu₁₀` 'my' | `-me-en-de₃-en` 'our' (`{meanēnē}`) |
| 2 | `-zu` 'your' | `-me-en-ze₂-en` 'your' (`{zunēnē}`) |
| 3.H | `-(a)-ni` 'his/her' (`{ane}`) | `-(a)-ne-ne` 'their' (`{anēnē}`) |
| 3.N | `-bi` 'its' (`{be}`) | — (no 3N plural) |

Order: `noun = possessive = (plural-{enē}) = case`.

### 6.3 Demonstrative (§8.4)

- Enclitic `{be}` 'this/that' — doubles as 3N possessive 'its' and
  serves the role of a definite article.
- Independent `ne-en` 'this', `ur₅` 'that'.

### 6.4 Interrogatives (§8.5)

`a-ba` 'who?' (human), `a-na` 'what?' (non-human), `me-a` 'where?',
`me-na` 'when?'.

### 6.5 Indefinite and reflexive (§8.6, §8.7)

- `lu₂ na-me` 'anyone' / 'someone'; `niĝ₂ na-me` 'anything'.
- Reflexive: `ni₂` + possessive: `ni₂-ĝu₁₀` 'myself', `ni₂-(a)-ni`
  'himself'.

---

## 7. Numerals (Jagersma ch. 9)

**Sexagesimal**: base 60. Resets at 60 (`ĝeš`), 3600 (`šar₂`), 36000
(`šar₂-u`).

| Number | Sumerian |
|---|---|
| 1 | `aš`, `dili`, `diš` |
| 2 | `min` |
| 3 | `eš₅` |
| 4 | `limmu` |
| 5 | `ia₂` |
| 6 | `aš₃` |
| 7 | `imin` |
| 8 | `ussu` |
| 9 | `ilimmu` |
| 10 | `u` |
| 60 | `ĝeš` (or `ĝeš₂`) |
| 600 | `ĝeš-u` |
| 3600 | `šar₂` |

70 = `ĝeš-u` ('60-10'); 100 = `ĝeš nimin` ('60-40'); 360 = `limmu ĝeš`
('4-60').

**Cardinals follow the noun**: `lugal min` 'two kings', `gud limmu`
'four oxen' (§9.3.1).

**Ordinals**: cardinal + `=kamma` (or `-kam`): `min-kam-ma` 'second',
`eš-kam-ma` 'third' (§9.4).

**Fractions** (§9.5): `igi-X-ŋal₂` 'one X-th' (literally "having X
eyes"); `šu-ru-a` = 1/2.

---

## 8. The finite verb (Jagersma ch. 11–25; appendix p. 743)

### 8.1 The slot template

The finite Sumerian verb has up to **nine prefix slots** + STEM + up to
**three suffix slots** (Jagersma §11.2.2; appendix p. 743):

```
[PREFM₁ proclitic]    [PREFM₂ prefix]    [{nga}]    [VENT {mu}]
   ↓                     ↓                  ↓           ↓
   nu / ḫa             ÷i / ÷a / ÷u /     'also'    mu  /  m
                       na(n) / ga /                   /  ma
                       bara / ši / na

[{ba}]    [IPP]                          [DIM block]                  [FPP]
   ↓        ↓                                ↓                           ↓
   ba    ÷ / e / n / b /                  IO marker (a/ra)             ÷ / e
         mē / enē / nnē                   {da}, {ta}, {ši}             n / b
                                          local {ni} / {e}

STEM   [{ed} IPFV]   [Person suffix Set A or B]   [NOM {÷a}]
                       ↓
                       en / Ø / e / enden /
                       enzen / eš / enē
```

**Boxes/columns are mutually exclusive** within their slot. Exception:
preformatives `{nu}` and `{ḫa}` can co-occur with `{÷i}` (and perhaps
`{÷a}`) (appendix p. 743 note).

### 8.2 Slot 1: preformatives

Every finite verb form has a **preformative**. The four functional
groups (Jagersma §11.2.2, §24, §25, §26):

#### 8.2.1 Vocalic preformatives (Jagersma ch. 24)

| Preformative | Surface | Function |
|---|---|---|
| `{÷i}` | `i-` / `ì-` / Ø before CV | **Default** — neutral preformative; almost every finite verb has it when no other applies (§24.3.2) |
| `{÷a}` | `a-` / `àm-` / Ø | In **Northern** dialect: passive in perfective forms (§24.5.2); in **Southern**: nearly absent |
| `{÷u}` | `u-` / `ù-` | **Relative past**: "when X had done ..."; marks one clause as temporally prior (§24.2) |

Surface forms collapse to zero before consonant clusters, but are
RETAINED before the cluster `/mC/` (e.g. before reduced ventive
`m-da-`): `ì-im-da-tuš` 'a stonecutter was on duty with it' (§22.2 ex.
22). This is one of the diagnostic patterns for which preformative is
present.

#### 8.2.2 Modal / negative preformatives (Jagersma ch. 25)

| Preformative | Form | Function |
|---|---|---|
| `{nu}` | `nu-` | Plain negation (§25.2) |
| `{ḫa}` | `ḫe₂-` / `ḫa-` | Affirmative, optative ("let X, may X"), 1/3rd command (§25.4) |
| `{ga}` | `ga-` | 1st-person volitional ("let me, let us") (§25.6) |
| `{na(n)}` | `na-` / `nan-` | Negative modal ("must not") (§25.5) |
| `{bara}` | `bara-` | Strong negation regardless of mood ("by no means, never") (§25.7) |

#### 8.2.3 The imperative (§25.3)

Distinctive structure:
- The **stem comes first** in the form.
- All affixes that would normally precede the stem are placed AFTER it.
- Plural imperative adds `{zen}` after the stem.

```
du₃                      'do!'           (SG)
du₃-ze₂-en               'do!'           (PL)
ku₄-ra-ni-ib₂            'enter into it' (with dimensional + person)
```

#### 8.2.4 Rare preformatives `{ši}` and `{na}` (§26)

Both poorly understood; rarely encountered. `{ši}` may be focal;
non-negative `{na}` may be affirmative.

### 8.3 Slot 2: prefix `{nga}` 'also' (Jagersma ch. 23)

Rare; means roughly 'also, too' or 'in addition'. Co-occurs with
negation: `nu-ga-ma-X` = NEG-also-1SG.IO-... (§23 ex. 4).

### 8.4 Slot 3: ventive prefix `{mu}` (Jagersma ch. 22)

Marks action **oriented toward the speaker** or the deictic centre.

**Forms.** `mu-` is the basic form. The /u/ is lost when followed by
the consonant slot: `mu-da-` → reduced `m-da-` (written `im-da-` after
the vocalic prefix, §22.2). Also `ma-` before some IO prefixes.

**Semantics (§22.3).**
- With motion verbs: 'come' rather than 'go'. `mu-ĝen` 'he came' vs
  `ĝen` 'he went'.
- With other verbs: directional/affective overlay — the action affects
  or is oriented to the speaker / king / deictic centre.
- Very common in royal inscriptions (Gudea cylinders) where the
  king is the deictic centre.

**Constraint**: cannot co-occur with the initial person-prefix `{b}`
(§22.4).

### 8.5 Slot 4: prefix `{ba}` (Jagersma ch. 17, 21)

`{ba}` has two functions:
1. **3N indirect-object prefix** (ch. 17): "for it, for that thing".
2. **Middle marker** (ch. 21): indirect reflexive ("for himself"),
   change of state (inchoative), or **passive** (the most common
   Sumerian passive).

Disambiguation: if `{ba}` is followed by a dimensional prefix, it's the
IO-prefix; if it's directly before the stem (or only with FPP), it's
the middle marker.

### 8.6 Slot 5: initial person-prefixes (Jagersma ch. 16)

Mark the gender/person/number of the IO, OO, or comitative complement.

| IPP | Person |
|---|---|
| `{÷}` | 1SG |
| `{e}` | 2SG |
| `{n}` | 3SG.H |
| `{b}` | 3N |
| `{mē}` | 1PL |
| `{enē}` | 2PL |
| `{nnē}` | 3PL.H |

The IPP is almost always followed by a dimensional prefix that
specifies the relational meaning. The local prefix `{ni}` 'in' is the
exception — it is NEVER preceded by an IPP (§16.2, §20.2).

### 8.7 Slot 6: dimensional prefixes (Jagersma ch. 17–20)

A finite verb can contain **0 to 4 dimensional prefixes** (§11.2.2).
They are cognate with the case markers (§4) and refer to participants
with case-marked NP coreferents.

#### 8.7.1 Indirect-object prefixes (IO; ch. 17)

| Prefix | Form | Person |
|---|---|---|
| `{ba}` | `ba-` | 3N.IO |
| `{nna}` | `n-na-` | 3SG.H.IO |
| `{nnē}` ~ `{nnē÷a}` | `nnē-` / `nnē-a-` | 3PL.H.IO |
| `{ra}` | `r-a-` | 2SG.IO |
| `{ma}` | `m-a-` | 1SG.IO |
| `{mē}` ~ `{mē÷a}` | `mē-` | 1PL.IO |

Coreferent: an NP in DAT (human) or DIR (non-human). The recipient or
beneficiary.

#### 8.7.2 Oblique-object prefixes (OO; ch. 18)

| Prefix | Form | Person |
|---|---|---|
| `{bi}` / `{b}` | `bi-` / `b-` | 3N |
| `{nni}` / `{n}` | `n-ni-` / `n-` | 3SG.H |
| `{ri}` / `{e}` | `ri-` / `e-` | 2SG |
| `{mu}` / `{÷}` | `mu-` / `÷-` | 1SG (reuses ventive form) |

Coreferent: an NP in DAT (human) or DIR (non-human), same as IO. The
distinction is the **verbal prefix**, not the NP case. Uses:
- **Causative** (§18.3.2): "X made Y do Z", with Y in DAT/DIR.
- **"In(to) contact with"** location (§18.3.3): "place X on Y", "put X
  into contact with Y".

IO and OO are mutually exclusive (§18.4).

#### 8.7.3 {da}, {ta}, {ši} (ch. 19)

| Prefix | Meaning | Coreferent NP case |
|---|---|---|
| `{da}` | 'with' | COM |
| `{ta}` | 'from' | ABL |
| `{ši}` | 'to, toward' | TERM |

`{ta}` becomes /ra/ between vowels in Gudea+ texts (§19.3.1).

`{da}` is heavily used in possession constructions: `nu-mu-da-tuku` 'he
does not have it' = lit. "it is not with him" (§19.2 ex.).

#### 8.7.4 Local prefixes (ch. 20)

| Prefix | Meaning | Coreferent NP case |
|---|---|---|
| `{ni}` | 'in' | LOC `{÷a}` |
| `{e}` | 'on' | DIR `{e}` |

`{ni}` is structurally unique: it is **never preceded by an IPP**
(§16.2.1, §20.2). Used heavily for placement/location: `mu-ni-řú` 'he
erected it (there)'.

`{e}` is homophonous with: ergative case `{e}`, directive case `{e}`,
and 2SG IPP `{e}`. Context disambiguates.

### 8.8 Slot 7: final person-prefixes (FPP; Jagersma ch. 13)

| FPP | Person | Slot use |
|---|---|---|
| `{÷}` | 1SG.H | rare; usually unwritten |
| `{e}` | 2SG.H | |
| `{n}` | 3SG.H | most frequent |
| `{b}` | 3N | |
| `{nnē}` | 3PL.H | uncommon; see §13.3 |

**Function depends on aspect** (§15.2):
- In **perfective**: FPP = A (transitive subject) or oblique object.
- In **imperfective**: FPP = DO (direct object) or oblique object.

### 8.9 STEM (Jagersma ch. 12)

The verb root. Possibly reduplicated (verbal number / aspect; §12.4).

Stem alternation patterns (§12.4.2):
- Suppletion: `ĝen` (PFV 'go') ~ `du/du-un` (IPFV); `du₁₁.g` (PFV
  'say') ~ `e` (IPFV); `úš` (SG 'die') ~ `ug₇`/`ug-ug` (PL).
- Reduplication: `dab₅` (SG 'seize') ~ `dab₅-dab₅` (PL).
- Vowel change: rare.

**Verbal number** (§12.4.1) is determined by the number of ABSOLUTIVE
arguments (S or DO), not by transitive-subject number. "All went" uses
PL stem; "he placed all of them" uses PL stem.

### 8.10 Slot 9: imperfective suffix `{ed}` (Jagersma §15.3)

Inserted between stem and person suffix in some imperfective forms.
Surface: `-e-de₃-`, `-e-da-`, `-e-d-`.

```
gen-e-de₃         '(in order) to go'           (gen-IPFV-NFIN)
šum₂-mu-de₃       'to give'                    (šum₂.IPFV-IPFV-NFIN)
```

### 8.11 Slot 10–11: person suffixes (Jagersma ch. 14)

Two sets:

| Person | Set A (default) | Set B (IPFV transitive) |
|---|---|---|
| 1SG | `{en}` | `{en}` |
| 2SG | `{en}` | `{en}` |
| 3SG.H or 3N | `Ø` | `{e}` |
| 1PL | `{enden}` | `{enden}` |
| 2PL | `{enzen}` | `{enzen}` |
| 3PL.H | `{eš}` | `{enē}` |

**Function**:
- In **perfective**: PS-A = S or DO. With 3PL.H, `{eš}` marks DO.
- In **imperfective transitive**: PS-B = A.
- In **imperfective intransitive**: PS-A = S.

This asymmetry is why imperfective inflection has a mixed
accusative/tripartite pattern (§15.2.3).

### 8.12 Slot 12: nominalizer `{÷a}` (Jagersma ch. 31)

Marks the form as a subordinate clause (relative, temporal,
complement). Surface: `-a` after vowel; assimilated `-Ca` after a
consonant (matches the consonant: `=ba` after /b/, `=na` after /n/,
`=ra` after /r/, etc.; spelling often drops the consonant after /š/
and /ḫ/; §27.3.3).

```
in-na-an-šúm-ma               'who/that he gave it to him'
                              (...n-na-n-šum₂-Ø-{÷a})

u₄ ... in-dab₅-ba-a           'when he took ...'
                              (...-÷a=÷a — NOM + LOC)
```

### 8.13 Outermost: enclitics on the verb (Jagersma §11.2.2, §27.3.3)

When a nominalized verb form serves as the head of an NP, it takes the
usual NP enclitics in order: `[possessive] [plural-{enē}] [case] [copula]`.

```
mu-řú-a-kam       =  mu-řú-÷a=ak=÷am
'who built it'    =  '(he is) of/concerning the one who built it'
                     (V-NOM=GEN=COPULA, §11.2.2 ex. 13)
```

---

## 9. Aspect: perfective vs imperfective (Jagersma ch. 15)

### 9.1 Inflection patterns (§15.2)

Sumerian's central morphological distinction. NOT a tense distinction
in the European sense — perfective covers states, timeless truths, and
completed past actions; imperfective covers incomplete/ongoing/future
(Jagersma §15.4, after Krecher 1995).

| Type | Perfective | Imperfective |
|---|---|---|
| Transitive subject (A) | FPP | PS-B (suffix) |
| Direct object (DO) | PS-A (suffix) | FPP |
| Intransitive subject (S) | PS-A (suffix) | PS-A (suffix) |
| Stem | basic | sometimes distinct (§12.3) |
| `{ed}` suffix | absent | sometimes present |

### 9.2 Worked transitive contrast

**Perfective transitive** (§15.2.2):
```
b-šúm-Ø                 'he gave it'
3N.A=FPP-give-3SG.DO=PS-A:Ø

(actually written with preformative and any dimensional prefixes:
  i₃-b-šúm-Ø   →  ib-šum₂   or   mu-na-an-šum₂)
```

**Imperfective transitive** (§15.2.3):
```
b-šúm-e                 'he will give / he gives it'
3N.DO=FPP-give-3SG.A=PS-B
```

In the perfective, the 3N suffix is `Ø` (PS-A 3N) — surfaces as a bare
stem after the FPP. In the imperfective, the 3N suffix is `e` (PS-B)
— surfaces as `-e`.

### 9.3 Intransitive

Both aspects use PS-A for S; FPP is generally empty:
```
ĝen-Ø               'he went'       (PFV intransitive)
i₃-du-e             'he will go'    (IPFV — different stem `du` for IPFV `go`)
```

### 9.4 Main uses

**Perfective (§15.4.2)**:
- Completed past action ("he built")
- State ("he is strong" — adjective + perfective)
- Timeless truth ("water flows")
- The unmarked default — most administrative texts.

**Imperfective (§15.4.3)**:
- Future or ongoing action ("he will give", "he is giving")
- Habitual / generic ("she gives daily")
- Subjunctive-like in some subordinate clauses
- Some narrative past where dynamicity is highlighted

### 9.5 No special aspect-glose for perfective

By convention (Jagersma §1.3.2), perfective is the **unmarked** aspect.
Forms without an `IPFV` tag in interlinear glosses are perfective. The
cheat sheet follows this — when in doubt, perfective.

---

## 10. Voice and valency (Jagersma §11.5, ch. 21)

### 10.1 Active (default)
The transitive A is in ERG; DO in ABS; verb agrees with both.

### 10.2 Passive (§11.5.3, §21.3.4, §24.5.2)

Two strategies:
1. **Middle `{ba}` + perfective** (the dominant Sumerian passive):
   ```
   ba-an-řú                'it was built'   (ba-n-řú — 3N.S/DO, no agent)
   ```
2. **Northern preformative `{÷a}` + perfective**: same effect, used in
   Nippur-area texts (§24.5.2).

### 10.3 Middle / change of state / indirect reflexive (§21.3)

All expressed by `{ba}`:
- **Change of state**: `ba-úš` 'he died' (became dead)
- **Indirect reflexive**: `ba-an-šum₂` 'he gave it to himself /
  for himself'

### 10.4 Causative (§18.3.2)

Not a morphological affix. Uses an OO-prefix + the causee in DAT/DIR:
```
mu-na-ni-in-ku₄          'he made her enter into it for him'
VP-3SG.IO-in-3SG.A-enter-3N.S/DO   (§11 ex. 7)
```

---

## 11. Subordination (Jagersma ch. 27, 31)

### 11.1 The nominalizer `{÷a}` (§27.3.3, §31)

The chief subordination strategy. A finite verb form takes `{÷a}` as
its last suffix (before clitics), making the clause function as an NP.
The nominalized clause then takes a **case marker** that indicates its
subordinate function:

| Construction | Marker | Meaning |
|---|---|---|
| V-`{÷a}`=`{÷a}` | LOC on NOM | "when X did Y" |
| V-`{÷a}`=`{še}` | TERM on NOM | "because X did Y" |
| V-`{÷a}`=`{ta}` | ABL on NOM | "after X did Y" |
| V-`{÷a}`=`{ak}` | GEN on NOM | relative clause modifying a noun |
| V-`{÷a}` (no case) | NOM bare | complement clause ("that X did Y") |

Examples:
```
u₄ NN-šè ba-a-re-eš-a-ne
'on the day the men who went to NN' (i.e., 'the men who went to NN, on their day')
u₄ ... ba=÷er-eš-÷a=enē=ak       — temporal phrase + relative + plural + GEN
                                  (Jagersma §27.3.3 ex. 8; D; 21)

inim ama-ne-ne nu-ù-ub-kúr-ne-a
'that they would not change the command of their mother'
inim ama=anēnē=ak=Ø nu=÷i-b-kúr-enē-÷a
                                  (§27.3.3 ex. 9)
```

### 11.2 Conjunctions (§27.3.2)

Old Sumerian had essentially no subordinating conjunctions. A few
adverbial subordinators emerge:
- `en-na` 'until'
- `u₄-da` 'if'
- `tukum-bé` 'if'
- `ù` 'and' — Akkadian loan, enters in Ur III; before that, juxtaposition

### 11.3 Conditionals (§27.6.6)

Old texts use juxtaposition. Later texts use `tukum-bé` 'if':
```
tukum-bé nu-na-an-šúm íb-tab-be₆-a
'if he did not give it to him, that he would double it'
                                  (§11.4.2 ex. 15; N; 21)
```

### 11.4 Relative clauses (§27.5)

The nominalized clause is attached to a head noun. The head takes the
case marker:
```
gud ba-úš-a-bi              'the ox that died'
                            gud  ba-÷úš-÷a=be
                            ox MM-die-NOM=this
```

---

## 12. Non-finite verbal forms (Jagersma ch. 28)

Four non-finite forms:

| Form | Aspect | NOM | Use |
|---|---|---|---|
| Present participle (§28.2) | PFV | no | Timeless truth, generic |
| Past participle (§28.3) | PFV | yes (`{÷a}`) | Past action; specific state |
| Imperfective participle (§28.4) | IPFV | no | Generic ongoing |
| `{ed}` participle (§28.5) | IPFV | yes (`{÷a}`) | Specific incomplete |

```
ba-úš-Ø                       'one who died'        (PFV pres. ptcp.)
ba-úš-a                       'who died'            (PFV past ptcp.)
šúm-mu                        'giving'              (IPFV pres. ptcp.)
šúm-mu-de₃                    'about to give'       (IPFV {ed} ptcp.)
```

These behave as verbal nouns/adjectives. The past participle is the
basic Sumerian "relative clause" form when no finite verb is needed.

---

## 13. Copular and nominal clauses (Jagersma ch. 29, 30)

### 13.1 The copula verb `me` 'be' (§29.1)

The only Sumerian copula. Used in nearly all non-verbal predications.
Inflects as a regular finite verb in some contexts.

### 13.2 Enclitic copula `{÷am}` (§29.2.3)

A phonologically reduced enclitic that attaches to the predicate. THE
most common copular construction.

| Subject | Form | Spelling |
|---|---|---|
| 3N.S / 3SG.H.S | `=÷am` | `-am₃` |
| 1SG.S | `=me-en` | `-me-en` |
| 2SG.S | `=me-en` | `-me-en` |
| 3PL.H.S | `=me-eš` | `-me-eš` |
| 1PL.S | `=me-enden` | `-me-en-den` |
| 2PL.S | `=me-enzen` | `-me-en-zen` |

Examples:
```
ensi₂-kam               'he is the ruler'           ensi₂.k=Ø=÷am
sipa-da-am₃             'he is the shepherd'        sipa.d=Ø=÷am
še dub-sar-ne-kam       'it is barley of the scribes'
                        še dub.sar=enē=ak=Ø=÷am     (§29.2.3 ex. 24)
```

### 13.3 Special copula forms with modal/negative

- With `{ḫa}`: `ḫe₂-em` 'let it be' (ḫa=÷i-me-Ø)
- With `{nu}`: usually expressed by the **nominal-clause** construction
  (§30.4): `alan kù nu` 'this statue is not silver' — just NP + `nu`.

---

## 14. Coordination (Jagersma §5.4, §27.4)

- **Juxtaposition** is the primary strategy for coordinating NPs and
  clauses, especially in Old Sumerian.
- **`ù` 'and'** is an Akkadian loan. Becomes more common in Ur III
  texts but is never required.

Examples:
```
an ki                       'heaven and earth'              (juxt.)
ud₅ udu                     'goats and sheep'               (juxt.)
NN ù NN₂                    'NN and NN2'                    (later texts; OB)
```

---

## 15. Period notes — what changes across time

When the speaker/period is unspecified, **default to ED (Early
Dynastic, 24–25th c.)**. Stylistic and morphological differences when
explicitly other periods:

### 15.1 ED (Old Sumerian) (Jagersma's primary corpus)

- Vowel harmony active: vocalic prefix surfaces as `e-` not `i-`
  (`e-né-ĝar` for later `i₃-ni-ĝar`).
- Dividing lines on tablets cut the text into smaller units.
- Genitive `{ak}` syllable-final /k/ → /h/ (Old Sumerian); fully lost
  by Ur III.
- Adjective-noun order in older texts gives way to noun-adjective.
- `{÷a}` preformative still found in Southern dialect (later
  disappears).
- Verbal forms more morphologically complete; fewer omissions.
- Many compound verbs in fixed phrasings (`šu—ti` 'receive', `igi—bar`
  'look at') already established.

### 15.2 Old Akkadian (23rd c.)

- Transitional period; Sumerian increasingly influenced by Akkadian
  contact.
- More frequent omission of grammatical morphemes in writing.
- Many Akkadian loanwords entering (the older `-a` layer).

### 15.3 Lagash II / Gudea (22nd c.)

- The Gudea cylinders: rich literary Sumerian, lots of ventive `{mu}`.
- Sound shift: intervocalic /t/ in dimensional `{ta}` → /r/.
- N-Adj order now standard.

### 15.4 Ur III (21st c.)

- Massive administrative corpus.
- Genitive /k/ fully lost in syllable-final position.
- Spelling becomes more morphologically explicit (the /a/ of `{ak}` is
  more often written; CV-spellings used more for grammatical
  morphemes).
- The Akkadian loan `ù` 'and' appears.

### 15.5 Old Babylonian Sumerian (19th–17th c.)

- Sumerian is no longer a living vernacular; texts are by Akkadian-
  speaking scribes.
- Heavy scribal regularization; morphology often hypercorrect.
- The literary corpus (ETCSL) is mostly OB-period copies of older
  works.

---

## 16. Workflow for English → Sumerian (LLM agent)

Use these MCP tools in this order:

1. **`start_here()`** once per session — pulls the agent prompt.
2. **`get_grammar_reference()`** — pulls this document.
3. For each English term/phrase:
   - **`translate_english(word)`** → rank candidates by `sense_count`
     and `sense_pct`. Prefer (a) high sense_count, (b) high sense_pct
     (so the meaning is central, not fringe).
   - **`find_compound(phrase)`** → look for fixed multi-word
     expressions BEFORE composing word-by-word.
4. **`find_collocations(cf)`** → discover phrasal patterns
   ('king-of-X', 'father-of-X', year-name templates).
5. **`lookup_entry(oid)`** → see all senses, periods, compounds for the
   chosen candidate.
6. **`get_inflections(oid)`** → see attested morphology before
   constructing a new form.
7. **`see_examples(oid, period='Early Dynastic')`** → cite primary
   sources (the default period is ED — see §15).
8. **`cuneify(spelling)`** → render the final composition in Unicode
   cuneiform.

For **Sumerian → English**:
- **`translate_sumerian(transliteration)`** → per-token English
  glosses; detects case suffixes.
- **`parse_phrase(transliteration)`** → grammatical pre-annotation:
  classifies each token's phrase role (subject_ergative,
  oblique_dative, etc.). Use this when ambiguity matters (e.g.
  ergative vs directive `-e`).
- **`analyze_form(spelling)`** → decompose a single spelling into
  candidate lemmas + their morphological role.
- **`find_verb_form(cf, prefix=…, dimensional=[…], ...)`** → look up
  attested forms for a verb's spec.

For **literary content** (hymns, myths, royal hymns, proverbs):
- **`etcsl_search_english(query)`** — FTS over ETCSL English
  translations (bilingual).
- **`etcsl_lines_with_lemma(lemma)`** — find ETCSL lines containing a
  given lemma.
- **`etcsl_search_sumerian(query)`** — FTS over ETCSL Sumerian.
- **`etcsl_lookup_text(text_id)`** — read a whole composition.

For **artifact context**:
- **`lookup_artifact(p_id)`** and **`find_artifacts(...)`** — query the
  CDLI catalogue.

---

## 17. Worked examples

### 17.1 ED royal inscription

Original (Old Sumerian, Enmetena, ED IIIb):
```
kur-kur e-ma-ḫuŋ
kur     -kur       =Ø ÷i-m(u)-ba-n-ḫuŋ-Ø
mountain-mountain=ABS VP-VENT-MM-3SG.A-hire-3N.S/DO
'He hired the foreign lands for himself.'
                              (Jagersma §4.3.4 ex. 9; Ent. 28 3:1; L; 25)
```

Slot-by-slot:
- `÷i` — vocalic preformative (§24.3.2)
- `mu` → `m` — ventive (§22) — speaker/king orientation
- `ba` — middle marker (§21.3.2) — "for himself" / indirect reflexive
- `n` — FPP 3SG.A (§13.2.3) — Enmetena did the hiring
- `ḫuŋ` — stem 'hire'
- `Ø` — PS-A 3N.DO (§14.4) — perfective default

Cuneify: `kur-kur` → 𒆳𒆳; `e-ma-ḫuŋ` (with Old Sumerian vowel-harmony
spelling) → 𒂊𒈠𒃶.

### 17.2 Ur III administrative line

```
gu₄ niga gu₃-de₂-a ensi₂ lagas{ki}-ka-ke₄ mu-na-šum₂
gu₄ niga.k        gu₃.de₂.a ensi₂.k lagas=ak=ak=e Ø-mu-nna-n-šum₂-Ø
ox  fattened    Gudea     ruler   Lagash=GEN=GEN=ERG VP-VENT-3SG.IO-3SG.A-give-3N.S/DO
'A fattened ox was given to (?) by Gudea, ruler of Lagash.'
```

This shows:
- Triple genitive on `lagas{ki}` (Lagash → ruler → genitive marker), with the
  ERG `=e` attaching to the outermost (§7.2.1 ex. 13).
- Verbal form with VENT + IO-prefix `{nna}` (3SG.IO, ch. 17) + FPP `n`
  (3SG.A, §13.2.3) + stem `šum₂` + PS-A 3N.DO `Ø`.

### 17.3 Literary line (ETCSL-style)

```
lugal sukud-da an-šè nu-mu-un-da-lá
lu₂ sukud  -Ø -÷a  =Ø an   =še    nu=Ø-mu-n -da -lá -Ø
man be.high-NFIN-NOM=ABS heaven=TERM NEG=VP-VENT-3SG-with-stretch-3SG.S/DO
'The highest man cannot reach out until heaven.'
                          (Jagersma §31.3.2 ex. 5; GH A 28; OB ms)
```

Note:
- `sukud-da` = adjective + nominalizer `{÷a}` — a "past participle"
  used attributively, giving comparative/superlative force (§31.3.2).
- The verb has VENT + 3SG IPP + COM-prefix `{da}` — "(can) reach
  out with X to Y".

---

## 18. Citation policy reminder

This cheat sheet cites Jagersma 2010 sections (`§N.M`) for every
grammatical claim. When you reason about a Sumerian form, **carry the
citation through** to your reply so the user can verify against the
primary reference. Example: "The ergative `=e` marks the agent of a
transitive verb (Jagersma §7.3)."

---

## 19. Quick-reference bibliography (sections cited above)

- §1.2.2 sources; §1.2.3 dialects; §1.3.1 terminology
- §2.2 outline of orthography; §2.7 transliteration
- §3.2.2 aspirated stops; §3.2.3 voiceless stops; §3.9 vowels;
  §3.9.3 OS vowel harmony; §3.10 syllable structure; §3.11 stress
- §4.3.4 grammatical word (compound verbs); §4.4.4 clitic order;
  §4.5 word classes
- §5.2 NP structure; §5.4 coordination
- §6.2 gender; §6.3 plural `{enē}`; §6.4 reduplication; §6.5 compounds;
  §6.8 proper names
- §7.1 cases intro; §7.2 genitive; §7.3 ergative; §7.4 absolutive;
  §7.5 dative; §7.6 directive; §7.7 locative; §7.8 terminative;
  §7.9 adverbiative; §7.10 ablative; §7.11 comitative; §7.12 equative
- §8.2 personal pronouns; §8.3 possessives; §8.4 demonstratives;
  §8.5 interrogatives; §8.7 reflexive
- §9.2 numeral system; §9.3 syntax of cardinals; §9.4 ordinals
- §10.4 adjective syntax; §10.5 de-adjectival verbs; §10.7 comparison
- §11.2 verb morphology; §11.4.3 ergative-split alignment;
  §11.4.4 IO/OO; §11.4.6 word order; §11.5 voice; §11.6 terminology
- §12.3 imperfective stems; §12.4 verbal number
- §13.2 FPP forms; §13.3 plurality strategies
- §14 person suffixes
- §15.1 aspect intro; §15.2.2 perfective inflection;
  §15.2.3 imperfective inflection; §15.3 stem forms; §15.4 uses
- §16.2 IPP forms; §16.3 usage
- §17 IO-prefixes; §18 OO-prefixes; §18.3.2 causatives
- §19.2 {da}; §19.3 {ta}; §19.4 {ši}
- §20.2 {ni}; §20.3 {e}
- §21.3 middle uses of {ba}
- §22.2 ventive forms; §22.3 ventive meaning
- §23 {nga}
- §24.2 {÷u}; §24.3 {÷i}/{÷a} forms; §24.4 Southern usage;
  §24.5 Northern usage
- §25.2 {nu}; §25.3 imperative; §25.4 {ḫa}; §25.5 {na(n)};
  §25.6 {ga}; §25.7 {bara}
- §27.3 nominalization-based subordination; §27.5 relative clauses;
  §27.6 conditionals
- §28.2–§28.5 the four non-finite forms; §28.6 pronominal conjugation
- §29.2 enclitic copula `{÷am}`
- §30 nominal clauses
- §31 the suffix `{÷a}`

Appendix p. 743: verb-slot diagram (the chart in §8.1 above).
