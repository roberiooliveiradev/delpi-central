from __future__ import annotations

from app.application.dto.retrabalho.retrabalho_query_request import RetrabalhoQueryRequest
from app.domain.ports.retrabalho.retrabalho_repository_port import RetrabalhoRepositoryPort
from app.domain.quality.retrabalho.retrabalho_view_scope import RETRABALHO_HORAS_IMPRODUTIVAS_VIEW


class GetRetrabalhoHealthUseCase:
    def __init__(self, repository: RetrabalhoRepositoryPort) -> None:
        self._repository = repository

    def execute(self) -> dict:
        row = self._repository.check_health()
        return {
            "status": "ok" if row else "degraded",
            "view": RETRABALHO_HORAS_IMPRODUTIVAS_VIEW,
            "sampleFilial": row.get("filial") if row else None,
        }
