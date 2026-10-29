"""Repositório NC indisponível — degradação honesta.

Usado quando ``ENG_NC_REPOSITORY`` não está configurada: toda operação
levanta ``NcRepositoryError`` → o edge responde ``unavailable`` (503),
nunca lista vazia falsa nem dados sintéticos como se fossem oficiais.
"""

from __future__ import annotations

from datetime import date
from typing import Any

from engineering_app.domain.nonconformity.errors import NcRepositoryError
from engineering_app.domain.nonconformity.models import NcActor

_MESSAGE = (
    "Persistência NC não configurada neste ambiente "
    "(ENG_NC_REPOSITORY ausente)."
)


class UnavailableNonconformityRepository:
    """Implementa ``NonconformityRepository`` falhando honestamente."""

    def list_records(self, **kwargs: Any) -> dict[str, Any]:
        raise NcRepositoryError(_MESSAGE)

    def get_record(self, record_id: str) -> dict[str, Any] | None:
        raise NcRepositoryError(_MESSAGE)

    def export_records(self) -> list[dict[str, Any]]:
        raise NcRepositoryError(_MESSAGE)

    def list_history(self, record_id: str) -> list[dict[str, Any]] | None:
        raise NcRepositoryError(_MESSAGE)

    def list_problem_tag_catalog(self) -> list[dict[str, Any]]:
        raise NcRepositoryError(_MESSAGE)

    def list_occurrence_dates(self) -> list[date]:
        raise NcRepositoryError(_MESSAGE)

    def find_import_duplicate(self, **kwargs: Any) -> dict[str, Any] | None:
        raise NcRepositoryError(_MESSAGE)

    def create_record(self, *, actor: NcActor, **kwargs: Any) -> dict[str, Any]:
        raise NcRepositoryError(_MESSAGE)

    def update_record(
        self, *, record_id: str, status: str, actor: NcActor, **kwargs: Any
    ) -> dict[str, Any] | None:
        raise NcRepositoryError(_MESSAGE)

    def delete_record(self, record_id: str) -> bool:
        raise NcRepositoryError(_MESSAGE)

    def delete_all_records(self) -> int:
        raise NcRepositoryError(_MESSAGE)
