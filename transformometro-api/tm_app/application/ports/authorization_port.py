"""Authorization port for Diagnostic governed writes.

The Core is the single permission authority — this port never resolves
roles, groups or overrides locally. Implementations must return a
principal whose permissions were observed from the canonical authority
fresh enough for the operation at hand (``authorize_fresh`` bypasses any
RBAC cache and fails closed when the authority is unreachable).

Stable error codes (transport-agnostic):
``diagnostic.authentication_required``, ``diagnostic.authorization_denied``,
``diagnostic.authorization_unavailable``.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


class DiagnosticAuthorizationError(PermissionError):
    """Authorization failure with a stable semantic code."""

    def __init__(self, code: str, message: str) -> None:
        self.code = code
        super().__init__(f"{code}: {message}")


@dataclass(frozen=True)
class AuthorizationPrincipal:
    """End-user principal observed from the canonical authority.

    ``principal_type`` is the canonical shared-auth marker — only ``"user"``
    is an end-user. ``rbac_fresh`` records that permissions came from a
    non-cached authority lookup.
    """

    user_id: str
    email: str | None
    is_superadmin: bool
    permissions: tuple[str, ...]
    principal_type: str
    rbac_fresh: bool


class AuthorizationPort(Protocol):
    """Fresh, fail-closed authorization for material Diagnostic writes."""

    async def authorize_fresh(self) -> AuthorizationPrincipal:
        """Return an end-user principal authorized for ``transformometro.access``.

        Must raise ``DiagnosticAuthorizationError`` when:
        - no authenticated principal exists (``diagnostic.authentication_required``);
        - the principal is not an end-user (``diagnostic.authorization_denied``);
        - the user lacks ``transformometro.access`` (``diagnostic.authorization_denied``);
        - the canonical authority cannot be consulted fresh
          (``diagnostic.authorization_unavailable``) — never fall back to
          stale/cached authorization for a material write.
        """
        ...
