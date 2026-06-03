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
from app.domain.ports.notification_repository import NotificationDTO

logger = logging.getLogger(__name__)

_TEMPLATE_ID = "app_access_granted_v1"

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
    Notificação automática (app_access_granted_v1) quando o usuário ganha:
    - acesso a novas aplicações, e/ou
    - novas rotas/funcionalidades (permissões de rota ainda não acessíveis).

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
        self._send_notification(user, gain)

    def _send_notification(self, user, gain: AccessGain) -> None:
        template_spec = NOTIFICATION_TEMPLATES[_TEMPLATE_ID]
        first_name = (user.name or "").split()[0] if user.name else ""
        new_app_ids = {app.id for app in gain.new_apps}

        app_names: list[str] = []
        seen_app_ids: set[str] = set()

        for app in gain.new_apps:
            if app.id in seen_app_ids:
                continue
            seen_app_ids.add(app.id)
            app_names.append(app.name)

        # Apps só com rotas novas (já tinha o app) entram na lista textual
        for app, _route in gain.new_routes:
            if app.id in new_app_ids or app.id in seen_app_ids:
                continue
            seen_app_ids.add(app.id)
            app_names.append(app.name)

        feature_labels: list[str] = []
        seen_features: set[str] = set()
        app_name_set = {name.casefold() for name in app_names}

        for app, route in gain.new_routes:
            # App inteiro novo: não listar rotas (evita duplicar o nome no corpo)
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

        system_names = [item.name for item in gain.new_system_permissions]
        system_names_str = ", ".join(system_names) if system_names else ""

        app_names_str = ", ".join(app_names) if app_names else ""
        feature_names_str = ", ".join(feature_labels) if feature_labels else ""

        title = template_spec.default_title
        if system_names_str and not app_names_str and not feature_names_str:
            title = "Novas permissões de administração"

        message = self._build_access_message(
            first_name,
            app_names_str=app_names_str,
            system_names_str=system_names_str,
            feature_names_str=feature_names_str,
        )

        if gain.new_apps:
            navigable_apps = gain.new_apps
        else:
            seen_nav: dict[str, object] = {}
            for app, _route in gain.new_routes:
                seen_nav[app.id] = app
            navigable_apps = list(seen_nav.values())

        if system_names_str and not navigable_apps:
            action_target = "/admin"
            action_label = "Abrir administração"
        elif len(navigable_apps) == 1:
            action_target = navigable_apps[0].base_path or "/"
            action_label = f"Abrir {navigable_apps[0].name}"
        else:
            action_target = "/"
            action_label = "Ver aplicativos"

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
                    "templateId": _TEMPLATE_ID,
                    "vars": {
                        "userName": first_name,
                        "appNames": app_names_str,
                        "featureNames": feature_names_str,
                        "systemPermissionNames": system_names_str,
                    },
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
    def _build_access_message(
        first_name: str,
        *,
        app_names_str: str,
        system_names_str: str,
        feature_names_str: str,
    ) -> str:
        segments: list[str] = []
        if app_names_str:
            segments.append(f"acesso a: {app_names_str}")
        if system_names_str:
            segments.append(f"permissões de sistema: {system_names_str}")

        if not segments:
            if feature_names_str:
                return (
                    f"Olá, {first_name}! Você recebeu novas funcionalidades: "
                    f"{feature_names_str}."
                )
            return (
                f"Olá, {first_name}! Você recebeu novos recursos na plataforma."
            )

        message = f"Olá, {first_name}! Você recebeu {' e '.join(segments)}."
        if feature_names_str:
            message = f"{message} Novas funcionalidades: {feature_names_str}."
        return message

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
