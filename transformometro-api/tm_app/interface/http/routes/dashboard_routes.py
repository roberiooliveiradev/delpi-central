from __future__ import annotations

from fastapi import APIRouter, Query
from fastapi.responses import Response

from tm_app.application.services.dashboard_alerts_service import DashboardAlertsService
from tm_app.application.services.dashboard_export_service import DashboardExportService
from tm_app.application.services.dashboard_live_service import DashboardLiveService
from tm_app.application.services.dashboard_recalc_service import DashboardRecalcService
from tm_app.core.responses import ok
from tm_app.core.serialize import rows_to_json

router = APIRouter(prefix="/transformometro/dashboard", tags=["Transformômetro Dashboard"])

_live = DashboardLiveService()


@router.post("/recalcular")
def recalcular_dashboard(
    revisao_id: str | None = None,
    processo_id: str | None = None,
    competencia_inicio: str | None = None,
    competencia_fim: str | None = None,
):
    """Opcional: atualiza cache em `dashboard_calculos`. As rotas GET já calculam em tempo real."""
    result = DashboardRecalcService().recalculate(
        revisao_id=revisao_id,
        processo_id=processo_id,
        competencia_inicio=competencia_inicio,
        competencia_fim=competencia_fim,
    )
    result["observacao"] = (
        "Cache materializado atualizado. Os endpoints GET do dashboard não dependem deste passo."
    )
    if result.get("mode") == "incremental":
        return ok(result, "Cache do dashboard atualizado (incremental).")
    return ok(result, "Cache do dashboard atualizado (completo).")


@router.get("/resumo")
def dashboard_resumo(
    filial_id: str | None = None,
    setor_id: str | None = None,
    competencia_inicio: str | None = None,
    competencia_fim: str | None = None,
):
    summary = _live.build_summary(
        filial_id=filial_id,
        setor_id=setor_id,
        competencia_inicio=competencia_inicio,
        competencia_fim=competencia_fim,
    )
    return ok(summary)


@router.get("/evolucao")
def dashboard_evolucao(
    filial_id: str | None = None,
    setor_id: str | None = None,
    competencia_inicio: str | None = None,
    competencia_fim: str | None = None,
):
    rows = _live.query_evolucao(
        filial_id=filial_id,
        setor_id=setor_id,
        competencia_inicio=competencia_inicio,
        competencia_fim=competencia_fim,
    )
    return ok({"total": len(rows), "items": rows})


@router.get("/processos")
def dashboard_processos(
    filial_id: str | None = None,
    setor_id: str | None = None,
    competencia: str | None = None,
    competencia_inicio: str | None = None,
    competencia_fim: str | None = None,
    limit: int = Query(default=50, ge=1, le=200),
):
    rows = _live.query_ranking_processos(
        filial_id=filial_id,
        setor_id=setor_id,
        competencia=competencia,
        competencia_inicio=competencia_inicio,
        competencia_fim=competencia_fim,
        limit=limit,
    )
    return ok({"total": len(rows), "items": rows_to_json(rows)})


@router.get("/alertas")
def dashboard_alertas(
    meses_consecutivos: int = Query(default=3, ge=1, le=24),
    filial_id: str | None = None,
    setor_id: str | None = None,
    familia_processo: str | None = None,
    competencia_inicio: str | None = None,
    competencia_fim: str | None = None,
):
    data = DashboardAlertsService(min_consecutive_months=meses_consecutivos).list_negative_savings_alerts(
        filial_id=filial_id,
        setor_id=setor_id,
        familia_processo=familia_processo,
        competencia_inicio=competencia_inicio,
        competencia_fim=competencia_fim,
    )
    return ok(data, "Alertas de economia líquida negativa.")


@router.get("/por-familia")
def dashboard_por_familia(
    filial_id: str | None = None,
    competencia_inicio: str | None = None,
    competencia_fim: str | None = None,
):
    rows = _live.query_resumo_por_familia(
        filial_id=filial_id,
        competencia_inicio=competencia_inicio,
        competencia_fim=competencia_fim,
    )
    return ok({"total": len(rows), "items": rows_to_json(rows)})


@router.get("/export.csv")
def dashboard_export_csv(
    filial_id: str | None = None,
    setor_id: str | None = None,
    familia_processo: str | None = None,
    competencia_inicio: str | None = None,
    competencia_fim: str | None = None,
):
    content = DashboardExportService().build_csv(
        filial_id=filial_id,
        setor_id=setor_id,
        familia_processo=familia_processo,
        competencia_inicio=competencia_inicio,
        competencia_fim=competencia_fim,
    )
    return Response(
        content=content,
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": 'attachment; filename="transformometro-dashboard.csv"'},
    )


@router.get("/export.xls")
def dashboard_export_excel(
    filial_id: str | None = None,
    setor_id: str | None = None,
    familia_processo: str | None = None,
    competencia_inicio: str | None = None,
    competencia_fim: str | None = None,
):
    content = DashboardExportService().build_excel_html(
        filial_id=filial_id,
        setor_id=setor_id,
        familia_processo=familia_processo,
        competencia_inicio=competencia_inicio,
        competencia_fim=competencia_fim,
    )
    return Response(
        content=content.encode("utf-8"),
        media_type="application/vnd.ms-excel; charset=utf-8",
        headers={"Content-Disposition": 'attachment; filename="transformometro-dashboard.xls"'},
    )
