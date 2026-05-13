"""Translator MCP server: bootstrap surface for agents.

The Translator domain is the opinionated workflow surface — it hosts the
agent system prompt (`oracc://prompt/agent`) and the Sumerian grammar
references (`oracc://grammar/sumerian`) as MCP resources, and exposes
those same documents as tool functions for tools-only MCP clients:

- `start_here()` returns the agent prompt
- `get_grammar_reference()` returns the dual-register grammar bundle

Substantive translation work happens via the four data MCPs
(ePSD2, ETCSL, CDLI, Signs) which agents compose under the workflow
the Translator server documents. Phase 5 will split the Translator
into its own server entry point with no data tools of its own — just
the bootstrap surface plus zero or more of the data MCPs proxied
through.

The resource registrations themselves (`@mcp.resource(...)`) are
FastMCP-instance-coupled and live at the entry-point script that owns
the FastMCP instance; this module exposes their body functions for the
entry point to wire up.
"""

from __future__ import annotations

from ..log import log_call
from ..models.translator import GrammarReferenceResponse
from ..paths import AGENT_PROMPT_DOC, GRAMMAR_DOC, MEADOW_GRAMMAR_DOC

_ACADEMIC_GRAMMAR_CACHE: str | None = None
_TEMPLE_GRAMMAR_CACHE: str | None = None  # None = "file absent at startup"
_AGENT_PROMPT_CACHE: str | None = None

_TEMPLE_HANDOFF_BANNER = (
    "\n\n"
    "═══════════════════════════════════════════════════════════════\n"
    "  TEMPLE REGISTER COMPANION — switching from academic to in-temple grammar\n"
    "  Above: Jagersma 2010 (rigorous, attested, period-aware).\n"
    "  Below: Meadow's Sumerian 101 classroom lessons + Siri Nin's commentary\n"
    "         (prayer-ready pedagogy; what the temple actually teaches).\n"
    "  Conflicts resolved per §18 of the temple file:\n"
    "    • temple composition → temple file is normative\n"
    "    • reading attested texts → Jagersma is normative\n"
    "═══════════════════════════════════════════════════════════════\n\n"
)


def _load_academic_grammar() -> str:
    """Read + cache prompt/SUMERIAN_GRAMMAR.md (Jagersma 2010)."""
    global _ACADEMIC_GRAMMAR_CACHE
    if _ACADEMIC_GRAMMAR_CACHE is None:
        if not GRAMMAR_DOC.exists():
            _ACADEMIC_GRAMMAR_CACHE = (
                "# prompt/SUMERIAN_GRAMMAR.md missing\n\n"
                f"Expected at {GRAMMAR_DOC}. Re-run the project setup."
            )
        else:
            _ACADEMIC_GRAMMAR_CACHE = GRAMMAR_DOC.read_text(encoding="utf-8")
    return _ACADEMIC_GRAMMAR_CACHE


def _load_temple_grammar() -> str | None:
    """Read + cache prompt/MEADOW_GRAMMAR.md, or None when absent.

    None means the temple companion isn't shipped with this deployment;
    callers should treat the bootstrap as academic-only.
    """
    global _TEMPLE_GRAMMAR_CACHE
    if _TEMPLE_GRAMMAR_CACHE is None and MEADOW_GRAMMAR_DOC.exists():
        _TEMPLE_GRAMMAR_CACHE = MEADOW_GRAMMAR_DOC.read_text(encoding="utf-8")
    return _TEMPLE_GRAMMAR_CACHE


def _load_grammar() -> str:
    """Single-string view: academic + (optional) temple, concatenated
    with the handoff banner. Used by the `oracc://grammar/sumerian`
    resource where a single markdown blob is the right wire shape."""
    academic = _load_academic_grammar()
    temple = _load_temple_grammar()
    if temple is None:
        return academic
    return academic + _TEMPLE_HANDOFF_BANNER + temple


def _load_agent_prompt() -> str:
    """Read + cache the agent system prompt from disk."""
    global _AGENT_PROMPT_CACHE
    if _AGENT_PROMPT_CACHE is None:
        if not AGENT_PROMPT_DOC.exists():
            return (
                "# prompt/AGENT_PROMPT.md missing\n\n"
                f"Expected at {AGENT_PROMPT_DOC}. Re-run the project setup."
            )
        _AGENT_PROMPT_CACHE = AGENT_PROMPT_DOC.read_text(encoding="utf-8")
    return _AGENT_PROMPT_CACHE


# ─── Resource bodies (registered by entry-point) ─────────────────


@log_call
def grammar_cheatsheet() -> str:
    """Body for the `oracc://grammar/sumerian` MCP resource. Returns
    the combined academic + temple grammar references as a single
    markdown document. The resource registration (uri / name / title /
    description / mime_type) lives at the entry-point script."""
    return _load_grammar()


