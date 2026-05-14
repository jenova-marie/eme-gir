# Lesson 101-2 — Basic Verbs

> **Agent role.** You are teaching the second session. The learner has
> completed lesson 101-1 (pronunciation, cuneiform overview, nouns, plurals,
> adjectives) — open with a brief recap, then introduce verbs. The goal is
> that by the end of this session the learner can read a basic
> SUBJECT-OBJECT-VERB sentence and identify the verbal chain.
>
> Reach for the eme-gir MCP servers whenever the learner asks "is that
> attested?" — particularly `eme-gir-epsd2.see_examples` to pull a real
> tablet line containing the verb under discussion.

---

## §0 — Recap of lesson 1

Before you move on, confirm the learner can list these. If they can't,
re-explain in 30 seconds:

1. A cuneiform sign can be a **word**, a **syllable**, or a **determinative**.
2. Nouns are **human-class** or **non-human-class** (not male/female).
3. Simple nouns are one sign; compound nouns are two signs joined by a
   hyphen (`dub-sar` "scribe").
4. Plurals: `-ene` (human only), reduplication, or unmarked.
5. Adjectives come **after** the noun, optionally with `-a` and an
   auslaut. Stative verbs can be adjectives if you stick an `-a` on them.

Worked recap examples:

- `lu₂ gal` — "big man"
- ᵈinanna kug-ga — "holy Inanna"

---

## §1 — What a verb actually does

Four terms the learner needs before we touch a single Sumerian sentence.
Walk through them slowly:

| Term | Definition | English example |
| --- | --- | --- |
| **Transitive** | the subject acts on an object | *Gilly hit the ball.* |
| **Intransitive** | no object — the subject just acts | *Gilly walks.* |
| **Active** | subject performs the action | *Gilly hit the ball.* |
| **Passive** | subject receives the action | *Gilly was hit by the ball.* |

**Diagnostic question:** *"Is the subject doing something to someone or
something else?"*  Yes → transitive. No → intransitive.

> **Drill 1.1.** Classify each as transitive or intransitive.
>
> 1. The lion roared.
> 2. The lion ate the sheep.
> 3. The temple stood.
> 4. The king built the temple.
>
> <details><summary>Answer</summary>
> 1. Intransitive. 2. Transitive. 3. Intransitive. 4. Transitive.
> </details>

---

## §2 — Anatomy of a verbal chain

A Sumerian finite verb is built like this:

```
[ prefixes ] - [ VERB BASE ] - [ suffixes ]
   who/what acted,        the verb itself,    who/what was acted on,
   movement, mood,                            tense, mood, plurality
   negation, etc.
```

The whole thing is one phonological word — the **verbal chain**.

Walk through this example carefully — write it on a whiteboard if you have
one:

> **lugal-e   e₂   mu-un-du₃**
>
> *"The king built the temple."*

| Piece | Role |
| --- | --- |
| `lugal` | "king" — subject |
| `-e` | **ergative** suffix → marks "king" as the actor |
| `e₂` | "temple/house" — direct object |
| `mu-` | conjugation prefix (we'll learn its meaning in lesson 3 — for now: it's there because the action was perfective and oriented toward the speaker) |
| `-un-` | "he/she" agent marker (the `n` is the 3rd-person-human marker; the `u` is just a vowel borrowed from the prefix before it) |
| `du₃` | verb base "to build" |

### 2.1 Default tense = perfective (past)

Sumerian's bare verb is **perfective**, which English usually maps to
**simple past**: `mu-un-du₃` = "she built (it)" not "she builds (it)." We'll
learn the present/future (imperfective) forms in lesson 4.

### 2.2 Word order

> **SUBJECT — OBJECT — VERB**

Almost every Sumerian sentence follows SOV. Read sentences right-to-left
relative to English and you'll be close.

> **Drill 2.1.** Identify the subject, object, and verb in:
>
> `munus-e kaš mu-un-naŋ`
>
> <details><summary>Answer</summary>
> Subject: munus (woman) + ergative `-e`. Object: kaš (beer). Verb:
> mu-un-naŋ "she drank." Translation: *the woman drank the beer.*
> </details>

