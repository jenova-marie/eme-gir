"""Per-domain MCP server entry points.

Five independent FastMCP servers, each exposing ONE conceptual surface:

| Module | Server identifier | Tools | Default HTTP port |
|---|---|---|---|
| servers.epsd2 | eme-gir-epsd2 | 13 ePSD2 dictionary + corpus tools | 5052 |
| servers.etcsl | eme-gir-etcsl | 4 ETCSL literary corpus tools | 5053 |
| servers.cdli | eme-gir-cdli | 2 CDLI artifact catalogue tools | 5054 |
| servers.ogsl | eme-gir-ogsl | 2 OGSL sign rendering tools | 5055 |
| servers.translator | eme-gir-translator | bootstrap resources + 2 wrappers | 5056 |

Run any one of them with:
    python -m servers.<name> [--transport stdio|http] [--host HOST] [--port PORT]

The shared boilerplate (Auth0 OAuth, DNS-rebinding transport security,
startup banner, argparse) lives in `eme_gir.server`. Each entry point
is ~30-40 lines: import tools, build the FastMCP instance, register
the domain's tools, call run_server.

The legacy `mcp_server.py` at the repo root remains as the all-in-one
"register everything" server for backwards compatibility.
"""
