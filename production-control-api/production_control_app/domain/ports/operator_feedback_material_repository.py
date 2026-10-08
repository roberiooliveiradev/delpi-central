"""Port — materiais estruturados do Operator Feedback (C5).

A tabela operator_feedback_materials (V017) é filha de operator_feedbacks:
cada linha é um material SD4 que o operador marcou como faltante, com
snapshot congelado e lifecycle próprio pending -> picked -> delivered.

A CRIAÇÃO não mora aqui: o insert é atômico junto ao feedback pelo
OperatorFeedbackRepositoryPort.create(materials=...) — uma única transação
ou existe tudo, ou nada (mesmo padrão de create_plan do pick plan).

Esta port cobre leitura e as transições do Alimentador de Linha.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class OperatorFeedbackMaterialRepositoryPort(ABC):
    @abstractmethod
    def list_for_feedbacks(
        self, feedback_ids: list[str]
    ) -> dict[str, list[dict[str, Any]]]:
        """Materiais agrupados por feedback_id — enriquecimento em lote dos
        DTOs (inbox PCP, cockpit) sem N+1."""

    @abstractmethod
    def get_material(self, material_id: str) -> dict[str, Any] | None:
        """Material por id, já com dados do feedback pai
        (branch/status da OP) para autorização e realtime."""

    @abstractmethod
    def list_active_requests(self, *, branch: str) -> list[dict[str, Any]]:
        """Fila urgente do Alimentador: materiais pending|picked cujo
        feedback ainda está ativo (open|acknowledged).

        Feedback resolved sai da fila automaticamente — o histórico fica
        no banco, mas ninguém continua separando material de impedimento
        encerrado.
        """

    @abstractmethod
    def mark_picked(
        self, material_id: str, *, picked_by: str
    ) -> dict[str, Any] | None:
        """Transição condicional atômica pending -> picked.

        Exige feedback do material ainda ativo (open|acknowledged):
        resolved é terminal para a fila operacional. None = nada transitou;
        o service relê e distingue idempotente de inválido.
        """

    @abstractmethod
    def mark_delivered(
        self, material_id: str, *, delivered_by: str
    ) -> dict[str, Any] | None:
        """Transição condicional atômica picked -> delivered (mesma regra)."""
