# app/application/event_handlers/rbac_notification_event_handler.py

from __future__ import annotations

import logging
from uuid import UUID

from app.application.services.rbac_access_delta_service import (
    AccessGain,
    RbacAccessDeltaService,
)
from app.domain.events.admin_events import AdminChangedEvent
from app.domain.notifications.notification_templates import NOTIFICATION_TEMPLATES
from app.domain.notifications.portal_routes import PORTAL_APP_LAUNCHER_ROUTE
from app.domain.ports.notification_repository import NotificationDTO

logger = logging.getLogger(__name__)

_APP_ACCESS_TEMPLATE_ID = "app_access_granted_v1"
_SYSTEM_ACCESS_TEMPLATE_ID = "system_access_granted_v1"

_ACTIONS_USER_TARGETED = frozenset({
    "group_added_to_user",
    "role_added_to_user",
})

_ACTIONS_ROLE_CHANGE = frozenset({
    "permission_added_to_role",
    "role_permissions_replaced",
})

_ACTIONS_GROUP_CHANGE = frozenset({
    "role_added_to_group",
    "group_roles_replaced",
})

_ACTIONS_USER_REPLACE = frozenset({
    "roles_replaced",
    "groups_replaced",
})

_ALL_HANDLED_ACTIONS = (
    _ACTIONS_USER_TARGETED
    | _ACTIONS_ROLE_CHANGE
    | _ACTIONS_GROUP_CHANGE
    | _ACTIONS_USER_REPLACE
)


