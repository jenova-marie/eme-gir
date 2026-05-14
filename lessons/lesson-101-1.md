# Lesson 101-1 — Introduction to Sumerian

> **Agent role.** You are teaching the first session of a Sumerian 101 course
> distilled from Meadow's classroom-e₂-nun-na lectures. The learner has zero
> prior exposure. Move section by section in the order below — do not skip
> ahead. Each section has a short drill the learner does before you reveal the
> answer. Be encouraging; Sumerian is famously irregular and learners panic
> easily. Repeat the mantra **"rules AND exceptions to almost every rule"**
> often.

## Where to send the learner for primary-source lookups

The eme-gir MCP servers expose the same data Meadow points at in the source
videos (EPSD2, ETCSL, CDLI, OGSL). When the learner asks "is this real?" or
"is this attested?" — reach for them:

- `eme-gir-epsd2.translate_english` — English → Sumerian candidates ranked by
  attestation count. Use this on every vocabulary item the learner asks about.
- `eme-gir-epsd2.lookup_entry` / `see_examples` — show the entry detail page
  and a real attested line from a real tablet.
- `eme-gir-ogsl.cuneify` — render any transliteration as Unicode glyphs so the
  learner sees what they would see on a tablet.
- `eme-gir-ogsl.lookup_sign` — look up a sign by name (`LUGAL`) or value
  (`lugal`) to show every reading it carries.

Always call `start_here()` on each server once at the beginning of the
session — the server's own onboarding is canonical and supersedes anything
you remember from training.

---

## §1 — Pronunciation

Three letters trip up English speakers. Drill these first:

| Letter | Sound | Example |
| --- | --- | --- |
| **ŋ** (sometimes written **ğ**) | "ng" as in *running* | **ŋ**iri "foot" → *ngiri* |
| **š** | "sh" as in *ship* | **š**aŋ "head" → *shang* |
| **ḫ** | "kh" / "ch" as in Scottish *loch* | **ḫ**ul "evil" → *khul* |

Other letters use their typical IPA / English values. Vowels are pure — `a` is
*ah*, `e` is *eh*, `i` is *ee*, `u` is *oo*. There is no `o` in Sumerian.

> **Drill 1.1.** Read aloud: `ŋar`, `šum`, `ḫul`, `kalag`, `lugal`.
>
> <details><summary>Answer</summary>
>
> *ngar, shoom, khool, kah-lag, loo-gal*. The doubled vowel in *lugal* is
> just an English notation — both vowels are short.
> </details>

---

## §2 — Cuneiform overview

A single cuneiform sign can do **three different jobs**, and you have to read
context to know which. This is the central insight of the lesson.

### 2.1 As a logogram (a whole word/idea)

| Sign | Transliteration | Meaning |
| --- | --- | --- |
| 𒂍 | e₂ | "house, temple" |
| 𒇽 | lu₂ | "man" |
| 𒃲 | gal | "big, great" |
| 𒈗 | lugal | "king" |

### 2.2 As a syllable in a longer word

Cuneiform signs can be borrowed for their phonetic value. `ga-an-du₃` reads
literally as three signs you might gloss elsewhere as "milk-sky-build" — but
in this context they spell out the verb form `ga-an-du₃` "let me build."

### 2.3 As a determinative (an unspoken category marker)

A determinative tells the reader *what kind of thing follows*. It is **written
but not spoken**. Conventionally written as a superscript in modern
transliteration.

| Determinative | Marks | Example |
| --- | --- | --- |
| 𒀭 = ᵈ (diŋir) | a divine name | 𒀭𒂗𒆤 = ᵈEnlil — "(the god) Enlil" |
| 𒆠 = ki (after a word) | a place name | tir-an-naᵏⁱ = "Uruk (place)" |
| 𒄑 = ŋeš (before a word) | something made of wood | ŋeš-eren = "cedar (wood)" |

### 2.4 Subscript numbers (du, du₂, du₁₀, du₁₁…)

Different signs with the **same phonetic value** are distinguished by
subscript numbers. The numbers are not pronounced — they're an Assyriological
convention so we can tell the signs apart on the page.

| Form | Meaning |
| --- | --- |
| du | to walk / to go |
| du₁₀ | sweet, good (adj) / to enjoy (v) |
| du₁₁ | to speak |

So `mu-un-du` alone is ambiguous; `mu-un-du₁₁` is unambiguously "he said."

### 2.5 Spelling drift across periods

Sometimes the **same word** is written two ways in different eras:
`du₁₀` and `dug` both mean "good/sweet." Old Sumerian tends toward `dug`;
later periods drop the final consonant. Don't treat these as two words.

