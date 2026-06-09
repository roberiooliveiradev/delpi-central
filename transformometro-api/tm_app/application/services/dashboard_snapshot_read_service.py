from __future__ import annotations

from typing import Any

from tm_app.infrastructure.persistence.repositories.dashboard_data_repository import (
    DashboardCalculoRepository,
)


class DashboardSnapshotReadService:
    """Leituras sobre ``dashboard_calculos`` / ``processo_competencia_snapshot`` para chat e integrações."""

    def __init__(self) -> None:
        self._repo = DashboardCalculoRepository()

    def meta(self) -> dict[str, Any]:
        return {
            "source": "dashboard_calculos",
            "row_count": self._repo.count(),
            "latest_calculated_at": self._repo.latest_calculated_at(),
            "aggregated_view": "processo_competencia_snapshot",
        }

    def resumo(
        self,
        *,
        filial_id: str | None = None,
        setor_id: str | None = None,
        competencia_inicio: str | None = None,
        competencia_fim: str | None = None,
    ) -> dict[str, Any]:
        summary = self._repo.query_resumo(
            filial_id=filial_id,
            setor_id=setor_id,
            competencia_inicio=competencia_inicio,
            competencia_fim=competencia_fim,
        )
        return {"meta": self.meta(), "summary": summary}

    def processos(
        self,
        *,
        filial_id: str | None = None,
        setor_id: str | None = None,
        familia_processo: str | None = None,
        processo_id: str | None = None,
        competencia_inicio: str | None = None,
        competencia_fim: str | None = None,
        limit: int = 200,
    ) -> dict[str, Any]:
        rows = self._repo.query_processo_competencia_snapshot(
            filial_id=filial_id,
            setor_id=setor_id,
            familia_processo=familia_processo,
            processo_id=processo_id,
            competencia_inicio=competencia_inicio,
            competencia_fim=competencia_fim,
            limit=limit,
        )
        return {"meta": self.meta(), "total": len(rows), "items": rows}

    def linhas(
        self,
        *,
        processo_id: str | None = None,
        revisao_id: str | None = None,
        filial_id: str | None = None,
        setor_id: str | None = None,
        competencia_inicio: str | None = None,
        competencia_fim: str | None = None,
        limit: int = 500,
    ) -> dict[str, Any]:
        rows = self._repo.query_linhas(
            processo_id=processo_id,
            revisao_id=revisao_id,
            filial_id=filial_id,
            setor_id=setor_id,
            competencia_inicio=competencia_inicio,
            competencia_fim=competencia_fim,
            limit=limit,
        )
        return {"meta": self.meta(), "total": len(rows), "items": rows}
