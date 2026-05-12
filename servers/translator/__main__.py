"""Translator MCP server — bootstrap workflow surface for agents.

This server is the OPINIONATED workflow surface. It exposes ONLY the
agent bootstrap content:

Resources:
  oracc://prompt/agent       — the system prompt teaching the
                                end-to-end workflow over the data servers
  oracc://grammar/sumerian   — dual-register grammar (Jagersma 2010
                                academic + Meadow/Siri Nin temple companion)

Tool wrappers (for tools-only MCP clients that don't surface resources):
  start_here()               — returns the agent prompt body
  get_grammar_reference()    — returns the dual grammar as a structured
                                response with academic/temple/combined fields

This server has NO data tools of its own. The agent should connect to
the four data MCPs separately (ePSD2, ETCSL, CDLI, Signs) and use this
server's bootstrap content to guide its workflow over them.

Run:
    python -m servers.translator                     # stdio (Claude Code)
    python -m servers.translator --transport http    # HTTP on :5056
"""

from __future__ import annotations

from eme_gir.log import init_logging
from eme_gir.server import READ_ONLY_ANNOTATIONS, make_server, run_server
from eme_gir.tools.translator import (
    agent_prompt as _agent_prompt_body,
    get_grammar_reference,
    grammar_cheatsheet as _grammar_cheatsheet_body,
    start_here,
)

log = init_logging("eme-gir-translator")

mcp = make_server(
    name="eme-gir-translator",
    instructions=(
        "Sumerian translation BOOTSTRAP surface. This server hosts the "
        "agent system prompt and the dual-register Sumerian grammar "
        "reference as MCP resources (and as tool wrappers for clients "
        "that don't surface resources). It has NO data tools of its own — "
        "for that, connect to the four data MCPs separately:\n"
        "  • eme-gir-epsd2       — dictionary + corpus tools\n"
        "  • eme-gir-etcsl       — Oxford literary corpus (bilingual)\n"
        "  • eme-gir-cdli        — artifact catalogue + image links\n"
        "  • eme-gir-ogsl        — cuneiform sign rendering\n\n"
        "FIRST STEPS for an agent:\n"
        "  1. start_here() — get the recommended end-to-end workflow.\n"
        "  2. get_grammar_reference() — get the dual academic + temple "
        "grammar (~80 KB) for working memory.\n"
        "Then call the data MCPs as the workflow prescribes."
    ),
)

# Resources — registered with this server's FastMCP instance; body
# functions live in eme_gir.tools.translator.
mcp.resource(
    "oracc://grammar/sumerian",
    name="Sumerian grammar — academic + temple references",
    title="Sumerian grammar: Jagersma 2010 + Meadow's temple-register lessons",
    description=(
        "Two grammar references concatenated (~80 KB combined). FIRST: "
        "Jagersma 2010 academic reference (twelve enclitic cases, the "
        "nine-slot finite-verb template, perfective vs imperfective "
        "inflection, all preformatives, dimensional prefixes, "
        "nominalization-based subordination — every rule §-cited to "
        "Jagersma). SECOND: temple-register companion from Meadow's "
        "Sumerian 101 classroom-e₂-nun-na lessons + Siri Nin's commentary "
        "(PNC mnemonic, 'pesky -a' three-tip heuristic, Emesal "
        "liturgical register). Cite as (Jagersma §N.M) for academic "
        "claims; (Meadow §101-N) or (Siri Nin) for temple claims."
    ),
    mime_type="text/markdown",
)(_grammar_cheatsheet_body)

mcp.resource(
    "oracc://prompt/agent",
    name="Sumerian translation agent — system prompt",
    title="Agent system prompt: how to use these tools end-to-end",
    description=(
        "Drop-in system prompt teaching an LLM agent the recommended "
        "workflow for using this suite's tools: decompose English → rank "
        "candidates with translate_english → check find_compound + "
        "find_collocations for fixed idioms → choose perfective vs "
        "imperfective aspect → apply case suffixes mirrored in the "
        "verbal prefix chain → use find_verb_form / get_inflections to "
        "pull attested morphology → verify with see_examples → render "
        "with cuneify. Also covers Sumerian → English, the etcsl_* "
        "literary tools, the CDLI link-rendering requirement, the CC BY "
        "3.0 UK Oxford-attribution requirement for ETCSL data, the "
        "required output format, and a worked example."
    ),
    mime_type="text/markdown",
)(_agent_prompt_body)

# Tool wrappers around the bootstrap content (for tools-only MCP clients).
mcp.tool(annotations=READ_ONLY_ANNOTATIONS)(start_here)
mcp.tool(annotations=READ_ONLY_ANNOTATIONS)(get_grammar_reference)


if __name__ == "__main__":
    # Translator has no SQLite dependencies — the bootstrap docs are
    # plain markdown files on disk, read via the loaders in
    # eme_gir.tools.translator.
    run_server(mcp, log, default_port=5056)
