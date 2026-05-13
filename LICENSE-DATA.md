# LICENSE-DATA — data layer licensing

The **code** in this repository is licensed under the MIT License (see
[`LICENSE`](LICENSE)). The **data** the code downloads, parses, indexes,
and serves is licensed separately under three different regimes,
described in this document.

> **Why this file exists.** Earlier versions of this repo's documentation
> casually described the Oracc and CDLI data as "CC0 / public domain"
> and described ETCSL as "CC BY 3.0 UK". **All three claims were wrong.**
> This document is the authoritative statement of what the data actually
> says about itself.

---

## 1. Oracc / ePSD2 / OGSL — **CC BY-SA 3.0 Unported**

**Source:** [oracc.museum.upenn.edu](https://oracc.museum.upenn.edu) (Steve Tinney et al., U Penn).

**Canonical license statement:** [`oracc.museum.upenn.edu/doc/about/licensing`](https://oracc.museum.upenn.edu/doc/about/licensing) — *"anybody can download texts, change them and publish them again as long as the source is mentioned and the new work is released under the same (or similar) license."*

**Effect:** [Creative Commons Attribution-ShareAlike 3.0 Unported](https://creativecommons.org/licenses/by-sa/3.0/).

- ✅ Free to use, redistribute, modify, even commercially.
- ⚠️ **Attribution is required.** Every published reuse must credit Oracc.
- ⚠️ **ShareAlike propagates.** Any work that includes "a substantial portion" of Oracc data must itself be released under CC BY-SA 3.0 or a compatible license. This is copyleft inheritance.

### What this repo bundles or builds from Oracc data

| Artifact | License inheritance |
|---|---|
| `corpus/*.zip` (208 zips, ~3.1 GB; original Oracc bulk JSON) | CC BY-SA 3.0 — Oracc's original work |
| `data/glossary.sqlite` (~3.4 GB; built from `epsd2/gloss-sux.json`) | CC BY-SA 3.0 (derivative work, ShareAlike) |
| `data/text_index.sqlite` (~10 MB; built from `catalogue.json` files) | CC BY-SA 3.0 (derivative work) |
| `data/collocations.sqlite`, `data/inflected_collocations.sqlite` | CC BY-SA 3.0 (derivative work, n-grams over corpus text) |
| `corpus/ogsl.zip` (OGSL sign list) | CC BY-SA 3.0 — Oracc's original work |

All MCP responses that quote, paraphrase, or summarize this data carry the canonical attribution string in their `attribution` field:

> *ePSD2 / Oracc: electronic Pennsylvania Sumerian Dictionary, 2nd
> edition (oracc.museum.upenn.edu/epsd2), prepared by Steve Tinney
> and the Oracc team at the University of Pennsylvania. Data licensed
> under Creative Commons Attribution-ShareAlike 3.0 Unported
> (CC BY-SA 3.0); see oracc.museum.upenn.edu/doc/about/licensing.
> Attribution is required; substantial reuses must propagate the
> ShareAlike license.*

### What ShareAlike means for downstream users of this repo

If you redistribute `data/glossary.sqlite` (or any of the other Oracc-derived
SQLite indexes), or build a service whose substantive data layer is this
repo's data layer, **your derivative work's data layer must be released
under CC BY-SA 3.0 or a compatible license**. The MIT-licensed *code* in
this repo does not extinguish that obligation — Oracc's terms attach to
the data, not the code. In practice this usually means publishing
upstream-compatible attribution, granting CC BY-SA-compatible terms to
your downstream users, and declining to claim more restrictive rights
than your input source granted you.

What does NOT trigger ShareAlike (in our reading; not legal advice):
- Returning a single `lookup_entry` result to one user — de minimis.
- Code that operates on the data without redistributing it.
- Personal / non-publishing research use.

What DOES trigger ShareAlike:
- Bundling the SQLite indexes in a downstream package, image, or repo.
- Building a public web service on top of the data layer (the service's data outputs propagate the license).
- Republishing a sizeable extract of the glossary in another format.

---

## 2. ETCSL (Oxford) — **No Creative Commons license** — academic copyright + citation

**Source:** [etcsl.orinst.ox.ac.uk](https://etcsl.orinst.ox.ac.uk) (Black, Cunningham, Robson, Zólyomi et al., Oxford 1998–2006).

**Canonical statement:** ETCSL credits page — *"Copyright © J.A. Black, G. Cunningham, E. Robson, and G. Zólyomi 1998-2006... The authors have asserted their moral rights."* The project has only ever published a **citation request**, not a redistribution grant.

**Effect:** Traditional academic copyright. There is no Creative Commons license, no explicit grant of redistribution rights, and no public dedication to the public domain.

### What this means

ETCSL is widely *treated* as openly licensed by the digital humanities community, but that reflects:
1. The project's defunct status (funding ended 2006, no active enforcement).
2. Academic fair use / fair dealing for non-commercial scholarly tools.
3. The moral-rights assertion not being aggressively policed.

**Not** an explicit license grant.

Our project's posture:
- Personal / academic / non-commercial use of the bulk corpus is probably covered by fair use / fair dealing in most jurisdictions. We treat it that way.
- We pass the Oxford citation through with every quotation, as the project explicitly requests.
- The republication question — **bulk redistribution of the entire 394-composition corpus inside this repo's `data/etcsl.sqlite`** — is the part that is least clearly defensible. We accept that risk for this personal-research deployment; downstream users who plan to republish should consult their own counsel.

### Canonical citation string

Returned in the `attribution` field of every `etcsl_*` tool response:

> *ETCSL: Black, J.A., Cunningham, G., Robson, E., and Zólyomi, G.,
> The Electronic Text Corpus of Sumerian Literature
> (etcsl.orinst.ox.ac.uk), Oxford 1998-2006. © The Authors; the
> authors have asserted their moral rights. The ETCSL project has
> NOT released this corpus under any Creative Commons license;
> redistribution is governed by traditional academic copyright with
> a citation request. When quoting an ETCSL line or paragraph, cite
> this attribution verbatim.*

### What this repo bundles from ETCSL

| Artifact | License posture |
|---|---|
| `data/etcsl.zip` (~4.9 MB cached download from the Oxford Text Archive) | © Black et al.; cached for offline use, not redistributed onward |
| `data/etcsl.sqlite` (~31 MB; 394 texts, 34K lines, 160K words) | © Black et al.; derivative database used for FTS5 search |

---

## 3. CDLI — mixed regime (catalogue text / imagery)

**Source:** [cdli.mpiwg-berlin.mpg.de](https://cdli.mpiwg-berlin.mpg.de) (Cuneiform Digital Library Initiative; originally UCLA, hosted by Max Planck Institute for the History of Science Berlin since 2022).

**Canonical statement:** [CDLI Terms of Use](https://cdli.mpiwg-berlin.mpg.de/about).

- **Catalogue text** (P-numbers, designations, provenience, period, museum custody, dimensions, publication history): *"Text in the pages of CDLI may be freely copied, aggregated and re-used according to common and fair academic practice; we request, in the case of re-use of considerable textual data, that mention be made of the source of such material, with reference to CDLI and its web address."* — close to CC BY in effect; **citation required**.
- **Tablet photographs and line drawings** on cdli.earth: *"Commercial use or publication of these images is prohibited without prior written permission from the project and/or the institutions/authors named in conjunction with particular texts."* — **non-commercial only**. Image copyright rests variously with CDLI, the photographer, and the holding museum; many tablets carry additional museum-specific restrictions.

### What this repo bundles from CDLI

| Artifact | License posture |
|---|---|
| `data/cdli_cat.csv` (~147 MB; the catalogue CSV from the cdli-gh GitHub mirror) | Catalogue text reusable with citation |
| `data/cdli.sqlite` (~157 MB; 353K-row derivative DB) | Catalogue text reusable with citation |
| Tablet imagery | **Not hosted by this repo.** All `photo_url` / `lineart_url` values returned by our tools link directly to cdli.earth, so image-licensing remains CDLI's domain. |

### Canonical citation string

Returned in the `attribution` field of every `lookup_artifact` / `find_artifacts` response:

> *CDLI: Cuneiform Digital Library Initiative (cdli.earth), hosted by
> Max Planck Institute for the History of Science (Berlin) since 2022.
> Catalogue text is freely reusable per CDLI's terms of use with
> citation to CDLI as the source. Imagery on cdli.earth is NOT openly
> licensed — non-commercial use only, with image copyright resting
> variously with CDLI, the photographer, and the holding museum.
> This server hosts no imagery; all image URLs link directly to
> cdli.earth.*

---

## 4. Summary matrix

| Data source | License | Attribution | Redistribution | Notes |
|---|---|:---:|:---:|---|
| **Oracc / ePSD2 / OGSL** | CC BY-SA 3.0 | required | OK with copyleft | ShareAlike propagates |
| **ETCSL** | Academic copyright | required (citation) | grey zone | No CC license |
| **CDLI catalogue text** | "fair academic practice" | required | OK with citation | Close to CC BY in effect |
| **CDLI imagery** | non-commercial only | required | Not redistributed by us | All links point to cdli.earth |
| **This repo's code** | MIT | not required | unrestricted | See `LICENSE` |

If you redistribute this repository or build a downstream system on top of it, the **code** half is MIT (unrestricted) but the **data** half carries the three licenses above. The strictest of them — Oracc's ShareAlike — sets the floor for the data layer: any substantial reuse must remain CC BY-SA 3.0-compatible.

---

## 5. Recourse + corrections

If you're a rights holder for any of these corpora and believe this document misrepresents your terms, please open an issue on the GitHub repo or email the maintainer. We will correct it immediately.

This document was written on **2026-05-13** based on the license statements published on the respective project websites as of that date. License terms can change; the authoritative statement is always the upstream project, not this file.
