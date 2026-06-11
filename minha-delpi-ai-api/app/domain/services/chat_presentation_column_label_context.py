"""Contrato estreito para rótulos/colunas tabulares — Playbook 12 R19."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol

from app.domain.services.external_actions.external_action_column_label_service import (
    ExternalActionColumnLabelService,
)


class ColumnLabelContext(Protocol):
    """Port mínimo consumido por `ChatPresentationOperationalTableService`."""

    @property
    def path(self) -> str:
        ...

    @property
    def schema_labels(self) -> dict[str, str] | None:
        ...

    @property
    def schema_formats(self) -> dict[str, str] | None:
        ...

    def resolve_columns_for_items(
        self,
        items: list[dict[str, Any]],
        *,
        path: str = "",
        profile_name: str | None = None,
    ) -> list[dict[str, Any]]:
        ...

    def format_field_value(self, key: str, value: object) -> str:
        ...


@dataclass(frozen=True)
class ExternalActionColumnLabelContext:
    """Adapter canônico — colunas + schema ativo do turno."""

    column_labels: ExternalActionColumnLabelService
    schema_labels: dict[str, str] | None = None
    schema_formats: dict[str, str] | None = None
    path: str = ""

    def resolve_columns_for_items(
        self,
        items: list[dict[str, Any]],
        *,
        path: str = "",
        profile_name: str | None = None,
    ) -> list[dict[str, Any]]:
        return self.column_labels.resolve_columns_for_items(
            items,
            path=path or self.path,
            profile_name=profile_name,
            schema_labels=self.schema_labels,
        )

    def format_field_value(self, key: str, value: object) -> str:
        return self.column_labels.format_field_value(
            key,
            value,
            schema_formats=self.schema_formats,
        )