> **Drill 2.1.** What three things can a single cuneiform sign be?
>
> <details><summary>Answer</summary>
> A logogram (whole word), a syllable, or a determinative.
> </details>
>
> **Drill 2.2.** In `𒀭𒂗𒆤`, what is the role of `𒀭`?
>
> <details><summary>Answer</summary>
> A determinative — it tells the reader that the name *Enlil* that follows is
> divine. It is silent.
> </details>

---

## §3 — Nouns

### 3.1 No gender — but yes, noun class

Sumerian doesn't mark masculine vs feminine the way Romance languages do.
Instead, every noun is in one of two **classes**:

- **Human class** — gods, people, occupational titles, kinship terms.
  - Possessive "his/hers" is `-ani`.
- **Non-human class** — animals, objects, plants, places, abstractions.
  - Possessive "its" is `-bi`.

This class system will come back when we get to case endings (lesson 3) and
verbal conjugation prefixes (lesson 3). Memorize the principle now: **the two
classes are HUMAN and NON-HUMAN, not male and female**.

### 3.2 Simple nouns (one sign = one word)

| Sign | Transliteration | Meaning |
| --- | --- | --- |
| 𒈗 | lugal | king |
| 𒂍 | e₂ | house, temple |
| 𒊩 | munus | woman |
| 𒌉 | dumu | child, son |

### 3.3 Compound nouns (two signs glued with a hyphen)

| Cuneiform | Parts | Compound meaning |
| --- | --- | --- |
| 𒁾𒊬 | dub "tablet" + sar "to write" | dub-sar "scribe" (literally *tablet-writer*) |
| 𒂍𒃲 | e₂ "house" + gal "great" | e₂-gal "palace" (literally *great house*) |

A **hyphen** is the visual cue for "these signs form one compound noun." If
you see `e₂ gal` (with a space, no hyphen) that's *house big* — the adjective
construction we'll cover in §5 — and it means the same thing in this case.
Cool fact: Sumerian palaces really are just "great houses."

> **Drill 3.1.** What's the difference between *dub-sar* and *dub sar*?
>
> <details><summary>Answer</summary>
> Trick question: in transliteration the hyphen marks a compound noun, but
> the underlying signs are identical. Both surface forms refer to a scribe.
> </details>

---

## §4 — Plurals

There are **three** ways to mark a noun as plural. They are not
interchangeable.

### 4.1 The plural suffix `-ene` (HUMAN class only)

`-ene` only attaches to human-class nouns. It usually appears with an
auslaut consonant pulled forward (see §5 for the auslaut concept):

- diŋir + ene → `diŋir-re-ne` "gods" (r-auslaut from `diŋir`)
- lugal + ene → `lugal-le-ne` "kings"

You can also see **reduplication** combined with `-ene`:
`diŋir-diŋir-re-ne` = "all the gods, the multitude of gods."

### 4.2 Reduplication of the noun

Write the noun twice. `lugal-lugal` = "kings."  This works for both classes
but is more common for non-human. It can carry a flavor of "many" or "all of
them."

### 4.3 No marking at all — context decides

`lugal i₃-ŋen` can mean "the king walked" or "the kings walked"; the verb
chain may or may not disambiguate. **Sumerian regularly leaves number
unmarked.**

> **Drill 4.1.** Pluralize: *diŋir*, *gud* "ox," *munus*, *e₂*.
>
> <details><summary>Answer</summary>
>
> - *diŋir* (human-class): `diŋir-re-ne` OR `diŋir-diŋir-re-ne`.
> - *gud* (non-human): `gud-gud` (reduplication) — `-ene` won't fit.
> - *munus* (human): `munus-e-ne` or `munus-munus`.
> - *e₂* (non-human): `e₂-e₂` or simply context.
>
> Refuse the urge to slap `-ene` on non-human nouns; it's a beginner trap.
> </details>

---

## §5 — Adjectives, the auslaut, and "the pesky -a"

### 5.1 Position: adjectives go AFTER the noun

In English: **big house**. In Sumerian: **e₂ gal** ("house big"). Always.

| Sumerian | English |
| --- | --- |
| lu₂ gal | big man |
| ᵈinanna kug-ga | holy Inanna |
| lugal maḫ | exalted king |

### 5.2 Verbs as adjectives — add `-a`

Many Sumerian "adjectives" are really stative verbs (*to be holy*, *to be
great*). To use one as an adjective, you tack `-a` onto the end:

- kug "to be holy/pure" → kug-**a** "holy" → written `kug-ga`
- maḫ "to be exalted" → maḫ-**a** "exalted" → written `maḫ-a`

### 5.3 The auslaut

Sumerian doesn't like a vowel sitting alone at the end of a word. When you
add a vowel suffix to a consonant-ending word, the **final consonant of the
word reappears at the start of the next sign** — this is called an
**auslaut**.

- kug + a → ku-**ga** (the g reappears, glued to the a)
- diŋir + ene → diŋir-**re**-ne (r-auslaut)
- lugal + ene → lugal-**le**-ne (l-auslaut)

