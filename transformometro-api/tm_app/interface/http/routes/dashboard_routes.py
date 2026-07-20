from __future__ import annotations

import logging

from fastapi import APIRouter, Query, Request
from fastapi.responses import Response

from tm_app.application.services.dashboard_alerts_service import DashboardAlertsService
from tm_app.application.services.dashboard_export_service import DashboardExportService
from tm_app.application.services.dashboard_live_service import DashboardLiveService
from tm_app.application.services.dashboard_recalc_service import DashboardRecalcService
from tm_app.application.services.dashboard_snapshot_read_service import (
    DashboardSnapshotReadService,
)
from tm_app.application.services.transformometro_realtime_notify import notify_catalog_updated
from tm_app.core.auth_actor import actor_from_request
from tm_app.core.errors import format_api_error
from tm_app.core.responses import fail, ok
from tm_app.core.serialize import rows_to_json
from tm_app.interface.http.filial_access_http import check_dashboard_filial_access

router = APIRouter(prefix="/transformometro/dashboard", tags=["Transformômetro Dashboard"])
logger = logging.getLogger(__name__)

_live = DashboardLiveService()
_snapshot = DashboardSnapshotReadService()


def _scope_error_response(
    request: Request,
    view: str | None,
    filial_id: str | None,
    setor_id: str | None,
):
    if err := check_dashboard_filial_access(
        request,
        view=view,
        filial_id=filial_id,
        setor_id=setor_id,
    ):
        return err
    return None


@router.post("/recalcular")
def recalcular_dashboard(
    request: Request,
    revisao_id: str | None = None,
    processo_id: str | None = None,
    competencia_inicio: str | None = None,
    competencia_fim: str | None = None,
):
    """Opcional: atualiza cache em `dashboard_calculos`. As rotas GET já calculam em tempo real."""
    try:
        result = DashboardRecalcService().recalculate(
            revisao_id=revisao_id,
            processo_id=processo_id,
            competencia_inicio=competencia_inicio,
            competencia_fim=competencia_fim,
        )
    except Exception as exc:
        logger.exception("dashboard_recalc_failed")
        return fail(format_api_error(exc), 500)

    user_id, _email, _name = actor_from_request(request)
    notify_catalog_updated(
        catalog_id="dashboard",
        action="recalcular",
        actor_user_id=user_id,
        payload={
            "revisao_id": revisao_id,
            "processo_id": processo_id,
            "mode": result.get("mode"),
        },
    )

    result["observacao"] = (
        "Cache materializado atualizado. Os endpoints GET do dashboard não dependem deste passo."
    )
    if result.get("mode") == "incremental":
        return ok(result, "Cache do dashboard atualizado (incremental).")
    return ok(result, "Cache do dashboard atualizado (completo).")


@router.get(
    "/snapshot/meta",
    operation_id="get_dashboard_snapshot_meta",
    summary="Metadados do cache materializado do dashboard",
    description=(
        "Retorna contagem de linhas e `latest_calculated_at` de `dashboard_calculos`. "
        "Use antes de consultas analíticas para verificar se o cache está populado."
    ),
    tags=["Transformômetro Snapshot"],
)
def dashboard_snapshot_meta():
    return ok(
        _snapshot.meta(),
        "Metadados do cache materializado (dashboard_calculos).",
    )


@router.get(
    "/snapshot/resumo",
    operation_id="get_dashboard_snapshot_resumo",
    summary="KPIs agregados a partir do cache materializado",
    description=(
        "Economia bruta/líquida, investimentos e horas economizadas somados em "
        "`dashboard_calculos`, com filtros opcionais de filial, setor e competência."
    ),
    tags=["Transformômetro Snapshot"],
)
def dashboard_snapshot_resumo(
    request: Request,
    view: str | None = Query(default=None),
    filial_id: str | None = None,
    setor_id: str | None = None,
    competencia_inicio: str | None = None,
    competencia_fim: str | None = None,
):
    if err := _scope_error_response(request, view, filial_id, setor_id):
        return err
    data = _snapshot.resumo(
        view=view,
        filial_id=filial_id,
        setor_id=setor_id,
        competencia_inicio=competencia_inicio,
        competencia_fim=competencia_fim,
    )
    return ok(data, "Resumo agregado a partir do cache materializado.")


