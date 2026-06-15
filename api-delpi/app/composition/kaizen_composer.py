from __future__ import annotations

from app.infrastructure.persistence.plugins.repositories.kaizen.postgres_kaizen_repository import (
    PostgresKaizenRepository,
)


def build_kaizen_repository() -> PostgresKaizenRepository:
    return PostgresKaizenRepository()
