from __future__ import annotations

from app.infrastructure.persistence.plugins.repositories.scheduling.postgres_scheduling_repository import (
    PostgresSchedulingRepository,
)


def build_scheduling_repository() -> PostgresSchedulingRepository:
    return PostgresSchedulingRepository()
