"""Single source of truth for corpus attribution + citation strings.

Every eme-gir data server (ePSD2, OGSL, ETCSL, CDLI) must surface license
attribution to the LLM agent consuming it. Because these servers run inside
*generic third-party chat clients* (Claude Desktop, ChatGPT-with-MCP, Cursor,
…) the server author does not own the final render step, so attribution can
never be deterministically forced into the model's answer. We instead maximize
the probability that it survives synthesis with three layers, all sourced from
the constants below:

1. ``*_ATTRIBUTION`` — the full, verbatim license string. Carried on every
   tool response's ``attribution`` field (unchanged) AND served as an MCP
   resource (``license://…``) so the per-call cite can stay short.
2. ``*_CITATION_SHORT`` — a one-line token cheap enough to survive synthesis,
   carried on every response's ``citation_short`` field.
3. ``*_PRESENTATION`` — a point-of-use imperative carried on every response's
   ``presentation`` field, telling the agent to reproduce the short cite
   (including for numeric data and rendered glyphs, not only quoted prose).

This module imports nothing from :mod:`eme_gir.models` or :mod:`eme_gir.tools`
so it can be a dependency of both without an import cycle. The four
``*_ATTRIBUTION`` names are re-exported from their original ``eme_gir.tools.*``
modules for backwards compatibility.

License facts (see ``LICENSE-DATA.md`` for the full statement):
- Oracc / ePSD2 / OGSL — CC BY-SA 3.0 Unported (attribution required;
  ShareAlike propagates to substantial reuses).
- ETCSL — NOT under any Creative Commons license; traditional academic
  copyright (© Black, Cunningham, Robson, Zólyomi 1998-2006) with a required
  citation.
- CDLI — catalogue text reusable per CDLI's fair-academic-practice terms with
  citation; imagery on cdli.earth is non-commercial only.
"""

from __future__ import annotations

from typing import Callable

# ──────────────────────────────────────────────────────────────────
# Full verbatim attribution strings (the canonical source)
# ──────────────────────────────────────────────────────────────────

EPSD2_ATTRIBUTION = (
    "ePSD2 / Oracc: electronic Pennsylvania Sumerian Dictionary, 2nd "
    "edition (oracc.museum.upenn.edu/epsd2), prepared by Steve Tinney and "
    "the Oracc team at the University of Pennsylvania. Data licensed under "
    "Creative Commons Attribution-ShareAlike 3.0 Unported (CC BY-SA 3.0); "
    "see oracc.museum.upenn.edu/doc/about/licensing. Attribution is "
    "required; substantial reuses must propagate the ShareAlike license."
)

OGSL_ATTRIBUTION = (
    "OGSL: Oracc Global Sign List, maintained by Steve Tinney and the "
    "Oracc team, distributed via oracc.museum.upenn.edu. Data licensed "
    "under Creative Commons Attribution-ShareAlike 3.0 Unported "
    "(CC BY-SA 3.0); see oracc.museum.upenn.edu/doc/about/licensing. "
    "Attribution is required; substantial reuses must propagate the "
    "ShareAlike license."
)

ETCSL_ATTRIBUTION = (
    "ETCSL: Black, J.A., Cunningham, G., Robson, E., and Zólyomi, G., "
    "The Electronic Text Corpus of Sumerian Literature "
    "(etcsl.orinst.ox.ac.uk), Oxford 1998-2006. © The Authors; the "
    "authors have asserted their moral rights. The ETCSL project has NOT "
    "released this corpus under any Creative Commons license; redistribution "
    "is governed by traditional academic copyright with a citation request. "
    "When quoting an ETCSL line or paragraph, cite this attribution verbatim."
)

CDLI_ATTRIBUTION = (
    "CDLI: Cuneiform Digital Library Initiative (cdli.earth), hosted by "
    "Max Planck Institute for the History of Science (Berlin) since 2022. "
    "Catalogue text is freely reusable per CDLI's terms of use with "
    "citation to CDLI as the source. Imagery on cdli.earth is NOT openly "
    "licensed — non-commercial use only, with image copyright resting "
    "variously with CDLI, the photographer, and the holding museum. "
    "This server hosts no imagery; all image URLs link directly to "
    "cdli.earth (see https://cdli.mpiwg-berlin.mpg.de/about for terms)."
)

# ──────────────────────────────────────────────────────────────────
# Short citation tokens (cheap enough to survive synthesis)
# ──────────────────────────────────────────────────────────────────

EPSD2_CITATION_SHORT = "ePSD2 (CC BY-SA 3.0)"
OGSL_CITATION_SHORT = "OGSL (CC BY-SA 3.0)"
ETCSL_CITATION_SHORT = "ETCSL, Oxford 1998–2006 © The Authors (not CC-licensed)"
CDLI_CITATION_SHORT = "CDLI (cdli.earth) — catalogue text reusable with citation"

# ──────────────────────────────────────────────────────────────────
# Point-of-use imperatives
# ──────────────────────────────────────────────────────────────────


def _cc_presentation(short: str, license_uri: str) -> str:
    return (
        "REQUIRED: when you present ANY field from this result to the user — "
        "including numeric counts, spellings, or rendered cuneiform glyphs, "
        "not only quoted text — reproduce the `citation_short` below verbatim "
        "in a single Sources section of your reply. Do not paraphrase it. "
        f'Citation: "{short}". Full license: resource `{license_uri}`.'
    )


EPSD2_PRESENTATION = _cc_presentation(EPSD2_CITATION_SHORT, "license://oracc-epsd2")
OGSL_PRESENTATION = _cc_presentation(OGSL_CITATION_SHORT, "license://oracc-ogsl")

ETCSL_PRESENTATION = (
    "REQUIRED — CONDITION OF USE, NOT A COURTESY: ETCSL is NOT released "
    "under any Creative Commons license. If you quote, paraphrase, OR merely "
    "cite a text_id from this result, reproduce the `citation_short` below "
    "verbatim in a Sources section of your reply. Do not alter it. "
    f'Citation: "{ETCSL_CITATION_SHORT}". Full license: resource '
    "`license://etcsl`."
)

CDLI_PRESENTATION = _cc_presentation(CDLI_CITATION_SHORT, "license://cdli")

# ──────────────────────────────────────────────────────────────────
# MCP resource body factory
# ──────────────────────────────────────────────────────────────────


def license_banner(server_name: str, full_attribution: str) -> str:
    """Build the directive banner prepended to a server's `start_here()`.

    Placed at the very top of the bootstrap text so that when a user runs
    the warm-up ("use the start_here tool of mcp servers …"), the agent's
    first action is to surface each server's data license to the user
    before doing anything else. The license text is sourced from the
    canonical `*_ATTRIBUTION` constant so it can never drift.
    """
    return (
        f"> 📜 **FIRST ACTION — do this before calling any other tool:** "
        f"show the user the data license for `{server_name}` quoted below, "
        f"verbatim, then continue.\n"
        f">\n"
        f"> **{server_name} — data license & attribution:**\n"
        f">\n"
        f"> {full_attribution}\n\n"
        f"---\n\n"
    )


def make_license_body(full_attribution: str) -> Callable[[], str]:
    """Return a zero-arg body function for an MCP ``license://…`` resource.

    The body yields the full verbatim attribution string plus a pointer to
    the repo's ``LICENSE-DATA.md`` for the complete legal statement. Used by
    each data server's ``mcp.resource(...)`` registration.
    """

    def _body() -> str:
        return (
            f"{full_attribution}\n\n"
            "Full data-license statement for all four eme-gir corpora: see "
            "LICENSE-DATA.md in the source repository."
        )

    return _body
