"""Per-server prompt-file loader with caching.

Each data-MCP server (`eme-gir-{epsd2,etcsl,cdli,ogsl}`) exposes a
`start_here()` tool that returns the contents of a server-specific
markdown prompt file under `prompt/`. The prompts describe that one
server's tool inventory, recommended workflow, valid filter
enumeration values (the CDLI-genre / ETCSL-text-id / etc. gotchas),
and common usage patterns — scoped to the data-source so an agent
connected to just one data MCP gets focused bootstrap content rather
than the full cross-server workflow that the Translator server's
prompt covers.

The `load_prompt` helper reads + caches the file on first call.
Missing files return a placeholder error message that is NOT cached,
so an operator can create the prompt file later and have it picked up
on the next invocation without restarting the server process.
"""

from __future__ import annotations

from pathlib import Path

_CACHE: dict[Path, str] = {}


def load_prompt(path: Path) -> str:
    """Read + cache a per-server prompt markdown file.

    Args:
        path: absolute Path to the prompt file (typically from
              `eme_gir.paths`'s *_PROMPT_DOC constants).

    Returns:
        The file's UTF-8 text contents (cached after first read). If
        the file is missing, returns a brief placeholder error
        message instructing the operator to create the file. The
        missing-file response is NOT cached, so a future call after
        the file is created will pick it up without a server restart.
    """
    cached = _CACHE.get(path)
    if cached is not None:
        return cached
    if not path.exists():
        return (
            f"# {path.name} missing\n\n"
            f"Expected at {path}.\n\n"
            f"Create this file to provide bootstrap context for the agent: "
            f"tool inventory, workflow, valid filter enumeration values, "
            f"and common gotchas specific to this server's data source. "
            f"The `start_here()` tool will pick up the new file on its "
            f"next invocation (no server restart needed)."
        )
    text = path.read_text(encoding="utf-8")
    _CACHE[path] = text
    return text
