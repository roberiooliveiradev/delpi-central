"""Facade de domain para descoberta de rótulos de coluna via port."""

from __future__ import annotations

from typing import ClassVar

from app.domain.ports.presentation_column_label_discovery_port import (
    PresentationColumnLabelDiscoveryPort,
)


class PresentationColumnLabelDiscoveryService:
    _port: ClassVar[PresentationColumnLabelDiscoveryPort | None] = None

    @classmethod
    def configure(cls, port: PresentationColumnLabelDiscoveryPort) -> None:
        cls._port = port

    @classmethod
    def resolve_labels(
        cls,
        keys: list[str],
        *,
        path: str = "",
        schema_labels: dict[str, str] | None = None,
        profile_labels: dict[str, str] | None = None,
        fields: dict[str, str] | None = None,
    ) -> dict[str, str]:
        if cls._port is None:
            return {}

        try:
            return cls._port.resolve_labels(
                keys,
                path=path,
                schema_labels=schema_labels,
                profile_labels=profile_labels,
                fields=fields,
            )
        except Exception:
            return {}
