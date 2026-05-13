# `eme-gir-cdli` — CDLI artifact catalogue MCP server

You are connected to a local snapshot of the **Cuneiform Digital Library
Initiative (CDLI)** artifact catalogue: **353,283 cuneiform-bearing objects**
indexed by P-id with provenience, period, museum custody, dimensions,
publication history, and URLs to CDLI-hosted photographs / line drawings.
Snapshot date: **August 2022**. Data is CC0; no network calls; sub-50 ms
SQLite lookups.

This server is **not** about translation or dictionary lookup — for that, see
the ePSD2 / ETCSL / OGSL servers. This one tells you **what an artifact
physically is**, **where it was found**, **who holds it now**, and **how to
link to its CDLI page** so the user can see the object.

---

## The two tools

### `lookup_artifact(p_id: str)`

One P-id → one full catalogue record. Accepts `P347156`, `347156`, or `p347156`
(normalized internally). Returns a `CDLIArtifact` with every column we
indexed: designation, primary_publication, publication_history, period,
provenience, museum_collection, museum_no, accession_no, genre, subgenre,
language, material, object_type, dimensions, condition, plus computed
image URLs (see "URLs on every artifact" section below for rendering rules).

**Use when:** you have a P-id already (typically from an ePSD2
`see_examples` result or an ETCSL line citation) and need its full
provenience + museum + publication metadata for a citation.

### `find_artifacts(provenience=, period=, museum_collection=, genre=, language=, limit=)`

Filtered query over the 353K-row catalogue. All filters are **case-insensitive
SUBSTRING** matches, ANDed together. Returns a `FindArtifactsResponse`
with `filter_spec`, `total_matches` (raw count before limit), and `results`
(top-N records, default 20, cap 200).

**Use when:** the question is about a *class* of artifacts, not a specific
one — "Ur III tablets from Drehem in the British Museum", "Old Babylonian
literary tablets from Nippur", "Akkadian seals from Kanesh".

---

## Filter enumeration values

**These are the real strings in the catalogue.** Substring-match against them.
Guessing free-form English (like `"Royal Inscription"` when CDLI uses
`"Royal/Monumental"`) returns 0 rows.

### `genre` — text genre

The catalogue has ~25 distinct values. Top values by row count:

| genre | rows | substring-match tip |
|---|---:|---|
| `Administrative` | 194,556 | the dominant ledger / receipt corpus |
| `Royal/Monumental` | 22,278 | **royal inscriptions + monumental statuary** (with the slash, NOT `"Royal Inscription"`) |
| `Legal` | 16,572 | contracts, court records |
| `Letter` | 15,846 | correspondence |
| `Literary` | 9,662 | hymns, myths, epics — also see the ETCSL server |
| `Lexical` | 8,149 | sign-list / vocabulary texts |
| `School` | 3,896 | school exercises (often duplicate lexical / proverbs) |
| `Omen` | 3,042 | divinatory |
| `Mathematical` | 1,947 | numerical / problem texts |
| `Astronomical` | 1,628 | celestial observations |
| `Prayer/Incantation` | 972 | ritual speech |
| `Ritual` | 420 | |

Data-quality wrinkles in this column:
- Case inconsistency: both `"Administrative"` and `"administrative"` exist
  as separate rows. Use `genre="administrative"` to substring-match either
  (LOWER+LIKE handles both).
- Uncertain values: `"Administrative ?"`, `"Lexical ?"`, `"uncertain"`,
  `"fake (modern)"` — these are real flag values, not noise.
- To catch "any royal-context object", filter `genre="Royal"` — covers
  `"Royal/Monumental"` plus any subgenre.

### `period` — historical period

**Every period string is suffixed with `(ca. NNNN-NNNN BC)`**. Substring match
on the period name alone:

