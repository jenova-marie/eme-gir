"""Response models for the Translator MCP server.

The Translator server is the opinionated workflow surface. Its main job
is hosting the agent bootstrap resources (`oracc://prompt/agent`,
`oracc://grammar/sumerian`) and their corresponding tool wrappers
(`start_here`, `get_grammar_reference`) for tools-only MCP clients.
Substantive translation work happens via the four data MCPs
(ePSD2, ETCSL, CDLI, Signs) which agents compose under the workflow
the Translator server documents.

Currently only `get_grammar_reference()` has a structured response
worth a Pydantic model; `start_here()` returns plain markdown.
"""

from __future__ import annotations

from pydantic import Field

from .common import _Permissive


class GrammarReferenceResponse(_Permissive):
    """Response shape for get_grammar_reference.

    Two grammar references are bundled — pick whichever fits your
    bootstrap pipeline:

    - `academic` (always present): the Jagersma-2010-based reference
      from prompt/SUMERIAN_GRAMMAR.md. Rigorous, attested, period-aware;
      every claim §-cited. Use for reading attested texts and for any
      academic correspondence.
    - `temple` (optional): the temple-register companion from
      prompt/MEADOW_GRAMMAR.md — Meadow's Sumerian 101 classroom-e₂-nun-na
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
        description="Markdown of prompt/SUMERIAN_GRAMMAR.md — the Jagersma-2010-based academic reference. ~40 KB. Every grammatical claim carries an inline §-citation.",
    )
    temple: str | None = Field(
        None,
        description="Markdown of prompt/MEADOW_GRAMMAR.md — Meadow's classroom lessons + Siri Nin's commentary. ~48 KB. None when the file is absent from this deployment.",
    )
    combined: str = Field(
        ...,
        description="Both documents concatenated with a clearly-marked separator banner. ~80 KB when both are present; equals `academic` alone when `temple` is None.",
    )
    temple_available: bool = Field(
        ...,
        description="True when the temple companion is shipped with this deployment; False when only the academic reference is present.",
    )
