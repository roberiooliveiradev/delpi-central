"""Port — persistência do Operator Feedback (impedimentos do operador).

Registros históricos e independentes: nenhuma operação lê ou escreve o snapshot
da Carga Máquina, e run_id é contexto opcional — nunca dependência.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import date
from typing import Any


class OperatorFeedbackRepositoryPort(ABC):
    @abstractmethod
    def create(
        self,
        *,
        branch: str,
        production_order: str,
        operation_code: str,
        reported_work_center: str,
        feedback_type: str,
        reason_code: str,
        operator_code: str,
        operator_name: str,
        note: str | None = None,
        bench_session_id: str | None = None,
        run_id: str | None = None,
        product_code: str | None = None,
        product_description: str | None = None,
        pa_product_code: str | None = None,
        due_date: date | str | None = None,
    ) -> dict[str, Any]:
        """Cria feedback open. OperatorFeedbackConflict se já houver
        impedimento ativo igual (mesma chave lógica) — a garantia final é o
        índice parcial do banco, não um SELECT prévio."""

    @abstractmethod
    def get(self, feedback_id: str) -> dict[str, Any] | None:
        """Feedback por id."""

    @abstractmethod
    def get_active(
        self,
        *,
        branch: str,
        production_order: str,
        operation_code: str,
        feedback_type: str,
        reason_code: str,
    ) -> dict[str, Any] | None:
        """Impedimento ativo (open|acknowledged) da chave lógica, se existir."""

    @abstractmethod
    def list_active(
        self,
        *,
        branch: str,
        reported_work_center: str | None = None,
    ) -> list[dict[str, Any]]:
        """Impedimentos ativos da filial — inbox do PCP (C3) e leitura por CT (C4)."""

    @abstractmethod
    def list_active_for_operation(
        self,
        *,
        branch: str,
        production_order: str,
        operation_code: str,
    ) -> list[dict[str, Any]]:
        """Impedimentos ativos pela identidade funcional da OP/operação.

        NÃO filtra por reported_work_center: o feedback pertence à OP/operação
        e sobrevive à transferência de CT (o cockpit do CT destino continua
        vendo o impedimento criado no CT de origem).
        """

    @abstractmethod
    def acknowledge(
        self, feedback_id: str, *, acknowledged_by: str
    ) -> dict[str, Any] | None:
        """Transição condicional atômica open -> acknowledged.

        Retorna a linha atualizada ou None quando o status atual não é
        open (ou o id não existe): quem decide a semântica é o service,
        que relê e distingue acknowledged-idempotente de resolved-terminal.
        """

    @abstractmethod
    def resolve(
        self,
        feedback_id: str,
        *,
        resolved_by: str,
        resolution_note: str | None = None,
    ) -> dict[str, Any] | None:
        """Transição condicional atômica open|acknowledged -> resolved.

        Mesma convenção do acknowledge: None = nada transitou.
        """
