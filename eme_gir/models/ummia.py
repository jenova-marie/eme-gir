"""Response models for the Ummia MCP server.

Ummia is the teaching surface for Meadow's Sumerian 101 lesson series
plus the dual-register Sumerian grammar reference (Jagersma 2010
academic + Meadow/Siri Nin temple companion). Most of Ummia's tools
return plain markdown strings — the lesson prompts and the persona
prompt. `get_grammar_reference()` is the one tool with a structured
response, modeled here.
"""

from __future__ import annotations

from pydantic import Field

from .common import _Permissive


class GrammarReferenceResponse(_Permissive):
    """Response shape for get_grammar_reference.

    Two grammar references are bundled — pick whichever fits your
    bootstrap pipeline:

    - `academic` (always present): the Jagersma-2010-based reference
      from lessons/JAGERSMA_GRAMMAR.md. Rigorous, attested, period-aware;
      every claim §-cited. Use for reading attested texts and for any
      academic correspondence.
    - `temple` (optional): the temple-register companion from
      lessons/MEADOW_GRAMMAR.md — Meadow's Sumerian 101 classroom-e₂-nun-na
      lessons plus Entu Siri Nin's commentary. Prayer-ready pedagogy,
      the PNC mnemonic, the 'pesky -a' three-tip heuristic, Emesal
      liturgical register, worked temple examples. Use for prayer
      composition and in-house liturgical style. `None` when the
      deployment doesn't ship the temple file.
    - `combined`: both documents joined with a separator banner, ready
      to drop into a system prompt as a single context blob.

    Conflict-resolution policy: temple file is normative for new in-temple
    composition; academic file is normative for reading attested forms.
    See §18 of the temple file for the full disagreement table.

    Citation conventions to carry through into agent replies:
      • academic claims → cite as `(Jagersma §N.M)`
      • temple claims   → cite as `(Meadow §101-N)` or `(Siri Nin)`

    Default period for unspecified-period translations: ED (Early
    Dynastic, ~2900-2350 BCE) — Jagersma's primary descriptive ground.
    """

    academic: str = Field(
        ...,
        description="Markdown of lessons/JAGERSMA_GRAMMAR.md — the Jagersma-2010-based academic reference. ~40 KB. Every grammatical claim carries an inline §-citation.",
    )
    temple: str | None = Field(
        None,
        description="Markdown of lessons/MEADOW_GRAMMAR.md — Meadow's classroom lessons + Siri Nin's commentary. ~48 KB. None when the file is absent from this deployment.",
    )
    combined: str = Field(
        ...,
        description="Both documents concatenated with a clearly-marked separator banner. ~80 KB when both are present; equals `academic` alone when `temple` is None.",
    )
    temple_available: bool = Field(
        ...,
        description="True when the temple companion is shipped with this deployment; False when only the academic reference is present.",
    )