class RbacNotificationEventHandler:
    """
    Notificações automáticas quando o usuário ganha acesso RBAC:
    - app_access_granted_v1: novas apps e/ou rotas/funcionalidades;
    - system_access_granted_v1: permissões do módulo system (administração).
    Cada tipo é enviado em notificação separada quando ambos ocorrem juntos.

    Compara o estado atual com o anterior, ignorando permissões que o usuário
    já possuía por outro papel ou grupo.
    """

    def __init__(self, uow):
        self.uow = uow
        self._delta_service = RbacAccessDeltaService(
            uow.permission_queries,
            uow.cache,
            uow.app_queries,
        )
        self._notified_users: set[str] = set()

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

    def _dispatch(self, event: AdminChangedEvent) -> None:
        if event.action in _ACTIONS_USER_TARGETED:
            if not event.target_user_id:
                return
            self._notify_user(
                UUID(event.target_user_id),
                self._previous_codes_for_user_event(event),
            )
            return

        if event.action in _ACTIONS_USER_REPLACE:
            if not event.target_user_id:
                return
            previous = self._previous_codes_for_user_replace_event(event)
            if previous is None:
                return
            self._notify_user(UUID(event.target_user_id), previous)
            return

        if event.action in _ACTIONS_ROLE_CHANGE:
            self._dispatch_role_change(event)
            return

        if event.action in _ACTIONS_GROUP_CHANGE:
            self._dispatch_group_change(event)

    def _dispatch_role_change(self, event: AdminChangedEvent) -> None:
        payload = event.payload or {}
        role_id = UUID(str(payload["roleId"]))
        added_codes = self._added_permission_codes_for_role_event(event, role_id)
        if not added_codes:
            return

        user_ids = self._get_user_ids_by_role(role_id)
        for uid in user_ids:
            previous = self._delta_service.previous_codes_after_role_permission_change(
                uid,
                False,
                role_id,
                added_codes,
            )
            self._notify_user(uid, previous)

    def _dispatch_group_change(self, event: AdminChangedEvent) -> None:
        payload = event.payload or {}
        group_id = UUID(str(payload["groupId"]))

        if event.action == "role_added_to_group":
            added_role_ids = {UUID(str(payload["roleId"]))}
        else:
            raw = payload.get("addedRoleIds") or []
            added_role_ids = {UUID(str(item)) for item in raw}
            if not added_role_ids:
                return

        user_ids = self._get_user_ids_by_group(group_id)
        for uid in user_ids:
            previous = self._delta_service.previous_codes_excluding_group_roles(
                uid,
                False,
                group_id,
                added_role_ids,
            )
            self._notify_user(uid, previous)

    def _notify_user(self, user_id: UUID, previous_codes: list[str]) -> None:
        user_id_str = str(user_id)
        if user_id_str in self._notified_users:
            return

        user = self.uow.users.get_by_id(user_id)
        if not user or not user.active:
            return

        if bool(user.is_superadmin):
            return

        gain = self._delta_service.compute_gain(
            user_id,
            False,
            previous_codes=previous_codes,
        )
        if not gain.has_gain:
            return

        self._notified_users.add(user_id_str)
        self._send_notifications(user, gain)

    def _send_notifications(self, user, gain: AccessGain) -> None:
        first_name = (user.name or "").split()[0] if user.name else ""
        app_names, feature_labels, navigable_apps = self._collect_app_context(gain)
        system_names = [item.name for item in gain.new_system_permissions]

        has_app_gain = bool(
            app_names or feature_labels or gain.new_apps or gain.new_routes
        )
        has_system_gain = bool(system_names)

        if has_app_gain:
            self._send_app_access_notification(
                user,
                first_name=first_name,
                app_names=app_names,
                feature_labels=feature_labels,
                navigable_apps=navigable_apps,
            )

        if has_system_gain:
            self._send_system_access_notification(
                user,
                first_name=first_name,
                system_names=system_names,
            )

    def _collect_app_context(
        self, gain: AccessGain
    ) -> tuple[list[str], list[str], list]:
        new_app_ids = {app.id for app in gain.new_apps}
        app_names: list[str] = []
        seen_app_ids: set[str] = set()

        for app in gain.new_apps:
            if app.id in seen_app_ids:
                continue
            seen_app_ids.add(app.id)
            app_names.append(app.name)

        for app, _route in gain.new_routes:
            if app.id in new_app_ids or app.id in seen_app_ids:
                continue
            seen_app_ids.add(app.id)
            app_names.append(app.name)

        feature_labels: list[str] = []
        seen_features: set[str] = set()
        app_name_set = {name.casefold() for name in app_names}

        for app, route in gain.new_routes:
            if app.id in new_app_ids:
                continue

            text = self._format_feature_label(app, route)
            if not text:
                continue
            if text.casefold() in app_name_set:
                continue
            if text in seen_features:
                continue
            seen_features.add(text)
            feature_labels.append(text)

        if gain.new_apps:
            navigable_apps = gain.new_apps
        else:
            seen_nav: dict[str, object] = {}
            for app, _route in gain.new_routes:
                seen_nav[app.id] = app
            navigable_apps = list(seen_nav.values())

        return app_names, feature_labels, navigable_apps

    def _send_app_access_notification(
        self,
        user,
        *,
        first_name: str,
        app_names: list[str],
        feature_labels: list[str],
        navigable_apps: list,
    ) -> None:
        template_spec = NOTIFICATION_TEMPLATES[_APP_ACCESS_TEMPLATE_ID]
        app_names_str = ", ".join(app_names) if app_names else ""
        feature_names_str = ", ".join(feature_labels) if feature_labels else ""

        message = self._build_app_access_message(
            first_name,
            app_names_str=app_names_str,
            feature_names_str=feature_names_str,
        )

        if len(app_names) > 1 or len(navigable_apps) > 1:
            action_target = PORTAL_APP_LAUNCHER_ROUTE
            action_label = "Ver aplicativos"
        elif len(navigable_apps) == 1:
            action_target = navigable_apps[0].base_path or "/"
            action_label = f"Abrir {navigable_apps[0].name}"
        else:
            action_target = PORTAL_APP_LAUNCHER_ROUTE
            action_label = "Ver aplicativos"

        self._persist_notification(
            user,
            template_spec=template_spec,
            template_id=_APP_ACCESS_TEMPLATE_ID,
            title=template_spec.default_title,
            message=message,
            action_label=action_label,
            action_target=action_target,
            vars={
                "userName": first_name,
                "appNames": app_names_str,
                "featureNames": feature_names_str,
            },
        )

    def _send_system_access_notification(
        self,
        user,
        *,
        first_name: str,
        system_names: list[str],
    ) -> None:
        template_spec = NOTIFICATION_TEMPLATES[_SYSTEM_ACCESS_TEMPLATE_ID]
        system_names_str = ", ".join(system_names)

        message = template_spec.default_message.format(
            userName=first_name,
            systemPermissionNames=system_names_str,
        )

        self._persist_notification(
            user,
            template_spec=template_spec,
            template_id=_SYSTEM_ACCESS_TEMPLATE_ID,
            title=template_spec.default_title,
            message=message,
            action_label="Abrir administração",
            action_target="/admin",
            vars={
                "userName": first_name,
                "systemPermissionNames": system_names_str,
            },
        )

    def _persist_notification(
        self,
        user,
        *,
        template_spec,
        template_id: str,
        title: str,
        message: str,
        action_label: str,
        action_target: str,
        vars: dict[str, str],
    ) -> None:
        notification_id = self.uow.notifications.create(
            NotificationDTO(
                user_id=str(user.id),
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
                    "templateId": template_id,
                    "vars": vars,
                },
                expires_at=None,
                read=False,
            )
        )

        self.uow.collect_event(
            AdminChangedEvent(
                entity="notifications",
                action="notification_created",
                payload={
                    "notificationId": str(notification_id),
                    "category": template_spec.category,
                },
                target_user_id=str(user.id),
            )
        )

    def _previous_codes_for_user_event(self, event: AdminChangedEvent) -> list[str]:
        payload = event.payload or {}
        user_id = UUID(event.target_user_id)

        if event.action == "group_added_to_user":
            group_id = UUID(str(payload["groupId"]))
            return self._delta_service.previous_codes_excluding_groups(
                user_id, False, {group_id}
            )

        if event.action == "role_added_to_user":
            role_id = UUID(str(payload["roleId"]))
            return self._delta_service.previous_codes_excluding_user_roles(
                user_id, False, {role_id}
            )

        return []

    def _previous_codes_for_user_replace_event(
        self, event: AdminChangedEvent
    ) -> list[str] | None:
        payload = event.payload or {}
        user_id = UUID(event.target_user_id)

        if event.action == "roles_replaced":
            raw = payload.get("addedRoleIds") or []
            if not raw:
                return None
            snapshot = payload.get("previousPermissionCodes")
            if isinstance(snapshot, list):
                return [str(code) for code in snapshot if code]
            exclude = {UUID(str(item)) for item in raw}
            return self._delta_service.previous_codes_excluding_user_roles(
                user_id, False, exclude
            )

        if event.action == "groups_replaced":
            raw = payload.get("addedGroupIds") or []
            if not raw:
                return None
            snapshot = payload.get("previousPermissionCodes")
            if isinstance(snapshot, list):
                return [str(code) for code in snapshot if code]
            exclude = {UUID(str(item)) for item in raw}
            return self._delta_service.previous_codes_excluding_groups(
                user_id, False, exclude
            )

        return None

    def _added_permission_codes_for_role_event(
        self, event: AdminChangedEvent, role_id: UUID
    ) -> set[str]:
        payload = event.payload or {}

        if event.action == "permission_added_to_role":
            code = (payload.get("permissionCode") or "").strip()
            return {code} if code else set()

        raw_ids = payload.get("addedPermissionIds") or []
        if not raw_ids:
            return set()

        perms = self.uow.permission_queries.list_permissions_by_role_id(role_id)
        id_to_code = {str(p.id): p.code for p in perms}

        codes: set[str] = set()
        for raw in raw_ids:
            code = id_to_code.get(str(raw))
            if code:
                codes.add(code)
        return codes

    def _get_user_ids_by_role(self, role_id: UUID) -> list[UUID]:
        direct = set(self.uow.rbac_queries.list_user_ids_by_role(role_id))
        via_group = set(self.uow.rbac_queries.list_user_ids_by_group_role(role_id))
        return [UUID(uid) for uid in (direct | via_group)]

    def _get_user_ids_by_group(self, group_id: UUID) -> list[UUID]:
        ids = self.uow.rbac_queries.list_user_ids_by_group(group_id)
        return [UUID(uid) for uid in ids]

    @staticmethod
    def _build_app_access_message(
        first_name: str,
        *,
        app_names_str: str,
        feature_names_str: str,
    ) -> str:
        if app_names_str:
            message = f"Olá, {first_name}! Você recebeu acesso a: {app_names_str}."
            if feature_names_str:
                message = f"{message} Novas funcionalidades: {feature_names_str}."
            return message

        if feature_names_str:
            return (
                f"Olá, {first_name}! Você recebeu novas funcionalidades: "
                f"{feature_names_str}."
            )

        return f"Olá, {first_name}! Você recebeu novos aplicativos na plataforma."

    @staticmethod
    def _format_feature_label(app, route) -> str | None:
        label = (route.label or "").strip()
        path = (route.path or "").strip()

        if not label and not path:
            return None

        generic = frozenset(
            {"abrir", "início", "inicio", "home", "ver", "acessar", "open", "start"}
        )
        if label and label.casefold() in generic:
            label = ""

        if label and label.casefold() != (app.name or "").casefold():
            return f"{app.name}: {label}"

        if path and path != "/":
            return f"{app.name}: {path}"

        return None
