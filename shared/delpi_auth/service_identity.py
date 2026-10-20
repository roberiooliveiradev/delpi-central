"""Authenticated technical service identity.

Produced by ``ServiceTokenValidator`` from a verified client-credentials JWT.
It is intentionally distinct from the user principal minted by the auth
middleware: no ``is_superadmin`` flag exists here and no permission shortcut
may be derived from it.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping


@dataclass(frozen=True)
class ServiceIdentity:
    client_id: str
    subject: str
    scopes: frozenset[str]
    audience: tuple[str, ...]
    issuer: str
    expires_at: int | None = None

    principal_type: str = field(default="service", init=False)

    def has_scope(self, scope: str) -> bool:
        return scope in self.scopes

    @classmethod
    def from_claims(cls, claims: Mapping[str, Any], *, client_id: str) -> "ServiceIdentity":
        raw_aud = claims.get("aud")
        if isinstance(raw_aud, str):
            audience = (raw_aud,)
        else:
            audience = tuple(str(item) for item in (raw_aud or ()))
        scope_claim = claims.get("scope")
        scopes = frozenset(
            item for item in str(scope_claim or "").split() if item
        )
        exp = claims.get("exp")
        return cls(
            client_id=client_id,
            subject=str(claims.get("sub") or ""),
            scopes=scopes,
            audience=audience,
            issuer=str(claims.get("iss") or ""),
            expires_at=int(exp) if exp is not None else None,
        )
