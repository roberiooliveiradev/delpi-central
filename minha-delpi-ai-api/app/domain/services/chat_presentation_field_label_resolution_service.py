"""Entrada canônica para humanização e tradução de rótulos de campo (Playbook 12 § R17).

Delega resolução e formatação a `ExternalActionColumnLabelService` — consumidores
devem preferir este módulo em novos código; APIs legadas permanecem no serviço de colunas.
"""

from __future__ import annotations

from typing import Any

from app.domain.services.external_actions.external_action_column_label_service import (
    ExternalActionColumnLabelService,
)


class ChatPresentationFieldLabelResolutionService:
    """Facade fino — uma cascata para colunas tabulares, perfil KV e formatação de valor."""

    @classmethod
    def resolve_labels(
        cls,
        keys: list[str],
        *,
        path: str = "",
        profile_name: str | None = None,
        schema_labels: dict[str, str] | None = None,
        enable_discovery: bool = True,
    ) -> dict[str, str]:
        return ExternalActionColumnLabelService().resolve_field_labels(
            keys,
            path=path,
            profile_name=profile_name,
            schema_labels=schema_labels,
            enable_discovery=enable_discovery,
        )

    @classmethod
    def resolve_label(
        cls,
        key: str,
        *,
        path: str = "",
        profile_name: str | None = None,
        schema_labels: dict[str, str] | None = None,
        enable_discovery: bool = True,
    ) -> str:
        token = str(key or "").strip()

        if not token:
            return ""

        labels = cls.resolve_labels(
            [token],
            path=path,
            profile_name=profile_name,
            schema_labels=schema_labels,
            enable_discovery=enable_discovery,
        )

        return labels.get(token, "")

    @classmethod
    def format_value(
        cls,
        key: str,
        value: object,
        *,
        schema_formats: dict[str, str] | None = None,
    ) -> str:
        return ExternalActionColumnLabelService().format_field_value(
            key,
            value,
            schema_formats=schema_formats,
        )

    @classmethod
    def build_kv_rows(
        cls,
        payload: dict[str, Any],
        *,
        format_value,
        path: str = "",
        profile_name: str | None = None,
        schema_labels: dict[str, str] | None = None,
        schema_formats: dict[str, str] | None = None,
        skip_keys: set[str] | None = None,
        enable_discovery: bool = True,
    ) -> list[dict[str, str]]:
        """Monta linhas campo/valor com rótulos e valores humanizados."""
        skipped = skip_keys or set()
        items = [
            (str(key), value)
            for key, value in payload.items()
            if str(key) not in skipped and value not in (None, "")
        ]

        if not items:
            return []

        keys = [key for key, _ in items]
        label_map = cls.resolve_labels(
            keys,
            path=path,
            profile_name=profile_name,
            schema_labels=schema_labels,
            enable_discovery=enable_discovery,
        )

        rows: list[dict[str, str]] = []

        for key, value in items:
            rows.append(
                {
                    "campo": label_map.get(key) or cls.resolve_label(key, schema_labels=schema_labels),
                    "valor": format_value(key, value, schema_formats=schema_formats),
                }
            )

        return rows
