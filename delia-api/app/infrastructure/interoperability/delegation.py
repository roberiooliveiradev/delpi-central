"""User-delegated credential provider — C3-MCP-INTEROP-01R1A.

Single confidential DÉLIA requester client + RFC 8693 token exchange:

    Portal user bearer
    → DÉLIA (this module)
    → resource-bound token for the SAME user
    → selected specialist MCP

Fail-closed invariants enforced before any returned token is used or
cached: subject preserved, not a service principal, ``mcp:tools``
present, exactly the requested resource audience present, other
approved MCP resource audiences absent, expiration valid. An HTTP 200
from the issuer is never sufficient on its own.

Secrets/tokens are never logged, never persisted, never exposed upward
— provider failures map to semantic ``MCP_AUTHENTICATION_FAILED`` only.
"""

from __future__ import annotations

import base64
import hashlib
import json
import threading
import time
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from typing import Any, Protocol

from app.application.specialist_interop.errors import (
    MCP_AUTHENTICATION_FAILED,
    MCP_TIMEOUT,
    SpecialistInteropError,
)
from app.infrastructure.http.bounded_request import (
    BoundedHttpTimeout,
    bounded_request,
)
from app.infrastructure.interoperability.config import (
    SpecialistConnectionProfile,
)

EXCHANGE_GRANT_TYPE = "urn:ietf:params:oauth:grant-type:token-exchange"
SUBJECT_TOKEN_TYPE = "urn:ietf:params:oauth:token-type:access_token"
EXCHANGE_SCOPE = "openid profile email mcp:tools"

# Safety margin so a cached token is never returned near its `exp`.
_EXPIRY_SAFETY_MARGIN_SECONDS = 15.0
_ABSOLUTE_HARD_CAP_SECONDS = 300.0


class DelegatedCredentialProvider(Protocol):
    """Provider-neutral delegated-credential boundary.

    The MCP adapter is the only consumer. Implementations must obtain a
    short-lived credential bound to the current authenticated subject
    and the profile's approved MCP resource — or fail closed.
    """

    def credential_for(
        self,
        profile: SpecialistConnectionProfile,
        *,
        timeout_seconds: float | None = None,
    ) -> str:
        """Return a delegated bearer for (current subject, resource).

        ``timeout_seconds`` is an optional reduction-only caller bound
        on any required exchange — ``None`` keeps the configured
        exchange ceiling; a non-positive remainder fails fast with a
        timeout semantic, never a fresh window.
        """

    def invalidate(self, profile: SpecialistConnectionProfile) -> None:
        """Drop any cached credential for (current subject, resource).

        Called after a rejected MCP authentication so the next call
        re-exchanges instead of reusing a refused credential.
        """


def _decode_claims(token: str) -> Mapping[str, Any]:
    """Unverified claim read — used only for subject correlation.

    The subject bearer was already signature-validated upstream by the
    auth middleware; exchanged tokens are signature-validated via the
    injected validator before this is used on them.
    """
    try:
        parts = token.split(".")
        if len(parts) != 3:
            return {}
        padded = parts[1] + "=" * (-len(parts[1]) % 4)
        claims = json.loads(base64.urlsafe_b64decode(padded))
    except (ValueError, json.JSONDecodeError, UnicodeDecodeError):
        return {}
    return claims if isinstance(claims, Mapping) else {}


def _subject_fingerprint(subject_token: str) -> str:
    """Stable, non-reversible cache-key fragment — never logged raw."""
    return hashlib.sha256(subject_token.encode("utf-8")).hexdigest()[:32]


@dataclass(slots=True)
class _CacheEntry:
    token: str
    expires_at: float


