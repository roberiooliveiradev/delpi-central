"""Thin read adapters over the canonical Revision/Evidence authorities.

No SQL is duplicated here — the adapters delegate to ``RevisaoRepository``
and ``RevisaoEvidenceRepository`` and only map their canonical rows into
the small application read DTOs. Read-only: these adapters expose no
write path at all.
"""

from __future__ import annotations

from typing import Any

from tm_app.application.ports.evidence_reader_port import (
    EvidenceReaderPort,
    EvidenceRef,
)
from tm_app.application.ports.revision_reader_port import (
    RevisionContext,
    RevisionReaderPort,
)
from tm_app.infrastructure.persistence.repositories.revision_evidence_repository import (
    RevisaoEvidenceRepository,
)
from tm_app.infrastructure.persistence.repositories.revision_repository import (
    RevisaoRepository,
)


def _str_or_none(value: Any) -> str | None:
    return str(value) if value is not None else None


class RevisionReaderAdapter(RevisionReaderPort):
    """RevisionReaderPort backed by the canonical RevisaoRepository.

    ``RevisaoRepository.get`` already excludes soft-deleted revisions, so
    unresolved reads surface as ``None`` — never fabricated context.
    """

    def __init__(self, repository: RevisaoRepository | None = None) -> None:
        self._repository = repository or RevisaoRepository()

    def get(self, revision_id: str) -> RevisionContext | None:
        row = self._repository.get(revision_id)
        if row is None:
            return None
        return RevisionContext(
            revision_id=str(row["revisao_id"]),
            processo_id=str(row["processo_id"]),
            instancia_id=_str_or_none(row.get("instancia_id")),
            versao_revisao=str(row["versao_revisao"]),
            cenario_tipo=str(row["cenario_tipo"]),
            revisao_referencia_id=_str_or_none(
                row.get("revisao_referencia_id")
            ),
        )


class EvidenceReaderAdapter(EvidenceReaderPort):
    """EvidenceReaderPort backed by RevisaoEvidenceRepository.

    ``list_by_revisao`` is already revision-scoped and excludes
    soft-deleted evidence — soft-deleted rows never resolve and there is
    no cross-revision fallback path in this adapter.
    """

    def __init__(
        self, repository: RevisaoEvidenceRepository | None = None
    ) -> None:
        self._repository = repository or RevisaoEvidenceRepository()

    def list_by_revision(self, revision_id: str) -> list[EvidenceRef]:
        return [
            EvidenceRef(
                evidence_id=str(row["evidencia_id"]),
                revisao_id=str(row["revisao_id"]),
                tipo=str(row["tipo"]),
                nome_arquivo=row.get("nome_arquivo"),
                descricao=row.get("descricao"),
            )
            for row in self._repository.list_by_revisao(revision_id)
        ]
