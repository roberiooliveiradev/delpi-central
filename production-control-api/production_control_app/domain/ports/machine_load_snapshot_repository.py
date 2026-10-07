"""Port — snapshot congelado da carga máquina (uma fila viva por filial)."""

from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import date
from typing import Any, Iterator


class MachineLoadSnapshotRepositoryPort(ABC):
    @abstractmethod
    def get(self, *, branch: str) -> dict[str, Any] | None:
        """Retorna a fila da filial (payload_json + janela + generation_id), ou None."""

    @abstractmethod
    def upsert(
        self,
        *,
        branch: str,
        start_date: date,
        end_date: date,
        payload: dict[str, Any],
        generation_id: str,
        refreshed_by: str | None,
        schema_version: int = 1,
        source: str = "api-delpi",
    ) -> dict[str, Any]:
        """Substitui a fila da filial (WORKING) abrindo a ``generation_id`` nova do refresh."""

    @abstractmethod
    def update_payload(
        self, *, branch: str, payload: dict[str, Any], conn: Any = None
    ) -> dict[str, Any]:
        """Atualiza só o JSON (ex.: sequência manual) sem mexer em refreshed_at nem em generation_id.

        conn escreve dentro de uma transação aberta — dual-write LIVE
        (WORKING + PUBLISHED) commita ou falha atomicamente.
        """

    @abstractmethod
    def transaction(self) -> Iterator[Any]:
        """Conexão/transação compartilhada: commit ao sair, rollback em erro.

        Permite que writes cobertos por conn (ex.: publicação da fila)
        comitam ou falhem atomicamente.
        """

    @abstractmethod
    def get_for_update(self, *, branch: str, conn: Any) -> dict[str, Any] | None:
        """Lê a fila WORKING da filial com SELECT ... FOR UPDATE em conn.

        Serializa publicação x mutações: quem publica trabalha sobre o estado
        consistente mais recente da linha.
        """
