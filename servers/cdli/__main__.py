"""CDLI artifact catalogue MCP server.

Two tools:
- lookup_artifact(p_id) → full CDLI catalogue record for one tablet
- find_artifacts(...)   → filtered search across 353K artifacts

Run:
    python -m servers.cdli                           # stdio (Claude Code)
    python -m servers.cdli --transport http          # HTTP on :5054
"""

from __future__ import annotations

from eme_gir.log import init_logging
from eme_gir.paths import CDLI_DB
from eme_gir.server import READ_ONLY_ANNOTATIONS, make_server, run_server
from eme_gir.tools.cdli import find_artifacts, lookup_artifact, start_here

log = init_logging("eme-gir-cdli")

mcp = make_server(
    name="eme-gir-cdli",
    instructions=(
        "Cuneiform Digital Library Initiative (CDLI) artifact catalogue: "
        "353K cuneiform-bearing objects indexed by P-id with provenience "
        "(find spot), period, museum custody, dimensions, publication "
        "history, and links to CDLI-hosted photographs / line drawings.\n\n"
        "Two tools:\n"
        "  • lookup_artifact(p_id) — full record for one P-id (e.g. 'P347156').\n"
        "  • find_artifacts(provenience=..., period=..., museum_collection=..., "
        "genre=..., language=..., limit=20) — filtered search; each filter "
        "is matched as a case-insensitive SUBSTRING.\n\n"
        "Image URLs (`photo_url`, `lineart_url`, plus thumbnails) point "
        "directly to cdli.earth — we host no imagery. CDLI catalogue is "
        "CC0; attribution is courteous but not legally required."
    ),
)

# Register the two CDLI tools + the server's start_here bootstrap.
mcp.tool(annotations=READ_ONLY_ANNOTATIONS)(start_here)
mcp.tool(annotations=READ_ONLY_ANNOTATIONS)(lookup_artifact)
mcp.tool(annotations=READ_ONLY_ANNOTATIONS)(find_artifacts)


if __name__ == "__main__":
    run_server(
        mcp, log,
        default_port=5054,
        required_dbs=[(CDLI_DB, "build_cdli_db.py")],
    )
