"""Repository — SYS_USR lookup by email."""

from __future__ import annotations

from typing import Any

from app.infrastructure.persistence.totvs.base_repository import BaseRepository
from app.infrastructure.persistence.totvs.protheus_users.protheus_users_sql import (
    build_protheus_user_by_email_sql,
)


class ProtheusUsersRepository(BaseRepository):
    def find_by_email(self, email: str) -> list[dict[str, Any]]:
        normalized = (email or "").strip().lower()
        if not normalized or "@" not in normalized:
            raise ValueError("email must be a valid address")

        with self as repo:
            rows = repo.execute_query(build_protheus_user_by_email_sql(), (normalized,))

        return [
            {
                "protheus_user_id": (row.get("protheus_user_id") or "").strip(),
                "code": (row.get("code") or "").strip() or None,
                "name": (row.get("name") or "").strip() or None,
                "email": (row.get("email") or "").strip() or None,
            }
            for row in rows
            if (row.get("protheus_user_id") or "").strip()
        ]
