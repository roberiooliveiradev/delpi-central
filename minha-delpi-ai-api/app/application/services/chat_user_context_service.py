import logging

from app.domain.ports.core_api_gateway_port import CoreApiGatewayPort
from app.infrastructure.config.settings import Settings

logger = logging.getLogger("minha-delpi-ai-api.user_context")


class ChatUserContextService:
    """Constrói bloco textual com informações do usuário para injeção no prompt."""

    def __init__(self, core_api_gateway: CoreApiGatewayPort):
        self.core_api_gateway = core_api_gateway

    def build_user_context(self, access_token: str | None) -> str:
        if not access_token or not getattr(Settings, "CHAT_USER_CONTEXT_ENABLED", True):
            return ""

        try:
            me = self.core_api_gateway.get_me(access_token)
        except Exception:
            logger.debug("user_context_fetch_failed", exc_info=True)
            return ""

        if not me or me.get("authorized") is False:
            return ""

        apps = self._fetch_apps(access_token)

        return self._format_context(me, apps)

    def _fetch_apps(self, access_token: str) -> list[dict]:
        try:
            return self.core_api_gateway.get_apps(access_token)
        except Exception:
            logger.debug("user_context_apps_fetch_failed", exc_info=True)
            return []

    def _format_context(self, me: dict, apps: list[dict]) -> str:
        parts = ["[Informações do usuário atual]"]

        name = me.get("name") or ""
        email = me.get("email") or ""
        if name:
            parts.append(f"Nome: {name}")
        if email:
            parts.append(f"Email: {email}")

        is_superadmin = me.get("is_superadmin", False)
        if is_superadmin:
            parts.append("Perfil: Superadministrador")

        roles = me.get("roles") or []
        if roles:
            parts.append(f"Papéis: {', '.join(roles)}")

        groups = me.get("groups") or []
        if groups:
            parts.append(f"Grupos: {', '.join(groups)}")

        permissions = me.get("permissions") or []
        if permissions:
            perm_display = permissions[:30]
            line = f"Permissões ({len(permissions)}): {', '.join(perm_display)}"
            if len(permissions) > 30:
                line += f" … e mais {len(permissions) - 30}"
            parts.append(line)

        if apps:
            app_names = [
                a.get("label") or a.get("name") or a.get("key", "")
                for a in apps
                if a.get("label") or a.get("name") or a.get("key")
            ]
            if app_names:
                parts.append(f"Apps disponíveis ({len(app_names)}): {', '.join(app_names)}")

        if len(parts) <= 1:
            return ""

        return "\n".join(parts)
