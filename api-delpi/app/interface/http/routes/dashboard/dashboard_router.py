from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query

from delpi_auth.authorization import require_any_permission

from app.application.security.api_delpi_permissions import (
    DASHBOARD_COMMERCIAL_VIEW,
    DASHBOARD_ENGINEERING_VIEW,
    DASHBOARD_FINANCIAL_VIEW,
    DASHBOARD_HR_VIEW,
    DASHBOARD_LMPS_VIEW,
    DASHBOARD_PRODUCTION_VIEW,
    DASHBOARD_QUALITY_VIEW,
    DASHBOARD_SUPPLIES_VIEW,
    API_DELPI_ACCESS,
    API_DELPI_QUALITY_ACCESS,
)
from app.application.services.strategic_indicators.dashboard_department_idd_service import (
    get_dashboard_department_idd_service,
)
from app.application.services.strategic_indicators.dashboard_department_indicators_service import (
    get_dashboard_department_indicators_service,
)
from app.application.services.strategic_indicators.dashboard_si_indicator_metric_service import (
    get_dashboard_si_indicator_metric_service,
)
from app.application.services.strategic_indicators.si_indicator_tv_catalog import (
    load_si_indicator_tv_catalog,
    locale_labels,
    operation_id_for,
    path_for,
)
from app.interface.http.openapi_agent_metadata import (
    DASHBOARD_DEPARTMENT_IDD,
    DASHBOARD_DEPARTMENT_INDICATORS,
    DASHBOARD_DEPARTMENTS_INDICATORS,
    agent_route,
)
from app.interface.http.query_param_enums import (
    BRANCH_QUERY_OPTIONAL,
    SI_DEPARTMENT_ID_QUERY_OPTIONAL,
    SI_DEPARTMENT_ID_QUERY_REQUIRED,
    SI_DEPARTMENT_ID_VALUES,
)
from app.interface.http.route_response_helpers import api_delpi_success

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])

DASHBOARD_IDD_ACCESS = sorted(
    {
        API_DELPI_ACCESS,
        API_DELPI_QUALITY_ACCESS,
        DASHBOARD_COMMERCIAL_VIEW,
        DASHBOARD_ENGINEERING_VIEW,
        DASHBOARD_FINANCIAL_VIEW,
        DASHBOARD_HR_VIEW,
        DASHBOARD_LMPS_VIEW,
        DASHBOARD_PRODUCTION_VIEW,
        DASHBOARD_QUALITY_VIEW,
        DASHBOARD_SUPPLIES_VIEW,
    }
)

_ALLOWED_DEPARTMENT_IDS = frozenset(SI_DEPARTMENT_ID_VALUES)

_DEPARTMENT_INDICATOR_FIELDS = {
    "department_id": "Departamento",
    "department_name": "Nome do departamento",
    "idd": "IDD",
    "score": "Nota",
    "classification": "Classificação",
    "indicators": "Indicadores",
    "indicator_id": "Indicador",
    "name": "Nome do indicador",
    "goals": "Metas",
    "realized": "Realizado",
    "goal_value": "Meta",
    "value": "Valor realizado",
    "gap": "Gap",
    "weight_pct": "Peso (%)",
}


def _normalize_department_id(department_id: str) -> str:
    normalized_id = department_id.strip().lower()
    if normalized_id not in _ALLOWED_DEPARTMENT_IDS:
        raise HTTPException(
            status_code=422,
            detail="department_id inválido para consulta de IDD departamental.",
        )
    return normalized_id


@router.get("/department-idd", **DASHBOARD_DEPARTMENT_IDD)
@require_any_permission(DASHBOARD_IDD_ACCESS)
def get_dashboard_department_idd(
    department_id: str = SI_DEPARTMENT_ID_QUERY_REQUIRED(),
    competence: str | None = Query(
        default=None,
        description="Reference month as YYYY-MM.",
    ),
    start_date: str | None = Query(
        default=None,
        description="Period start (YYYY-MM-DD).",
    ),
    end_date: str | None = Query(
        default=None,
        description="Period end (YYYY-MM-DD).",
    ),
    branch: str | None = BRANCH_QUERY_OPTIONAL(),
):
    normalized_id = _normalize_department_id(department_id)

    item = get_dashboard_department_idd_service().get_department_idd(
        department_id=normalized_id,
        start_date=start_date,
        end_date=end_date,
        branch=branch,
        competence=competence,
    )

    return api_delpi_success(
        {"item": item},
        operation_id=DASHBOARD_DEPARTMENT_IDD["operation_id"],
        entity="dashboard_department_idd",
        shape="scalar",
        message="IDD departamental consultado com sucesso",
    )


@router.get("/department-indicators", **DASHBOARD_DEPARTMENT_INDICATORS)
@require_any_permission(DASHBOARD_IDD_ACCESS)
def get_dashboard_department_indicators(
    department_id: str = SI_DEPARTMENT_ID_QUERY_REQUIRED(),
    competence: str | None = Query(
        default=None,
        description="Reference month as YYYY-MM.",
    ),
    start_date: str | None = Query(
        default=None,
        description="Period start (YYYY-MM-DD).",
    ),
    end_date: str | None = Query(
        default=None,
        description="Period end (YYYY-MM-DD).",
    ),
    branch: str | None = BRANCH_QUERY_OPTIONAL(),
):
    normalized_id = _normalize_department_id(department_id)

    item = get_dashboard_department_indicators_service().get_department_indicators(
        department_id=normalized_id,
        start_date=start_date,
        end_date=end_date,
        branch=branch,
        competence=competence,
    )

    return api_delpi_success(
        {"item": item},
        operation_id=DASHBOARD_DEPARTMENT_INDICATORS["operation_id"],
        entity="dashboard_department_indicators",
        shape="playbook_report",
        message="IDD, metas e realizado do departamento consultados com sucesso",
        fields=_DEPARTMENT_INDICATOR_FIELDS,
    )


