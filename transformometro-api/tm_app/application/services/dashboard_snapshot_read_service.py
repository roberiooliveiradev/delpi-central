from __future__ import annotations

from typing import Any

from tm_app.application.services.dashboard_live_service import DashboardLiveService
from tm_app.application.services.dashboard_view_scope_service import (
    DashboardScopeFilters,
    DashboardViewScopeService,
)
from tm_app.config import settings
from tm_app.infrastructure.persistence.repositories.dashboard_data_repository import (
    DashboardCalculoRepository,
)

_RESUMO_KEYS = (
    "solucoes_implementadas",
    "economia_bruta_total",
    "economia_liquida_total",
    "investimento_unico_total",
    "custo_recorrente_total",
    "custo_recursos_compartilhados_total",
    "investimento_total",
    "horas_economizadas_total",
)


class DashboardSnapshotReadService:
    """Leituras analíticas para chat e integrações.

    Fonte única = motor live (mesmo cálculo do dashboard) com ``DashboardQueryCache``.
    A tabela materializada legada ``dashboard_calculos`` só é usada como fast-path
    quando ``TM_DASHBOARD_PERSIST_CACHE`` está ligado e o cache está populado.
    """

    def __init__(self) -> None:
        self._repo = DashboardCalculoRepository()
        self._live = DashboardLiveService()
        self._scope = DashboardViewScopeService()

    def _use_persisted(self) -> bool:
        """True só quando o cache materializado deve alimentar as leituras."""
        if not settings.TM_DASHBOARD_PERSIST_CACHE:
            return False
        try:
            return self._repo.count() > 0
        except Exception:
            return False

    def meta(self) -> dict[str, Any]:
        persisted = self._use_persisted()
        base = {
            "aggregated_view": "processo_competencia_snapshot",
            "evolucao_view": "dashboard_competencia_evolucao",
            "instancia_view": "instancia_operacional_snapshot",
        }
        if persisted:
            return {
                **base,
                "mode": "persisted",
                "source": "dashboard_calculos",
                "row_count": self._repo.count(),
                "latest_calculated_at": self._repo.latest_calculated_at(),
            }
        return {
            **base,
            "mode": "live",
            "source": "cadastro_tempo_real",
            "row_count": None,
            "latest_calculated_at": None,
        }

    def _resolve(
        self,
        *,
        view: str | None = None,
        filial_id: str | None = None,
        setor_id: str | None = None,
    ) -> DashboardScopeFilters:
        return self._scope.resolve(view=view, filial_id=filial_id, setor_id=setor_id)

    def resumo(
        self,
        *,
        view: str | None = None,
        filial_id: str | None = None,
        setor_id: str | None = None,
        competencia_inicio: str | None = None,
        competencia_fim: str | None = None,
    ) -> dict[str, Any]:
        scope = self._resolve(view=view, filial_id=filial_id, setor_id=setor_id)
        if self._use_persisted():
            summary = self._repo.query_resumo(
                filial_id=scope.filial_id,
                setor_id=scope.setor_id,
                competencia_inicio=competencia_inicio,
                competencia_fim=competencia_fim,
            )
        else:
            full = self._live.build_summary(
                filial_id=scope.filial_id,
                setor_id=scope.setor_id,
                competencia_inicio=competencia_inicio,
                competencia_fim=competencia_fim,
            )
            summary = {key: full.get(key, 0) for key in _RESUMO_KEYS}
        return {
            "meta": {**self.meta(), "scope": self._scope.scope_meta(scope)},
            "summary": summary,
        }

    def processos(
        self,
        *,
        view: str | None = None,
        filial_id: str | None = None,
        setor_id: str | None = None,
        familia_processo: str | None = None,
        processo_id: str | None = None,
        competencia_inicio: str | None = None,
        competencia_fim: str | None = None,
        limit: int = 200,
    ) -> dict[str, Any]:
        scope = self._resolve(view=view, filial_id=filial_id, setor_id=setor_id)
        if self._use_persisted():
            rows = self._repo.query_processo_competencia_snapshot(
                filial_id=scope.filial_id,
                setor_id=scope.setor_id,
                familia_processo=familia_processo,
                processo_id=processo_id,
                competencia_inicio=competencia_inicio,
                competencia_fim=competencia_fim,
                limit=limit,
            )
        else:
            rows = self._live.processo_competencia_rows(
                filial_id=scope.filial_id,
                setor_id=scope.setor_id,
                familia_processo=familia_processo,
                processo_id=processo_id,
                competencia_inicio=competencia_inicio,
                competencia_fim=competencia_fim,
            )[:limit]
        return {
            "meta": {**self.meta(), "scope": self._scope.scope_meta(scope)},
            "total": len(rows),
            "items": rows,
        }

    def linhas(
        self,
        *,
        view: str | None = None,
        processo_id: str | None = None,
        revisao_id: str | None = None,
        filial_id: str | None = None,
        setor_id: str | None = None,
        competencia_inicio: str | None = None,
        competencia_fim: str | None = None,
        limit: int = 500,
    ) -> dict[str, Any]:
        scope = self._resolve(view=view, filial_id=filial_id, setor_id=setor_id)
        if self._use_persisted():
            rows = self._repo.query_linhas(
                processo_id=processo_id,
                revisao_id=revisao_id,
                filial_id=scope.filial_id,
                setor_id=scope.setor_id,
                competencia_inicio=competencia_inicio,
                competencia_fim=competencia_fim,
                limit=limit,
            )
        else:
            rows = self._live_linhas(
                scope=scope,
                processo_id=processo_id,
                revisao_id=revisao_id,
                competencia_inicio=competencia_inicio,
                competencia_fim=competencia_fim,
                limit=limit,
            )
        return {
            "meta": {**self.meta(), "scope": self._scope.scope_meta(scope)},
            "total": len(rows),
            "items": rows,
        }

    def instancias(
        self,
        *,
        view: str | None = None,
        filial_id: str | None = None,
        setor_id: str | None = None,
        limit: int = 500,
    ) -> dict[str, Any]:
        scope = self._resolve(view=view, filial_id=filial_id, setor_id=setor_id)
        if self._use_persisted():
            rows = self._repo.query_instancias_operacionais(
                filial_id=scope.filial_id,
                setor_id=scope.setor_id,
                limit=limit,
            )
        else:
            items = self._live.list_processos_calculados(
                filial_id=scope.filial_id,
                setor_id=scope.setor_id,
            )
            rows = [_map_instancia_live(item) for item in items][:limit]
        return {
            "meta": {**self.meta(), "scope": self._scope.scope_meta(scope)},
            "total": len(rows),
            "items": rows,
        }

    def _live_linhas(
        self,
        *,
        scope: DashboardScopeFilters,
        processo_id: str | None,
        revisao_id: str | None,
        competencia_inicio: str | None,
        competencia_fim: str | None,
        limit: int,
    ) -> list[dict[str, Any]]:
        rows = self._live.calculation_rows(
            filial_id=scope.filial_id,
            setor_id=scope.setor_id,
            competencia_inicio=competencia_inicio,
            competencia_fim=competencia_fim,
        )
        raw = self._live.load_filtered_raw(
            filial_id=scope.filial_id,
            setor_id=scope.setor_id,
        )
        processos_by_id = {
            str(p.get("processo_id")): p for p in raw.processos if p.get("processo_id")
        }
        mapped: list[dict[str, Any]] = []
        for row in rows:
            if processo_id and str(row.get("processo_id") or "") != str(processo_id):
                continue
            if revisao_id and str(row.get("revisao_id") or "") != str(revisao_id):
                continue
            proc = processos_by_id.get(str(row.get("processo_id") or ""), {})
            mapped.append(_map_linha_live(row, proc))
        mapped.sort(
            key=lambda r: (str(r.get("competencia") or ""), str(r.get("codigo_processo") or "")),
            reverse=True,
        )
        return mapped[:limit]


