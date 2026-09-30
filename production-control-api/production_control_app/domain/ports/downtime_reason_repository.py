"""Port — catálogo governado de motivos de parada MES."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class DowntimeReasonRepositoryPort(ABC):
    @abstractmethod
    def get(self, code: str) -> dict[str, Any] | None:
        """Motivo por código estável (minúsculo, aparado)."""

    @abstractmethod
    def list_active(self) -> list[dict[str, Any]]:
        """Motivos ativos, ordenados por sort_order."""

    @abstractmethod
    def list_all(self) -> list[dict[str, Any]]:
        """Ativos e inativos, ordenados por sort_order, code — visão administrativa."""

    @abstractmethod
    def create(
        self,
        *,
        code: str,
        label: str,
        category: str,
        requires_note: bool,
        sort_order: int,
    ) -> dict[str, Any]:
        """Insere motivo novo (ativo). A PK é a barreira final contra duplicidade —
        ``UniqueViolation`` vira erro de domínio, nunca erro cru do Postgres."""

    @abstractmethod
    def update(
        self,
        code: str,
        *,
        label: str,
        category: str,
        requires_note: bool,
        sort_order: int,
    ) -> dict[str, Any] | None:
        """Atualiza somente campos administráveis. ``code``, os defaults OEE
        (``default_planned``/``default_counts_as_availability_loss``) e
        ``created_at`` são imutáveis por contrato."""

    @abstractmethod
    def set_active(self, code: str, *, active: bool) -> dict[str, Any] | None:
        """Desativa/reativa motivo sem apagar histórico que o referencia."""
