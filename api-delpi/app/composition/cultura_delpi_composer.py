from __future__ import annotations

from app.infrastructure.persistence.plugins.repositories.cultura_delpi.postgres_cultura_delpi_repository import (
    PostgresCulturaDelpiRepository,
)


def build_cultura_delpi_repository() -> PostgresCulturaDelpiRepository:
    return PostgresCulturaDelpiRepository()
