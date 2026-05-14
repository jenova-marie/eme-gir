# Jagersma 2010 — chapter-by-chapter notes

Per-chapter structured digest of Bram Jagersma, *A Descriptive Grammar of
Sumerian* (PhD dissertation, Universiteit Leiden, 2010, 776 pp).

Every grammatical claim in `JAGERSMA_GRAMMAR.md` should be traceable to a
citation in this file. Examples retain Jagersma's notation; the cheat sheet
translates to Oracc convention per `JAGERSMA_CONVENTIONS.md`.

---

## Ch 1 — Introduction (§1, pp. 1–14)

**Scope of the grammar.** Jagersma describes Sumerian as documented in
third-millennium texts (~2500–2000 BCE) — the only window with spelling
explicit enough to do morphological work (§1.2.2). Earlier texts
(proto-cuneiform 3200–3000 BCE, archaic Ur ~2800 BCE) are too defective;
later texts (Old Babylonian onward) are by scribes for whom Sumerian was
a learned second language.

**Dialects (§1.2.3).** Jagersma recognises two main dialects:
- **Southern Sumerian** = Lagaš, Umma, Ur (the largest corpus)
- **Northern Sumerian** = Nippur, Adab, and points further north
The two diverge most visibly in the use of the vocalic prefixes {÷i} and
{÷a} (§24): the prefix {÷a} virtually disappears from Southern but
develops a passive use in Northern (§24.5).

**Death of Sumerian (§1.2.4).** Sumerian died as a vernacular by the early
second millennium BCE, displaced by Akkadian; survived as a liturgical
and scholarly language to the end of the first millennium BCE.

**Terminology reform (§1.3.1).** Jagersma deliberately departs from
older traditions:
- 'preterite' / 'present-future' → **perfective** / **imperfective**
  (also replacing 'ḫamṭu' / 'marû'); see §15 for semantics.
- 'dative case' is split: NP marker stays 'dative' (§7.5), the
  homonymous verbal prefix becomes 'indirect-object prefix' (§17).
- 'locative-terminative' case is abolished, split into **directive case**
  (NP marker, §7.6) and **local prefix** (verb, §20).
- 'oblique object' restricted to a specific clausal role (§18.1).
- 'participle' kept as a label of convenience for non-finite forms, but
  Jagersma flags it as imperfect (§28.1).

**Notational conventions (§1.3.2).** Examples have four lines:
transliteration → morphemic analysis → glosses → translation + source
citation. Word signs are in **bold**, sound signs in ***bold italics***
(§2.7). Perfective forms are **not** explicitly glossed; imperfectives
are always tagged `IPFV`. Source references end with `; PROVENIENCE; CENTURY`
(L=Lagash, U=Umma, D=Drehem, N=Nippur, A=Adab, I=Isin, Ur=Ur, ?=unknown;
century in BCE, e.g. `21` = Ur III period).

---

## Ch 2 — The writing system (§2, pp. 15–30)

**Two sign types (§2.2).** Logograms (word signs) express lexemes;
phonograms (sound signs) represent sound sequences. Many signs are
multifunctional: KA is the logogram for ka 'mouth', zú 'tooth', kiri₃
'nose', du₁₁.g 'speak', inim 'word', and also a phonogram with value
*ka*. Numeric subscripts disambiguate values: `du` belongs to DU, `du₂`
to TU, `du₃` to GAG, `du₁₁` to KA.

**Determinatives and phonetic complements (§2.2).** Determinatives are
auxiliary logograms identifying semantic class (`{d}inanna`, `{ki}umma`,
`{ĝeš}apin`). Phonetic complements specify a sign's reading (Oracc keeps
them inline; Jagersma uses superscripts).

**Sign-to-text mapping (§2.2).** The script does not mark word
boundaries but does mark larger units: dividing lines (case/line
separators on tablets). Anything separated by a dividing line is at
least two words; anything written with a single sign is at most one
word (§4.3.2).

**Early development (§2.3).** Originally purely logographic (~3200 BCE),
then phonographic writing arose in the first half of the third
millennium. Key inventions:
- **VC signs** for syllable-final consonants (§2.4)
- **V signs** for vowel length (§2.5)

**Defective spelling (§2.4).** Syllable-final consonants are frequently
omitted; this is the central reason early Sumerian (pre-2500 BCE) is
unsuited to grammatical work — too many invisible morphemes.

**Transliteration (§2.7).** Standard Sumerological transliteration does
not distinguish logograms from phonograms. Jagersma's bold/italic
convention is an innovation for linguistic clarity but is not
standardly carried into Oracc — see `JAGERSMA_CONVENTIONS.md`.

---

## Ch 3 — Phonology (§3, pp. 31–68)

**Consonant inventory.** Phonemes proven by minimal pairs in sound
signs (§3.1):

| Series | Bilabial | Coronal | Velar | Glottal |
|---|---|---|---|---|
| Voiceless aspirated stops (§3.2.2) | /p/ | /t/ | /k/ | — |
| Plain voiceless stops (§3.2.3) | /b/ | /d/ | /g/ | /÷/ (§3.2.4) |
| Affricates (§3.3) | — | /z/, /ř/ | — | — |
| Fricatives (§3.4) | — | /s/, /š/ | /ḫ/ | /h/ |
| Nasals (§3.5) | /m/ | /n/ | /ŋ/ | — |
| Liquids (§3.6, §3.7) | — | /l/, /r/ | — | — |
| Glide (§3.8) | — | /j/ | — | — |

Notes:
- The /b/, /d/, /g/ series is transliterated voiced but in the third
  millennium was pronounced plain voiceless; voicing arose ~2000 BCE in
  most environments (§3.2.3).
- The aspirated stops /p/, /t/, /k/ are generally lost in syllable-final
  position (§3.2.2). Only ak 'make', lu₅.k 'live', ka.k 'mouth',
  ensi₂.k 'ruler', and the genitive marker `{ak}` preserve a final /k/,
  and even those are unstable.
