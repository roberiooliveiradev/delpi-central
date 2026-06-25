"""Catálogo formal de perfis RBAC expostos pelo admin do chat."""

from __future__ import annotations

from app.domain.security.chat_permission_constants import (
    CHAT_ACCESS_PERMISSION,
    CHAT_ADMIN_PERMISSION,
    CHAT_HISTORY_VIEW_PERMISSION,
    CHAT_KNOWLEDGE_MANAGE_PERMISSION,
    CHAT_TOOLS_MANAGE_PERMISSION,
    CHAT_TOOLS_USE_PERMISSION,
)


class AdminRbacProfileCatalogService:
    """Perfis formais derivados das permissões atuais do chat (bridge até core-api centralizar roles)."""

    _PROFILES: tuple[dict, ...] = (
        {
            "key": "admin",
            "label": "Administrador",
            "description": "Configura diretrizes, exporta auditoria e gerencia o admin do chat.",
            "mapsFromRoles": ["admin"],
            "requiredAnyPermission": [CHAT_ADMIN_PERMISSION],
            "capabilities": [
                "guidelines.create",
                "guidelines.publish",
                "guidelines.archive",
                "audit.export",
                "tools.manage",
            ],
        },
        {
            "key": "operator",
            "label": "Operador de conhecimento",
            "description": "Mantém documentos da base e ferramentas operacionais do chat.",
            "mapsFromRoles": ["operator"],
            "requiredAnyPermission": [
                CHAT_KNOWLEDGE_MANAGE_PERMISSION,
                CHAT_TOOLS_MANAGE_PERMISSION,
            ],
            "capabilities": [
                "knowledge.delete",
                "knowledge.reindex",
                "tools.manage",
            ],
        },
        {
            "key": "auditor",
            "label": "Auditor",
            "description": "Visualiza histórico e trilhas do chat sem alterar configurações críticas.",
            "mapsFromRoles": ["auditor"],
            "requiredAnyPermission": [
                CHAT_ADMIN_PERMISSION,
                CHAT_HISTORY_VIEW_PERMISSION,
            ],
            "capabilities": [
                "audit.view",
            ],
        },
        {
            "key": "viewer",
            "label": "Usuário do chat",
            "description": "Acessa o chat e ferramentas autorizadas pela sessão.",
            "mapsFromRoles": ["viewer"],
            "requiredAnyPermission": [CHAT_ACCESS_PERMISSION],
            "capabilities": [
                "chat.access",
                "tools.use",
            ],
        },
    )

    @classmethod
    def list_profiles(cls) -> list[dict]:
        return [dict(item) for item in cls._PROFILES]

    @classmethod
    def resolve_active_profile_keys(cls, roles: list[str]) -> list[str]:
        role_set = {str(role).strip() for role in roles if str(role).strip()}
        active: list[str] = []

        for profile in cls._PROFILES:
            mapped = set(profile.get("mapsFromRoles") or [])
            if role_set.intersection(mapped):
                active.append(str(profile["key"]))

        return active

    @classmethod
    def build_matrix(cls, capabilities: dict) -> list[dict]:
        rows: list[dict] = []

        for profile in cls._PROFILES:
            profile_caps = list(profile.get("capabilities") or [])
            rows.append(
                {
                    "profileKey": profile["key"],
                    "profileLabel": profile["label"],
                    "capabilities": profile_caps,
                    "allowedCount": sum(
                        1
                        for key in profile_caps
                        if cls._capability_allowed(key, capabilities)
                    ),
                }
            )

        return rows

    @classmethod
    def build_contract(cls) -> dict:
        return {
            "source": "minha-delpi-ai-api",
            "formalProfilesInCoreApi": False,
            "note": (
                "Perfis formais centralizados no core-api permanecem backlog de plataforma; "
                "este catálogo espelha as permissões Keycloak/chat já efetivas no admin."
            ),
            "permissionKeys": sorted(
                {
                    permission
                    for profile in cls._PROFILES
                    for permission in profile.get("requiredAnyPermission") or []
                }
            ),
        }

    @classmethod
    def _capability_allowed(cls, capability_key: str, capabilities: dict) -> bool:
        mapping = {
            "guidelines.create": capabilities.get("canCreateGuidelines"),
            "guidelines.publish": capabilities.get("canPublishGuidelines"),
            "guidelines.archive": capabilities.get("canArchiveGuidelines"),
            "knowledge.delete": capabilities.get("canDeleteKnowledgeDocuments"),
            "knowledge.reindex": capabilities.get("canReindexKnowledgeDocuments"),
            "audit.view": capabilities.get("canViewAudit"),
            "audit.export": capabilities.get("canExportAudit"),
            "tools.manage": capabilities.get("canManageTools"),
            "tools.use": capabilities.get("canUseTools"),
            "chat.access": capabilities.get("canViewAdmin")
            or capabilities.get("canUseTools"),
        }

        return bool(mapping.get(capability_key))
