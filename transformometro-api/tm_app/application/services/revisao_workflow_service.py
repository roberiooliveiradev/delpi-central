from __future__ import annotations

from typing import Any

from tm_app.core.catalogs import STATUS_APROVACAO_REVISAO, assert_in
from tm_app.infrastructure.persistence.repositories.revisao_repository import RevisaoRepository


class RevisaoWorkflowError(ValueError):
    pass


class RevisaoWorkflowService:
    _SUBMIT_FROM = frozenset({"rascunho", "rejeitada"})

    def __init__(self, repo: RevisaoRepository | None = None) -> None:
        self._repo = repo or RevisaoRepository()

    def submeter(self, revisao_id: str) -> dict[str, Any]:
        return self._transition(revisao_id, "em_analise", from_statuses=self._SUBMIT_FROM)

    def aprovar(self, revisao_id: str, aprovado_por_email: str | None) -> dict[str, Any]:
        return self._transition(
            revisao_id,
            "aprovada",
            from_statuses=frozenset({"em_analise"}),
            aprovado_por_email=aprovado_por_email,
        )

    def rejeitar(
        self,
        revisao_id: str,
        motivo: str | None,
        aprovado_por_email: str | None,
    ) -> dict[str, Any]:
        if not (motivo or "").strip():
            raise RevisaoWorkflowError("Informe o motivo da rejeição.")
        return self._transition(
            revisao_id,
            "rejeitada",
            from_statuses=frozenset({"em_analise"}),
            motivo_rejeicao=motivo.strip(),
            aprovado_por_email=aprovado_por_email,
        )

    def _transition(
        self,
        revisao_id: str,
        to_status: str,
        *,
        from_statuses: frozenset[str],
        aprovado_por_email: str | None = None,
        motivo_rejeicao: str | None = None,
    ) -> dict[str, Any]:
        assert_in(to_status, STATUS_APROVACAO_REVISAO, "status_aprovacao")
        current = self._repo.get(revisao_id)
        if not current:
            raise RevisaoWorkflowError("Revisão não encontrada.")

        atual = str(current.get("status_aprovacao") or "rascunho")
        if atual not in from_statuses:
            raise RevisaoWorkflowError(
                f"Não é possível alterar de '{atual}' para '{to_status}'."
            )

        row = self._repo.set_status_aprovacao(
            revisao_id,
            to_status,
            aprovado_por_email=aprovado_por_email if to_status in ("aprovada", "rejeitada") else None,
            motivo_rejeicao=motivo_rejeicao if to_status == "rejeitada" else None,
        )
        if not row:
            raise RevisaoWorkflowError("Falha ao atualizar status da revisão.")
        return row

    @staticmethod
    def ensure_can_activate(revisao: dict[str, Any]) -> None:
        status = str(revisao.get("status_aprovacao") or "rascunho")
        if status != "aprovada":
            raise RevisaoWorkflowError(
                "Somente revisões aprovadas podem ser ativadas. Submeta e aprove a revisão antes."
            )
