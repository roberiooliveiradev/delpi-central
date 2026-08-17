# app/application/services/notification_app_access_service.py

from __future__ import annotations

from uuid import UUID

from app.application.services.app_authorization_service import AppAuthorizationService
from app.application.services.notification_catalog_service import NotificationCatalogService
from app.application.unit_of_work import UnitOfWork
from app.domain.notifications.notification_catalog_types import NotificationCatalog
from app.domain.notifications.notification_preference_policy import (
    normalize_muted_categories,
)
from app.domain.services.permission_resolver import PermissionResolver


def resolve_notification_app_id(
    uow: UnitOfWork,
    *,
    source_app: str | None,
    action_target: str | None,
    metadata: dict | None,
) -> str | None:
    """
    Identifica o plugin/app do portal associado à notificação.
    Retorna None quando não há vínculo com app (notificações globais do sistema).
    """
    apps = uow.app_queries.list_active_apps_with_routes()
    if not apps:
        return None

    app_ids = {app.id for app in apps}
    source_app_aliases = NotificationCatalogService.get().source_app_plugin_aliases

    candidates: list[str] = []

    for raw in (
        source_app,
        (metadata or {}).get("source") if isinstance(metadata, dict) else None,
        (metadata or {}).get("sourceApp") if isinstance(metadata, dict) else None,
    ):
        if not raw or not isinstance(raw, str):
            continue
        key = raw.strip().lower()
        if not key:
            continue
        candidates.append(key)
        candidates.append(key.replace("_", "-"))
        mapped = source_app_aliases.get(key)
        if mapped:
            candidates.append(mapped)

    for candidate in candidates:
        if candidate in app_ids:
            return candidate

    if action_target and isinstance(action_target, str):
        path = action_target.strip().rstrip("/") or "/"
        for app in apps:
            base = (app.base_path or "/").rstrip("/") or "/"
            if path == base or path.startswith(f"{base}/"):
                return app.id

    return None


def list_accessible_plugin_ids_for_user(uow: UnitOfWork, user_id: str) -> frozenset[str]:
    """Plugin IDs que o usuário pode abrir (mesma regra de GET /me/apps)."""
    try:
        user_uuid = UUID(str(user_id).strip())
    except (TypeError, ValueError):
        return frozenset()

    user = uow.users.get_by_id(user_uuid)
    if not user or not user.active:
        return frozenset()

    apps = uow.app_queries.list_active_apps_with_routes()
    if not apps:
        return frozenset()

    resolver = PermissionResolver(uow.permission_queries, uow.cache)
    permissions = resolver.resolve(user.id, bool(user.is_superadmin))
    authorized = AppAuthorizationService().filter_app_ids(
        apps,
        permissions,
        bool(user.is_superadmin),
    )
    return frozenset(authorized)


def filter_mutable_categories_for_user(
    accessible_plugin_ids: frozenset[str],
    *,
    catalog: NotificationCatalog | None = None,
) -> frozenset[str]:
    """
    Preferências silenciáveis visíveis ao usuário:
    - kind=platform → sempre
    - kind=app → só se pluginId estiver nos apps autorizados
    """
    source = catalog or NotificationCatalogService.get()
    visible: set[str] = set()
    for category_id, spec in source.categories.items():
        if not spec.mutable:
            continue
        if (spec.kind or "platform").strip().lower() != "app":
            visible.add(category_id)
            continue
        plugin_id = (spec.plugin_id or "").strip()
        if plugin_id and plugin_id in accessible_plugin_ids:
            visible.add(category_id)
    return frozenset(visible)


def merge_muted_categories_preserving_hidden(
    previous_muted: list[str],
    next_muted: list[str],
    *,
    visible_mutable: frozenset[str],
    all_mutable: frozenset[str],
) -> list[str]:
    """
    Ao salvar preferências, não apaga silêncios de apps sem acesso
    (categorias ocultas na UI).
    """
    preserved = [
        category
        for category in normalize_muted_categories(
            previous_muted,
            mutable_categories=all_mutable,
        )
        if category not in visible_mutable
    ]
    updated = normalize_muted_categories(
        next_muted,
        mutable_categories=visible_mutable,
    )
    return sorted(set(preserved) | set(updated))


def filter_user_ids_with_app_access(
    uow: UnitOfWork,
    user_ids: list[str],
    *,
    source_app: str | None,
    action_target: str | None,
    metadata: dict | None,
) -> list[str]:
    """
    Remove destinatários que não possuem permissão para abrir o app de origem
    (mesma regra de GET /me/apps).
    """
    app_id = resolve_notification_app_id(
        uow,
        source_app=source_app,
        action_target=action_target,
        metadata=metadata,
    )
    if not app_id:
        return user_ids

    apps = uow.app_queries.list_active_apps_with_routes()
    target_app = next((app for app in apps if app.id == app_id), None)
    if target_app is None:
        return []

    auth_service = AppAuthorizationService()
    resolver = PermissionResolver(uow.permission_queries, uow.cache)

    allowed: list[str] = []

    for raw_user_id in user_ids:
        try:
            user_uuid = UUID(str(raw_user_id).strip())
        except (TypeError, ValueError):
            continue

        user = uow.users.get_by_id(user_uuid)
        if not user or not user.active:
            continue

        permissions = resolver.resolve(user.id, bool(user.is_superadmin))
        authorized_ids = auth_service.filter_app_ids(
            [target_app],
            permissions,
            bool(user.is_superadmin),
        )

        if app_id in authorized_ids:
            allowed.append(str(user.id))

    return allowed