@router.get(
    "/snapshot/processos",
    operation_id="get_dashboard_snapshot_processos",
    summary="Processos agregados por competência (view processo_competencia_snapshot)",
    description=(
        "Lista economia e investimento por processo e mês. Preferir esta rota para "
        "ranking, comparativos mensais e perguntas do tipo «quanto economizou o processo X»."
    ),
    tags=["Transformômetro Snapshot"],
)
def dashboard_snapshot_processos(
    request: Request,
    view: str | None = Query(default=None),
    filial_id: str | None = None,
    setor_id: str | None = None,
    familia_processo: str | None = None,
    processo_id: str | None = None,
    competencia_inicio: str | None = None,
    competencia_fim: str | None = None,
    limit: int = Query(default=200, ge=1, le=1000),
):
    if err := _scope_error_response(request, view, filial_id, setor_id):
        return err
    data = _snapshot.processos(
        view=view,
        filial_id=filial_id,
        setor_id=setor_id,
        familia_processo=familia_processo,
        processo_id=processo_id,
        competencia_inicio=competencia_inicio,
        competencia_fim=competencia_fim,
        limit=limit,
    )
    return ok(
        {"meta": data["meta"], "total": data["total"], "items": rows_to_json(data["items"])},
        "Processos agregados por competência (view processo_competencia_snapshot).",
    )


@router.get(
    "/snapshot/instancias",
    operation_id="get_dashboard_snapshot_instancias",
    summary="Instâncias operacionais (view instancia_operacional_snapshot)",
    description=(
        "Lista instâncias com economia diária, payback e data de implantação "
        "a partir da última competência materializada — leitura rápida para dashboard e integrações."
    ),
    tags=["Transformômetro Snapshot"],
)
def dashboard_snapshot_instancias(
    request: Request,
    view: str | None = Query(default=None),
    filial_id: str | None = None,
    setor_id: str | None = None,
    limit: int = Query(default=500, ge=1, le=5000),
):
    if err := _scope_error_response(request, view, filial_id, setor_id):
        return err
    data = _snapshot.instancias(
        view=view,
        filial_id=filial_id,
        setor_id=setor_id,
        limit=limit,
    )
    return ok(
        {"meta": data["meta"], "total": data["total"], "items": rows_to_json(data["items"])},
        "Instâncias operacionais (view instancia_operacional_snapshot).",
    )


@router.get(
    "/snapshot/linhas",
    operation_id="get_dashboard_snapshot_linhas",
    summary="Linhas detalhadas revisão × competência no cache",
    description=(
        "Detalhe fino de `dashboard_calculos` (revisão, cenário, KPIs mensais). "
        "Use quando precisar de breakdown por revisão ou auditoria linha a linha."
    ),
    tags=["Transformômetro Snapshot"],
)
def dashboard_snapshot_linhas(
    request: Request,
    view: str | None = Query(default=None),
    processo_id: str | None = None,
    revisao_id: str | None = None,
    filial_id: str | None = None,
    setor_id: str | None = None,
    competencia_inicio: str | None = None,
    competencia_fim: str | None = None,
    limit: int = Query(default=500, ge=1, le=2000),
):
    if err := _scope_error_response(request, view, filial_id, setor_id):
        return err
    data = _snapshot.linhas(
        view=view,
        processo_id=processo_id,
        revisao_id=revisao_id,
        filial_id=filial_id,
        setor_id=setor_id,
        competencia_inicio=competencia_inicio,
        competencia_fim=competencia_fim,
        limit=limit,
    )
    return ok(
        {"meta": data["meta"], "total": data["total"], "items": rows_to_json(data["items"])},
        "Linhas detalhadas do cache (revisão × competência).",
    )


@router.get("/resumo")
def dashboard_resumo(
    request: Request,
    view: str | None = Query(default=None),
    filial_id: str | None = None,
    setor_id: str | None = None,
    competencia_inicio: str | None = None,
    competencia_fim: str | None = None,
):
    if err := _scope_error_response(request, view, filial_id, setor_id):
        return err
    summary = _live.build_summary(
        view=view,
        filial_id=filial_id,
        setor_id=setor_id,
        competencia_inicio=competencia_inicio,
        competencia_fim=competencia_fim,
    )
    return ok(summary)


