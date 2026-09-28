"""Canonical fresh-authorization adapter for Diagnostic writes.

Composition:
    request context (shared delpi_auth) → bearer token
    → ``load_user_rbac(token, force_refresh=True)`` (Core /me, no cache,
      no stale fallback — fail-closed)
    → end-user principal check (``principal_type == "user"``)
    → ``transformometro.access`` membership

No local RBAC: roles/groups/overrides are resolved exclusively by the
Core. The ``principal_type`` marker minted by the shared middleware is
the canonical distinction between human end-users and service
principals — service tokens mint ``"service"`` and can never satisfy a
material conversational write.
"""

from __future__ import annotations

from delpi_auth.middleware.fastapi_auth import load_user_rbac
from delpi_auth.request_context import (
    get_current_user,
    get_request_authorization,
)

from tm_app.application.ports.authorization_port import (
    AuthorizationPort,
    AuthorizationPrincipal,
    DiagnosticAuthorizationError,
)
from tm_app.application.security.transformometro_permissions import (
    ACCESS_PERMISSION,
)


def _raise(code: str, message: str) -> None:
    raise DiagnosticAuthorizationError(code, message)


class FreshAuthorizationAdapter(AuthorizationPort):
    """Fails closed: no fresh Core answer, no write."""

    async def authorize_fresh(self) -> AuthorizationPrincipal:
        user = get_current_user()
        if user is None:
            _raise(
                "diagnostic.authentication_required",
                "principal autenticado ausente.",
            )

        # Canonical marker from the shared middleware — "user" is the only
        # acceptable end-user principal for material Diagnostic writes.
        if getattr(user, "principal_type", None) != "user":
            _raise(
                "diagnostic.authorization_denied",
                "write material exige principal end-user.",
            )

        authorization = (get_request_authorization() or "").strip()
        scheme, _, token = authorization.partition(" ")
        if scheme.lower() != "bearer" or not token.strip():
            _raise(
                "diagnostic.authentication_required",
                "credencial do usuário indisponível para autorização fresh.",
            )

        try:
            rbac = await load_user_rbac(token.strip(), force_refresh=True)
        except Exception as exc:
            raise DiagnosticAuthorizationError(
                "diagnostic.authorization_unavailable",
                "authority de permissões indisponível para verificação fresh.",
            ) from exc

        permissions = tuple(rbac.get("permissions") or ())
        is_superadmin = bool(rbac.get("is_superadmin", False))
        if not (is_superadmin or ACCESS_PERMISSION in permissions):
            _raise(
                "diagnostic.authorization_denied",
                "Sem permissão transformometro.access.",
            )

        return AuthorizationPrincipal(
            user_id=str(rbac.get("id") or getattr(user, "id", "")),
            email=rbac.get("email") or getattr(user, "email", None),
            is_superadmin=is_superadmin,
            permissions=permissions,
            principal_type="user",
            rbac_fresh=True,
        )
