# app/infrastructure/persistence/app_audit.py

from __future__ import annotations

from uuid import UUID

from app.infrastructure.db.models import App


def apply_app_audit(
    row: App,
    *,
    user_id: str | None,
    email: str | None,
    on_create: bool = False,
) -> None:
    if on_create:
        if user_id:
            row.created_by_user_id = UUID(user_id)
        if email:
            row.created_by_email = email

    if user_id:
        row.updated_by_user_id = UUID(user_id)
    if email:
        row.updated_by_email = email