@router.get("/evolucao")
def dashboard_evolucao(
    request: Request,
    view: str | None = Query(default=None),
    filial_id: str | None = None,
    setor_id: str | None = None,
    competencia_inicio: str | None = None,
    competencia_fim: str | None = None,
):
    if err := _scope_error_response(request, view, filial_id, setor_id):
        return err
    rows = _live.query_evolucao(
        view=view,
        filial_id=filial_id,
        setor_id=setor_id,
        competencia_inicio=competencia_inicio,
        competencia_fim=competencia_fim,
    )
    return ok({"total": len(rows), "items": rows})


@router.get("/processos")
def dashboard_processos(
    request: Request,
    view: str | None = Query(default=None),
    filial_id: str | None = None,
    setor_id: str | None = None,
    competencia: str | None = None,
    competencia_inicio: str | None = None,
    competencia_fim: str | None = None,
    limit: int = Query(default=50, ge=1, le=200),
):
    if err := _scope_error_response(request, view, filial_id, setor_id):
        return err
    rows = _live.query_ranking_processos(
        view=view,
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
    request: Request,
    meses_consecutivos: int = Query(default=3, ge=1, le=24),
    view: str | None = Query(default=None),
    filial_id: str | None = None,
    setor_id: str | None = None,
    familia_processo: str | None = None,
    competencia_inicio: str | None = None,
    competencia_fim: str | None = None,
):
    if err := _scope_error_response(request, view, filial_id, setor_id):
        return err
    data = DashboardAlertsService(min_consecutive_months=meses_consecutivos).list_negative_savings_alerts(
        view=view,
        filial_id=filial_id,
        setor_id=setor_id,
        familia_processo=familia_processo,
        competencia_inicio=competencia_inicio,
        competencia_fim=competencia_fim,
    )
    return ok(data, "Alertas de economia líquida negativa.")


@router.get("/vencimentos")
def dashboard_vencimentos(
    request: Request,
    dias: int = Query(default=90, ge=1, le=365),
    incluir_vencidas: bool = Query(default=True),
    view: str | None = Query(default=None),
    filial_id: str | None = None,
    setor_id: str | None = None,
    familia_processo: str | None = None,
):
    if err := _scope_error_response(request, view, filial_id, setor_id):
        return err
    data = _live.list_vencimentos(
        dias=dias,
        incluir_vencidas=incluir_vencidas,
        view=view,
        filial_id=filial_id,
        setor_id=setor_id,
        familia_processo=familia_processo,
    )
    return ok(data, "Revisões prestes a vencer e vencidas.")


@router.get("/por-familia")
def dashboard_por_familia(
    request: Request,
    view: str | None = Query(default=None),
    filial_id: str | None = None,
    setor_id: str | None = None,
    competencia_inicio: str | None = None,
    competencia_fim: str | None = None,
):
    if err := _scope_error_response(request, view, filial_id, setor_id):
        return err
    rows = _live.query_resumo_por_familia(
        view=view,
        filial_id=filial_id,
        setor_id=setor_id,
        competencia_inicio=competencia_inicio,
        competencia_fim=competencia_fim,
    )
    return ok({"total": len(rows), "items": rows_to_json(rows)})


@router.get("/export.csv")
def dashboard_export_csv(
    request: Request,
    view: str | None = Query(default=None),
    filial_id: str | None = None,
    setor_id: str | None = None,
    familia_processo: str | None = None,
    competencia_inicio: str | None = None,
    competencia_fim: str | None = None,
):
    if err := _scope_error_response(request, view, filial_id, setor_id):
        return err
    content = DashboardExportService().build_csv(
        view=view,
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
    request: Request,
    view: str | None = Query(default=None),
    filial_id: str | None = None,
    setor_id: str | None = None,
    familia_processo: str | None = None,
    competencia_inicio: str | None = None,
    competencia_fim: str | None = None,
):
    if err := _scope_error_response(request, view, filial_id, setor_id):
        return err
    content = DashboardExportService().build_excel_html(
        view=view,
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