class InMemoryDelegatedTokenCache:
    """Process-local, user+resource scoped delegated-token cache.

    Key isolation: (subject token fingerprint, resource audience) —
    no cross-user or cross-resource reuse is possible. Expiry is always
    the earlier of the configured TTL (hard-capped) and the token's own
    ``exp`` minus a safety margin. No persistence, no background
    refresh, no raw-token observability.
    """

    def __init__(
        self,
        *,
        max_ttl_seconds: float,
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        self._max_ttl = min(float(max_ttl_seconds), _ABSOLUTE_HARD_CAP_SECONDS)
        self._clock = clock
        self._lock = threading.Lock()
        self._entries: dict[tuple[str, str], _CacheEntry] = {}

    def get(
        self, subject_fingerprint: str, resource_audience: str
    ) -> str | None:
        key = (subject_fingerprint, resource_audience)
        with self._lock:
            entry = self._entries.get(key)
            if entry is None:
                return None
            if entry.expires_at <= self._clock():
                self._entries.pop(key, None)
                return None
            return entry.token

    def put(
        self,
        subject_fingerprint: str,
        resource_audience: str,
        token: str,
        *,
        token_exp_epoch: float | None,
        wall_clock: Callable[[], float] = time.time,
    ) -> None:
        now = self._clock()
        expires_at = now + self._max_ttl
        if token_exp_epoch is not None:
            # Convert token exp (wall clock) to monotonic budget.
            remaining = float(token_exp_epoch) - wall_clock()
            expires_at = min(
                expires_at, now + max(0.0, remaining - _EXPIRY_SAFETY_MARGIN_SECONDS)
            )
        key = (subject_fingerprint, resource_audience)
        with self._lock:
            self._entries[key] = _CacheEntry(token=token, expires_at=expires_at)

    def invalidate(
        self, subject_fingerprint: str, resource_audience: str
    ) -> None:
        with self._lock:
            self._entries.pop((subject_fingerprint, resource_audience), None)


class KeycloakDelegatedCredentialProvider:
    """RFC 8693 token exchange through the single DÉLIA requester client.

    Keycloak/HTTP mechanics are confined here. ``subject_bearer_getter``
    supplies the current request's authenticated Portal bearer
    (request-scoped — never persisted). ``token_validator`` performs
    canonical signature/issuer/audience validation of the exchange
    output; tests inject a deterministic fake.
    """

    def __init__(
        self,
        *,
        token_url: str,
        client_id: str,
        client_secret: str,
        timeout_seconds: float,
        http_post: Callable[..., Any],
        subject_bearer_getter: Callable[[], str | None],
        token_validator: Callable[[str], Mapping[str, Any]],
        cache: InMemoryDelegatedTokenCache,
        known_resource_audiences: frozenset[str],
        host_header: str = "",
    ) -> None:
        self._known_resource_audiences = frozenset(known_resource_audiences)
        self._host_header = host_header
        self._token_url = token_url
        self._client_id = client_id
        self._client_secret = client_secret
        self._timeout_seconds = timeout_seconds
        self._http_post = http_post
        self._subject_bearer_getter = subject_bearer_getter
        self._token_validator = token_validator
        self._cache = cache

    def credential_for(
        self,
        profile: SpecialistConnectionProfile,
        *,
        timeout_seconds: float | None = None,
    ) -> str:
        subject_token = (self._subject_bearer_getter() or "").strip()
        if not subject_token:
            raise SpecialistInteropError(
                MCP_AUTHENTICATION_FAILED,
                "no authenticated subject credential in request scope",
            )
        subject_claims = _decode_claims(subject_token)
        subject_sub = subject_claims.get("sub")
        if not isinstance(subject_sub, str) or not subject_sub:
            raise SpecialistInteropError(
                MCP_AUTHENTICATION_FAILED,
                "subject credential carries no subject claim",
            )
        subject_exp = subject_claims.get("exp")
        if not isinstance(subject_exp, (int, float)) or float(
            subject_exp
        ) <= time.time():
            raise SpecialistInteropError(
                MCP_AUTHENTICATION_FAILED,
                "subject credential is expired or malformed",
            )
        fingerprint = _subject_fingerprint(subject_token)
        resource = profile.resource_audience
        cached = self._cache.get(fingerprint, resource)
        if cached is not None:
            return cached

        if not (
            self._token_url
            and self._client_id
            and self._client_secret
            and resource
            and profile.exchange_audience
        ):
            raise SpecialistInteropError(
                MCP_AUTHENTICATION_FAILED,
                "delegated credential exchange is not configured",
            )

        raw = self._exchange(
            subject_token,
            profile.exchange_audience,
            timeout_seconds=timeout_seconds,
        )
        token = self._validated_token(raw, subject_sub, resource)
        exp = _decode_claims(token).get("exp")
        self._cache.put(
            fingerprint,
            resource,
            token,
            token_exp_epoch=float(exp) if isinstance(exp, (int, float)) else None,
        )
        return token

    def invalidate(self, profile: SpecialistConnectionProfile) -> None:
        subject_token = (self._subject_bearer_getter() or "").strip()
        if not subject_token:
            return
        self._cache.invalidate(
            _subject_fingerprint(subject_token), profile.resource_audience
        )

    def _exchange(
        self,
        subject_token: str,
        audience: str,
        *,
        timeout_seconds: float | None = None,
    ) -> Mapping[str, Any]:
        # LOOP-03R2A-R2: the caller's remaining budget is a
        # reduction-only ceiling on the whole exchange — connect,
        # headers and body drain share one wall-clock deadline. An
        # exhausted remainder fails fast as MCP_TIMEOUT with zero
        # wire calls; it never widens into a fresh configured window.
        effective_timeout = (
            self._timeout_seconds
            if timeout_seconds is None
            else min(float(timeout_seconds), self._timeout_seconds)
        )
        if effective_timeout <= 0:
            raise SpecialistInteropError(
                MCP_TIMEOUT,
                "delegated credential exchange budget exhausted",
            )
        headers = {"Host": self._host_header} if self._host_header else None
        try:
            response = bounded_request(
                self._http_post,
                self._token_url,
                headers=headers,
                data={
                    "grant_type": EXCHANGE_GRANT_TYPE,
                    "client_id": self._client_id,
                    "client_secret": self._client_secret,
                    "subject_token": subject_token,
                    "subject_token_type": SUBJECT_TOKEN_TYPE,
                    "audience": audience,
                    "scope": EXCHANGE_SCOPE,
                },
                timeout_seconds=effective_timeout,
            )
        except BoundedHttpTimeout as exc:
            raise SpecialistInteropError(
                MCP_TIMEOUT,
                "delegated credential exchange timed out",
            ) from exc
        except Exception as exc:
            raise SpecialistInteropError(
                MCP_AUTHENTICATION_FAILED,
                "delegated credential exchange transport failed",
            ) from exc
        status = getattr(response, "status_code", None)
        if status != 200:
            # Provider denial (invalid secret, exchange not permitted,
            # audience rejected) — never surface the raw body upward.
            raise SpecialistInteropError(
                MCP_AUTHENTICATION_FAILED,
                "delegated credential exchange denied",
            )
        try:
            body = response.json()
        except Exception as exc:
            raise SpecialistInteropError(
                MCP_AUTHENTICATION_FAILED,
                "delegated credential exchange returned malformed output",
            ) from exc
        if not isinstance(body, Mapping) or not isinstance(
            body.get("access_token"), str
        ):
            raise SpecialistInteropError(
                MCP_AUTHENTICATION_FAILED,
                "delegated credential exchange returned malformed output",
            )
        return body

    def _validated_token(
        self, body: Mapping[str, Any], subject_sub: str, resource: str
    ) -> str:
        token = body["access_token"]
        try:
            claims = self._token_validator(token)
        except Exception as exc:
            raise SpecialistInteropError(
                MCP_AUTHENTICATION_FAILED,
                "delegated credential failed validation",
            ) from exc
        if not isinstance(claims, Mapping):
            raise SpecialistInteropError(
                MCP_AUTHENTICATION_FAILED,
                "delegated credential returned no claims",
            )

        sub = claims.get("sub")
        if not isinstance(sub, str) or not sub:
            raise SpecialistInteropError(
                MCP_AUTHENTICATION_FAILED,
                "delegated credential has no subject",
            )
        if sub != subject_sub:
            raise SpecialistInteropError(
                MCP_AUTHENTICATION_FAILED,
                "delegated credential subject mismatch",
            )
        if sub.startswith("service-account-"):
            raise SpecialistInteropError(
                MCP_AUTHENTICATION_FAILED,
                "service principal is not a delegated user credential",
            )
        # R1B-R3: requester binding — the exchanged credential must be
        # issued for the configured DÉLIA requester client. `azp` is a
        # transport binding only — never business authorization.
        if claims.get("azp") != self._client_id:
            raise SpecialistInteropError(
                MCP_AUTHENTICATION_FAILED,
                "delegated credential requester binding mismatch",
            )

        aud = claims.get("aud")
        audiences = set(aud if isinstance(aud, list) else [aud])
        if resource not in audiences:
            raise SpecialistInteropError(
                MCP_AUTHENTICATION_FAILED,
                "delegated credential is not bound to the target resource",
            )
        other_resources = self._known_resource_audiences - {resource}
        if audiences & other_resources:
            raise SpecialistInteropError(
                MCP_AUTHENTICATION_FAILED,
                "delegated credential carries foreign resource audiences",
            )

        scopes = set(str(claims.get("scope") or "").split())
        if "mcp:tools" not in scopes:
            raise SpecialistInteropError(
                MCP_AUTHENTICATION_FAILED,
                "delegated credential missing mcp:tools scope",
            )

        exp = claims.get("exp")
        if not isinstance(exp, (int, float)) or float(exp) <= time.time():
            raise SpecialistInteropError(
                MCP_AUTHENTICATION_FAILED,
                "delegated credential is expired or has no expiry",
            )
        return token
