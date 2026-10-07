# app/application/use_cases/update_user_notification_category_preference_use_case.py
"""Toggle admin de uma categoria de notificação para um usuário específico.

Espelha a semântica do painel self-service:
- desativar (mute ON) limpa destaque e e-mail da categoria;
- ativar destaque ou e-mail remove o silêncio da categoria;
- demais flags não tocam nas outras listas.
"""

from __future__ import annotations

from typing import Any
from uuid import UUID

from app.application.services.notification_catalog_service import (
    NotificationCatalogService,
)
from app.application.unit_of_work import UnitOfWork
from app.application.use_cases.get_notification_preferences_use_case import (
    NotificationPreferencesResult,
)
from app.application.use_cases.update_notification_preferences_use_case import (
    UpdateNotificationPreferencesUseCase,
)


class UpdateUserNotificationCategoryPreferenceUseCase:

    def __init__(self, uow: UnitOfWork):
        self.uow = uow

    def execute(
        self,
        user_id: str,
        *,
        category: str,
        enabled: bool | None = None,
        important: bool | None = None,
        email: bool | None = None,
    ) -> NotificationPreferencesResult:
        normalized = (category or "").strip().lower()
        spec = NotificationCatalogService.get().categories.get(normalized)
        if spec is None:
            raise ValueError("unknown notification category")
        if not spec.mutable:
            raise ValueError("notification category is not mutable")
        if enabled is None and important is None and email is None:
            raise ValueError("no preference flag provided")

        try:
            user_uuid = UUID(str(user_id).strip())
        except (TypeError, ValueError) as exc:
            raise ValueError("invalid user id") from exc
        target = self.uow.users.get_by_id(user_uuid)
        if target is None:
            raise LookupError("user not found")

        muted = set(
            self.uow.notification_preferences.get_muted_categories(str(target.id))
        )
        important_set = set(
            self.uow.notification_preferences.get_important_categories(str(target.id))
        )
        email_set = set(
            self.uow.notification_preferences.get_email_categories(str(target.id))
        )

        if enabled is False:
            muted.add(normalized)
            important_set.discard(normalized)
            email_set.discard(normalized)
        elif enabled is True:
            muted.discard(normalized)

        if important is True:
            muted.discard(normalized)
            important_set.add(normalized)
        elif important is False:
            important_set.discard(normalized)

        if email is True:
            muted.discard(normalized)
            email_set.add(normalized)
        elif email is False:
            email_set.discard(normalized)

        return UpdateNotificationPreferencesUseCase(self.uow).execute(
            str(target.id),
            muted_categories=sorted(muted),
            important_categories=sorted(important_set),
            email_categories=sorted(email_set),
        )