- The affricate /ř/ (Jagersma's special symbol — sometimes called the
  "Sumerian r" or "dr") is contextually distinct from /r/; Oracc does not
  preserve the distinction (§3.3.2).
- /ŋ/ is a separate phoneme written `ĝ` (Jagersma) or `ŋ` (Oracc) (§3.5.4).
- The glottal stop /÷/ is a real consonant whose presence explains many
  apparent vowel-initial morphemes (§3.2.4).

**Vowels (§3.9).** Four short vowels /a, e, i, u/. Long vowels /ā, ē, ī, ū/
are independent phonemes (proved by spelling distinctions like `da` vs
`da-a`).

**Old Sumerian vowel harmony (§3.9.3).** In Old Sumerian (24–25th c.)
the vocalic prefix surfaces as /e/ instead of /i/ when followed by a
syllable containing /e/. Disappears by Ur III. This is a key dating
feature.

**Syllable structure (§3.10).** Strictly CV(C); no consonant clusters at
syllable boundaries.

**Stress (§3.11).** Primary stress on the final syllable of the
phonological word. Vowel deletion in word-initial position of long
phonological words is a stress-driven phenomenon (e.g. `eden=ak` → `dè-na`).

---

## Ch 4 — Words and word classes (§4, pp. 69–86)

**Word definition (§4.3).** Sumerian word = orthographic + phonological +
grammatical word, but these don't always coincide. Clitics are
grammatical words (separable) but phonological words with their host
(§4.3.4–4.3.5).

**Compound verbs.** What Sumerologists call "compound verbs" (e.g.
`igi—bar` 'look at', `gu₃—de₂` 'call', `šu—ti` 'receive') are
**idiomatic expressions of separate grammatical words**, not single
verbs (§4.3.4). The nominal part can be separated from the verbal part
by other words. This matters for our `find_compound` MCP tool — the
compound is a phrase pattern, not a fused stem.

**Word classes (§4.5).** Sumerian has:
- **Nouns** (chapter 6)
- **Pronouns** (chapter 8)
- **Numerals** (chapter 9)
- **Adjectives** (chapter 10) — small closed class; grammatically more
  like verbs than nouns (§10.5)
- **Verbs** (chapter 11)
- **Ideophones** (§4.5.4) — a true word class expressing specific sounds
  in a fixed template (e.g. *gu-da-gu-da*)
- **Conjunctions** — only the Akkadian loan ù 'and' and a few
  subordinators (§27.3.2)

**No adverbs (§4.5.3).** What is glossed as an "adverb" is usually a
noun phrase in an oblique case (mainly adverbiative or terminative).

**Order of clitics (§4.4.4).** Phrase-internal order on the last word
of an NP: `[stem] - [possessive] - [plural marker {enē}] - [case marker]
- [enclitic copula]`. The case marker comes after possessive and number
and before the copula. This order is reliable across periods.

---

## Ch 5 — The noun phrase (§5, pp. 87–100)

**NP structure (§5.2).** Head-final-ish but with most modifiers
following:
`[noun] [adjective] [genitive NP] [possessive] [demonstrative] [plural] [case]`

Examples:
- `lugal kalag-ga` 'the strong king' (noun + adj)
- `é lugal-la-na` 'in the house of his king' (noun + GEN + LOC stacked)
- `dumu-ne-ne-er` 'to their children' (noun + plural + DAT)

**Appositive NPs (§5.3).** Apposition is shown by juxtaposition (no
linker); the case marker attaches to the apposition group:
`ki lagas{ki}` 'the land Lagash', `en-na, muḫaldim` 'Enna, the cook'.

**Coordination (§5.4).** Mostly by juxtaposition before Ur III. The
Akkadian loan ù 'and' creeps in later (§27.4).

**NP-final case stacking.** Multiple case markers can stack on the last
word of nested NPs (§7.1, ex. 1): `mu ensi₂ ĝir-su{ki}-ka-še` =
`[mu [ensi₂.k [ĝir.su=ak]=ak]=še]` 'because of the governor of Girsu' —
two genitive markers + terminative all on the last word.

---

## Ch 6 — Nouns (§6, pp. 101–136)

**Gender (§6.2).** Two genders:
- **Human** — humans + deities (including objects with deity status)
- **Non-human** — everything else
Plural marking and pronouns depend on gender; only human nouns have a
plural.

**Plural marker `{enē}` (§6.3).** Postnominal enclitic for human plural
only. Forms: full `=enē`, contracted `=nē` after a vowel. Spelled `-(e)-ne`.

Examples: `lugal=enē` 'the kings', `dingir-re-ne` 'the gods',
`dub-sar-ne` 'the scribes'.

Non-human plurality is expressed only via reduplication of the noun
(§6.4) or by context — there is no non-human plural marker.

**Reduplication (§6.4).** Used for plurality or distribution: `kur-kur`
'foreign lands', `du₁₀-du₁₀` 'all the goods'. Reduplication is a single
grammatical word.

**Compounding (§6.5).** Several types:
- **N-N**: `é-maš` 'sheepfold', `ki-šár` 'horizon'
- **N-Adj / Adj-N**: `gu₃-zi` 'true voice', `e-zi` 'right side'
- **N-Participle**: `lugal-zi-il-la` 'the king who raised X', extremely
  productive
