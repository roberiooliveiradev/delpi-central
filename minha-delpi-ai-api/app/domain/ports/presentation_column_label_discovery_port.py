from __future__ import annotations

from abc import ABC, abstractmethod


class PresentationColumnLabelDiscoveryPort(ABC):
    """Descobre rótulos PT-BR para colunas ausentes do vocabulário JSON."""

    @abstractmethod
    def resolve_labels(
        self,
        keys: list[str],
        *,
        path: str = "",
        schema_labels: dict[str, str] | None = None,
        profile_labels: dict[str, str] | None = None,
        fields: dict[str, str] | None = None,
    ) -> dict[str, str]:
        raise NotImplementedError
