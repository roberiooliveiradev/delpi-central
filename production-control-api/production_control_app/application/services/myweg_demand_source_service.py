"""Origem interna MyWEG para Demanda — última coleta aceita da filial 02.

Etapa 1: projeção somente leitura. Não conecta a ``GET /demand``, não altera
cobertura nem UI. Reusa ``get_latest_batch`` + ``list_batch_records_for_compare``.
"""

from __future__ import annotations

from typing import Any

from production_control_app.core.security import (
    PC_ACCESS,
    PC_DEMAND_VIEW,
    PC_MYWEG_NEEDS_VIEW,
    PC_VIEW_FILIAL_02,
    can,
)
from production_control_app.domain.errors import (
    BranchAccessDenied,
    InvalidBranch,
    MyWegNeedsBatchNotFound,
)
from production_control_app.domain.myweg_demand_source_contract import (
    DEMAND_SOURCE_BRANCH,
    SOURCE_MYWEG,
)
from production_control_app.domain.myweg_needs_contract import ALLOWED_BRANCH, FORBIDDEN_BRANCH
from production_control_app.domain.ports.myweg_needs_repository import MyWegNeedsRepositoryPort
from production_control_app.domain.services.myweg_demand_projection import (
    project_myweg_demand_lines,
    summarize_projection,
)


class MyWegDemandSourceService:
    def __init__(self, repository: MyWegNeedsRepositoryPort) -> None:
        self._repository = repository

    def project_latest(
        self,
        user: object | None,
        *,
        branch: str,
        require_demand_permission: bool = True,
    ) -> dict[str, Any]:
        """Monta a projeção interna da última coleta MyWEG da filial 02.

        ``require_demand_permission`` permanece True por padrão: a origem só deve
        ser consumida por quem já pode ver Demanda + Necessidades WEG. Em testes
        unitários do projetor puro, use o domínio diretamente.
        """
        code = str(branch or "").strip()
        if code == FORBIDDEN_BRANCH:
            raise InvalidBranch(
                "A origem MyWEG para Demanda não se aplica à filial 01."
            )
        if code != DEMAND_SOURCE_BRANCH:
            raise InvalidBranch(f"Filial inválida para origem MyWEG Demanda: {branch!r}.")

        self._assert_can_project(user, require_demand_permission=require_demand_permission)

        batch = self._repository.get_latest_batch()
        if batch is None:
            raise MyWegNeedsBatchNotFound("Nenhuma coleta MyWEG aceita encontrada.")

        batch_branch = str(batch.get("branch") or "").strip()
        if batch_branch and batch_branch != ALLOWED_BRANCH:
            raise MyWegNeedsBatchNotFound(
                "A última coleta MyWEG não pertence à filial 02."
            )

        batch_id = str(batch.get("id") or "").strip()
        if not batch_id:
            raise MyWegNeedsBatchNotFound("Coleta MyWEG sem identificador.")

        rows = self._repository.list_batch_records_for_compare(batch_id=batch_id)
        lines = project_myweg_demand_lines(
            rows,
            batch_id=batch_id,
            collected_at=batch.get("collected_at"),
            branch=ALLOWED_BRANCH,
        )
        return {
            "source": SOURCE_MYWEG,
            "branch": ALLOWED_BRANCH,
            "wired_to_demand_endpoint": False,
            "batch": {
                "id": batch_id,
                "collection_id": batch.get("collection_id"),
                "collected_at": batch.get("collected_at"),
                "imported_at": batch.get("imported_at"),
                "collection_date": batch.get("collection_date"),
                "record_count": int(batch.get("record_count") or 0),
                "status": batch.get("status"),
            },
            "items": [line.to_dict() for line in lines],
            "summary": summarize_projection(lines),
        }

    @staticmethod
    def _assert_can_project(
        user: object | None,
        *,
        require_demand_permission: bool,
    ) -> None:
        if not can(user, PC_ACCESS):
            raise PermissionError("Você não tem permissão para acessar o Portal PCP.")
        if not can(user, PC_MYWEG_NEEDS_VIEW):
            raise PermissionError(
                "Você não tem permissão para consultar Necessidades WEG."
            )
        if not can(user, PC_VIEW_FILIAL_02):
            raise BranchAccessDenied("Sem permissão para a filial 02.")
        if require_demand_permission and not can(user, PC_DEMAND_VIEW):
            raise PermissionError("Você não tem permissão para ver a demanda.")
