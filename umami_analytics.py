"""Umami analytics dispatcher for the MCP server.

Fire-and-forget tool-call telemetry to a self-hosted Umami instance.
Off by default; opt-in via env vars (see init_from_env). When enabled,
every MCP tool invocation produces one Umami event with name = the
tool's function name and data = {duration_ms, outcome, arg_keys,
result_count, error_kind?}.

Privacy boundary (deliberate, do not relax without thinking):
- We send tool NAMES, ARG-KEY NAMES, latency, success/error counts,
  result-item counts.
- We do NOT send tool ARGUMENT VALUES, query strings, request bodies,
  result content, IPs, session IDs, Auth0 client identifiers, or
  anything else that could turn the analytics dashboard into a
  transcript leak. A user's `translate_english("homophobia")` query
  must NOT show up in Umami — only the fact that translate_english
  was called once with one arg key.

Threading model:
- A single bounded queue + one daemon worker thread does the actual
  HTTP POSTs against Umami's /api/send endpoint, with a 2-second
  timeout per request. Tool handlers never block on the network or
  on Umami being available.
- Queue is bounded at 1000 events. When Umami is down for an extended
  period, the queue fills, new events are dropped silently rather than
  growing unbounded — analytics MUST NOT consume RAM that the corpus
  needs.
- All exceptions inside the worker are swallowed. Analytics never
  surfaces failures into tool callers.

Configured via mcp_server.py at startup; queried via the module-level
emit() shim from inside _log_call.
"""

from __future__ import annotations

import logging
import os
import queue
import threading

import httpx

log = logging.getLogger("epsd2.umami")


class _UmamiClient:
    """Background-thread Umami event dispatcher. Use the module-level
    emit() shim rather than constructing this directly."""

    def __init__(
        self,
        url: str,
        website_id: str,
        hostname: str,
        api_key: str | None = None,
    ) -> None:
        self.endpoint = f"{url.rstrip('/')}/api/send"
        self.website_id = website_id
        self.hostname = hostname
        self.api_key = api_key
        self._q: queue.Queue[tuple[str, dict] | None] = queue.Queue(maxsize=1000)
        self._client = httpx.Client(timeout=2.0)
        self._thread = threading.Thread(
            target=self._worker, name="umami-dispatch", daemon=True
        )
        self._thread.start()

    def event(self, name: str, data: dict) -> None:
        """Enqueue a single event for async dispatch. Non-blocking; drops
        the event silently when the queue is full."""
        try:
            self._q.put_nowait((name, data))
        except queue.Full:
            log.debug("umami queue full, dropping event %s", name)

    def _worker(self) -> None:
        # Drain the queue forever, POSTing each event. The thread is
        # daemon, so it dies with the process — no explicit shutdown
        # needed.
        while True:
            item = self._q.get()
            if item is None:
                break
            try:
                name, data = item
                # Umami's /api/send schema (v2.x): {type, payload}
                # where payload mirrors the browser-side `umami.track`
                # call. `url` and `hostname` are required by the
                # schema; `name` + `data` are the actual event payload.
                payload = {
                    "type": "event",
                    "payload": {
                        "website": self.website_id,
                        "hostname": self.hostname,
                        "url": "/mcp",
                        "name": name,
                        "data": data,
                    },
                }
                headers = {
                    "Content-Type": "application/json",
                    # Umami's bot-filter looks at User-Agent; identify
                    # ourselves so events aren't dropped as bot traffic.
                    "User-Agent": "epsd2-mcp/1.0 (Mozilla/5.0)",
                }
                if self.api_key:
                    headers["x-umami-api-key"] = self.api_key
                self._client.post(self.endpoint, json=payload, headers=headers)
            except Exception as e:
                # Analytics failures NEVER bubble up. Tool callers must
                # not be able to tell whether Umami is reachable or not.
                log.debug("umami POST failed: %s", e)
            finally:
                self._q.task_done()


_INSTANCE: _UmamiClient | None = None


def init_from_env() -> _UmamiClient | None:
    """Read EPSD2_UMAMI_* env vars and lazily construct the dispatcher.

    Returns the constructed client on success, or None when analytics
    should remain disabled (default — required env vars not set).

    Required env vars:
        EPSD2_UMAMI_URL          base URL of the Umami instance, e.g.
                                  https://umami.recoverysky.app
        EPSD2_UMAMI_WEBSITE_ID   Umami website UUID (from the dashboard)

    Optional:
        EPSD2_UMAMI_HOSTNAME     hostname to report (default: 'epsd2-mcp').
                                  Use this to distinguish multiple
                                  deployments (prod vs staging) under
                                  the same Umami website.
        EPSD2_UMAMI_API_KEY      API key if your Umami instance requires
                                  one for /api/send (most don't).
    """
    global _INSTANCE
    url = os.environ.get("EPSD2_UMAMI_URL", "").strip()
    wid = os.environ.get("EPSD2_UMAMI_WEBSITE_ID", "").strip()
    if not url or not wid:
        return None
    hostname = os.environ.get("EPSD2_UMAMI_HOSTNAME", "").strip() or "epsd2-mcp"
    api_key = os.environ.get("EPSD2_UMAMI_API_KEY", "").strip() or None
    _INSTANCE = _UmamiClient(
        url=url,
        website_id=wid,
        hostname=hostname,
        api_key=api_key,
    )
    return _INSTANCE


def is_enabled() -> bool:
    """True when analytics is wired up and live."""
    return _INSTANCE is not None


def emit(name: str, data: dict) -> None:
    """Fire-and-forget event. No-op when analytics is disabled.

    Called from _log_call after every tool invocation. Must NEVER raise."""
    if _INSTANCE is not None:
        _INSTANCE.event(name, data)


def _count_result_items(result) -> int | None:
    """Best-effort count of "interesting" items in a tool result, for the
    result_count analytics field. Looks at common top-level list keys
    (results, matches, lines, tokens, blocks, spellings, candidates).
    Returns None when no list-shaped key is found (e.g. cuneify, which
    returns one rendered string)."""
    if result is None:
        return None
    # Pydantic models — get the dict representation cheaply
    if hasattr(result, "model_dump"):
        try:
            d = result.model_dump()
        except Exception:
            return None
    elif isinstance(result, dict):
        d = result
    else:
        return None
    for key in (
        "results", "matches", "lines", "tokens", "blocks",
        "spellings", "candidates",
    ):
        v = d.get(key)
        if isinstance(v, list):
            return len(v)
    return None
