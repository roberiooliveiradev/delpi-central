from __future__ import annotations

from app.application.services.kaizen.kaizen_evidence_storage import KaizenEvidenceStorage
from app.application.use_cases.kaizen.import_kaizens_use_case import ImportKaizensUseCase
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


def build_import_kaizens_use_case() -> ImportKaizensUseCase:
    """Importa kaizens de itens JSON já mapeados (backup/migração entre ambientes)."""
    return ImportKaizensUseCase(record_repository=build_kaizen_repository())
