"""OGSL cuneiform sign rendering MCP server.

Two tools:
- cuneify(spelling)     → render Oracc transliteration as Unicode glyphs
- lookup_sign(query, limit) → sign name ↔ phonetic value ↔ Unicode glyph

Run:
    python -m servers.ogsl                           # stdio (Claude Code)
    python -m servers.ogsl --transport http          # HTTP on :5055
"""

from __future__ import annotations

from eme_gir.attribution import OGSL_ATTRIBUTION, make_license_body
from eme_gir.cuneify import OGSL_ZIP
from eme_gir.log import init_logging
from eme_gir.server import READ_ONLY_ANNOTATIONS, make_server, run_server
from eme_gir.tools.ogsl import cuneify, lookup_sign, start_here

log = init_logging("eme-gir-ogsl")

mcp = make_server(
    name="eme-gir-ogsl",
    instructions=(
        "Cuneiform sign rendering via the Oracc Global Sign List (OGSL). "
        "Two tools:\n"
        "  • cuneify(spelling) — convert an Oracc transliteration like "
        "'lugal-e e₂ mu-na-du₃' into Unicode cuneiform glyphs (𒈗𒂊 𒂍 "
        "𒈬𒈾𒆕). Handles hyphen-joined signs, braced determinatives, "
        "compound graphemes, and morphology tails. Unknown signs render "
        "as □ placeholders.\n"
        "  • lookup_sign(query, limit) — look up a sign by name "
        "('LUGAL') OR phonetic value ('lugal'), returning the Unicode "
        "glyph, all known readings, and Unicode metadata.\n\n"
        "This server is useful beyond Sumerian — Akkadian, Hittite, "
        "Hurrian, and Elamite all use cuneiform and share OGSL.\n\n"
        "OGSL data is licensed CC BY-SA 3.0 (attribution required; "
        "ShareAlike propagates to substantial reuses) — reproduce each "
        "result's `citation_short` in your reply.\n\n"
        "By calling these tools you accept the source's terms of use."
    ),
)

mcp.resource(
    "license://oracc-ogsl",
    name="OGSL — license & attribution",
    title="OGSL / Oracc data license (CC BY-SA 3.0)",
    description=(
        "Full attribution + license statement for the OGSL sign-list data "
        "served by this server. CC BY-SA 3.0 Unported: attribution required; "
        "ShareAlike propagates to substantial reuses."
    ),
    mime_type="text/markdown",
)(make_license_body(OGSL_ATTRIBUTION))

mcp.tool(annotations=READ_ONLY_ANNOTATIONS)(start_here)
mcp.tool(annotations=READ_ONLY_ANNOTATIONS)(cuneify)
mcp.tool(annotations=READ_ONLY_ANNOTATIONS)(lookup_sign)


if __name__ == "__main__":
    run_server(
        mcp, log,
        default_port=5055,
        required_dbs=[(OGSL_ZIP, "download_corpus.py")],
    )
