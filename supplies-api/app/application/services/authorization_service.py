from __future__ import annotations

from app.application.security.supplies_permissions import OPERATIONAL_UNITS, has_canonical_access
from app.domain.entities import EffectiveUser
from app.domain.exceptions import AuthorizationError, CoreApiUnavailableError
from app.infrastructure.gateways.core_api_http_gateway import CoreApiHttpGateway


class AuthorizationService:
    def __init__(self, core_gateway: CoreApiHttpGateway | None = None) -> None:
        self.core_gateway = core_gateway or CoreApiHttpGateway()

    def resolve_effective_user(self, access_token: str, *, keycloak_sub: str | None = None) -> EffectiveUser:
        me = self.core_gateway.get_me(access_token)
        if not me.get("id"):
            raise CoreApiUnavailableError("Core /me missing user id")

        permissions = {str(code) for code in (me.get("permissions") or []) if code}
        return EffectiveUser(
            id=str(me["id"]),
            email=str(me.get("email") or ""),
            name=str(me["name"]) if me.get("name") else None,
            permissions=permissions,
            is_superadmin=bool(me.get("is_superadmin", False)),
            keycloak_sub=keycloak_sub,
            access_token=access_token,
        )

    def require_permission(self, user: EffectiveUser, permission: str) -> None:
        if user.has_permission(permission):
            return
        raise AuthorizationError("Forbidden")

    def allowed_units(self, user: EffectiveUser) -> list[str]:
        """Operational branches for data filters. Not a permission grant."""
        if user.is_superadmin or has_canonical_access(user):
            return list(OPERATIONAL_UNITS)
        return []

    def require_unit(self, user: EffectiveUser, branch: str) -> None:
        if user.is_superadmin:
            return
        if branch not in self.allowed_units(user):
            raise AuthorizationError("Forbidden")

    def require_units(self, user: EffectiveUser, branches: list[str]) -> None:
        cleaned = [str(item or "").strip() for item in branches if str(item or "").strip()]
        if not cleaned:
            raise AuthorizationError("Forbidden")
        for branch in cleaned:
            self.require_unit(user, branch)
