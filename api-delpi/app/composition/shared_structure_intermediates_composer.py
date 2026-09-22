"""Composition — intermediários compartilhados entre PAs ativos."""

from __future__ import annotations

from app.application.use_cases.production.get_shared_structure_intermediates_use_case import (
    GetSharedStructureIntermediatesUseCase,
)
from app.infrastructure.persistence.totvs.production.shared_structure_intermediates_repository import (
    SharedStructureIntermediatesRepository,
)


def build_get_shared_structure_intermediates_use_case() -> (
    GetSharedStructureIntermediatesUseCase
):
    return GetSharedStructureIntermediatesUseCase(
        repository=SharedStructureIntermediatesRepository()
    )