This is purely orthographic — when we **normalize** a sentence (write it the
way it would sound morphemically) we write `kug.a`, `diŋir.ene`, `lugal.ene`
and forget about the auslaut.

### 5.4 The silent `-g` (kala(g), maḫ, etc.)

Some words have a "hidden" final consonant that only surfaces when a vowel
follows. `kala(g)` "to be strong":

- ᵈinanna **kala-ga** "mighty Inanna" — the g surfaces because of the
  adjective-`-a`.
- lugal mu-un-**kala** "the king was strong" — bare verb, no suffix, no g.

The parentheses in `kala(g)` mean: this g is silent until a vowel comes
along to wake it up.

### 5.5 Sometimes the `-a` is just dropped

Both of these are valid:

- `lugal gal` "great king"
- `lugal gal-la` "great king" (with the l-auslaut + a)

Treat the unmarked form as the default and the `-a` form as an emphasis or
period preference. **Don't get rigid about this.**

### 5.6 Doubled adjective = plural noun

If the adjective is reduplicated, the noun is usually plural:

- munus maḫ-maḫ "mighty women" (not "a mighty mighty woman").

> **Drill 5.1.** Translate to English: `dumu tur`, `e₂-gal gal`, `lugal maḫ`.
>
> <details><summary>Answer</summary>
>
> - `dumu tur` — small child (tur = "small")
> - `e₂-gal gal` — great palace (palace = compound noun, gal = adjective)
> - `lugal maḫ` — exalted king
>
> Note that `e₂-gal gal` and `e₂ gal gal` would both be tolerable — the
> first reads "palace big," the second "house big big" → "a really big
> house," same idea in different syntactic shape.
> </details>

---

## §6 — Three takeaways for adjectives

State these explicitly at the end of the section. The learner WILL forget
them:

1. **Adjectives come after the noun they modify.**
2. **They sometimes carry an `-a` (with auslaut) — especially when the
   underlying word is a stative verb.**
3. **They may be unmarked.** When in doubt, try both and see which makes
   sense.

---

## §7 — End-of-lesson exercise

Have the learner translate each item. They are encouraged to use
[EPSD2](https://oracc.museum.upenn.edu/epsd2/sux) (or `translate_english`
via the eme-gir-epsd2 MCP) to look up unfamiliar words. Remind them: **when
multiple meanings exist, pick the one with the highest attestation count.**

### Part A — English to Sumerian (single words)

1. god
2. house
3. big
4. great
5. eat
6. woman
7. man
8. mother
9. speak
10. ruler

<details><summary>Answer key</summary>

1. diŋir
2. e₂
3. gal
4. maḫ
5. gu₇
6. munus
7. lu₂
8. ama
9. dug₄
10. ensi₂

Multiple-meaning words are common — any defensible answer the learner can
back up with EPSD2 is correct.

</details>

### Part B — Sign reading

11. In the sentence `𒈗 𒂊 𒀭 𒈹 𒊏 𒈬 𒌦 𒅗`, what role does the `𒀭` play?

<details><summary>Answer</summary>
A determinative — it marks the following name (Inanna) as divine. Silent in
speech.
</details>

### Part C — Noun + adjective phrases

Translate. When the second element ends in `-ga`/`-la`, it's likely a
verb-turned-adjective; look up the part before the hyphen.

1. lu₂ gal
2. ama dug₃-ga
3. dumu tur
4. lugal maḫ
5. e₂-gal gal
6. lugal gal-gal
7. diŋir-re-ne
8. lugal-la-ni (remember `-ani` = "his/her")

<details><summary>Answer key</summary>

1. big man
2. sweet mother (dug₃ "to be sweet/good," adj form)
3. little child
4. exalted king
5. great palace
6. great kings (reduplicated adjective ⇒ plural noun)
7. gods (human-class plural with r-auslaut + `-ene`)
8. his/her king

</details>

---

## §8 — Teaching notes for the agent

- **The three jobs of a cuneiform sign** is the single most important
  takeaway from this lesson. If the learner walks away knowing nothing else,
  they need to know that a sign can be a word, a syllable, OR a
  determinative.
- The auslaut concept feels deeply weird the first time. Re-show it after
  every adjective example until it sticks.
- Avoid the temptation to teach the case endings yet — they come in lesson
  3. Stop at "adjectives come after the noun."
- Sumerian is irregular. Whenever the learner pushes back ("but you said
  X"), agree that the rule exists AND the exception exists. The phrase
  "Sumerian is more like a suggestion of an idea than a solid idea" comes
  straight from the original lesson and is worth quoting.
- Next session: lesson 102-2 (Basic Verbs). Preview by saying: "Next time
  we'll learn how to build a sentence with a verb, and what `mu-un-` means
  at the start of so many verbs."
