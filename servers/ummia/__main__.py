"""Ummia MCP server — teacher persona for the Sumerian 101 lesson series
plus the dual-register Sumerian grammar reference.

Ummia (𒌝𒈪𒀀 *um-mi-a*, ePSD2 lemma `ummia[expert]N` — 453× attested
in ED + Ur III + OB) is the canonical Sumerian word for the master
teacher of the e₂-dub-ba. The Old Babylonian "Schooldays" literary
compositions use this term when a student addresses their teacher.
This server wraps Meadow's classroom-e₂-nun-na Sumerian 101 lesson
series in the Ummia teaching persona AND owns the dual-register
Sumerian grammar reference (Jagersma 2010 academic + Meadow / Siri
Nin temple companion).

Tools:
  start_here()             — Ummia persona prompt + lesson menu (⭐ first)
  get_lesson_101_1()       — Introduction to Sumerian
  get_lesson_101_2()       — Basic Verbs
  get_lesson_101_3()       — Case Markers, Possession & Pronouns
  get_lesson_101_4()       — Advanced Verbs: Person, Tense & Reduplication
  get_lesson_101_5()       — Advanced Case Markers, Modal Prefixes & Subordination
  get_grammar_reference()  — dual academic + temple grammar (~80 KB combined)

Resource:
  oracc://grammar/sumerian — same content as get_grammar_reference(),
                             served as an MCP resource for spec-complete
                             clients (tools-only clients should use the
                             tool wrapper above).

No data tools — Ummia is a teaching surface. Substantive lookups
(dictionary, attestations, cuneiform rendering, artifact images,
literary parallels) compose with the four eme-gir data MCPs:
  • eme-gir-epsd2       — dictionary + corpus
  • eme-gir-ogsl        — cuneiform sign rendering
  • eme-gir-etcsl       — Oxford literary corpus
  • eme-gir-cdli        — artifact catalogue + image links

Run:
    python -m servers.ummia                     # stdio (Claude Code)
    python -m servers.ummia --transport http    # HTTP on :5058
"""

from __future__ import annotations

from eme_gir.log import init_logging
from eme_gir.server import READ_ONLY_ANNOTATIONS, make_server, run_server
from eme_gir.tools.ummia import (
    get_grammar_reference,
    get_lesson_101_1,
    get_lesson_101_2,
    get_lesson_101_3,
    get_lesson_101_4,
    get_lesson_101_5,
    grammar_cheatsheet as _grammar_cheatsheet_body,
    start_here,
)

log = init_logging("eme-gir-ummia")

mcp = make_server(
    name="eme-gir-ummia",
    instructions=(
        "Ummia (𒌝𒈪𒀀 um-mi-a, 'master teacher / expert' — 453× "
        "attested across ED, Ur III, and OB; the canonical word for "
        "the head teacher of the e₂-dub-ba in the Schooldays literary "
        "tradition) — master teacher of the scribes of the Temple of "
        "Inanna's Light. This server is the TEACHING surface for "
        "Meadow's Sumerian 101 lesson series, distilled and adapted "
        "for one-on-one instruction with an LLM teaching agent; it "
        "also owns the dual-register Sumerian grammar reference "
        "(Jagersma 2010 academic + Meadow / Siri Nin temple companion, "
        "~80 KB combined).\n\n"
        "FIRST STEPS for an agent:\n"
        "  1. start_here() — adopt the Ummia persona; read the "
        "lesson menu and teaching workflow.\n"
        "  2. get_grammar_reference() — fetch the dual academic + "
        "temple grammar for your working memory; you'll reach for "
        "it constantly while teaching.\n"
        "  3. When the student names a lesson, call the matching "
        "get_lesson_101_N() — the returned markdown is YOUR teaching "
        "script (numbered sections, per-section drills with hidden "
        "answers, end-of-lesson exercise with full answer key).\n\n"
        "No data tools — for vocabulary lookups, cuneiform rendering, "
        "attested lines, and artifact images, compose with the "
        "eme-gir-{epsd2,ogsl,etcsl,cdli} data MCPs. Call each one's "
        "start_here() once at the start of the session per the "
        "standing user instruction."
    ),
)

# Resource — registered with this server's FastMCP instance; body
# function lives in eme_gir.tools.ummia (grammar_cheatsheet).
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

mcp.tool(annotations=READ_ONLY_ANNOTATIONS)(start_here)
mcp.tool(annotations=READ_ONLY_ANNOTATIONS)(get_lesson_101_1)
mcp.tool(annotations=READ_ONLY_ANNOTATIONS)(get_lesson_101_2)
mcp.tool(annotations=READ_ONLY_ANNOTATIONS)(get_lesson_101_3)
mcp.tool(annotations=READ_ONLY_ANNOTATIONS)(get_lesson_101_4)
mcp.tool(annotations=READ_ONLY_ANNOTATIONS)(get_lesson_101_5)
mcp.tool(annotations=READ_ONLY_ANNOTATIONS)(get_grammar_reference)


if __name__ == "__main__":
    # Ummia has no SQLite dependencies — the lesson, persona, and
    # grammar prompts are plain markdown files on disk, read via the
    # loaders in eme_gir.tools.ummia.
    run_server(mcp, log, default_port=5058)