@log_call
def agent_prompt() -> str:
    """Body for the `oracc://prompt/agent` MCP resource. Returns the
    drop-in agent system prompt. The resource registration metadata
    lives at the entry-point script."""
    return _load_agent_prompt()


# ─── Tool wrappers around the two bootstrap resources ─────────────
#
# The MCP spec exposes the bootstrap content as RESOURCES, which spec-
# complete clients discover via resources/list and read via
# resources/read. But in practice many production MCP clients only wire
# up tools/list (Claude variants, agent runtimes, IDE integrations) —
# for those, the bootstrap content is invisible no matter how cleanly
# the resource is declared. These two tools are belt-and-suspenders:
# they expose the same content via the universally-supported tools
# surface so the resource-blind clients can still self-bootstrap. Spec-
# complete clients should prefer the resource form (cheaper, no tool
# round-trip, semantically the right primitive); the tools are a
# compatibility shim, not the architectural primary.


@log_call
def start_here() -> str:
    """⭐ CALL THIS FIRST. Returns the Sumerian translation agent's
    system prompt as text — the bootstrap that teaches you how to use
    the rest of the tools end-to-end.

    The returned markdown covers:
      • Recommended workflow for English → Sumerian translation
        (decompose → translate_english → find_compound →
        find_collocations → choose ḫamṭu vs marû aspect → apply
        case suffixes → find_verb_form / get_inflections →
        see_examples → cuneify)
      • Reverse direction (Sumerian → English) tools
      • The four etcsl_* literary tools and when to reach for them
      • Required Oxford citation for any ETCSL-derived data; required
        Oracc CC BY-SA 3.0 attribution for ePSD2/OGSL data
      • Required output format and a fully worked example

    The prompt also instructs you to call `get_grammar_reference()`
    next to fetch the Sumerian grammar cheat sheet for working
    memory. That's the second and final bootstrap step.

    (Spec-complete MCP clients can read this content from the
    `oracc://prompt/agent` resource instead — but most production
    clients only surface tools, so this is exposed as a tool too.)
    """
    return _load_agent_prompt()


@log_call
def get_grammar_reference() -> GrammarReferenceResponse:
    """Return BOTH Sumerian grammar references — academic + temple —
    as a structured response.

    Call this after start_here(). The response carries:

    1. `academic` (always present, ~40 KB): the Jagersma-2010-based
       reference from prompt/SUMERIAN_GRAMMAR.md. Comprehensive
       distillation of Bram Jagersma's *A Descriptive Grammar of
       Sumerian* (PhD diss., Leiden 2010, 776 pp). Covers transliteration
       conventions, phonology, the twelve enclitic cases with ambiguity
       tables, gender/plural, pronouns/numerals/adjectives, the nine-slot
       finite-verb template, perfective vs imperfective inflection,
       preformatives (vocalic + modal + negative), dimensional prefixes,
       ventive + middle, non-finite forms, copular/nominal clauses, and
       nominalization-based subordination. Every grammatical rule carries
       an inline Jagersma section citation (e.g. §7.3).

    2. `temple` (optional, ~48 KB): the temple-register companion from
       prompt/MEADOW_GRAMMAR.md — Meadow's Sumerian 101 classroom-
       e₂-nun-na lessons plus Entu Siri Nin's commentary. The PNC
       mnemonic, the 'pesky -a' three-tip heuristic, the perfective-
       default temple composition style, the Emesal liturgical register,
       and worked temple examples (dedication formulas, royal-
       inscription lines, prayer-direct imperatives). Cite as
       `(Meadow §101-N)` or `(Siri Nin)`. None when the deployment
       doesn't ship the temple file.

    3. `combined`: both documents concatenated with a separator banner,
       ready to drop into a system prompt as a single context blob.

    4. `temple_available`: a True/False flag for the temple companion's
       presence.

    Use the academic part for rigor and attested-form questions; use the
    temple part for prayer composition and in-house liturgical style.
    Section §18 of the temple file documents where the two diverge and
    which is normative when they do.

    Default period for unspecified-period translations: ED (Early
    Dynastic, ~2900-2350 BCE) — Jagersma's primary descriptive ground.

    (Spec-complete MCP clients can read the `combined` form from the
    `oracc://grammar/sumerian` resource instead — but most production
    clients only surface tools, so this is exposed as a tool too.)
    """
    academic = _load_academic_grammar()
    temple = _load_temple_grammar()
    combined = academic if temple is None else academic + _TEMPLE_HANDOFF_BANNER + temple
    return GrammarReferenceResponse(
        academic=academic,
        temple=temple,
        combined=combined,
        temple_available=temple is not None,
    )
