"""Port — triagem/tratamento gerencial de paradas MES (1:1 por downtime)."""

from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any


class DowntimeTreatmentRepositoryPort(ABC):
    @abstractmethod
    def get(
        self, downtime_id: str, *, conn: Any | None = None
    ) -> dict[str, Any] | None:
        """Triagem da parada, se existir."""

    @abstractmethod
    def upsert(
        self,
        downtime_id: str,
        *,
        branch: str,
        work_center: str,
        analysis: str,
        cause_kind: str,
        cause_note: str | None,
        action_needed: bool,
        justification: str,
        expected_updated_at: datetime | None,
        actor_ref: str,
        actor_name: str,
        conn: Any | None = None,
    ) -> dict[str, Any]:
        """Cria/atualiza a triagem com precondição otimista por updated_at.

        expected_updated_at=None exige criação (conflito se já existir);
        valor informado exige a linha naquele instante — divergência vira
        DowntimeTreatmentConflict.
        """

    @abstractmethod
    def link_request(
        self,
        downtime_id: str,
        *,
        request_id: str,
        request_type_code: str,
        actor_ref: str,
        actor_name: str,
        conn: Any | None = None,
    ) -> dict[str, Any]:
        """Vincula a solicitação externa; idempotente para o mesmo id."""

    @abstractmethod
    def conclude(
        self,
        downtime_id: str,
        *,
        reason: str,
        actor_ref: str,
        actor_name: str,
        conn: Any | None = None,
    ) -> dict[str, Any]:
        """Encerra o tratamento com justificativa; uma única conclusão."""