| substring → | actually matches |
|---|---|
| `"Ur III"` | `Ur III (ca. 2100-2000 BC)` (110,984 rows) |
| `"Old Babylonian"` | `Old Babylonian (ca. 1900-1600 BC)` (66,236) **AND** `Early Old Babylonian (ca. 2000-1900 BC)` (8,597) |
| `"Neo-Assyrian"` | `Neo-Assyrian (ca. 911-612 BC)` (35,478) |
| `"Neo-Babylonian"` | `Neo-Babylonian (ca. 626-539 BC)` (15,633) — note also `... ?` uncertain rows |
| `"Middle Hittite"` | `Middle Hittite (ca. 1500-1100 BC)` (14,692) |
| `"Old Akkadian"` | `Old Akkadian (ca. 2340-2200 BC)` (9,974) |
| `"Ebla"` | `Ebla (ca. 2350-2250 BC)` (7,111) |
| `"Old Assyrian"` | `Old Assyrian (ca. 1950-1850 BC)` (6,452) |
| `"Achaemenid"` | `Achaemenid (547-331 BC)` (5,746) |
| `"Uruk III"` | `Uruk III (ca. 3200-3000 BC)` (4,899) — archaic |
| `"Lagash II"` | `Lagash II (ca. 2200-2100 BC)` (4,646) — Gudea period |
| `"ED IIIb"` | `ED IIIb (ca. 2500-2340 BC)` (4,579) |
| `"Middle Assyrian"` | `Middle Assyrian (ca. 1400-1000 BC)` (4,559) |
| `"Hellenistic"` | `Hellenistic (323-63 BC)` (3,351) |
| `"ED IIIa"` | `ED IIIa (ca. 2600-2500 BC)` (1,867) |
| `"Uruk IV"` | `Uruk IV (ca. 3350-3200 BC)` (1,848) — archaic, earliest writing |
| `"Proto-Elamite"` | `Proto-Elamite (ca. 3100-2900 BC)` (1,729) |

`"Early Dynastic"` would NOT match `ED IIIa/IIIb` (CDLI uses `ED` not `Early Dynastic`). Use `ED III` to get both subperiods.

### `language` — linguistic content

| language | rows |
|---|---:|
| `Sumerian` | 139,961 |
| `Akkadian` | 84,736 |
| `Hittite` | 14,669 |
| `undetermined` | 8,493 |
| `Eblaite` | 6,871 |
| `Sumerian; Akkadian` (bilingual) | 2,844 |
| `Elamite` | 2,702 |
| `Ugaritic` | 1,107 |

Substring match `"Sumerian"` catches both pure-Sumerian rows AND bilingual `"Sumerian; Akkadian"`.

### `provenience` — find-spot

Format: `"Modern-name (mod. Modern-place)"`. Major sites:

| substring → | site | rows |
|---|---|---:|
| `"Girsu"` | Girsu (mod. Tello) — Lagash state capital | 37,045 |
| `"Umma"` | Umma (mod. Tell Jokha) | 35,343 |
| `"Nippur"` | Nippur (mod. Nuffar) — religious center | 27,112 |
| `"Nineveh"` | Nineveh (mod. Kuyunjik) — Assyrian capital, Ashurbanipal's library | 26,187 |
| `"Drehem"` *or* `"Puzriš-Dagan"` | Puzriš-Dagan (mod. Drehem) — Ur III animal-management center | 16,848 |
| `"Ḫattusa"` *or* `"Boğazkale"` | Hittite capital | 14,519 |
| `"Uruk"` | Uruk (mod. Warka) — Inana's city | 13,422 |
| `"Ur"` | Ur (mod. Tell Muqayyar) — Ur III capital | 11,023 |
| `"Mari"` | Mari (mod. Tell Hariri) | 9,758 |
| `"Ebla"` | Ebla (mod. Tell Mardikh) | 6,893 |
| `"Assur"` | Assur (mod. Qalat Sherqat) — Old Assyrian capital | 6,406 |
| `"Kanesh"` *or* `"Kültepe"` | Anatolian trading colony, Old Assyrian | 6,025 |
| `"Susa"` | Susa (mod. Shush) — Elamite | 4,215 |
| `"Babili"` *or* `"Babylon"` | Bābili (mod. Babylon) | 3,579 |

### `museum_collection` — current custody

| substring → | rows |
|---|---:|
| `"British Museum"` | 74,877 |
| `"Penn"` *or* `"Philadelphia"` | 26,358 (Penn Museum) |
| `"Istanbul"` | 19,008 (Arkeoloji Müzeleri) |
| `"Iraq"` | 17,179 (National Museum of Iraq, Baghdad) |
| `"Ankara"` | 15,846 (Anadolu Medeniyetleri Müzesi) |
| `"Yale"` | 15,821 + 11,128 (Yale Babylonian Collection + Nies sub-collection) |
| `"Berlin"` | 13,149 (Vorderasiatisches Museum) |
| `"Louvre"` | 12,346 (Musée du Louvre, Paris) |
| `"Cornell"` | 10,445 (Cornell, Ithaca NY) |
| `"Ashmolean"` | 6,538 (Oxford) |
| `"Chicago"` | 6,420 (OI / ISAC) |
| `"Harvard"` | 4,695 (Harvard Museum of the Ancient Near East) |

### `object_type` (not directly filterable as a `find_artifacts` arg, but visible on results)

`tablet` (296,950, 84% of the catalogue), `seal (not impression)` (15,524), `tablet & envelope` (7,194), `cone` (5,855), `brick` (4,249), `prism` (1,279), `bulla` (1,884). The catalogue is overwhelmingly tablets.

---

## URLs on every artifact — REQUIRED rendering

