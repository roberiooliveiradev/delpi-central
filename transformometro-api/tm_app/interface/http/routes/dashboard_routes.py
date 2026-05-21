from __future__ import annotations

from fastapi import APIRouter, Query

from tm_app.application.services.dashboard_recalc_service import DashboardRecalcService
from tm_app.core.responses import ok
from tm_app.core.serialize import row_to_json, rows_to_json
from tm_app.domain.services.dashboard_calculator import DashboardCalculatorService
from tm_app.infrastructure.persistence.repositories.dashboard_data_repository import (
    DashboardCalculoRepository,
    DashboardDataRepository,
)

router = APIRouter(prefix="/transformometro/dashboard", tags=["Transformômetro Dashboard"])


@router.post("/recalcular")
def recalcular_dashboard():
    result = DashboardRecalcService().recalculate()
    return ok(result, "Dashboard recalculado.")


@router.get("/resumo")
def dashboard_resumo(
    filial_id: str | None = None,
    setor_id: str | None = None,
    competencia_inicio: str | None = None,
    competencia_fim: str | None = None,
):
    row = DashboardCalculoRepository().query_resumo(
        filial_id=filial_id,
        setor_id=setor_id,
        competencia_inicio=competencia_inicio,
        competencia_fim=competencia_fim,
    )
    if not row or DashboardCalculoRepository().count() == 0:
        raw = DashboardDataRepository().load_raw()
        summary = DashboardCalculatorService().build_summary(
            raw,
            filial_id=filial_id,
            start_date=competencia_inicio,
            end_date=competencia_fim,
        )
        return ok(summary)

    investimento = float(row.get("investimento_unico_total") or 0)
    economia_liquida = float(row.get("economia_liquida_total") or 0)
    roi_medio = 0.0
    if investimento > 0:
        roi_medio = (economia_liquida - investimento) / investimento

    return ok(
        {
            "solucoes_implementadas": int(row.get("solucoes_implementadas") or 0),
            "economia_liquida_total": float(row.get("economia_liquida_total") or 0),
            "economia_bruta_total": float(row.get("economia_bruta_total") or 0),
            "horas_economizadas_total": float(row.get("horas_economizadas_total") or 0),
            "investimento_unico_total": investimento,
            "custo_recorrente_total": float(row.get("custo_recorrente_total") or 0),
            "roi_medio": round(roi_medio, 4),
            "linhas_materializadas": DashboardCalculoRepository().count(),
        }
    )


@router.get("/evolucao")
def dashboard_evolucao(
    filial_id: str | None = None,
    setor_id: str | None = None,
    competencia_inicio: str | None = None,
    competencia_fim: str | None = None,
):
    rows = DashboardCalculoRepository().query_evolucao(
        filial_id=filial_id,
        setor_id=setor_id,
        competencia_inicio=competencia_inicio,
        competencia_fim=competencia_fim,
    )
    if rows:
        return ok({"total": len(rows), "items": rows_to_json(rows)})

    raw = DashboardDataRepository().load_raw()
    summary = DashboardCalculatorService().build_summary(
        raw,
        filial_id=filial_id,
        start_date=competencia_inicio,
        end_date=competencia_fim,
    )
    return ok({"total": len(summary.get("evolucao_mensal", [])), "items": summary["evolucao_mensal"]})


@router.get("/processos")
def dashboard_processos(
    filial_id: str | None = None,
    setor_id: str | None = None,
    competencia: str | None = None,
    limit: int = Query(default=50, ge=1, le=200),
):
    repo = DashboardCalculoRepository()
    if repo.count() > 0:
        rows = repo.query_ranking_processos(
            filial_id=filial_id,
            setor_id=setor_id,
            competencia=competencia,
            limit=limit,
        )
        return ok({"total": len(rows), "items": rows_to_json(rows)})

    raw = DashboardDataRepository().load_raw()
    items = DashboardCalculatorService().build_process_list(raw)
    if filial_id:
        items = [i for i in items if (i.get("filial_id") or "") == filial_id]
    if setor_id:
        items = [i for i in items if (i.get("setor_id") or "") == setor_id]
    return ok({"total": len(items), "items": items[:limit]})