---

## §3 — Simple vs. compound verbs

### 3.1 Simple verbs — one base

- du₃ "to build"
- du "to go/walk"
- gi₄ "to return"
- dim₂ "to form, fashion"

### 3.2 Compound verbs — noun + verb glued together

These are noun-plus-verb idioms that act as a single lexical item. The
noun usually narrows the verb's meaning. Compound verbs are written with a
**long dash** between the noun and the verb (`–`):

| Compound | Parts | Meaning |
| --- | --- | --- |
| inim–gi₄ | inim "word" + gi₄ "return" | "to answer, to reply" |
| gu₃–de₂ | gu₃ "voice" + de₂ "pour" | "to speak (out)" |
| igi–bar | igi "eye" + bar "cut open" | "to look at" |
| za₃-mi₂–dug₄ | za₃-mi₂ "praise" + dug₄ "say" | "to praise" |

In EPSD2 / `translate_english` you have to search the parts as separate
words; if you search "za₃-mi₂–dug₄" you'll get zero hits. Use `zamin` or the
two parts. **Pass this tip to the learner explicitly.**

> **Drill 3.1.** Which of these are compound verbs?
>
> 1. mu-un-du₃
> 2. gu₃ mu-un-de₂
> 3. i₃-gub
> 4. igi mu-un-ši-in-bar
>
> <details><summary>Answer</summary>
> 2 and 4 are compound verbs (gu₃–de₂ "to speak"; igi–bar "to look").
> 1 is a simple verb (du₃). 3 is a simple verb (gub "to stand").
> </details>

---

## §4 — Participles and passives (the first taste of "the pesky -a")

You already met `-a` in lesson 1 as the adjective-from-verb marker
(`kug-ga` "holy"). It does **more jobs** with verbs:

### 4.1 Participle ("-ing")

If you see a bare verb with `-a` and no full verbal chain in front of it,
try translating it as a present participle:

- ᵈUtu e₃-a — "the rising sun" (e₃ "to come out" + -a → "rising")
- dug₄-ga — "speaking" (or "spoken" — see 4.2)
- ŋar-ra — "placing" / "placed"

### 4.2 Passive

The same `-a` can mark a passive participle:

- šum₂-ma — "given"
- ŋar-ra — "placed, set"

> **Tip for the learner.** When you see a verb with a trailing `-a`, try
> both readings and keep the one that fits the sentence. Active participle
> first, passive second.

---

## §5 — The genitive `-ak` ("of")

This is the most important suffix in this lesson. **Marker:** `-ak`.
**Position:** after the *possessor*, not the *possessed*.
**Translation:** "X of Y" — but you translate left-to-right, so flip the
order in English.

### 5.1 The canonical example

> **e₂ lugal.ak** → "house of the king" → written `e₂ lugal-la`

How did `-ak` become `-la`?

1. Sumerian doesn't like to end a word with k → the **k drops**.
2. The remaining `a` needs a consonant — `lugal` ends in `l`, so the
   **l auslaut** brings the consonant forward → `-la`.

So `e₂ lugal-la` (surface form) = `e₂ lugal.ak` (normalized form) = "house
of the king."

### 5.2 The K comes back if something follows

If anything attaches **after** `-ak`, the k surfaces again:

> **dumu lugal-la-ke₄-ne** = `dumu lugal.ak.ene` = "sons of the king"

Note two important things:

1. The k of `-ak` is now written because the plural marker `-ene` follows
   it.
2. The plural marker attaches to **dumu** ("son"), not to **lugal**
   ("king"). Sumerian treats `[dumu lugal.ak]` as a single conceptual unit
   ("son-of-the-king") and pluralizes the whole unit. Pluralizing the king
   instead would be `dumu lugal.ene.ak` "son of the kings."

### 5.3 When the word ends in a vowel, the `a` of `-ak` may vanish

- nin ŋir₂-su = `nin ŋir₂.su.ak` = "the lady of Girsu"
  (no `-a` written because `su` ends in a vowel)
