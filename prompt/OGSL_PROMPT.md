# `eme-gir-ogsl` — cuneiform sign rendering MCP server

You are connected to a local copy of the **Oracc Global Sign List (OGSL)** —
the canonical catalogue of cuneiform signs maintained by Steve Tinney and
the Oracc team at the University of Pennsylvania. ~3,000+ signs, each with
Unicode codepoint(s), an OGSL sign name, and the full set of phonetic
readings that map to it. Data is CC0; no network calls; loaded once at
server start from `corpus/ogsl.zip`.

**Cross-language scope.** OGSL covers cuneiform across **every language
that used the script** — Sumerian, Akkadian, Hittite, Hurrian, Elamite,
Eblaite, Ugaritic, Hattic, Luwian. The same signs are read differently in
different languages (the LUGAL sign 𒈗 = `lugal` in Sumerian, `šarru` in
Akkadian); OGSL tracks both. This server is useful for any cuneiform
project, not just Sumerian.

---

## The two tools

### `cuneify(spelling: str)`

Convert an Oracc-style transliteration into Unicode cuneiform glyphs.
Returns a `CuneifyResponse`:

```
{
  "spelling":         "lugal-e e₂ mu-na-du₃",    # echo of input
  "cuneiform":        "𒈗𒂊 𒂍 𒈬𒈾𒆕",          # the glyphs
  "complete":         true,                      # no □ placeholders
  "placeholder_count": 0,                        # count of unknown signs
}
```

**Use when:** you've composed a Sumerian transliteration and want to
display the cuneiform glyphs alongside it. The final step of an
English → Sumerian translation reply.

### `lookup_sign(query: str, limit: int = 10)`

Look up a sign by name or phonetic value. Returns a `LookupSignResponse`
with up to `limit` matches (cap 30). Each match is a `SignInfo`:

```
{
  "sign_name":  "LUGAL",                                  # OGSL canonical name
  "glyph":      "𒈗",                                      # Unicode glyph
  "uname":      "CUNEIFORM SIGN LUGAL",                   # Unicode character name
  "hex":        "x12217",                                 # codepoint
  "values":     ["lugal", "šarru", "šar₃", ...],         # all phonetic readings
  "matched_by": "sign_name",                              # or "value:lugal"
}
```

**Use when:**

- You hit a placeholder `□` in `cuneify` output and need to investigate which sign(s) the renderer didn't recognize.
- You see an unfamiliar reading in attested text and want to know which sign it represents and what other readings that sign carries (polyphone disambiguation).
- You need the Unicode codepoint for a specific sign to embed it in a custom rendering.

---

## Transliteration conventions (input contract for `cuneify`)

The spelling string must follow Oracc's transliteration convention. The
renderer handles the following patterns:

