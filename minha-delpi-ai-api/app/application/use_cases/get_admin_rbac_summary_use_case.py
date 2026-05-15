from app.application.security.chat_permissions import (
    CHAT_ACCESS_PERMISSION,
    CHAT_ADMIN_PERMISSION,
    CHAT_HISTORY_VIEW_PERMISSION,
    CHAT_KNOWLEDGE_MANAGE_PERMISSION,
    CHAT_TOOLS_MANAGE_PERMISSION,
    CHAT_TOOLS_USE_PERMISSION,
)


class GetAdminRbacSummaryUseCase:
    def execute(self, user, core_user: dict | None = None) -> dict:
        if core_user:
            permissions = set(core_user.get("permissions") or [])
            is_superadmin = bool(core_user.get("is_superadmin"))
        else:
            permissions = set(getattr(user, "permissions", []) or [])
            is_superadmin = bool(getattr(user, "is_superadmin", False))

        roles = self._roles_for(permissions=permissions, is_superadmin=is_superadmin)
        capabilities = self._capabilities_for(
            permissions=permissions,
            is_superadmin=is_superadmin,
        )

        return {
            "userId": getattr(user, "sub", None) or (core_user or {}).get("id"),
            "isSuperadmin": is_superadmin,
            "roles": roles,
            "permissions": sorted(permissions),
            "capabilities": capabilities,
            "matrix": self._matrix(capabilities),
        }

    def _roles_for(self, *, permissions: set[str], is_superadmin: bool) -> list[str]:
        roles = []

        if is_superadmin or CHAT_ADMIN_PERMISSION in permissions:
            roles.append("admin")

        if (
            is_superadmin
            or CHAT_KNOWLEDGE_MANAGE_PERMISSION in permissions
            or CHAT_TOOLS_MANAGE_PERMISSION in permissions
        ):
            roles.append("operator")

        if (
            is_superadmin
            or CHAT_ADMIN_PERMISSION in permissions
            or CHAT_HISTORY_VIEW_PERMISSION in permissions
        ):
            roles.append("auditor")

        if is_superadmin or CHAT_ACCESS_PERMISSION in permissions:
            roles.append("viewer")

        return roles

    def _capabilities_for(self, *, permissions: set[str], is_superadmin: bool) -> dict:
        can_admin = is_superadmin or CHAT_ADMIN_PERMISSION in permissions
        can_manage_knowledge = (
            can_admin or CHAT_KNOWLEDGE_MANAGE_PERMISSION in permissions
        )
        can_manage_tools = can_admin or CHAT_TOOLS_MANAGE_PERMISSION in permissions
        can_use_tools = can_manage_tools or CHAT_TOOLS_USE_PERMISSION in permissions
        can_view_audit = can_admin or CHAT_HISTORY_VIEW_PERMISSION in permissions

        return {
            "canCreateGuidelines": can_admin,
            "canPublishGuidelines": can_admin,
            "canArchiveGuidelines": can_admin,
            "canDeleteKnowledgeDocuments": can_manage_knowledge,
            "canReindexKnowledgeDocuments": can_manage_knowledge,
            "canViewAudit": can_view_audit,
            "canExportAudit": can_admin,
            "canManageTools": can_manage_tools,
            "canUseTools": can_use_tools,
            "canViewAdmin": can_admin or can_manage_knowledge or can_manage_tools or can_view_audit,
        }

    def _matrix(self, capabilities: dict) -> list[dict]:
        return [
            {
                "key": "guidelines.create",
                "label": "Criar diretrizes",
                "allowed": capabilities["canCreateGuidelines"],
                "requiredPermission": CHAT_ADMIN_PERMISSION,
            },
            {
                "key": "guidelines.publish",
                "label": "Publicar diretrizes",
                "allowed": capabilities["canPublishGuidelines"],
                "requiredPermission": CHAT_ADMIN_PERMISSION,
            },
            {
                "key": "guidelines.archive",
                "label": "Arquivar diretrizes",
                "allowed": capabilities["canArchiveGuidelines"],
                "requiredPermission": CHAT_ADMIN_PERMISSION,
            },
            {
                "key": "knowledge.delete",
                "label": "Excluir documentos",
                "allowed": capabilities["canDeleteKnowledgeDocuments"],
                "requiredPermission": CHAT_KNOWLEDGE_MANAGE_PERMISSION,
            },
            {
                "key": "knowledge.reindex",
                "label": "Reindexar documentos",
                "allowed": capabilities["canReindexKnowledgeDocuments"],
                "requiredPermission": CHAT_KNOWLEDGE_MANAGE_PERMISSION,
            },
            {
                "key": "audit.view",
                "label": "Visualizar auditoria",
                "allowed": capabilities["canViewAudit"],
                "requiredPermission": CHAT_HISTORY_VIEW_PERMISSION,
            },
            {
                "key": "audit.export",
                "label": "Exportar auditoria",
                "allowed": capabilities["canExportAudit"],
                "requiredPermission": CHAT_ADMIN_PERMISSION,
            },
            {
                "key": "tools.manage",
                "label": "Gerenciar ferramentas",
                "allowed": capabilities["canManageTools"],
                "requiredPermission": CHAT_TOOLS_MANAGE_PERMISSION,
            },
        ]
