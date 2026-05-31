import logging
import re
from urllib.parse import urljoin

from app.domain.ports.core_api_gateway_port import CoreApiGatewayPort
from app.infrastructure.config.settings import Settings

logger = logging.getLogger("minha-delpi-ai-api.user_context")

_PII_FIELDS = ("name", "email")

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
    "permissões de",
    "permissões do",
    "permissões da",
    "permissao de",
    "permissao do",
    "permissao da",
    "funcionalidades de",
    "funcionalidades do",
    "funcionalidades da",
    "apps do papel",
    "apps da role",
    "apps do role",
    "o que entrega",
    "o que o papel",
    "o que a role",
    "o papel ",
    " a role ",
)


class ChatUserContextService:
    """Constrói bloco textual com informações do usuário para injeção no prompt."""

    def __init__(self, core_api_gateway: CoreApiGatewayPort):
        self.core_api_gateway = core_api_gateway

    @classmethod
    def is_user_identity_question(cls, message: str) -> bool:
        normalized = str(message or "").lower()
        return any(term in normalized for term in _USER_IDENTITY_TERMS)

    @staticmethod
    def _strip_pii(me: dict) -> dict:
        """Remove campos de PII (nome, email) do dict do usuário."""
        sanitized = dict(me)
        for field in _PII_FIELDS:
            sanitized.pop(field, None)
        return sanitized

    @classmethod
    def _core_api_url(cls, path: str) -> str:
        base = Settings.CORE_API_BASE_URL.rstrip("/") + "/"
        return urljoin(base, path.lstrip("/"))

    @classmethod
    def _has_ai_context_consent(cls, access_token: str) -> bool:
        """Verifica consentimento ``ai_context`` via core-api."""
        import requests

        try:
            resp = requests.get(
                cls._core_api_url("me/consents"),
                headers={"Authorization": f"Bearer {access_token}"},
                timeout=Settings.CORE_API_TIMEOUT_SECONDS,
            )
            if resp.status_code != 200:
                return False
            data = resp.json()
            items = data.get("items") if isinstance(data, dict) else data
            if isinstance(items, list):
                return any(
                    c.get("purpose") == "ai_context" and c.get("granted")
                    for c in items
                )
        except Exception:
            logger.debug("lgpd_consent_check_failed", exc_info=True)
        return False

    def _should_strip_pii(self, access_token: str) -> bool:
        if not getattr(Settings, "LGPD_REQUIRE_AI_CONSENT", False):
            return False
        return not self._has_ai_context_consent(access_token)

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

        if self._should_strip_pii(access_token):
            me = self._strip_pii(me)

        access_profile = self._fetch_access_profile(access_token)
        apps = self._apps_from_profile(access_profile) or self._fetch_apps(access_token)

        return self._format_context(me, apps, access_profile)

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

        # Resposta exibida ao próprio usuário: não remover PII (LGPD aplica só ao prompt LLM).
        access_profile = self._fetch_access_profile(access_token)
        apps = self._apps_from_profile(access_profile) or self._fetch_apps(access_token)
        return self._format_direct_answer(me, apps, message, access_profile)

    def _fetch_access_profile(self, access_token: str) -> dict | None:
        try:
            profile = self.core_api_gateway.get_access_profile(access_token)
        except Exception:
            logger.debug("user_context_access_profile_failed", exc_info=True)
            return None

        if not profile or profile.get("authorized") is False:
            return None

        return profile

    @staticmethod
    def _apps_from_profile(access_profile: dict | None) -> list[dict]:
        if not access_profile:
            return []

        apps = access_profile.get("effectiveApps")
        return apps if isinstance(apps, list) else []

    def _fetch_apps(self, access_token: str) -> list[dict]:
        try:
            return self.core_api_gateway.get_apps(access_token)
        except Exception:
            logger.debug("user_context_apps_fetch_failed", exc_info=True)
            return []

    def _format_context(
        self,
        me: dict,
        apps: list[dict],
        access_profile: dict | None = None,
    ) -> str:
        parts = [
            "[Dados do usuário que está conversando com você]",
            "REGRA: quando o usuário perguntar sobre si mesmo (quem sou, meus papéis, "
            "permissões de um papel, apps, funcionalidades, meu perfil, sobre mim, etc.), "
            "responda com os dados abaixo. Para um papel específico, use permissões e apps "
            "daquele papel — não misture com outros papéis.",
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

        profile_roles = (access_profile or {}).get("roles") or []
        if profile_roles:
            parts.append(self._format_roles_context(profile_roles))
        else:
            roles = me.get("roles") or []
            if roles:
                parts.append(f"Papéis do usuário: {', '.join(roles)}")

        groups = (access_profile or {}).get("groups") or me.get("groups") or []
        if groups:
            if isinstance(groups[0], dict):
                group_names = [g.get("name") for g in groups if g.get("name")]
            else:
                group_names = [str(g) for g in groups]
            if group_names:
                parts.append(f"Grupos do usuário: {', '.join(group_names)}")

        permissions = (access_profile or {}).get("effectivePermissions") or me.get(
            "permissions"
        ) or []
        if permissions:
            perm_display = permissions[:30]
            line = f"Permissões efetivas do usuário ({len(permissions)}): {', '.join(perm_display)}"
            if len(permissions) > 30:
                line += f" … e mais {len(permissions) - 30}"
            parts.append(line)

        if apps:
            parts.append(self._format_apps_context(apps, heading="Apps liberados ao usuário"))

        if len(parts) <= 2:
            return ""

        return "\n".join(parts)

    def _format_direct_answer(
        self,
        me: dict,
        apps: list[dict],
        message: str,
        access_profile: dict | None = None,
    ) -> str:
        """Formata resposta direta legível sem necessidade de LLM."""
        normalized = str(message or "").lower()
        name = me.get("name") or "Não informado"
        email = me.get("email") or "Não informado"
        roles = me.get("roles") or []
        groups = me.get("groups") or []
        permissions = me.get("permissions") or []
        is_superadmin = me.get("is_superadmin", False)

        profile_roles = (access_profile or {}).get("roles") or []
        matched_role = self._find_role_in_message(message, profile_roles)
        if matched_role and any(
            token in normalized
            for token in (
                "permiss",
                "funcional",
                "apps",
                "app ",
                "acesso",
                "entrega",
                "o que o papel",
                "o que a role",
            )
        ):
            return self._format_role_detail_answer(matched_role)

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
            if profile_roles:
                lines = [f"Seus papéis ({len(profile_roles)}):"]
                for role in profile_roles:
                    name = role.get("name") or "Papel"
                    sources = self._format_role_sources(role)
                    suffix = f" ({sources})" if sources else ""
                    perm_count = len(role.get("permissions") or [])
                    app_count = len(role.get("apps") or [])
                    lines.append(
                        f"- **{name}**{suffix} — {perm_count} permissão(ões), "
                        f"{app_count} app(s) com rotas"
                    )
                lines.append(
                    "\nPara detalhes de um papel, pergunte por exemplo: "
                    "\"quais as permissões de Chat Full?\""
                )
                return "\n".join(lines)
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

    @staticmethod
    def _normalize_match_text(value: str) -> str:
        return re.sub(r"[^a-z0-9]+", "", str(value or "").lower())

    @classmethod
    def _find_role_in_message(cls, message: str, roles: list[dict]) -> dict | None:
        normalized_message = cls._normalize_match_text(message)
        if not normalized_message or not roles:
            return None

        best_match: dict | None = None
        best_score = 0

        for role in roles:
            role_name = str(role.get("name") or "")
            normalized_role = cls._normalize_match_text(role_name)
            if not normalized_role:
                continue

            if normalized_role in normalized_message:
                score = len(normalized_role)
                if score > best_score:
                    best_match = role
                    best_score = score

        return best_match

    @staticmethod
    def _format_role_sources(role: dict) -> str:
        labels: list[str] = []
        for source in role.get("sources") or []:
            if source.get("type") == "direct":
                labels.append("atribuição direta")
            elif source.get("type") == "group" and source.get("groupName"):
                labels.append(f"grupo {source['groupName']}")
        return ", ".join(labels)

    @classmethod
    def _format_roles_context(cls, roles: list[dict]) -> str:
        lines = ["Papéis do usuário (detalhados):"]
        for role in roles:
            name = role.get("name") or "Papel"
            sources = cls._format_role_sources(role)
            lines.append(f"- {name}" + (f" [{sources}]" if sources else ""))
            if role.get("description"):
                lines.append(f"  Descrição: {role['description']}")
            permissions = role.get("permissions") or []
            if permissions:
                perm_codes = [p.get("code") for p in permissions if p.get("code")]
                preview = ", ".join(perm_codes[:12])
                if len(perm_codes) > 12:
                    preview += f" … +{len(perm_codes) - 12}"
                lines.append(f"  Permissões ({len(perm_codes)}): {preview}")
            apps = role.get("apps") or []
            if apps:
                app_names = [a.get("name") for a in apps if a.get("name")]
                lines.append(
                    f"  Apps/funcionalidades: {', '.join(app_names[:8])}"
                    + (f" … +{len(app_names) - 8}" if len(app_names) > 8 else "")
                )
        return "\n".join(lines)

    @staticmethod
    def _format_apps_context(apps: list[dict], *, heading: str) -> str:
        lines = [f"{heading} ({len(apps)}):"]
        for app in apps[:12]:
            app_name = app.get("name") or app.get("id") or "App"
            routes = app.get("routes") or []
            route_labels = [
                r.get("label") or r.get("path")
                for r in routes
                if r.get("label") or r.get("path")
            ]
            if route_labels:
                preview = ", ".join(route_labels[:6])
                if len(route_labels) > 6:
                    preview += f" … +{len(route_labels) - 6}"
                lines.append(f"- {app_name}: {preview}")
            else:
                lines.append(f"- {app_name}")
        if len(apps) > 12:
            lines.append(f"… e mais {len(apps) - 12} app(s)")
        return "\n".join(lines)

    @classmethod
    def _format_role_detail_answer(cls, role: dict) -> str:
        name = role.get("name") or "Papel"
        lines = [f"**Papel: {name}**"]

        if role.get("description"):
            lines.append(str(role["description"]))

        sources = cls._format_role_sources(role)
        if sources:
            lines.append(f"**Como você recebe este papel:** {sources}")

        permissions = role.get("permissions") or []
        lines.append(f"\n**Permissões ({len(permissions)}):**")
        if permissions:
            for perm in permissions[:40]:
                code = perm.get("code") or ""
                label = perm.get("name") or code
                description = (perm.get("description") or "").strip()
                module = perm.get("module")
                detail = description if description and description != label else label
                module_suffix = f" [{module}]" if module else ""
                lines.append(f"- `{code}` — {detail}{module_suffix}")
            if len(permissions) > 40:
                lines.append(f"- … e mais {len(permissions) - 40} permissão(ões)")
        else:
            lines.append("- Nenhuma permissão cadastrada para este papel.")

        apps = role.get("apps") or []
        lines.append(f"\n**Apps e funcionalidades ({len(apps)}):**")
        if apps:
            for app in apps[:10]:
                app_name = app.get("name") or app.get("id") or "App"
                routes = app.get("routes") or []
                lines.append(f"- **{app_name}**")
                for route in routes[:8]:
                    label = route.get("label") or route.get("path") or "Rota"
                    permission = route.get("permission")
                    if permission:
                        lines.append(f"  - {label} (`{permission}`)")
                    else:
                        lines.append(f"  - {label}")
                if len(routes) > 8:
                    lines.append(f"  - … e mais {len(routes) - 8} rota(s)")
            if len(apps) > 10:
                lines.append(f"- … e mais {len(apps) - 10} app(s)")
        else:
            lines.append(
                "- Nenhum app com rotas liberadas apenas por este papel "
                "(pode depender de combinação com outros papéis)."
            )

        return "\n".join(lines)