| Pattern | Example | Effect |
|---|---|---|
| **Hyphen-joined sign sequence** within one word | `lu₂-gal` | Each hyphen-separated piece is one sign; result is the concatenated glyphs (𒇽𒃲). |
| **Sign-list dot-compound** | `AB.GAR` | Uppercase dot-separated form names a compound by its constituent signs. |
| **Braced determinative (preposed)** | `{d}lugal`, `{ŋeš}gigir`, `{kuš}lu-ub₂`, `{na₄}za-gin₃`, `{munus}lukur` | Silent classifier rendered as its glyph before the word (`{d}` = divine 𒀭, `{ŋeš}` = wood 𒄑, `{kuš}` = leather, `{na₄}` = stone, `{munus}` = female). |
| **Braced determinative (postposed)** | `lugal{mušen}`, `unug{ki}` | Determinative comes AFTER the word (`{mušen}` = bird, `{ki}` = place). |
| **Multi-word spelling** | `gu₃ mu-un-de₂` | Whitespace separates words; rendered as glyph-block + space + glyph-block. |
| **Morphology tail (post-backslash)** | `lugal-bi\a` | The part before the `\` renders normally; everything after the `\` is dropped (treated as a non-glyph morphology annotation). |
| **Compound grapheme with pipes** | `muₓ(|KA×GAN₂@t|)` | The renderer uses the `\| … \|` inner form (treated as one compound sign). |
| **Subscript digits** for sign-value disambiguation | `du`, `du₂`, `du₃`, `du₁₀`, `du₁₁` | Each subscript variant is a different sign. Either Unicode subscripts (`du₃`) or ASCII digits (`du3`) works. |
| **`x` (lowercase)** | `mux(|KA×GAN₂@t|)` | Subscript-x marker meaning "value uncertain"; used inside compound notation. |

**What the renderer does NOT do:**

- It doesn't normalize between transliteration conventions (j↔ŋ, c↔š, etc.). Use Oracc-Sumerian conventions: `ŋ` (not `j` / `g̃`), `š` (not `c` / `sh`), `ḫ` (not `h` / `kh`).
- It doesn't interpret morphology. `lugal-e` renders as `lugal` + `-e` (two signs); the renderer doesn't know that `-e` is an ergative case suffix.

---

## Placeholder `□` (U+25A1) — handle honestly

When OGSL doesn't have a glyph for a reading you supplied, that piece
of the output is rendered as **`□`** (Unicode white square). The
response's `complete` field is `false` and `placeholder_count` tells
you how many `□` were emitted.

**Do not silently drop or hide these.** When a `cuneify` result has
placeholders, disclose the gap in your reply, e.g.:

> *Cuneiform: `𒈗𒂊 𒂍 □`. The verb form didn't render — `bi₂-in-du₃` is missing one sign from OGSL.*

Then call `lookup_sign(value)` on each problem reading to investigate
(it may be a sign-list naming mismatch, a compound grapheme that needs
pipe notation, or a genuine OGSL gap).

About 7% of Eme-gir glossary spellings include at least one sign that
renders as `□`. Most renderings (~93%) are complete.

---

## ASCII ↔ Unicode subscript normalization

`lookup_sign` normalizes ASCII digits in queries to Unicode subscripts
before matching, so both spellings work:

| Query | Normalized to | Matches |
|---|---|---|
| `"gu7"` | `gu₇` | sign `\|KA×GAR\|` (𒅥, "eat") |
| `"gu₇"` | `gu₇` | same |
| `"E2"` | `E₂` | sign `E₂` (𒂍, "house") |
| `"e2"` | `e₂` | same sign by phonetic value |
| `"lu2"` | `lu₂` | sign `LU₂` (𒇽, "man") |
| `"LUGAL"` | `LUGAL` | sign `LUGAL` (𒈗) — uppercase = sign name |

Convention: **uppercase = sign name**, **lowercase = phonetic value**.
The same sign typically has one canonical name and many values.

`cuneify` accepts ASCII subscripts the same way — `cuneify("lugal-e e2 mu-na-du3")` works identically to the Unicode-subscript version.

---

## Cross-cuneiform polyphony

Many signs have phonetic readings in multiple languages. `lookup_sign`
returns ALL known values, regardless of language. For example:

```
lookup_sign("LUGAL")
→ values: ["lugal", "lugala", "šar₃", "šarra", "šarru", "šarrum",
           "šugur", "rab₃", "sag₄", "saŋ₄", "lillan", "nurra",
           "bišeba", "bišebi", "haniš₂", "kaššeba", "kaššebi",
           "ŋušurₓ", "iliₓ", "nūr-ili", "šaraₓ"]
```

The Akkadian reading is `šarru` "king"; the Eblaite reading is
`bišebi`; the Hurrian reading is `kaššeba`; etc. When working in
Akkadian or Hittite, treat OGSL as your universal sign-name reference
and rely on the language-specific values list to find the reading you
need.

---

## Common workflows

### 1. Render a composed Sumerian transliteration as cuneiform
```
cuneify("lugal-e e₂ mu-na-du₃")
→ {"cuneiform": "𒈗𒂊 𒂍 𒈬𒈾𒆕", "complete": true, "placeholder_count": 0}
```
Render the `cuneiform` alongside the transliteration in your reply.

### 2. Investigate a placeholder
```
cuneify("…tricky-spelling…")
→ {"cuneiform": "…□…", "complete": false, "placeholder_count": 1}

# Find what's missing:
lookup_sign("tricky-value-here")
→ likely 0 results OR an unexpected sign
```

### 3. Look up an unfamiliar sign in attested text
```
You see "muₓ(|KA×GAN₂@t|)" in a corpus line and want to know what sign it is.
lookup_sign("|KA×GAN₂@t|")  # the pipe-form name is queryable
→ returns the sign with its Unicode codepoint + all readings
```

### 4. Disambiguate a polyphone
```
You see "du" in transliteration but the corpus has many du-signs (du, du₂, du₃, du₁₀, du₁₁).
lookup_sign("du")   → the bare-du sign
lookup_sign("du₃")  → the BUILD sign (different)
lookup_sign("du₁₁") → the SPEAK sign (yet different)
```
Each returned `sign_name` is distinct; use them to verify which sign a transliteration intends.

### 5. Cross-language sign identification (Akkadian, Hittite, etc.)
```
lookup_sign("šarru")
→ matches the LUGAL sign 𒈗 via "value:šarru" (Akkadian reading of the "king" sign)
```

---

## Quick reference — fields on every `SignInfo`

```
sign_name   ← OGSL canonical name (uppercase; may include compound notation like |KA×GAR|)
glyph       ← Unicode cuneiform character (single codepoint OR multi-glyph compound)
uname       ← Unicode character name (e.g. "CUNEIFORM SIGN LUGAL")
hex         ← Unicode codepoint hex (e.g. "x12217")
values      ← list of ALL phonetic readings across languages
matched_by  ← "sign_name" if the query hit the canonical name; "value:<v>" if it hit a phonetic value
```

And on every `CuneifyResponse`:

```
spelling           ← echo of input
cuneiform          ← rendered Unicode glyph string (with whitespace preserved between words)
complete           ← True iff no □ placeholders were emitted
placeholder_count  ← number of □ characters in the output
```
