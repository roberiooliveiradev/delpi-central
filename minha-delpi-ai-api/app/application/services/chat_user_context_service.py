import logging
import re

from app.domain.ports.core_api_gateway_port import CoreApiGatewayPort
from app.infrastructure.config.settings import Settings

logger = logging.getLogger("minha-delpi-ai-api.user_context")

_USER_IDENTITY_TERMS = (
    "quem sou eu",
    "quem sou",
    "meus papéis",
    "meus papeis",
    "meu papel",
    "meus grupos",
    "meu grupo",
    "minhas permissões",
    "minhas permissoes",
    "minha permissão",
    "minha permissao",
    "meu perfil",
    "meus dados",
    "meu email",
    "meu e-mail",
    "meu nome",
    "quais apps",
    "meus apps",
    "meus aplicativos",
    "sobre mim",
    "diz sobre mim",
    "sabe sobre mim",
    "informações sobre mim",
    "informacoes sobre mim",
    "o que sabe de mim",
    "o que diz sobre mim",
    "me fale sobre mim",
    "fale sobre mim",
    "quais são meus",
    "quais sao meus",
    "quais são minhas",
    "quais sao minhas",
    "o que tenho acesso",
    "que acesso eu tenho",
    "acesso a quais",
    "posso acessar",
)


class ChatUserContextService:
    """Constrói bloco textual com informações do usuário para injeção no prompt."""

    def __init__(self, core_api_gateway: CoreApiGatewayPort):
        self.core_api_gateway = core_api_gateway

    @classmethod
    def is_user_identity_question(cls, message: str) -> bool:
        normalized = str(message or "").lower()
        return any(term in normalized for term in _USER_IDENTITY_TERMS)

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

    def build_direct_answer(self, access_token: str | None, message: str) -> str | None:
        """Gera resposta direta (sem LLM) para perguntas sobre perfil do usuário."""
        if not access_token or not self.is_user_identity_question(message):
            return None

        try:
            me = self.core_api_gateway.get_me(access_token)
        except Exception:
            return None

        if not me or me.get("authorized") is False:
            return None

        apps = self._fetch_apps(access_token)
        return self._format_direct_answer(me, apps, message)

    def _fetch_apps(self, access_token: str) -> list[dict]:
        try:
            return self.core_api_gateway.get_apps(access_token)
        except Exception:
            logger.debug("user_context_apps_fetch_failed", exc_info=True)
            return []

    def _format_context(self, me: dict, apps: list[dict]) -> str:
        parts = [
            "[Dados do usuário que está conversando com você]",
            "REGRA: quando o usuário perguntar sobre si mesmo (quem sou, meus papéis, "
            "meus apps, meu perfil, sobre mim, etc.), responda com os dados abaixo.",
        ]

        name = me.get("name") or ""
        email = me.get("email") or ""
        if name:
            parts.append(f"Nome do usuário: {name}")
        if email:
            parts.append(f"Email do usuário: {email}")

        is_superadmin = me.get("is_superadmin", False)
        if is_superadmin:
            parts.append("Perfil: Superadministrador")

        roles = me.get("roles") or []
        if roles:
            parts.append(f"Papéis do usuário: {', '.join(roles)}")

        groups = me.get("groups") or []
        if groups:
            parts.append(f"Grupos do usuário: {', '.join(groups)}")

        permissions = me.get("permissions") or []
        if permissions:
            perm_display = permissions[:30]
            line = f"Permissões do usuário ({len(permissions)}): {', '.join(perm_display)}"
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
                parts.append(f"Apps que o usuário pode acessar ({len(app_names)}): {', '.join(app_names)}")

        if len(parts) <= 2:
            return ""

        return "\n".join(parts)

    def _format_direct_answer(self, me: dict, apps: list[dict], message: str) -> str:
        """Formata resposta direta legível sem necessidade de LLM."""
        normalized = str(message or "").lower()
        name = me.get("name") or "Não informado"
        email = me.get("email") or "Não informado"
        roles = me.get("roles") or []
        groups = me.get("groups") or []
        permissions = me.get("permissions") or []
        is_superadmin = me.get("is_superadmin", False)

        app_names = [
            a.get("label") or a.get("name") or a.get("key", "")
            for a in (apps or [])
            if a.get("label") or a.get("name") or a.get("key")
        ]

        if any(t in normalized for t in ("quais apps", "meus apps", "meus aplicativos", "posso acessar", "tenho acesso", "acesso a quais")):
            if app_names:
                lines = [f"Você tem acesso a **{len(app_names)} app(s)**:"]
                for app_name in app_names:
                    lines.append(f"- {app_name}")
                return "\n".join(lines)
            return "Não encontrei apps vinculados ao seu perfil."

        if any(t in normalized for t in ("meu papel", "meus papéis", "meus papeis")):
            if roles:
                lines = [f"Seus papéis ({len(roles)}):"]
                for role in roles:
                    lines.append(f"- {role}")
                return "\n".join(lines)
            return "Não encontrei papéis vinculados ao seu perfil."

        if any(t in normalized for t in ("minha permiss", "minhas permiss")):
            if permissions:
                lines = [f"Suas permissões ({len(permissions)}):"]
                for perm in permissions[:40]:
                    lines.append(f"- {perm}")
                if len(permissions) > 40:
                    lines.append(f"- … e mais {len(permissions) - 40}")
                return "\n".join(lines)
            return "Não encontrei permissões vinculadas ao seu perfil."

        if any(t in normalized for t in ("meu grupo", "meus grupos")):
            if groups:
                lines = [f"Seus grupos ({len(groups)}):"]
                for group in groups:
                    lines.append(f"- {group}")
                return "\n".join(lines)
            return "Não encontrei grupos vinculados ao seu perfil."

        parts = [f"**Seu perfil na Minha DELPI:**\n"]
        parts.append(f"- **Nome:** {name}")
        parts.append(f"- **Email:** {email}")
        if is_superadmin:
            parts.append("- **Perfil:** Superadministrador")
        if roles:
            parts.append(f"- **Papéis:** {', '.join(roles)}")
        if groups:
            parts.append(f"- **Grupos:** {', '.join(groups)}")
        if permissions:
            parts.append(f"- **Permissões ({len(permissions)}):** {', '.join(permissions[:15])}")
            if len(permissions) > 15:
                parts.append(f"  … e mais {len(permissions) - 15}")
        if app_names:
            parts.append(f"- **Apps disponíveis ({len(app_names)}):** {', '.join(app_names)}")

        return "\n".join(parts)
