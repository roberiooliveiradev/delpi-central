# app/application/use_cases/list_notification_category_users_use_case.py
"""Roster admin de usuários que podem receber uma categoria de notificação.

Devolve a página de usuários já com o estado das três preferências da
categoria (recebendo/destaque/e-mail), evitando N+1 na tela de gestão.

- ``app_id`` informado (categorias kind=app): apenas usuários com acesso
  efetivo ao app, mesma regra de GET /me/apps.
- ``app_id`` vazio (categorias de plataforma): todos os usuários ativos.
"""

from __future__ import annotations

from typing import Any

from app.application.services.directory_user_eligibility_service import (
    DirectoryUserEligibilityService,
)
from app.application.services.notification_app_access_service import (
    resolve_notification_app_id,
)
from app.application.services.notification_catalog_service import (
    NotificationCatalogService,
)
from app.application.unit_of_work import UnitOfWork

MAX_PAGE_SIZE = 200
SCAN_PAGE_SIZE = 100


class ListNotificationCategoryUsersUseCase:

    def __init__(self, uow: UnitOfWork):
        self.uow = uow

    def execute(
        self,
        *,
        category: str,
        q: str | None = None,
        page: int = 1,
        page_size: int = 50,
    ) -> dict[str, Any]:
        normalized_category = (category or "").strip().lower()
        spec = NotificationCatalogService.get().categories.get(normalized_category)
        if spec is None:
            raise ValueError("unknown notification category")

        safe_page = max(1, int(page or 1))
        safe_size = max(1, min(int(page_size or 50), MAX_PAGE_SIZE))
        query = (q or "").strip().lower() or None

        app_id = self._resolve_app_id(spec)
        if spec.kind == "app" and app_id is None:
            items, total = [], 0
        else:
            items, total = self._page_users(
                app_id=app_id if spec.kind == "app" else None,
                query=query,
                page=safe_page,
                page_size=safe_size,
            )

        preferences = self.uow.notification_preferences.get_preferences_for_users(
            [item["id"] for item in items]
        )
        mutable = bool(spec.mutable)
        rows: list[dict[str, Any]] = []
        for item in items:
            dto = preferences.get(item["id"])
            muted = set(dto.muted_categories) if dto else set()
            important = set(dto.important_categories) if dto else set()
            email = set(dto.email_categories) if dto else set()
            rows.append(
                {
                    **item,
                    "enabled": not mutable or normalized_category not in muted,
                    "important": normalized_category in important,
                    "emailEnabled": normalized_category in email,
                    "mutable": mutable,
                }
            )

        end = safe_page * safe_size
        return {
            "category": {
                "id": normalized_category,
                "label": spec.label,
                "notificationLabel": spec.preference_title,
                "mutable": mutable,
                "kind": spec.kind,
                "appId": app_id if spec.kind == "app" else None,
            },
            "items": rows,
            "page": safe_page,
            "pageSize": safe_size,
            "total": total,
            "hasMore": end < total,
        }

    def _resolve_app_id(self, spec) -> str | None:
        if spec.kind != "app":
            return None
        candidates = [spec.plugin_id, *spec.source_apps]
        for raw in candidates:
            if not raw:
                continue
            resolved = resolve_notification_app_id(
                self.uow,
                source_app=raw,
                action_target=None,
                metadata=None,
            )
            if resolved:
                return resolved
        return None

    def _page_users(
        self,
        *,
        app_id: str | None,
        query: str | None,
        page: int,
        page_size: int,
    ) -> tuple[list[dict[str, str]], int]:
        eligibility = DirectoryUserEligibilityService(self.uow)
        matches: list[dict[str, str]] = []
        scan_page = 1
        while True:
            users, total = self.uow.users.list_paginated(
                q=query,
                page=scan_page,
                page_size=SCAN_PAGE_SIZE,
                sort="name",
                direction="asc",
            )
            if not users:
                break
            for user in users:
                if not user.active:
                    continue
                if app_id and not eligibility.matches(user, app_id=app_id):
                    continue
                matches.append(
                    {"id": str(user.id), "name": user.name, "email": user.email}
                )
            if scan_page * SCAN_PAGE_SIZE >= int(total or 0):
                break
            if len(users) < SCAN_PAGE_SIZE:
                break
            scan_page += 1

        total_matches = len(matches)
        start = (page - 1) * page_size
        return matches[start : start + page_size], total_matches