def _map_linha_live(row: dict[str, Any], proc: dict[str, Any]) -> dict[str, Any]:
    investimento_total = (
        float(row.get("investimento_unico_mes") or 0)
        + float(row.get("custo_recorrente_mes") or 0)
        + float(row.get("custo_recursos_compartilhados_mes") or 0)
    )
    return {
        "dashboard_calculo_id": None,
        "revisao_id": row.get("revisao_id"),
        "processo_id": row.get("processo_id"),
        "codigo_processo": proc.get("codigo_processo"),
        "nome_processo": proc.get("nome_processo"),
        "competencia": row.get("competencia"),
        "instancia_id": row.get("instancia_id"),
        "filial_id": row.get("codigo_filial") or proc.get("filial_id"),
        "setor_id": row.get("codigo_setor") or proc.get("setor_id"),
        "cenario_tipo": row.get("cenario_tipo"),
        "revisao_ativa": row.get("revisao_ativa"),
        "economia_bruta": row.get("economia_bruta"),
        "economia_liquida_mes": row.get("economia_liquida_mes"),
        "investimento_unico_mes": row.get("investimento_unico_mes"),
        "custo_recorrente_mes": row.get("custo_recorrente_mes"),
        "custo_recursos_compartilhados_mes": row.get("custo_recursos_compartilhados_mes"),
        "investimento_total_mes": round(investimento_total, 2),
        "horas_economizadas_mes": row.get("horas_economizadas_mes"),
        "calculated_at": None,
    }


def _map_instancia_live(item: dict[str, Any]) -> dict[str, Any]:
    return {
        "instancia_id": item.get("instancia_id"),
        "processo_id": item.get("processo_id"),
        "codigo_processo": item.get("codigo_processo"),
        "nome_processo": item.get("nome_processo"),
        "status_processo": item.get("status_processo"),
        "todas_filiais_ativas": None,
        "filial_id": item.get("filial_id"),
        "nome_filial": None,
        "setor_id": item.get("setor_id"),
        "competencia_referencia": None,
        "economia_diaria": item.get("economia_diaria"),
        "payback_meses": item.get("payback_meses"),
        "data_implantacao": item.get("data_implantacao"),
    }
