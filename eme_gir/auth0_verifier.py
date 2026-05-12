"""Auth0 OAuth 2.1 bearer-token verifier for the FastMCP HTTP transport.

Plugs into FastMCP's resource-server-only auth path
(`mcp.server.auth.provider.TokenVerifier`). When wired in, every request
to /mcp/ is gated on a valid Auth0-issued RS256 JWT in the
`Authorization: Bearer ...` header — FastMCP's BearerAuthBackend +
RequireAuthMiddleware do the request-side enforcement; we just decode
the token and return an AccessToken (or None to reject).

Auth0 acts as the OAuth Authorization Server (AS) — it issues tokens
via /oauth/token and signs them with a per-tenant RS256 keypair whose
public half is published at https://{tenant}/.well-known/jwks.json.
This module is the Resource Server (RS) side: validate the signature,
audience, issuer, expiry, and required scope.

JWKS handling: PyJWKClient maintains its own LRU cache (10-min default
TTL on the lifetime cache, 5-min on unknown-kid lookups). The cache
miss does an HTTP GET against Auth0's JWKS endpoint, which is sync, so
we wrap the lookup in `asyncio.to_thread` to avoid blocking the
asyncio event loop on cold starts and key rotations.

See `mcp_server.py`'s entrypoint for the env-var contract that drives
this verifier; see START.md "Adding Auth0 OAuth" for setup steps."""

from __future__ import annotations

import asyncio
import logging
from typing import Iterable

import jwt
from jwt import PyJWKClient
from mcp.server.auth.provider import AccessToken, TokenVerifier

log = logging.getLogger("eme-gir.auth")


class Auth0TokenVerifier(TokenVerifier):
    """Validate Auth0-issued RS256 JWTs against this server's audience.

    Args:
        tenant_url: Auth0 tenant base URL, e.g. "https://my.auth0.com".
            No trailing slash; the issuer string is constructed by
            appending '/' (Auth0 emits `iss` with a trailing slash).
        audience: the API identifier configured in Auth0 for this server,
            e.g. "https://eme-gir.example.com". Tokens whose `aud` claim
            doesn't match are rejected — this is the RFC 8707 audience
            binding that prevents tokens from one MCP server being
            replayed against another.
        required_scope: a single scope name that must appear in the
            token's space-delimited `scope` claim. Defaults to None,
            meaning any valid Auth0 token grants full access. Set to
            'mcp:access' to enforce the project's standard scope.
    """

    def __init__(
        self,
        tenant_url: str,
        audience: str,
        required_scope: str | None = None,
    ) -> None:
        self.tenant_url = tenant_url.rstrip("/")
        self.audience = audience
        self.required_scope = required_scope
        # Auth0 emits `iss` claim WITH a trailing slash. PyJWT compares
        # the decoded `iss` against this string verbatim, so the trailing
        # '/' must be present.
        self.issuer = self.tenant_url + "/"
        self.jwks_client = PyJWKClient(
            f"{self.tenant_url}/.well-known/jwks.json",
            cache_keys=True,
        )

    async def verify_token(self, token: str) -> AccessToken | None:
        """Return AccessToken if the JWT is valid for this server, else None.

        FastMCP's BearerAuthBackend translates `None` into a 401 with the
        appropriate WWW-Authenticate challenge — there's no need to raise.
        """
        try:
            # PyJWKClient's get_signing_key_from_jwt is sync I/O on cache
            # miss (HTTP GET to Auth0's JWKS endpoint). Push it off the
            # event loop so a cold start or key rotation doesn't stall
            # other in-flight tool calls.
            signing_key = await asyncio.to_thread(
                self.jwks_client.get_signing_key_from_jwt, token
            )
            payload = jwt.decode(
                token,
                signing_key.key,
                algorithms=["RS256"],
                audience=self.audience,
                issuer=self.issuer,
                # Standard required claims — exp + iat checked by PyJWT.
                options={"require": ["exp", "iat"]},
            )
        except jwt.PyJWTError as e:
            # Includes ExpiredSignatureError, InvalidAudienceError,
            # InvalidIssuerError, InvalidSignatureError, etc.
            log.info(f"auth: rejected token ({type(e).__name__}: {e})")
            return None
        except Exception as e:
            # JWKS fetch failures, network errors, malformed key data —
            # never let an unexpected error look like an auth bypass.
            log.warning(f"auth: token verification failed unexpectedly: {e}")
            return None

        scopes = _parse_scopes(payload.get("scope"))
        if self.required_scope and self.required_scope not in scopes:
            log.info(
                f"auth: rejected token (missing required scope "
                f"{self.required_scope!r}; had {scopes!r})"
            )
            return None

        return AccessToken(
            token=token,
            # Prefer azp (authorized party — the app that requested the
            # token) over sub (the end-user); for machine-to-machine
            # tokens azp is the client_id, which is more useful in logs.
            client_id=payload.get("azp") or payload.get("sub", "unknown"),
            scopes=list(scopes),
            expires_at=payload.get("exp"),
            resource=self.audience,
        )


def _parse_scopes(scope_claim) -> Iterable[str]:
    """Extract scopes from a JWT `scope` claim.

    Auth0 emits scopes as a space-delimited string per OAuth 2.0 §3.3,
    but some IdPs use a list. Handle both.
    """
    if scope_claim is None:
        return ()
    if isinstance(scope_claim, str):
        return tuple(s for s in scope_claim.split() if s)
    if isinstance(scope_claim, (list, tuple)):
        return tuple(str(s) for s in scope_claim if s)
    return ()
