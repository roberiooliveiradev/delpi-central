"""Port — fila PUBLISHED da carga máquina (uma publicação atual por filial).

A publicação é uma cópia durável da geração enviada às bancadas. O contrato
futuro é derivado das gerações, sem flag persistida:

  WORKING.generation_id == PUBLISHED.generation_id → LIVE
  WORKING.generation_id <> PUBLISHED.generation_id → DRAFT/em preparação
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import date, datetime
from typing import Any


class MachineLoadPublicationRepositoryPort(ABC):
    @abstractmethod
    def get(self, *, branch: str, conn: Any = None) -> dict[str, Any] | None:
        """Retorna a publicação vigente da filial, ou None quando nunca publicada.

        conn lê dentro de uma transação aberta (publicação): bypass do
        row-cache, a leitura é autoritativa da transação.
        """

    @abstractmethod
    def upsert(
        self,
        *,
        branch: str,
        generation_id: str,
        start_date: date,
        end_date: date,
        payload: dict[str, Any],
        source_refreshed_at: datetime,
        source_refreshed_by: str | None,
        published_by: str | None,
        schema_version: int = 1,
        source: str = "api-delpi",
        conn: Any = None,
    ) -> dict[str, Any]:
        """Grava a publicação vigente da filial (uma por branch, ``published_at`` novo)."""

    @abstractmethod
    def update_payload(
        self, *, branch: str, payload: dict[str, Any], conn: Any = None
    ) -> dict[str, Any]:
        """Atualiza só o payload_json da publicação vigente.

        Mutações PCP em estado LIVE acompanham o WORKING sem virar nova
        publicação: generation_id, published_at/published_by e
        source_* permanecem intactos.
        """