- **N + case marker fossilized**: `ki-bal-a` 'rebel land' (lit. "place
  of crossing-over")
- **Coordinative**: `an-ki` 'heaven and earth', `iti-zal-la` 'past-month'

**Conversion (§6.6).** Deverbal nouns formed from a verb stem alone:
`gub` 'standing → standing-place', `dab₅` 'taking → captive'.

**Proper nouns (§6.8).** Often full clauses or NPs:
- `ur-{d}namma` (Urnamma) = "Servant-of-Namma"
- `lugal-an-da` = "King-with-An"
- `nin-ḫi-li-su` = "Lady-Filled-With-Allure"
Such "sentence-names" still inflect: `lugal-an-da=k=e` 'King-Anda's'.

---

## Ch 7 — The cases (§7, pp. 137–206)

**Twelve cases.** Jagersma describes **twelve** distinct cases (per the
Dutch summary, p. 745); the abbreviation table lists each. Each is
expressed by an **enclitic case marker** attached to the last word of
the NP. Multiple markers can stack (§7.1, §5.2).

| Case | Marker | Glose | Section |
|---|---|---|---|
| Absolutive | Ø | ABS | §7.4 |
| Ergative | {e} | ERG | §7.3 |
| Genitive | {ak} | GEN | §7.2 |
| Dative | {ra} | DAT | §7.5 |
| Directive | {e} | DIR | §7.6 |
| Locative | {÷a} | LOC | §7.7 |
| Locative₂ | {ne} | LOC2 | §7.7 (subsumed; rare) |
| Terminative | {še} | TERM | §7.8 |
| Adverbiative | {eš} | ADV | §7.9 |
| Ablative | {ta} | ABL | §7.10 |
| Comitative | {da} | COM | §7.11 |
| Equative | {gen} (often spelled `gin₇`) | EQU | §7.12 |

### §7.2 Genitive `{ak}`

- **Form.** `/ak/` between consonant and vowel; `/a/` between consonant
  and consonant (the /k/ becomes /h/ by Old Sumerian, lost by Ur III);
  contraction outcome with preceding vowel is usually masked by word-sign
  spelling.
- **Examples.** `lú lagas{ki}-ka` 'the man of Lagash' (lú lagas=ak=ak);
  `dam ur-{d}ba.u₂-ka-ke₄` 'the wife of Ur-Bau, X' (dam ur-bau=ak=ak=e).
- **Headless genitive (§7.2.4).** The genitive NP can stand without an
  overt head, as a relative or possessive expression: `lugal-la-kam`
  'it belongs to the king'.
- **Stacking.** Double and triple genitives are common (`šu-ku₆ ab-ba-ke₄-ne`
  'the sea fishermen' = šu.ku₆ ab=ak=enē=e, ex. 8 §7.2.1).

### §7.3 Ergative `{e}`

- Marks the transitive subject (Agent). Surface form: `=e` after a
  consonant; `=Ø` after a vowel (contraction; the case is "invisible" but
  present).
- Pattern: `gu₃-de₂-a=e é-ninnu mu-řú` 'Gudea built the Eninnu' (§11.4.6).
- Ergative and directive `{e}` are homophonous and must be distinguished
  by context, by the verbal-prefix coreference, and by clause structure.
  See §7.6.

### §7.4 Absolutive (Ø)

- Marks the intransitive subject (S) AND the direct object (DO).
- No overt marker.
- This is the Sumerian-language morphological ergative-absolutive
  alignment (§11.4.3). It's purely a CASE alignment; verbal agreement
  follows DIFFERENT alignments depending on aspect (§11.4.3, §15.2).

### §7.5 Dative `{ra}`

- **Human indirect object only** (§7.5.2). Use the directive (§7.6) for
  non-human indirect objects.
- Surface: `=ra` after consonant, `=r` after vowel.
- Example: `{d}en-líl-ra` 'to Enlil' (§7.5.1).
- Coreferential verbal prefix: indirect-object prefix `{nna}` (3SG.IO,
  ch. 17).

### §7.6 Directive `{e}`

- **Non-human indirect object** AND oblique-object marker.
- Surface form: `=e` after consonant, `=Ø` after vowel (homophonous
  with ergative).
- Disambiguation from ergative:
  1. The NP's semantics (transitive subject vs oblique target)
  2. The verbal coreference: ergative co-occurs with final
     person-prefix (FPP); directive co-occurs with an oblique-object
     prefix (ch. 18) or local prefix `{e}` (ch. 20).
- Used heavily with verbs of placing, going-onto, building (§7.6.2).

### §7.7 Locative `{÷a}` and Locative₂ `{ne}`

- `{÷a}` (LOC): "in, on" — primary locative.
- `{ne}` (LOC2): rare alternative locative attested for a few nouns
  (§7.7.2, p. 247). Marker `{ne}` overlaps with the locative₂ verbal
  prefix.
- Surface of `{÷a}` is just `=a` (the glottal stop usually unwritten).
- Coreferential verbal prefix: local `{ni}` (ch. 20).

### §7.8 Terminative `{še}`

- "To, toward, for" (§7.8.2).
- Surface: `=še` after consonant, `=š` after vowel.
- Coreferential verbal prefix: dimensional `{ši}` (ch. 19.4).
- Frequent in purpose expressions ("for X", "because of X"): `mu lugal-la-šè`
  'because of (lit. "for the name of") the king'.

### §7.9 Adverbiative `{eš}`

- Manner: "in the manner of X, as X".
- Surface: `=eš` always.
- Example: `lugal-eš` 'as king, kingly'; `dumu dab₅-ba-za-ke₄-eš` 'because
  of your captive child' (§7.2 ex. 16) — adverbiative on a stacked GEN.

### §7.10 Ablative `{ta}`

- "From, out of, by" (§7.10).
- Surface: `=ta` always (the /t/ has irregularly stable behaviour, unlike
  the comitative {da} — see §7.11.1, §19.3.1; the verbal prefix {ta}
  becomes /ra/ between vowels by the Ur III period).
- Coreferential verbal prefix: dimensional `{ta}` (§19.3).

### §7.11 Comitative `{da}`

- "With, together with" (§7.11.2).
- Surface: `=da` after consonant, `=d` after vowel.
- Coreferential verbal prefix: dimensional `{da}` (§19.2).
- Confusion with dative: word-final /r/ and /d/ were homophones; scribes
  sometimes write `=ra` (DAT) where `=da` (COM) is called for (§7.11.1).
  This is a SPELLING confusion, not a semantic one.

### §7.12 Equative `{gen}` ~ spelled `gin₇`

- "Like, as".
- Surface: invariant `=gen` / spelled `gin₇`.
- Example: `lugal-gen` 'like a king'.

### Case ambiguity summary (load-bearing for `parse_phrase`)

| Surface ending | Possible cases | Resolution |
|---|---|---|
| `=e` (post-C) | ERG, DIR | Verb's coreferent prefix; semantic role |
| `=a` (post-C) | LOC, GEN (after /k/-loss), NOM (verb suffix) | NP-internal head/V status; spelling |
| `=ne` | LOC2 (rare), or plural {enē} after vowel | Word morphology; productivity |
| `=še` | TERM | unambiguous |
| `=ta` | ABL | unambiguous |
| `=da` | COM | (note ‹da~ra› confusion) |

---

## Ch 8 — Pronouns (§8, pp. 207–240)

**Independent personal pronouns (§8.2).** Used for emphasis; rare in
running text.
- 1SG `ĝe₂₆` (older `ĝa₂.e`)
- 2SG `ze₂` / `zi.e` ('you')
- 3SG.H `e-ne` / `a-ne` ('he/she')
- 1PL `me-en-de-en` 
- 2PL `me-en-ze₂-en`
- 3PL.H `e-ne-ne`
- No 3N independent pronoun.

**Possessive pronouns (§8.3).** Enclitic on the noun.
| Person | Singular | Plural |
|---|---|---|
| 1 | `=ĝu` 'my' | `=meanēnē` 'our' |
| 2 | `=zu` 'your' | `=zunēnē` 'your' |
| 3.H | `=ane` 'his/her' | `=anēnē` 'their' |
| 3.N | `=be` 'its' | (3N has no plural) |

Order on NP: `noun = possessive = plural-{enē} = case`.

**Demonstratives (§8.4).**
- Enclitic: `{be}` 'this/that' (3N), used for 'the' definite-article-like
  function. Example: `kur-kur=be` 'these lands'.
- Independent: `ne-en` 'this', `ur₅` 'that'.

**Interrogatives (§8.5).** `a-ba` 'who?' (human), `a-na` 'what?'
(non-human), `me-a` 'where?', `me-na` 'when?'.

**Indefinite (§8.6).** `na-me`, `lú na-me` 'anyone', `niĝ₂ na-me`
'anything'. Often appears in negative clauses ('no one', 'nothing').

**Reflexive (§8.7).** Formed with `ni₂` + possessive: `ni₂=ĝu` 'myself',
`ni₂=ane` 'himself'.

---

## Ch 9 — Numerals (§9, pp. 241–266)

**Sexagesimal system (§9.2).** Sumerian counts base-60:
- 1 = `aš`, `dili`, `diš` 
- 2 = `min`
- 3 = `eš`
- 4 = `limmu`
- 5 = `ia₂`
- 6 = `aš₃`
- 7 = `imin`
- 8 = `ussu`
- 9 = `ilimmu`
- 10 = `u`
- 60 = `ĝeš` (sometimes `ĝeš₂`)
- 600 = `ĝeš-u` (60×10)
- 3600 = `šar₂`
- 36000 = `šar₂-u`

70 = `ĝeš-u` ('60-10'), 100 = `ĝeš nimin` ('60-40').

**Syntax (§9.3).** Cardinals follow the noun: `lugal min` 'two kings',
`gud limmu` 'four oxen'. They behave more like numerals-as-nouns than as
attributive adjectives.

**Ordinals (§9.4).** Formed with `=kamma` (sometimes `=kam`) on the
cardinal: `min-kamma` 'second', `eš-kamma` 'third'. Glose: ORD.

**Fractions (§9.5).** `igi-X-ĝál` 'one X-th' (literally "having X eyes"):
`igi-3-ĝál` = 1/3, `igi-4-ĝál` = 1/4. `šu-ru-a` = 1/2.

---

## Ch 10 — Adjectives (§10, pp. 267–284)

**Small closed class.** Sumerian has only a few dozen adjectives:
`kalag` 'strong', `kug` 'pure', `gibil` 'new', `sumun` 'old', `gula`
'great', `tur` 'small', `mah` 'lofty', `nigin/zid` 'right' …

**Grammatically verb-like (§10.5).** Adjectives can serve as verb stems
in finite intransitive (stative) forms: `kalag` → `kalag-ga-am₃` 'he is
strong', `kug-ge` 'will be pure'.

**Attributive use (§10.4.1).** Postnominal: `lugal kalag-ga` 'the strong
king'. NB: Sumerian shifted from N-Adj to N-Adj order during the third
millennium, possibly under Akkadian influence (§10.4.1).

**Reduplication (§10.3).** Intensifies: `gal-gal` 'very great',
`kalag-kalag-ga` 'mighty'.

**De-adjectival nouns (§10.6).** `=÷a` derives a noun: `kug-ga` 'pure
thing/silver', `kalag-ga` 'the strong one'.

**No comparative/superlative morphology (§10.7).** Comparison expressed
periphrastically with the equative case `=gen` or by absolute predication.

---

## Ch 11 — Verbs and verbal clauses (§11, pp. 285–308)

**Verbal stem.** Sumerian has only ~600–700 distinct verbal stems (§11.3);
contrast English (theoretically unlimited). No productive
verb-formation; novel verbal meanings expressed periphrastically or with
compound verbs (§4.3.4).

**Semantic types (§11.3).** Motion, rest, affect/manufacture, giving,
speech, perception, mental, corporeal, weather, "be"-class, modal-like.

**Finite vs non-finite (§11.2).** Finite forms include person markers
and preformatives; non-finite forms lack person markers (ch. 28).

### The finite verbal-form template (§11.2.2; appendix p. 743)

Slot order (left to right):

```
[Preformative₁ (proclitic): nu / ḫa]
  [Preformative₂ (prefix): ÷i / ÷a / ÷u / na(n) / ga / bara / ši / na]
    [{nga} 'also']
      [Ventive {mu} (or {ma})]
        [Middle/IO-prefix {ba}]
          [Initial person-prefix (IPP): ÷ / e / n / b / mē / enē / nnē]
            [Indirect-object prefix: (a) / (ra)]
              [Dimensional {da} / {ta} / {ši}]
                [Local prefix: ni / e]
                  [Final person-prefix (FPP): ÷ / e / n / b]
                    STEM
                      [{ed} imperfective suffix]
                        [Person suffix Set A or Set B]
                          [{÷a} nominalizer]
                            [enclitics — possessive, plural, case, copula]
```

Maximum: 9 prefix slots, stem, up to 3 suffixes. (§11 intro; Dutch
summary p. 746.)

NB: Elements from the same box/column cannot co-occur. Exception:
preformatives `{nu}` and `{ḫa}` can co-occur with `{÷i}` (and perhaps
`{÷a}`) (Appendix p. 743 note).

### Slot semantics (§11.2.3)

| Slot | Function |
|---|---|
| Preformative | TAM (tense/aspect/mood), negation, modality |
| Ventive {mu} | Action oriented toward speaker (§22.3) |
| {ba} | Middle / passive / change-of-state (§21); also 3N.NH IO |
| Initial person-prefix | Person of IO, OO, or comitative complement |
| Dimensional prefixes | Locative/comitative/ablative/terminative referents |
| Local prefix | Spatial: 'in' ({ni}) or 'on' ({e}) |
| Final person-prefix | Perfective: A (transitive subject); Imperfective: DO |
| {ed} suffix | Imperfective stem marker (§15.3) |
| Person suffix | Set A or B depending on aspect — see §15.2 |
| {÷a} nominalizer | Marks a subordinate clause (§31) |

### Ergative-split system (§11.4.3)

Sumerian is a **split-ergative** language with **three different
alignments** depending on subsystem:

| Subsystem | Alignment |
|---|---|
| Case marking | **Ergative** (S = DO ≠ A) |
| Perfective verbal inflection | **Ergative** (FPP marks A; PS-A marks S+DO) |
| Imperfective verbal inflection | **Partly accusative, partly tripartite** (FPP marks DO; PS-A vs PS-B distinguishes S, A by person) |
| Imperative | **Accusative** (no FPP; PS marks S=A) |
| Modal {ga} forms | **Accusative** |
| Indirect reflexive {ba} | **Accusative** |
| Syntax | **Neither** ergative nor accusative — free coordination |

This means: an analysis using only "subject" + "object" or only
"absolutive + ergative" misrepresents the morphology. Use the three
syntactic roles: **A** (transitive subject), **S** (intransitive
subject), **DO** (direct object).

### Indirect vs oblique object (§11.4.4)

- **Indirect object** (IO): expressed by **dative case** (humans) or
  **directive case** (non-humans); coreferent verbal prefix is an IO
  prefix (ch. 17). Beneficiary, recipient.
- **Oblique object** (OO): same NP marking (dative for humans,
  directive for non-humans); coreferent verbal prefix is an OO prefix
  (ch. 18). Causee, "in(to) contact with" location.
- An IO and an OO can co-occur in one clause (§11.4.4 ex. 17).

### Coreference (§11.4.5)

The verbal affix and an NP referring to the same participant are
**coreferential**, not in concord. A clause can have an affix without
an NP (e.g. dropped pronouns) OR an NP without an affix. When both are
present, mismatches in gender/person/case/number do happen but are
rare.

### Word order (§11.4.6)

**SOV** in transitive clauses: `Gudea Eninnu mu-řú` 'Gudea built the
Eninnu' (§11.4.6 ex. 23). The verb is **always clause-final**. Order of
preverbal NPs has rules (especially for topic/focus) but is much freer
than English.

### Voice and valency (§11.5)

- **Middle**: prefix `{ba}` (ch. 21).
- **Passive**: marked by prefix `{ba}` in some uses, by the
  preformative `{÷a}` in Northern Sumerian (§24.5), or by nominal-clause
  constructions.
- **Causative**: separate construction with oblique-object prefix +
  causee (§18.3.2). Not a morphological affix.

---

## Ch 12 — The verbal stem (§12, pp. 309–326)

**Verb formation (§12.2).** Stems are largely monomorphemic. New verbs
are not coined freely; new concepts use compound verbs.

**Imperfective stems (§12.3).** Many verbs have a distinct imperfective
stem. Strategies:
- **Suppletion**: `ĝen` (perfective 'go') ~ `du/duun` (imperfective);
  `du₁₁.g` 'say' (perfective) ~ `e` (imperfective).
- **Reduplication**: `dab₅` 'seize' ~ `dab₅-dab₅` (impf).
- **Vowel change**: a few verbs alternate stem-vowel.
- **No change**: most verbs use the same stem for both aspects;
  aspect distinction shown only via inflection (§15.2) and the {ed}
  suffix.

**Verbal number (§12.4).** Sumerian distinguishes singular vs plural
*action/state* (NOT subject number) in some verbs:
- **Stem alternation** (§12.4.2): `úš` 'die-SG' ~ `ug₇` (or `ug-ug`)
  'die-PL'; `tum₂` 'bring-SG' ~ `de₆` 'bring-PL'.
- **Reduplication** (§12.4.3): `gar` 'place-SG' ~ `gar-gar` 'place-PL'.
- The choice between singular and plural action stem is determined by
  the **number of S/DO arguments** (the absolutive), NOT by transitive
  subject number (§12.4.1).

**Plural suffix {en} (§12.5).** Some verbs add `{en}` to mark plural
action (rare and old).

**Verb `ak` 'make' (§12.6).** Has the most unusual stem behaviour,
losing its /k/ in nearly every inflected form. Useful demonstration of
how far surface spelling can diverge from underlying form.

---

## Ch 13 — The final person-prefixes (§13, pp. 327–342)

**Forms.**
| FPP | Person | Use |
|---|---|---|
| `{÷}` | 1SG.H | rare; usually unwritten |
| `{e}` | 2SG.H | |
| `{n}` | 3SG.H | the most frequent |
| `{b}` | 3N | |
| `{nnē}` | 3PL.H | plural strategy (§13.3) |

**Functions.**
- In **perfective**: FPP expresses the **transitive subject (A)** OR
  the oblique object.
- In **imperfective**: FPP expresses the **direct object (DO)** OR the
  oblique object.

Slot 7 in the verbal template; comes immediately before the stem.

---

## Ch 14 — The person suffixes (§14, pp. 343–358)

Two sets, identical for 1/2 person but differing for 3 person:

| Person | Set A (default) | Set B (imperfective transitive) |
|---|---|---|
| 1SG | `{en}` | `{en}` |
| 2SG | `{en}` | `{en}` |
| 3SG.H or 3N | `Ø` | `{e}` |
| 1PL | `{enden}` | `{enden}` |
| 2PL | `{enzen}` | `{enzen}` |
| 3PL.H | `{eš}` | `{enē}` |

- In **perfective**: PS-A expresses S (intransitive subject) or DO. With
  3PL.H, marks the DO with `{eš}`.
- In **imperfective transitive**: PS-B expresses A.
- In **imperfective intransitive**: PS-A expresses S.

The asymmetry is what makes the imperfective inflection partly
accusative and partly tripartite (§15.2.3).

---

## Ch 15 — Perfective and imperfective (§15, pp. 359–380)

**Aspect not tense (§15.1, §15.4.1).** Following Yoshikawa (1968b),
Diakonoff (1967), and Krecher (1995):
- **Perfective** expresses a **complete action**, a **state**, or a
  **timeless truth**. NEVER stative-via-imperfective (per Krecher 1995).
- **Imperfective** expresses an **incomplete action**.
- Tense is NOT primary; the past-ish reading of perfective in narrative
  is a SECONDARY consequence of completeness.

**Inflection patterns (§15.2.2, §15.2.3).**

Perfective transitive (§15.2.2):
- FPP = A; PS-A = DO. Example: `n-šúm-Ø` 'he gave it' (3SG.A
  gave 3N.DO).

Imperfective transitive (§15.2.3):
- FPP = DO; PS-B = A. Example: `b-šúm-e` 'he-will-give it' (3N.DO
  3SG.A-IPFV).

Intransitive (both aspects, §15.2.3):
- PS-A = S. The FPP is generally empty for intransitives.

**Imperfective stem marker {ed} (§15.3.2).** Inserted between stem and
person suffix in some imperfective forms; surface `e-de₃` / `e-dam`.
Distinguishes imperfective intransitive participles too (ch. 28).

**Uses of the imperfective (§15.4.3).**
- Future or ongoing action.
- Habitual / generic.
- Some narrative past where dynamicity is highlighted.
- Subjunctive-like in subordinate clauses.

---

## Ch 16 — Dimensional prefixes & initial person-prefixes (§16, pp. 381–398)

**Initial person-prefix (IPP) forms (§16.2).**
| IPP | Person |
|---|---|
| `{÷}` | 1SG |
| `{e}` | 2SG |
| `{n}` | 3SG.H |
| `{b}` | 3N |
| `{mē}` | 1PL |
| `{enē}` | 2PL |
| `{nnē}` | 3PL.H |

These mark the gender/person/number of an IO/OO/comitative complement
(§16.3.1). They occupy slot 5 and are usually followed by a dimensional
prefix that specifies the relational meaning.

Exception: the local prefix `{ni}` 'in' is NEVER preceded by an IPP
(§20.2). Always Ø-marked for person.

---

## Ch 17 — Indirect-object prefixes (§17, pp. 399–414)

**IO-prefix forms.** Each composed of IPP + the IO marker:
| Prefix | Form | Person of recipient |
|---|---|---|
| `{ba}` | ba | 3N.IO (replaces `{b+a}`) |
| `{nna}` | n + na | 3SG.H.IO — the most frequent IO prefix |
| `{nnē}` ~ `{nnē÷a}` | nnē or nnē-a | 3PL.H.IO |
| `{ra}` | r + a | 2SG.IO |
| `{ma}` | m + a | 1SG.IO |
| `{mē}` ~ `{mē÷a}` | mē | 1PL.IO |

**Function (§17.3).** Always coreferent with a noun phrase in DAT
(human) or DIR (non-human). Indirect objects are the recipient or
beneficiary of an action.

---

## Ch 18 — Oblique-object prefixes (§18, pp. 415–444)

**OO-prefix forms (§18.2).**
| Prefix | Form | Person |
|---|---|---|
| `{bi}` / `{b}` | bi / b | 3N |
| `{nni}` / `{n}` | nni / n | 3SG.H |
| `{ri}` / `{e}` | ri / e | 2SG |
| `{mu}` / `{÷}` | mu / ÷ | 1SG (reuses ventive form) |
| 3PL.H, 1PL, 2PL | various | (§18.2.6) |

**Uses (§18.3).**
- **Causative** (§18.3.2): "X made Y do Z" expressed by Y in DAT/DIR +
  OO-prefix on the causative verb.
- **"In(to) contact with"** locational (§18.3.3): "place X on Y", "put
  X into contact with Y".
- **Human OO for non-human spatial 'on'** (§18.3.4): rare; only the
  human OO-prefix is used.

OO and IO are mutually exclusive: only one dimensional prefix slot for
either (§18.4).

---

## Ch 19 — Dimensional prefixes {da}, {ta}, {ši} (§19, pp. 445–464)

**{da} 'with' (§19.2).** Comitative-prefix. Coreferent with NP in COM.
"X is with Y", "X has Y" (Sumerian uses {da} for 'have' constructions).

Example (§19.2): `nu-mu-da-tuku` 'he does not have it' = "it is not
with him".

**{ta} 'from' (§19.3).** Ablative-prefix. Coreferent with NP in ABL.
"X out of Y", "X away from Y".

Sound change (§19.3.1): in Gudea+ texts the /t/ of {ta} becomes /r/
between vowels — `ba-ta-zal` → `ba-ra-zal`. This is a phonological
process, not a different prefix.

**{ši} 'to(ward)' (§19.4).** Coreferent with NP in TERM. "X toward Y",
also some allative directionality.

---

## Ch 20 — Local prefixes (§20, pp. 465–486)

**{ni} 'in' (§20.2).** Coreferent with NP in LOC `{÷a}`. Always
appears WITHOUT a person-prefix (§16.2, §20.2.1). Used heavily for
location/placement.

**{e} 'on' (§20.3).** Coreferent with NP in DIR (when the directive
expresses 'on'). The local-prefix {e} is homophonous with both the
ergative case marker and the 2SG initial person-prefix; context
disambiguates.

---

## Ch 21 — {ba} as a middle marker (§21, pp. 487–496)

**{ba} (§21.3).** When NOT used as 3N.NH IO-prefix, {ba} is a **middle
marker** with three primary uses:

1. **Indirect reflexive** (§21.3.2): "did for himself" — when the IO
   refers to the same person as the A or S.
2. **Change of state** (§21.3.3): inchoative reading.
3. **Passive** (§21.3.4): the most common — Sumerian passive is
   chiefly expressed with {ba}.

When {ba} is followed by a verbal stem with no other dimensional prefix,
read it as middle/passive; when followed by another dimensional prefix,
it's the 3N IO-prefix.

---

## Ch 22 — Ventive prefix {mu} (§22, pp. 497–512)

**Form (§22.2).** Surfaces as `mu`, `m-`, or `ma-`. The vowel /u/ is
lost in `/muCV/` environments: `mu-da-` becomes `m-da-` (written `im-da-`
after the vocalic prefix); the vocalic prefixes {÷i}/{÷a} are then
RETAINED before the consonant cluster /mC/.

**Meaning (§22.3).** Marks an action **oriented toward the speaker** or
the deictic centre. Specifically:
- Motion verbs: "come" rather than "go": `mu-ĝen` 'he came' vs `ĝen` 'he
  went'.
- Other verbs: directional/affective overlay — the action is
  represented as benefitting or affecting the speaker / deictic centre.
- Common in royal inscriptions (Gudea cylinder), where the king is the
  deictic centre.

**Co-occurrence (§22.4).** Cannot occur with the 3N person prefix `{b}`
in initial slot.

---

## Ch 23 — Prefix {nga} (§23, pp. 513–516)

**{nga} 'also' (§23).** Rare; meaning poorly understood. Glossed 'also'.
Slot 2 of the verbal template. Co-occurs with {nu}: e.g. `nu-ga-ma-X` =
NEG-also-1SG.IO-... (§23 ex. 4).

---

## Ch 24 — Vocalic preformatives {÷u}, {÷i}, {÷a} (§24, pp. 517–550)

**Three vocalic prefixes (§24.2–§24.3).**
- `{÷i}` is the "neutral" preformative — appears whenever no other
  preformative is required. Spelled `ì-`, `i-`, or just the vowel.
- `{÷a}` is a contrastive preformative. In Southern Sumerian (Lagash
  etc.) it virtually disappears; in Northern Sumerian (Nippur) it
  develops a **passive** function.
- `{÷u}` is the **relative-past** preformative (§24.2). Spelled `ù-`.
  Marks a clause as temporally prior to another. "When X had done Y, Z".

**Southern vs Northern usage (§24.4 vs §24.5).** The two main dialects
diverge here:
- Southern: predominantly {÷i}, very rare {÷a}.
- Northern: {÷i} alternates with {÷a}; {÷a} on perfective forms can be
  passive.

**Vocalic preformatives are present in essentially every finite verbal
form** (§24.1) — but often surface as zero before a consonant cluster.
The deeper diagnostic for which preformative is present is the form's
behaviour before the ventive prefix /mC/ (§24.3.1).

---

## Ch 25 — Modal and negative preformatives (§25, pp. 551–576)

**{nu} 'not' (§25.2).** The standard negative proclitic. Spelled `nu-`.
Combines with imperfective for negative future; with perfective for
plain negation.

**Imperative (§25.3).** Distinctive form:
- The stem comes FIRST in the form (no preformatives or person prefixes
  before it).
- All affixes that would normally precede the stem are placed AFTER it.
- Plural imperative adds `{zen}` after the stem.
Example: `du₃` 'do!' (sg), `du₃-ze₂-en` 'do!' (pl).
Accusative pattern (§11.4.3): no FPP; PS-A on the addressee.

**{ḫa} (§25.4).** Modal proclitic. Three uses:
- Optative ('let X, may X'): `ḫa-mu-na-ab-šúm-mu` 'may he give it to him'.
- Affirmative ('indeed, surely').
- 1st/3rd person command (combined with `{÷i}` or `{÷a}`).
Spelled `ḫé-` or `ḫa-` depending on vowel harmony / period.

**{na(n)} 'must not' (§25.5).** Negative modal. Appears in 1st and 3rd
person prohibitions. Surface forms: `na-`, `nan-`.

**{ga} 'let me, let us' (§25.6).** Modal prefix for 1st-person
volitional. Restricted to 1SG and 1PL. Accusative pattern (§11.4.3): no
FPP; the singular form lacks a person suffix.
Example: `ga-na-šúm` 'let me give it to him'.

**{bara} 'never, by no means' (§25.7).** A strong negative regardless of
mood. Rare.

---

## Ch 26 — {na} (non-negative) and {ši} (§26, pp. 577–582)

**{na} (non-negative).** Rare and poorly understood; may be an
affirmative.

**{ši}.** Also rare and poorly understood; may overlap with the
terminative or have a focalizing function.

This is the shortest chapter — Jagersma flags both as open problems.

---

## Ch 27 — The complex sentence (§27, pp. 583–626)

**Subordination via nominalization (§27.3).** The chief Sumerian
strategy: the subordinate verb takes the nominalizing suffix `{÷a}`
(written `-a`), and the resulting nominalized form may be:
- An NP that takes a case marker indicating the subordinate clause's
  function (LOC `=÷a` = 'when'; TERM `=še` = 'because'; ABL `=ta` =
  'after'; GEN `=ak` = relative).
- The clause acts as a noun phrase.

Examples (§27.3 ex. 8–11):
- `ba-a-re-eš-a-ne` 'the men who went' — `=÷a` + `=enē=ak`
- `nu-ù-ub-kúr-ne-a` 'that they would not change ...' — `=÷a` alone
- `u₄ ... dab₅-ba-a` 'when he took ...' — `=÷a=÷a` (NOM + LOC)

**Conjunctions (§27.3.2).** Old Sumerian had essentially no
subordinating conjunctions. The Akkadian loan `ù` 'and' enters in Ur
III. A handful of adverbial subordinators emerge:
- `en-na` 'until'
- `u₄-da` 'if'
- `tukum-bé` 'if'

**Relative clauses (§27.5).** Mostly formed by attaching the nominalized
clause to a head noun, with the head taking the case marker.

**Conditionals (§27.6).** Old conditionals are juxtaposed clauses; later
texts use `tukum-bé` 'if' as a marker (§27.6.6).

---

## Ch 28 — Non-finite verbal forms (§28, pp. 627–676)

**Four non-finite forms.** Two perfective + two imperfective; each pair
has one form WITH and one WITHOUT the nominalizer `{÷a}`:

| Form | Aspect | NOM | Function |
|---|---|---|---|
| Present participle (§28.2) | Perfective | no | Timeless, generic action/state |
| Past participle (§28.3) | Perfective | yes | Past action or specific state |
| Imperfective participle (§28.4) | Imperfective | no | Generic ongoing action |
| {ed} participle (§28.5) | Imperfective | yes | Specific incomplete action |

**Forms.**
- Perfective non-finite stem: bare stem, optionally + `{÷a}` for past
  participle.
- Imperfective non-finite stem: stem + `{ed}` + optional `{÷a}`.

**Pronominal conjugation (§28.6).** Archaic non-finite construction
using a possessive pronoun to express the subject. Shows accusative
alignment (§11.4.3) — A and S use the same pronoun, DO does not.

---

## Ch 29 — Copular clauses (§29, pp. 677–714)

**The verb `me` 'be' (§29.1).** The only copula. Used in nearly all
non-verbal predications.

**Forms (§29.2).** Two presentations:
- **Finite copula**: regular finite verbal form of `me`.
- **Enclitic copula** `{÷am}`: a phonologically reduced enclitic that
  attaches to the predicate NP.

**Enclitic copula `{÷am}` forms (§29.2.3).**
| Subject | Form (3N default) | Spelling |
|---|---|---|
| 3N.S | `=÷am` | `-am₃` |
| 3SG.H.S | `=÷am` | `-am₃` |
| 1SG.S | `=me-en` | `-me-en` |
| 2SG.S | `=me-en` | `-me-en` |
| 3PL.H.S | `=me-eš` | `-me-eš` |
| 1PL.S | `=me-enden` | `-me-en-den` |
| 2PL.S | `=me-enzen` | `-me-en-zen` |

Used extensively in administrative texts (`X-am₃` 'it is X') and
identifying clauses.

**Special forms with modal/negative (§29.2.2).** With {ḫa}: `ḫa=÷i-me-Ø`
→ `ḫé-em`. With {nu}: `nu=÷i-me-Ø` → `nu-um` (rare; nominal clauses
preferred, §30).

---

## Ch 30 — Nominal clauses (§30, pp. 715–718)

**Rare construction.** A predicate without a copula. Used mainly under
negation with `nu` (the negative + nominal-clause construction is the
standard way to negate a copular clause; the negative copula `nu-um` is
rare): `alan ù kù nu` 'this statue is neither silver ...' (§30.4 ex. 22).

---

## Ch 31 — The nominalizing suffix `{÷a}` (§31, pp. 719–728)

**Multiple roles of `{÷a}`.** A single morpheme appears in many
contexts:
- Nominalizes finite verbal forms → subordinate clauses (§27, §31.4).
- Forms the past participle (§28.3).
- Attached to numerals `min` 'two' and `eš` 'three' to make definite
  reference: `2-na-bé` 'both, the two of them', `3-a-bé` 'the three of
  them' (§31.3.3).
- Adjectives: derives nouns and forms definite references (§10.6,
  §31.3.2).

**Surface form (§27.3.3).** `=÷a` post-vowel, assimilated `=Ca` post-
consonant (where C is the preceding consonant). E.g.: post-/b/ `=ba`,
post-/n/ `=na`, post-/r/ `=ra`, post-/š/ usually `=a` (spelling drops
the consonant).

**Why one morpheme?** Jagersma argues the unity is historical: the
nominalizer is the same morpheme across all uses, having developed
restrictive/definite-marking functions from a basic relative/nominalizing
core (§31.5).

---

## Cross-references for the cheat sheet

- Case-prefix coreference (§7 + ch. 17–20):
  - DAT case `{ra}` ↔ IO prefix `{nna}` (etc.) (ch. 17)
  - DIR case `{e}` ↔ OO prefix `{nni}` (etc.) (ch. 18) or local `{e}` (§20.3)
  - LOC case `{÷a}` ↔ local `{ni}` (§20.2)
  - COM case `{da}` ↔ dimensional `{da}` (§19.2)
  - ABL case `{ta}` ↔ dimensional `{ta}` (§19.3)
  - TERM case `{še}` ↔ dimensional `{ši}` (§19.4)
- Aspect ↔ inflection: §15.2.2 (perfective) and §15.2.3 (imperfective).
- Aspect ↔ uses: §15.4.2 (perfective uses), §15.4.3 (imperfective uses).
- Nominalization ↔ subordination: §27.3, §31.4.
- Compound verb ↔ phrase analysis: §4.3.4, also relevant to our
  `find_compound` MCP tool.
