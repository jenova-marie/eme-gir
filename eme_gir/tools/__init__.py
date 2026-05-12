"""Per-domain MCP tool implementations.

This package collects the MCP tool functions grouped by their source
domain — `cdli`, `etcsl`, `signs`, `epsd2`, `translator`. Each submodule
defines plain Python functions (decorated with `@log_call` for
entry/exit/timing/telemetry) that are then **registered** with one or
more FastMCP server instances by the per-server entry-point scripts
under `servers/`.

The tool definitions are decoupled from registration on purpose:
- A single tool function can be exposed by multiple servers (e.g. the
  Translator server might re-expose select ePSD2 tools).
- Phase 5 entry-point scripts register only the tools that belong to
  their domain — no shared FastMCP instance to import around.

Conventions:
- Tool functions accept primitives + return Pydantic response models
  from `eme_gir.models.<domain>`.
- `@log_call` is applied at the definition site so logging + telemetry
  is uniform regardless of which server registers the tool.
- Domain-private helpers (functions starting with `_`) live alongside
  the tool functions; shared-across-domains helpers live at the package
  root (eme_gir.cdli, eme_gir.cuneify, eme_gir.text_resolver, etc.).
"""