Every `CDLIArtifact` carries five URL-bearing fields:

| Field | When populated | What it links to |
|---|---|---|
| `cdli_url` | **Always.** | The artifact's CDLI page (`cdli.earth/artifacts/<cdli_id>`). User entry point. |
| `photo_url` | When CDLI has a photograph (`has_photo=true`). | Full-resolution JPG. |
| `photo_thumb_url` | Same condition. | Thumbnail for inline display. |
| `lineart_url` | When CDLI has a line drawing (`has_lineart=true`). | Full-resolution lineart JPG. |
| `lineart_thumb_url` | Same condition. | Thumbnail. |

**Your job: surface every populated URL as a Markdown link.**

- The `cdli_url` is always set — **render it unconditionally** for every artifact you cite. Never paste a bare P-id.
- `photo_url` and `lineart_url` are populated when the underlying assets exist; render them as separate hyperlinks alongside the cdli_url.
- When an image URL is `null`, simply omit it from the reply — don't say "no photo available", and don't fabricate a URL.

Canonical citation pattern when all fields are populated:

```
[P347156](https://cdli.earth/artifacts/347156) — *VS 24, 037*,
Vorderasiatisches Museum (Berlin), VAT 16439. Ur III, from Umma.
[photo](https://cdli.earth/.../photo.jpg) · [lineart](https://cdli.earth/.../lineart.jpg)
```

When only `cdli_url` is populated (image fields `null`):

```
[P347156](https://cdli.earth/artifacts/347156) — *VS 24, 037*,
Vorderasiatisches Museum (Berlin), VAT 16439. Ur III, from Umma.
```

If you want a thumbnail inline (where the rendering medium supports Markdown image syntax):

```
![tablet thumb](https://cdli.earth/.../photo_l.jpg)
```

Or with the bibliographic designation in the link text when `designation`
is populated:

```
[VS 24, 037 (P347156)](https://cdli.earth/artifacts/347156)
```

The same convention applies to **every cited tablet**, including ones
the agent receives via `see_examples` / `find_verb_form` from the ePSD2
server (which auto-splat CDLI URL fields onto each `AttestationLine`).
Whatever URLs the tool returns, render them — no editorializing about
what might or might not be available on the live cdli.earth site.

---

## Attribution

CDLI's catalogue is **CC0** — attribution is not legally required, but
every tool response carries an `attribution` string crediting the CDLI
team (originally UCLA, hosted by MPIWG Berlin since 2022). Pass it
through when citing a research result; it's the courteous default.

---

## Common workflows

### 1. Citing one tablet you already have a P-id for
```
lookup_artifact("P100256")
→ pull out: designation, period, provenience, museum_collection, museum_no
→ render as Markdown link + inline metadata
```

### 2. Surveying a class of artifacts
```
find_artifacts(
    provenience="Drehem",
    period="Ur III",
    museum_collection="British Museum",
    limit=20,
)
→ check total_matches first (e.g. "thousands of matches; here are 20")
→ list each as a clickable [P-id](url) — designation
```

### 3. Bilingual / cross-culture context
```
find_artifacts(language="Sumerian; Akkadian", limit=10)
→ bilingual interlinear texts (often Old Babylonian school exercises)
```

### 4. By scribal genre, not place
```
find_artifacts(genre="Royal/Monumental", language="Sumerian", limit=20)
→ Sumerian royal inscriptions across periods
```

### 5. Cross-server: enriching an ePSD2 citation
```
ePSD2 see_examples returns AttestationLine with text_id="P347156"
→ lookup_artifact("P347156") for the full provenience + museum record
→ assemble the citation: "P347156 obv. 3 — VS 24, 037, Vorderasiatisches
   Museum (Berlin), VAT 16439. Ur III, from Umma."
```

---

## Quick reference — fields on every `CDLIArtifact`

```
p_id, cdli_id, cdli_url                  ← always populated; render cdli_url unconditionally
photo_url, photo_thumb_url               ← render when populated; omit when null
lineart_url, lineart_thumb_url           ← render when populated; omit when null
has_photo, has_lineart                   ← booleans paired with the image URLs
designation                              ← bibliographic shorthand (RIME 1.08.03.02, YOS 14, 341)
primary_publication, publication_history, citation, composite_id
period, period_remarks, accounting_period, dates_referenced
provenience, provenience_remarks, findspot_remarks, findspot_square, excavation_no
museum_collection, museum_no, accession_no
genre, subgenre, language, material, object_type
height, width, thickness                 ← free-form strings; "?" common
condition_description, object_remarks
```

Most fields are nullable. Free-form text fields (publication_history,
provenience_remarks, condition_description) are useful for prose context;
enum-style fields (period, genre, language, provenience, museum_collection)
are what you filter on.
