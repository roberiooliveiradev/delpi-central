# app/application/event_handlers/rbac_notification_event_handler.py

from __future__ import annotations

import logging
from uuid import UUID

from app.application.services.app_authorization_service import AppAuthorizationService
from app.domain.events.admin_events import AdminChangedEvent
from app.domain.notifications.notification_templates import NOTIFICATION_TEMPLATES
from app.domain.ports.notification_repository import NotificationDTO
from app.domain.services.permission_resolver import PermissionResolver

logger = logging.getLogger(__name__)

_TEMPLATE_ID = "app_access_granted_v1"

_ACTIONS_USER_TARGETED = frozenset({
    "group_added_to_user",
    "role_added_to_user",
    "groups_replaced",
    "roles_replaced",
})

_ACTIONS_ROLE_CHANGE = frozenset({
    "permission_added_to_role",
    "role_permissions_replaced",
})

_ACTIONS_GROUP_CHANGE = frozenset({
    "role_added_to_group",
    "group_roles_replaced",
})

_ALL_HANDLED_ACTIONS = _ACTIONS_USER_TARGETED | _ACTIONS_ROLE_CHANGE | _ACTIONS_GROUP_CHANGE


class RbacNotificationEventHandler:
    """
    Dispara notificação automática quando um usuário ganha acesso a novas
    aplicações via:
    - Adição de grupo ou papel ao usuário
    - Adição de permissão a um papel (afeta todos os usuários com o papel)
    - Adição de papel a um grupo (afeta todos os usuários do grupo)
    """

    def __init__(self, uow):
        self.uow = uow

    def handle(self, event: AdminChangedEvent) -> None:
        if event.entity != "rbac":
            return
        if event.action not in _ALL_HANDLED_ACTIONS:
            return

        try:
            self._dispatch(event)
        except Exception:
            logger.exception(
                "Falha ao disparar notificação de acesso: action=%s payload=%s",
                event.action,
                event.payload,
            )

    # ------------------------------------------------------------------
    # Dispatch por tipo de evento
    # ------------------------------------------------------------------

    def _dispatch(self, event: AdminChangedEvent) -> None:
        if event.action in _ACTIONS_USER_TARGETED:
            if not event.target_user_id:
                return
            self._notify_user(
                user_id=UUID(event.target_user_id),
                permission_codes=self._codes_for_user_event(event),
            )

        elif event.action in _ACTIONS_ROLE_CHANGE:
            role_id = UUID(event.payload["roleId"])
            user_ids = self._get_user_ids_by_role(role_id)
            perm_codes = self._codes_for_role(role_id)
            for uid in user_ids:
                self._notify_user(user_id=uid, permission_codes=perm_codes)

        elif event.action in _ACTIONS_GROUP_CHANGE:
            group_id = UUID(event.payload["groupId"])
            user_ids = self._get_user_ids_by_group(group_id)
            perm_codes = self._codes_for_group(group_id)
            for uid in user_ids:
                self._notify_user(user_id=uid, permission_codes=perm_codes)

    # ------------------------------------------------------------------
    # Notificação individual
    # ------------------------------------------------------------------

    def _notify_user(self, user_id: UUID, permission_codes: list[str]) -> None:
        if not permission_codes:
            return

        user = self.uow.users.get_by_id(user_id)
        if not user or not user.active:
            return

        granted_apps = self._resolve_granted_apps(permission_codes, bool(user.is_superadmin))
        if not granted_apps:
            return

        template_spec = NOTIFICATION_TEMPLATES[_TEMPLATE_ID]
        app_names_str = ", ".join(app.name for app in granted_apps)
        first_name = (user.name or "").split()[0] if user.name else ""

        title = template_spec.default_title
        message = template_spec.default_message.replace(
            "{userName}", first_name
        ).replace("{appNames}", app_names_str)

        if len(granted_apps) == 1:
            action_target = granted_apps[0].base_path or "/"
            action_label = f"Abrir {granted_apps[0].name}"
        else:
            action_target = "/"
            action_label = "Ver aplicativos"

        self.uow.notifications.create(
            NotificationDTO(
                user_id=str(user_id),
                title=title,
                message=message,
                type=template_spec.default_type,
                category=template_spec.category,
                presentation="template",
                html_content=None,
                action_type="portal_route",
                action_label=action_label,
                action_target=action_target,
                icon="key-round",
                metadata={
                    "templateId": _TEMPLATE_ID,
                    "vars": {
                        "userName": first_name,
                        "appNames": app_names_str,
                    },
                },
                expires_at=None,
                read=False,
            )
        )

    # ------------------------------------------------------------------
    # Resolução de apps a partir de permission codes
    # ------------------------------------------------------------------

    def _resolve_granted_apps(self, permission_codes: list[str], is_superadmin: bool):
        apps = self.uow.app_queries.list_active_apps_with_routes()
        if not apps:
            return []

        auth_service = AppAuthorizationService()
        return auth_service.filter_apps(apps, permission_codes, is_superadmin)

    # ------------------------------------------------------------------
    # Resolução de permission_codes por tipo de evento
    # ------------------------------------------------------------------

    def _codes_for_user_event(self, event: AdminChangedEvent) -> list[str]:
        payload = event.payload or {}
        user_id = UUID(event.target_user_id)

        if event.action == "group_added_to_user":
            return self._codes_for_group(UUID(payload["groupId"]))

        if event.action == "role_added_to_user":
            return self._codes_for_role(UUID(payload["roleId"]))

        # groups_replaced / roles_replaced: permissões completas atuais
        resolver = PermissionResolver(self.uow.permission_queries, self.uow.cache)
        return resolver.resolve(user_id, False)

    def _codes_for_role(self, role_id: UUID) -> list[str]:
        perms = self.uow.permission_queries.list_permissions_by_role_id(role_id)
        return [p.code for p in perms]

    def _codes_for_group(self, group_id: UUID) -> list[str]:
        role_ids = self.uow.group_roles.list_role_ids(group_id)
        codes: set[str] = set()
        for role_id in role_ids:
            perms = self.uow.permission_queries.list_permissions_by_role_id(role_id)
            codes.update(p.code for p in perms)
        return list(codes)

    # ------------------------------------------------------------------
    # Resolução de usuários afetados
    # ------------------------------------------------------------------

    def _get_user_ids_by_role(self, role_id: UUID) -> list[UUID]:
        """Usuários com a role direta + via grupos."""
        direct = set(self.uow.rbac_queries.list_user_ids_by_role(role_id))
        via_group = set(self.uow.rbac_queries.list_user_ids_by_group_role(role_id))
        return [UUID(uid) for uid in (direct | via_group)]

    def _get_user_ids_by_group(self, group_id: UUID) -> list[UUID]:
        """Usuários membros do grupo."""
        ids = self.uow.rbac_queries.list_user_ids_by_group(group_id)
        return [UUID(uid) for uid in ids]