- e₂ lugal-la-na = `e₂ lugal.ani.ak` = "the house of her king"
  (the `a` of `-ak` swallows the `i` of `-ani` → `-na`)

### 5.4 Three quick rules

> 1. **Consonant-final noun** → write `-a` (often with auslaut).
>    Example: `lugal.ak` → `lugal-la`.
> 2. **Vowel-final noun** → `-a` may be dropped entirely, or the vowels
>    fuse.
>    Example: `ŋir₂.su.ak` → `ŋir₂-su`.
> 3. **Anything follows `-ak`** → the k is written.
>    Example: `lugal.ak.ene` → `lugal-la-ke₄-ne`.

Heads-up: older Sumerian is messier and you'll see `-ak` written on
vowel-final nouns too. Modern temple-Sumerian writers (Entu Siri, this
course's author) tend to write `-ak` explicitly because it's easier to
read.

> **Drill 5.1.** Normalize and translate:
>
> 1. e₂ diŋir-ra
> 2. dub-sar nin-ŋir₂-su
> 3. dumu lugal-la-ke₄-ne
>
> <details><summary>Answer</summary>
>
> 1. `e₂ diŋir.ak` — "house of the god"
> 2. `dub.sar nin.ŋir₂.su.ak` — "scribe of the lady of Girsu" (two
>    chained genitives, the second omitted because of the vowel-final
>    noun)
> 3. `dumu lugal.ak.ene` — "sons of the king" (k surfaces, plural on
>    *dumu*)
>
> </details>

---

## §6 — "The pesky `-a`": a three-tip heuristic

By now the learner has seen `-a` doing four different jobs. Drill the
**three diagnostic questions** they should ask, in this order:

1. **Is the base word an adjective (or a stative verb being used as one)?**
   → translate as adjective. (`kug-ga` "holy")
2. **Is the base word a verb?**
   → translate as participle ("-ing") OR passive ("-en"). Try active
   first. (`dug₄-ga` "speaking" / "spoken")
3. **Is the base word a noun?**
   1. Is there **another noun directly before it**? → genitive "of".
      (`e₂ lugal-la` "house of the king")
   2. No noun before it? → wait for Sumerian 201 (we'll meet `-a` as the
      locative "in" next lesson, and a few other functions later).

> **Drill 6.1.** Classify the `-a` in each:
>
> 1. ᵈinanna kug-ga
> 2. nin lugal-la
> 3. mu-un-ŋar-ra
>
> <details><summary>Answer</summary>
> 1. Adjective (`kug` "to be holy" + `-a`).
> 2. Genitive (`nin` is a noun, `lugal` is a noun → "lady of the king").
> 3. Participle/passive (`ŋar` "place" + `-a` → "placed").
> </details>

---

## §7 — Cuneiform inventory for this lesson

The learner should be able to read and write each of these.

| Sign | Reading | Sign | Reading |
| --- | --- | --- | --- |
| 𒈗 | lugal | 𒄭 | dug₃ |
| 𒂍 | e₂ | 𒇽 | lu₂ |
| 𒂊 | e | 𒂠 | še₃ |
| 𒂗 | en | 𒉼 | pana |
| 𒈬 | mu, ŋu₁₀ | 𒈾 | na |
| 𒀭 | an (sky / divine determinative) | 𒂵 | ga |
| 𒈹 | inanna | 𒅗 | dug₄ |
| 𒂼 | ama | 𒆬 | kug |
| 𒆤 | ke₄, lil₂ | 𒈤 | maḫ |
| 𒌦 | un, kalam | 𒅥 | gu₇ |
| 𒃲 | gal | 𒌉 | dumu |
| 𒆗 | kala(g) | 𒁺 | du |
| 𒆕 | du₃ | 𒆠𒉘 | ki-aŋ₂ (compound) |
| 𒊩 | munus | | |

Use `cuneify` on the eme-gir-ogsl server to render any transliteration
the learner asks about; use `lookup_sign` to show all readings of a given
sign.

---

## §8 — End-of-lesson exercise

### Part A — Normalize and translate

Reminders to give the learner:

- `-e` on a noun = **ergative**; marks the actor of a transitive sentence.
- `mu-un-` = **ventive** (motion toward the speaker) + **3rd-person agent**.
- Default verb tense = **perfective past**.
- `-a` on a noun is sometimes "into" (locative — we'll cover in lesson 3).
- `-a` on a noun can also be the genitive "of."
- `-ŋu₁₀` on a noun = "my" (lesson 3).
- `-še₃` = "to, toward."

1. ama-ŋu₁₀ e₂-a mu-un-du
2. lugal-e ᵈinanna za₃-mi₂ mu-un-dug₄  *(compound verb: za₃-mi₂–dug₄)*
3. lugal-lugal-e e₂ mu-un-du₃
4. lugal-la-ni e₂-a
5. munus-e kaš mu-un-naŋ
6. lu₂-e munus ne mu-un-su-ub  *(compound verb: ne–sub "to kiss")*
7. ŋa₂-e emegir mu-zu  *("ŋa₂-e" = "I" — translate the verb as 1st singular)*
8. piriŋ-e gukkal bi₂-ib₂-gu₇  *(bi₂-ib₂- = non-human agent, "it")*

<details><summary>Answer key</summary>

1. `ama.ŋu₁₀ e₂.a mu.un.du` — "My mother went into the house."
2. `lugal.e ᵈinanna za₃.mi₂ mu.un.dug₄` — "The king praised Inanna."
3. `lugal.lugal.e e₂ mu.un.du₃` — "The kings built the temple."
4. `lugal.ani e₂.ak` — "The house of her king." (genitive — no verb)
5. `munus.e kaš mu.un.naŋ` — "The woman drank the beer."
6. `lu₂.e munus.0 ne mu.un.sub` — "The man kissed the woman."
7. `ŋa₂.e emegir.0 mu.zu` — "I learned Sumerian!"
8. `piriŋ.e gukkal.0 bi₂.ib₂.gu₇` — "The lion ate the fat-tailed sheep."

</details>

### Part B — Transliterate, normalize, translate

Use the cuneiform inventory in §7.

1. `𒇽𒂊 𒂍𒃲 𒈬𒌦𒆕`
2. `𒀭𒈹𒂊 𒀭𒂗𒆤𒂠 𒈬𒌦𒅗`
3. `𒀭𒈹𒂊 𒂼𒈬 𒆠𒈬𒌦𒉘`  *(compound verb: ki-aŋ₂ "to love")*
4. `𒉼𒀭𒈾`

<details><summary>Answer key</summary>

1. `lu₂-e e₂-gal mu-un-du₃` = `lu₂.e e₂.gal mu.un.du₃` — "The man built the
   palace." (or "the big house")
2. `ᵈinanna-e ᵈen-lil₂-še₃ mu-un-dug₄` = `ᵈinanna.e ᵈenlil₂.še₃ mu.un.dug₄`
   — "Inanna spoke to Enlil."
3. `ᵈinanna-e ama-ŋu₁₀ ki mu-un-aŋ₂` = `ᵈinanna.e ama.ŋu₁₀ ki.mu.un.aŋ₂` —
   "Inanna loved my mother."
4. `pana an-na` = `pana an.ak` — "the bow of heaven" (i.e., a rainbow).

</details>

---

## §9 — Teaching notes for the agent

- The verbal chain is the single hardest topic in this lesson. Walk
  through `lugal-e e₂ mu-un-du₃` at least three times before introducing
  the genitive — the learner needs the chain to feel "normal" first.
- Don't yet explain what `mu-` means versus `ba-` versus `i₃-`. That's
  lesson 3. Tell the learner: "you'll learn the choice of prefix next
  week; for now, just notice that there is a prefix."
- The `-a` heuristic is the most useful thing in the lesson. Practice it
  on real attested forms — use `eme-gir-epsd2.see_examples` with `dug₄`
  or `ŋar` to surface lines with the `-a` ending and walk through which
  job it's doing.
- Next session: lesson 101-3 (Case Markers). Preview by telling the
  learner: "next time we'll meet the eight Sumerian prepositions, and
  why they go *after* the noun instead of before it."
