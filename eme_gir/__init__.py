"""eme-gir — local Oracc / ePSD2 + ETCSL + CDLI infrastructure for human
research and LLM-agent translation of Sumerian.

The `__version__` attribute is the single source of truth for the project
version. It is read by:

- `eme_gir.server.make_server()` — surfaced to MCP clients in the
  initialize handshake's `serverInfo.version` field
- The startup banner in `eme_gir.server.run_server()`
- Anywhere else in the codebase that needs to identify the running
  build (e.g. the www landing page, the Dockerfile labels)

Semantic versioning (semver.org): MAJOR.MINOR.PATCH. While the project
is < 1.0, MINOR bumps may break tool signatures or response shapes;
PATCH bumps are always backwards compatible. After 1.0, MAJOR bumps
signal breaking changes.

Bump this string when cutting a release. Tag the matching commit with
`git tag -a v$VERSION -m "..."` and add an entry to CHANGELOG.md under
the new version heading.
"""

__version__ = "0.1.0"
