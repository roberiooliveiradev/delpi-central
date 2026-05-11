from app.domain.exceptions.authorization_exceptions import MissingPermissionError
from app.domain.ports.core_api_gateway_port import CoreApiGatewayPort


class PermissionContextService:
    def __init__(self, core_api_gateway: CoreApiGatewayPort):
        self.core_api_gateway = core_api_gateway

    def load_context(self, access_token: str) -> dict:
        me = self.core_api_gateway.get_me(access_token)

        permissions = me.get("permissions") or []
        is_superadmin = bool(me.get("is_superadmin", False))

        return {
            "me": me,
            "permissions": set(str(permission) for permission in permissions),
            "is_superadmin": is_superadmin,
        }

    def require_permission(self, access_token: str, permission: str) -> dict:
        context = self.load_context(access_token)

        if context["is_superadmin"]:
            return context

        if permission not in context["permissions"]:
            raise MissingPermissionError(permission)

        return context

    def get_authorized_apps(self, access_token: str) -> list[dict]:
        return self.core_api_gateway.get_apps(access_token)

    def get_authorized_routes(self, access_token: str) -> list[dict]:
        return self.core_api_gateway.get_routes(access_token)
