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

_ACTIONS_WITH_TARGET_USER = frozenset({
    "group_added_to_user",
    "role_added_to_user",
    "groups_replaced",
    "roles_replaced",
})


class RbacNotificationEventHandler:
    """
    Dispara notificação automática quando um usuário ganha acesso a novas
    aplicações via adição de grupo ou papel.
    """

    def __init__(self, uow):
        self.uow = uow

    def handle(self, event: AdminChangedEvent) -> None:
        if event.entity != "rbac":
            return
        if event.action not in _ACTIONS_WITH_TARGET_USER:
            return
        if not event.target_user_id:
            return

        try:
            self._process(event)
        except Exception:
            logger.exception(
                "Falha ao disparar notificação de acesso para user=%s action=%s",
                event.target_user_id,
                event.action,
            )

    def _process(self, event: AdminChangedEvent) -> None:
        user_id = UUID(event.target_user_id)
        user = self.uow.users.get_by_id(user_id)
        if not user or not user.active:
            return

        new_app_names = self._resolve_new_app_names(event, user_id, bool(user.is_superadmin))
        if not new_app_names:
            return

        template_spec = NOTIFICATION_TEMPLATES[_TEMPLATE_ID]
        app_names_str = ", ".join(new_app_names)

        first_name = (user.name or "").split()[0] if user.name else ""

        title = template_spec.default_title
        message = template_spec.default_message.replace(
            "{userName}", first_name
        ).replace("{appNames}", app_names_str)

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
                action_label="Ver aplicativos",
                action_target="/apps",
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

    def _resolve_new_app_names(
        self,
        event: AdminChangedEvent,
        user_id: UUID,
        is_superadmin: bool,
    ) -> list[str]:
        """
        Identifica as apps que o grupo/papel adicionado concede acesso.
        Para ações de 'replace', resolve as permissões completas atuais.
        """
        apps = self.uow.app_queries.list_active_apps_with_routes()
        if not apps:
            return []

        permission_codes = self._get_granted_permission_codes(event, user_id)
        if not permission_codes:
            return []

        auth_service = AppAuthorizationService()
        authorized = auth_service.filter_apps(apps, permission_codes, is_superadmin)
        return [app.name for app in authorized]

    def _get_granted_permission_codes(
        self,
        event: AdminChangedEvent,
        user_id: UUID,
    ) -> list[str]:
        """
        Retorna os permission_codes concedidos pela mudança RBAC específica.
        - group_added_to_user: permissões das roles do grupo
        - role_added_to_user: permissões da role
        - groups_replaced / roles_replaced: todas as permissões atuais do usuário
        """
        payload = event.payload or {}

        if event.action == "group_added_to_user":
            group_id = UUID(payload["groupId"])
            role_ids = self.uow.group_roles.list_role_ids(group_id)
            codes: set[str] = set()
            for role_id in role_ids:
                perms = self.uow.permission_queries.list_permissions_by_role_id(role_id)
                codes.update(p.code for p in perms)
            return list(codes)

        if event.action == "role_added_to_user":
            role_id = UUID(payload["roleId"])
            perms = self.uow.permission_queries.list_permissions_by_role_id(role_id)
            return [p.code for p in perms]

        # groups_replaced / roles_replaced: permissões completas atuais
        resolver = PermissionResolver(self.uow.permission_queries, self.uow.cache)
        return resolver.resolve(user_id, False)