@router.get("/departments-indicators", **DASHBOARD_DEPARTMENTS_INDICATORS)
@require_any_permission(DASHBOARD_IDD_ACCESS)
def get_dashboard_departments_indicators(
    competence: str | None = Query(
        default=None,
        description="Reference month as YYYY-MM.",
    ),
    start_date: str | None = Query(
        default=None,
        description="Period start (YYYY-MM-DD).",
    ),
    end_date: str | None = Query(
        default=None,
        description="Period end (YYYY-MM-DD).",
    ),
    branch: str | None = BRANCH_QUERY_OPTIONAL(),
    department_id: str | None = SI_DEPARTMENT_ID_QUERY_OPTIONAL(),
):
    normalized_id = None
    if department_id is not None and department_id.strip():
        normalized_id = _normalize_department_id(department_id)

    payload = get_dashboard_department_indicators_service().list_departments_indicators(
        start_date=start_date,
        end_date=end_date,
        branch=branch,
        competence=competence,
        department_id=normalized_id,
    )

    return api_delpi_success(
        payload,
        operation_id=DASHBOARD_DEPARTMENTS_INDICATORS["operation_id"],
        entity="dashboard_departments_indicators",
        shape="playbook_report",
        message="Departamentos com IDD, metas e realizado consultados com sucesso",
        fields=_DEPARTMENT_INDICATOR_FIELDS,
    )


_SI_INDICATOR_SCALAR_FIELDS = {
    "indicator_id": "Indicador",
    "source_key": "Chave da fonte",
    "name": "Nome",
    "department_id": "Departamento",
    "value": "Valor",
    "has_value": "Possui valor",
    "realized": "Realizado",
    "comparable_goal": "Meta comparável",
    "goal_value": "Meta",
    "goal_label": "Rótulo da meta",
    "goals": "Metas",
    "value_unit": "Unidade",
    "value_prefix": "Prefixo",
    "value_suffix": "Sufixo",
    "value_decimals": "Casas decimais",
}


def _register_si_indicator_scalar_routes() -> None:
    """Registra N×2 rotas escalares (realizado/meta) a partir do catálogo SI."""

    for row in load_si_indicator_tv_catalog():
        indicator_id = row["indicator_id"]
        name = row["name"]

        for kind in ("realized", "meta"):
            op_id = operation_id_for(indicator_id, kind)
            route_path = path_for(indicator_id, kind)
            labels = locale_labels(name, kind)
            entity = (
                "dashboard_si_indicator_realized"
                if kind == "realized"
                else "dashboard_si_indicator_meta"
            )
            message = (
                f"{name} — realizado consultado com sucesso"
                if kind == "realized"
                else f"{name} — meta consultada com sucesso"
            )
            meta = agent_route(
                summary=labels["en"]["summary"],
                description=labels["en"]["description"],
                operation_id=op_id,
            )

            def _make_handler(
                *,
                closed_path: str,
                closed_meta: dict,
                closed_indicator_id: str,
                closed_kind: str,
                closed_op_id: str,
                closed_entity: str,
                closed_message: str,
            ):
                @router.get(closed_path, **closed_meta)
                @require_any_permission(DASHBOARD_IDD_ACCESS)
                def handler(
                    competence: str | None = Query(
                        default=None,
                        description="Reference month as YYYY-MM.",
                    ),
                    start_date: str | None = Query(
                        default=None,
                        description="Period start (YYYY-MM-DD).",
                    ),
                    end_date: str | None = Query(
                        default=None,
                        description="Period end (YYYY-MM-DD).",
                    ),
                    branch: str | None = BRANCH_QUERY_OPTIONAL(),
                ):
                    item = get_dashboard_si_indicator_metric_service().get_metric(
                        indicator_id=closed_indicator_id,
                        kind=closed_kind,  # type: ignore[arg-type]
                        start_date=start_date,
                        end_date=end_date,
                        branch=branch,
                        competence=competence,
                    )
                    if item is None:
                        raise HTTPException(
                            status_code=404,
                            detail=(
                                f"Indicador SI '{closed_indicator_id}' "
                                f"({closed_kind}) não encontrado."
                            ),
                        )
                    return api_delpi_success(
                        item,
                        operation_id=closed_op_id,
                        entity=closed_entity,
                        shape="scalar",
                        message=closed_message,
                        fields=_SI_INDICATOR_SCALAR_FIELDS,
                    )

                return handler

            _make_handler(
                closed_path=route_path,
                closed_meta=meta,
                closed_indicator_id=indicator_id,
                closed_kind=kind,
                closed_op_id=op_id,
                closed_entity=entity,
                closed_message=message,
            )


_register_si_indicator_scalar_routes()
