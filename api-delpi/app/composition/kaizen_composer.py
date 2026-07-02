from __future__ import annotations

from app.application.services.kaizen.kaizen_evidence_storage import KaizenEvidenceStorage
from app.application.use_cases.kaizen.import_kaizens_from_sheet_use_case import (
    ImportKaizensFromSheetUseCase,
)
from app.composition.quality_composer import _build_kaizen_repository as build_sheet_kaizen_repository
from app.infrastructure.persistence.plugins.repositories.kaizen.postgres_kaizen_evidence_repository import (
    PostgresKaizenEvidenceRepository,
)
from app.infrastructure.persistence.plugins.repositories.kaizen.postgres_kaizen_repository import (
    PostgresKaizenRepository,
)


def build_kaizen_repository() -> PostgresKaizenRepository:
    return PostgresKaizenRepository()


def build_kaizen_evidence_repository() -> PostgresKaizenEvidenceRepository:
    return PostgresKaizenEvidenceRepository()


def build_kaizen_evidence_storage() -> KaizenEvidenceStorage:
    return KaizenEvidenceStorage()


def build_import_kaizens_from_sheet_use_case() -> ImportKaizensFromSheetUseCase:
    return ImportKaizensFromSheetUseCase(
        sheet_source=build_sheet_kaizen_repository(),
        record_repository=build_kaizen_repository(),
    )
