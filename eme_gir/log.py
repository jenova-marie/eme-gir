"""Shared logging configuration + tool-call decorator for the MCP servers.

Phase 3 extraction of the `_log_call` decorator and the module-load
logging setup that formerly lived inline in mcp_server.py.

Public API:
    init_logging(server_name: str) -> logging.Logger
        One-shot logger configuration. Configures the root logger with
        stderr + rotating-file handlers and returns the namespaced
        `eme-gir` logger. Idempotent — repeat calls are no-ops, which
        keeps multi-import scenarios safe (Flask reloader, test
        harnesses, etc.).

    log : logging.Logger
        Module-level `eme-gir` logger. Direct access for code paths
        that don't call `init_logging` themselves (e.g. importing
        modules that emit log statements before the server entry-point
        runs).

    log_call(fn)
        Decorator. Wraps a tool function so each invocation logs
        entry + exit + timing, and emits one umami_analytics event per
        call (arg-key names only — no values — for privacy). Sits
        between @mcp.tool() and the bare function so FastMCP's
        Pydantic schema sees the original signature.

Per-server log files: `init_logging("epsd2")` writes to
`log/epsd2.log`; `init_logging("mcp_server")` writes to
`log/mcp_server.log`. Each MCP server entry point should call
`init_logging` with its own name so parallel-running servers don't
clobber each other's log files.

stdout is intentionally NOT a log target — it's reserved for the
JSON-RPC protocol stream on stdio transports, and any extra writes
there would corrupt the connection.
"""

from __future__ import annotations

import functools
import logging
import sys
import time
from logging.handlers import RotatingFileHandler
from typing import Any

from . import umami_analytics
from .paths import LOG_DIR

_LOG_FORMAT = logging.Formatter(
    "%(asctime)s.%(msecs)03d [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)

# Module-level logger; init_logging() configures the handlers attached
# to the root logger so this child inherits them. Importers can grab
# this directly for log statements that fire before init_logging runs.
log = logging.getLogger("eme-gir")

# Set in init_logging; guards against duplicate handler attachment
# across multi-import / reload scenarios.
_INITIALIZED = False


def init_logging(server_name: str = "mcp_server") -> logging.Logger:
    """Configure root-logger handlers (stderr + rotating file) and
    return the package's `eme-gir` logger. Idempotent.

    The rotating file handler writes to `log/{server_name}.log` so
    multiple MCP servers running in parallel get distinct files (e.g.
    `log/epsd2.log`, `log/etcsl.log`, `log/ummia.log`). 5 MB ×
    3 backups gives a ~15 MB ceiling per file.
    """
    global _INITIALIZED
    if _INITIALIZED:
        return log

    root = logging.getLogger()
    root.setLevel(logging.INFO)

    stderr_h = logging.StreamHandler(sys.stderr)
    stderr_h.setFormatter(_LOG_FORMAT)
    root.addHandler(stderr_h)

    log_file = LOG_DIR / f"{server_name}.log"
    file_h = RotatingFileHandler(log_file, maxBytes=5 * 1024 * 1024, backupCount=3)
    file_h.setFormatter(_LOG_FORMAT)
    root.addHandler(file_h)

    _INITIALIZED = True
    return log


def _summarize_result(result: Any) -> str:
    """Concise one-line description of a tool result for the exit log.

    Mirrors the shapes the tool functions actually return. Falls back to
    empty string when the result doesn't match a known shape — the
    timing line is still useful even without a summary.
    """
    if not isinstance(result, dict):
        return ""
    if "error" in result:
        return f" ⚠ ERROR: {str(result['error'])[:80]}"
    if "results" in result and isinstance(result["results"], list):
        summary = f" → {len(result['results'])} results"
        if "total_matches" in result:
            summary += f" (of {result['total_matches']} total)"
        return summary
    if "lines" in result and isinstance(result["lines"], list):
        summary = f" → {len(result['lines'])} lines"
        if result.get("period_filter"):
            summary += f" [period={result['period_filter']!r}]"
        return summary
    if "matches" in result and isinstance(result["matches"], list):
        return f" → {len(result['matches'])} matches"
    if "tokens" in result and isinstance(result["tokens"], list):
        return f" → {len(result['tokens'])} tokens"
    if "cuneiform" in result:
        cu = result["cuneiform"]
        summary = f" → {cu[:40]}"
        if not result.get("complete", True):
            summary += f" ({result.get('placeholder_count', 0)} □)"
        return summary
    if "morphology" in result:
        kinds = result.get("kinds") or []
        counts = {k: len(result["morphology"][k]) for k in kinds}
        return f" → {counts}"
    if "spellings" in result:
        return (
            f" → {result.get('cf','?')} [{result.get('gw','?')}], "
            f"{len(result['spellings'])} spellings, "
            f"{len(result.get('senses', []))} senses"
        )
    return ""


def log_call(fn):
    """Wrap a tool function so each invocation logs entry + exit + timing.

    Sits between @mcp.tool() and the bare function so FastMCP's pydantic
    schema sees the original signature (preserved by functools.wraps).
    Also emits one umami_analytics event per call.
    """
    @functools.wraps(fn)
    def wrapper(*args, **kwargs):
        arg_bits = []
        for k, v in kwargs.items():
            r = repr(v)
            if len(r) > 60:
                r = r[:57] + "..."
            arg_bits.append(f"{k}={r}")
        log.info(f"→ {fn.__name__}({', '.join(arg_bits)})")
        # arg_keys ships only the NAMES (sorted) — never the values —
        # so the analytics dashboard can answer "are agents passing
        # `period=...` to see_examples?" without leaking which period
        # any specific user queried.
        arg_keys = sorted(kwargs.keys())
        t0 = time.monotonic()
        try:
            result = fn(*args, **kwargs)
        except Exception as e:
            elapsed = (time.monotonic() - t0) * 1000
            log.exception(
                f"  ✗ {fn.__name__} ({elapsed:.0f}ms) raised "
                f"{type(e).__name__}: {e}"
            )
            umami_analytics.emit(fn.__name__, {
                "duration_ms": round(elapsed, 1),
                "outcome": "error",
                "error_kind": type(e).__name__,
                "arg_keys": arg_keys,
            })
            raise
        elapsed = (time.monotonic() - t0) * 1000
        summary = _summarize_result(result)
        log.info(f"  ← {fn.__name__} ({elapsed:.0f}ms){summary}")
        # Outcome is "error" when the result is a structured ErrorResponse
        # (tool returned cleanly but the operation failed — bad oid,
        # missing scope, etc.) and "ok" otherwise. Distinct from raised
        # exceptions, which take the except branch above.
        is_error = isinstance(result, dict) and "error" in result
        if not is_error and hasattr(result, "model_dump"):
            try:
                is_error = "error" in result.model_dump(exclude_none=True)
            except Exception:
                is_error = False
        umami_analytics.emit(fn.__name__, {
            "duration_ms": round(elapsed, 1),
            "outcome": "error" if is_error else "ok",
            "result_count": umami_analytics._count_result_items(result),
            "arg_keys": arg_keys,
        })
        return result
    return wrapper
