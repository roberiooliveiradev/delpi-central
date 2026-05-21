# app/infrastructure/persistence/app_audit.py

from __future__ import annotations

from uuid import UUID

from app.infrastructure.db.models import App


def apply_app_audit(
    row: App,
    *,
    user_id: str | None,
    name: str | None,
    on_create: bool = False,
) -> None:
    if on_create:
        if user_id:
            row.created_by_user_id = UUID(user_id)
        if name:
            row.created_by_name = name

    if user_id:
        row.updated_by_user_id = UUID(user_id)
    if name:
        row.updated_by_name = name
