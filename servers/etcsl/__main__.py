"""ETCSL (Oxford literary corpus) MCP server.

Four bilingual tools — every result carries both the Sumerian
transliteration and its English translation paragraph:
- etcsl_search_english(query, limit) → FTS5 over English translations
- etcsl_lines_with_lemma(lemma, limit) → literary uses of a lemma
- etcsl_lookup_text(text_id, start, line_limit) → read a whole composition
- etcsl_search_sumerian(query, limit) → FTS5 over Sumerian transliterations

Run:
    python -m servers.etcsl                          # stdio (Claude Code)
    python -m servers.etcsl --transport http         # HTTP on :5053

ETCSL is CC BY 3.0 UK — every tool result carries an `attribution`
field with the canonical citation string. Pass it through to the user.
"""

from __future__ import annotations

from eme_gir.log import init_logging
from eme_gir.paths import ETCSL_DB
from eme_gir.server import READ_ONLY_ANNOTATIONS, make_server, run_server
from eme_gir.tools.etcsl import (
    etcsl_lines_with_lemma,
    etcsl_lookup_text,
    etcsl_search_english,
    etcsl_search_sumerian,
)

log = init_logging("eme-gir-etcsl")

mcp = make_server(
    name="eme-gir-etcsl",
    instructions=(
        "Electronic Text Corpus of Sumerian Literature (ETCSL), Oxford "
        "1998-2006. 394 lemmatized literary compositions (hymns, myths, "
        "royal hymns, proverbs, the Sumerian King List, Inana's Descent, "
        "Gilgameš, Šulgi praise poems), shipped with English translations "
        "alongside every Sumerian line. Every tool result is BILINGUAL.\n\n"
        "Four tools:\n"
        "  • etcsl_search_english(query, limit) — FTS5 over the Oxford "
        "translations. Try 'kingship', 'underworld', '\"divine power\"', "
        "'descend*'.\n"
        "  • etcsl_lines_with_lemma(lemma, limit) — find literary lines "
        "containing a specific Sumerian lemma (cf, e.g. 'lugal', 'inana').\n"
        "  • etcsl_lookup_text(text_id, start, line_limit) — read a whole "
        "composition. Famous IDs: c.1.4.1 (Inana's Descent), c.1.8.1.4 "
        "(Gilgameš/Underworld), c.2.1.1 (Sumerian King List).\n"
        "  • etcsl_search_sumerian(query, limit) — FTS5 over Sumerian "
        "transliterations.\n\n"
        "ETCSL is licensed CC BY 3.0 UK — attribution is LEGALLY REQUIRED. "
        "Every response carries the canonical citation string in its "
        "`attribution` field; pass it through verbatim."
    ),
)

mcp.tool(annotations=READ_ONLY_ANNOTATIONS)(etcsl_search_english)
mcp.tool(annotations=READ_ONLY_ANNOTATIONS)(etcsl_lines_with_lemma)
mcp.tool(annotations=READ_ONLY_ANNOTATIONS)(etcsl_lookup_text)
mcp.tool(annotations=READ_ONLY_ANNOTATIONS)(etcsl_search_sumerian)


if __name__ == "__main__":
    run_server(
        mcp, log,
        default_port=5053,
        required_dbs=[(ETCSL_DB, "build_etcsl_db.py")],
    )
