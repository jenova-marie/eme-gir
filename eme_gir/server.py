"""Shared server boilerplate for the five MCP entry points.

Provides:
- `READ_ONLY_ANNOTATIONS` — every tool we ship is a pure read-only
  query, so this is the universal default. Pass it to `mcp.tool(...)`.
- `make_server(name, instructions)` — FastMCP factory that wires up
  Auth0 OAuth (when EME_GIR_REQUIRE_AUTH=1) + DNS-rebinding transport
  security (from EME_GIR_ALLOWED_HOSTS / _ORIGINS) using the project's
  standard env-var contract. Global env vars rather than per-server —
  operators typically share one Auth0 tenant + one allowed-hosts list
  across all five servers, so the simpler global toggle is the right
  default.
- `run_server(mcp, log, default_port, required_dbs=...)` — argparse
  loop + startup banner + transport selection (stdio | streamable-http).
  Each entry point passes its own logger + required SQLite paths so
  the missing-data failure mode is server-specific and informative.

Phase 5 entry points (servers/{epsd2,etcsl,cdli,signs,translator}/
__main__.py) are thin wrappers: import tools, import this module,
register tools, call `run_server`. Together with the existing
mcp_server.py (the legacy all-in-one) they expose every domain at its
own MCP endpoint while sharing the same data + infrastructure.
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

from mcp.server.fastmcp import FastMCP
from mcp.types import ToolAnnotations

from . import umami_analytics
from .paths import ROOT

READ_ONLY_ANNOTATIONS = ToolAnnotations(
    readOnlyHint=True,
    destructiveHint=False,
    idempotentHint=True,
    openWorldHint=False,
)


def _build_auth_kwargs() -> dict:
    """Read EME_GIR_AUTH0_* env vars and return auth/token_verifier kwargs.

    Returns an empty dict (auth disabled) unless EME_GIR_REQUIRE_AUTH=1.
    When enabled, returns {'auth': AuthSettings, 'token_verifier':
    Auth0TokenVerifier} suitable for splatting into the FastMCP constructor.

    Auth is OPT-IN and only meaningful for the streamable-HTTP transport;
    stdio runs unauthenticated regardless (per MCP spec, stdio uses
    environment-based credentials, not OAuth). The transport check
    happens at run() time — if EME_GIR_REQUIRE_AUTH=1 is set but stdio is
    selected, the constructed verifier sits idle, which is harmless.

    Required env vars when EME_GIR_REQUIRE_AUTH=1:
        EME_GIR_AUTH0_TENANT_URL          e.g. https://my-tenant.auth0.com
        EME_GIR_AUTH0_AUDIENCE            e.g. https://eme-gir.example.com
        EME_GIR_AUTH0_RESOURCE_SERVER_URL e.g. https://eme-gir.example.com
    Optional:
        EME_GIR_AUTH0_REQUIRED_SCOPE      defaults to 'mcp:access'
    """
    if os.environ.get("EME_GIR_REQUIRE_AUTH", "").strip().lower() not in {
        "1", "true", "on", "yes", "y", "enable", "enabled",
    }:
        return {}

    # Lazy imports — pyjwt + the SDK auth modules aren't needed unless
    # the operator opts in.
    from mcp.server.auth.settings import AuthSettings
    from pydantic import AnyHttpUrl

    from .auth0_verifier import Auth0TokenVerifier

    tenant_url = os.environ.get("EME_GIR_AUTH0_TENANT_URL", "").strip()
    audience = os.environ.get("EME_GIR_AUTH0_AUDIENCE", "").strip()
    resource_server_url = os.environ.get(
        "EME_GIR_AUTH0_RESOURCE_SERVER_URL", ""
    ).strip()
    required_scope = os.environ.get("EME_GIR_AUTH0_REQUIRED_SCOPE", "mcp:access").strip()

    missing = [
        name
        for name, value in [
            ("EME_GIR_AUTH0_TENANT_URL", tenant_url),
            ("EME_GIR_AUTH0_AUDIENCE", audience),
            ("EME_GIR_AUTH0_RESOURCE_SERVER_URL", resource_server_url),
        ]
        if not value
    ]
    if missing:
        raise RuntimeError(
            f"EME_GIR_REQUIRE_AUTH=1 but missing env vars: {', '.join(missing)}. "
            "See START.md 'Adding Auth0 OAuth' for the full env contract."
        )

    return {
        "auth": AuthSettings(
            issuer_url=AnyHttpUrl(tenant_url + "/"),
            resource_server_url=AnyHttpUrl(resource_server_url),
            required_scopes=[required_scope] if required_scope else None,
        ),
        "token_verifier": Auth0TokenVerifier(
            tenant_url=tenant_url,
            audience=audience,
            required_scope=required_scope or None,
        ),
    }


def _build_transport_security_kwargs() -> dict:
    """Read EME_GIR_ALLOWED_HOSTS / _ORIGINS / _DISABLE_DNS_REBINDING_PROTECTION
    env vars and return a transport_security kwarg for FastMCP.

    The MCP SDK's streamable-http transport ships with DNS-rebinding
    protection ON by default, with a localhost-only allowlist. Behind a
    reverse proxy (Caddy/nginx/traefik), every request gets rejected
    with `421 Misdirected Request: Invalid Host header`. The fix is to
    extend the allowlist to include the proxy's hostname.

    Env contract:
        EME_GIR_ALLOWED_HOSTS    comma-separated public hostnames
        EME_GIR_ALLOWED_ORIGINS  comma-separated Origin headers
        EME_GIR_DISABLE_DNS_REBINDING_PROTECTION
                               truthy → disable the check entirely.
                               Only safe when the reverse proxy enforces
                               Host validation upstream.

    Returns {} when no env vars are set (SDK default applies).
    """
    raw_hosts = os.environ.get("EME_GIR_ALLOWED_HOSTS", "").strip()
    raw_origins = os.environ.get("EME_GIR_ALLOWED_ORIGINS", "").strip()
    disable = os.environ.get(
        "EME_GIR_DISABLE_DNS_REBINDING_PROTECTION", ""
    ).strip().lower() in {"1", "true", "on", "yes", "y", "enable", "enabled"}

    if not (raw_hosts or raw_origins or disable):
        return {}

    from mcp.server.transport_security import TransportSecuritySettings

    if disable:
        return {
            "transport_security": TransportSecuritySettings(
                enable_dns_rebinding_protection=False,
            )
        }

    user_hosts = [h.strip() for h in raw_hosts.split(",") if h.strip()]
    user_origins = [o.strip() for o in raw_origins.split(",") if o.strip()]

    # Add port-wildcard variants `host:*` for each user-supplied host —
    # reverse proxies vary in whether they preserve the port suffix on
    # the inward Host header.
    hosts: list[str] = []
    for h in user_hosts:
        hosts.append(h)
        if not h.endswith(":*") and ":" not in h.split("]")[-1]:
            hosts.append(h + ":*")

    origins: list[str] = []
    for o in user_origins:
        origins.append(o)
        if not o.endswith(":*"):
            origins.append(o + ":*")

    # Always permit localhost variants so in-container healthchecks
    # (`curl http://localhost:<port>/...`) keep working.
    for default_host in (
        "localhost", "localhost:*",
        "127.0.0.1", "127.0.0.1:*",
        "::1", "[::1]:*",
    ):
        if default_host not in hosts:
            hosts.append(default_host)

    return {
        "transport_security": TransportSecuritySettings(
            enable_dns_rebinding_protection=True,
            allowed_hosts=hosts,
            allowed_origins=origins,
        )
    }


def make_server(name: str, instructions: str) -> FastMCP:
    """Create a FastMCP instance with the project's standard auth +
    transport-security configuration applied from env vars.

    Args:
        name: MCP server identifier (e.g. 'eme-gir-epsd2'). Surfaced in
              the MCP handshake; pick something descriptive and unique.
        instructions: server-level instruction string returned to
                      clients on initialize. Keep it tight — each
                      server's instructions should describe its OWN
                      tools, not the whole suite.
    """
    return FastMCP(
        name=name,
        instructions=instructions,
        **_build_auth_kwargs(),
        **_build_transport_security_kwargs(),
    )


def run_server(
    mcp: FastMCP,
    log,
    default_port: int,
    required_dbs: list[tuple[Path, str]] | None = None,
    description: str | None = None,
) -> None:
    """Standard argparse + startup banner + transport selection.

    Args:
        mcp: the FastMCP instance to run (with all tools already registered).
        log: logger to emit the startup banner through.
        default_port: HTTP port when --transport http and no --port given.
                      Suite-wide allocation: 5051 (legacy), 5052 (epsd2),
                      5053 (etcsl), 5054 (cdli), 5055 (signs), 5056
                      (translator). Flask web app uses 5050.
        required_dbs: list of (Path, build_hint) tuples. Each path must
                      exist before the server can serve any tool —
                      missing-data hint is in `build_hint` (e.g.
                      'python3 build_glossary_db.py'). Each server only
                      checks the DBs ITS tools need.
        description: optional argparse program description; auto-derived
                     from mcp.name if not given.
    """
    parser = argparse.ArgumentParser(
        prog=f"python -m servers.{mcp.name.removeprefix('eme-gir-')}",
        description=description or f"Run the {mcp.name} MCP server.",
    )
    parser.add_argument(
        "--transport", choices=["stdio", "http"], default="stdio",
        help="stdio (default) for local Claude Code; http for networked use",
    )
    parser.add_argument(
        "--host", default="127.0.0.1",
        help="HTTP bind address (default 127.0.0.1; use 0.0.0.0 to expose "
             "behind a reverse proxy on a private network)",
    )
    parser.add_argument(
        "--port", type=int, default=default_port,
        help=f"HTTP port (default {default_port})",
    )
    args = parser.parse_args()

    # Per-server data-presence check.
    for db_path, build_hint in (required_dbs or []):
        if not db_path.exists():
            log.error(
                f"{db_path.name} missing at {db_path}. "
                f"Build it: `python3 {build_hint}`"
            )
            sys.exit(1)

    log.info(f"{mcp.name} MCP server starting (cwd={Path.cwd()}, root={ROOT})")
    for db_path, _ in (required_dbs or []):
        log.info(f"  {db_path.name}={db_path.stat().st_size // (1024*1024)} MB")

    if mcp.settings.auth is not None:
        log.info(
            f"  auth=ENABLED (Auth0 issuer={mcp.settings.auth.issuer_url}, "
            f"audience={os.environ.get('EME_GIR_AUTH0_AUDIENCE')}, "
            f"required_scopes={mcp.settings.auth.required_scopes})"
        )
    else:
        log.info("  auth=disabled (set EME_GIR_REQUIRE_AUTH=1 to enable)")

    ts = mcp.settings.transport_security
    if ts is None:
        log.info(
            "  transport_security=default (SDK accepts Host: localhost / "
            "127.0.0.1 only — set EME_GIR_ALLOWED_HOSTS for proxy deploys)"
        )
    elif not ts.enable_dns_rebinding_protection:
        log.warning(
            "  transport_security=DISABLED (EME_GIR_DISABLE_DNS_REBINDING_PROTECTION "
            "is set — proxy MUST enforce Host validation upstream)"
        )
    else:
        log.info(
            f"  transport_security=ENABLED (allowed_hosts={ts.allowed_hosts}, "
            f"allowed_origins={ts.allowed_origins})"
        )

    # Umami analytics is global — initialized once even if multiple servers
    # run in the same process. init_from_env is idempotent.
    _umami = umami_analytics.init_from_env()
    if _umami is not None:
        log.info(
            f"  analytics=ENABLED (Umami endpoint={_umami.endpoint}, "
            f"website={_umami.website_id})"
        )
    else:
        log.info(
            "  analytics=disabled (set EME_GIR_UMAMI_URL + "
            "EME_GIR_UMAMI_WEBSITE_ID to enable)"
        )

    if args.transport == "stdio":
        log.info("  transport=stdio (one client over the parent process pipes)")
        if mcp.settings.auth is not None:
            log.warning(
                "  NOTE: stdio transport does not enforce OAuth (per MCP spec); "
                "auth wiring will sit idle. Use --transport http to enforce."
            )
        mcp.run()
    else:
        mcp.settings.host = args.host
        mcp.settings.port = args.port
        log.info(
            f"  transport=http (streamable-http) on {args.host}:{args.port}"
            f"{mcp.settings.streamable_http_path}"
        )
        mcp.run(transport="streamable-http")
