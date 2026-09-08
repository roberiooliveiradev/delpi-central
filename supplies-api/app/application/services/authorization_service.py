from __future__ import annotations

from app.domain.entities import EffectiveUser
from app.domain.exceptions import AuthorizationError, CoreApiUnavailableError
from app.infrastructure.gateways.core_api_http_gateway import CoreApiHttpGateway

UNIT_PREFIX = "supplies.unit.filial-"
LEGACY_UNIT_ALIASES = {
    "purchase-requests.unit.filial-01": "01",
    "purchase-requests.unit.filial-02": "02",
    "estoque-seguranca.view.filial-sc": "01",
    "estoque-seguranca.view.filial-es": "02",
}


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
        if user.is_superadmin:
            return ["01", "02"]

        units: set[str] = set()
        for code in user.permissions:
            if code.startswith(UNIT_PREFIX):
                units.add(code.removeprefix(UNIT_PREFIX))
            elif code in LEGACY_UNIT_ALIASES:
                units.add(LEGACY_UNIT_ALIASES[code])
        return sorted(units)

    def require_unit(self, user: EffectiveUser, branch: str) -> None:
        if user.is_superadmin:
            return
        allowed = self.allowed_units(user)
        if branch not in allowed:
            raise AuthorizationError("Forbidden")
