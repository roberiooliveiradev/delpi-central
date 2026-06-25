"""Regressão de seleção — rotas PAC Qualidade (api-delpi /quality/action-plans)."""

from __future__ import annotations

from typing import Any


def _pac_case(
    case_id: str,
    message: str,
    *,
    action_id: str,
    path: str,
    operation_id: str,
    summary: str,
    extra_actions: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    actions = [
        {
            "actionId": action_id,
            "method": "GET",
            "path": path,
            "operationId": operation_id,
            "summary": summary,
            "parametersSchema": [],
        }
    ]

    if extra_actions:
        actions.extend(extra_actions)

    return {
        "id": case_id,
        "message": message,
        "actions": actions,
        "expected_action_id": action_id,
    }


_PAC_LIST_DECOY = {
    "actionId": "pac-list-plans",
    "method": "GET",
    "path": "/quality/action-plans",
    "operationId": "list_quality_action_plans",
    "summary": "Lista paginada — plano de ação qualidade",
    "parametersSchema": [{"name": "page"}, {"name": "page_size"}],
}

_PAC_DASHBOARD_DECOY = {
    "actionId": "pac-dashboard",
    "method": "GET",
    "path": "/quality/action-plans/dashboard",
    "operationId": "get_quality_action_plans_dashboard",
    "summary": "Indicador — dashboard plano de ação qualidade",
    "parametersSchema": [],
}

_QUALITY_NC_DECOY = {
    "actionId": "quality-nonconformities",
    "method": "GET",
    "path": "/quality/nonconformities",
    "operationId": "list_nonconformities",
    "summary": "Lista paginada — não conformidade",
    "parametersSchema": [{"name": "date_start"}, {"name": "date_end"}],
}


PAC_QUALITY_SELECTION_CASES: list[dict[str, Any]] = [
    _pac_case(
        "PAC01",
        "Mostre o dashboard dos planos de ação de qualidade PAC",
        action_id="pac-dashboard",
        path="/quality/action-plans/dashboard",
        operation_id="get_quality_action_plans_dashboard",
        summary="Indicador — dashboard plano de ação qualidade",
        extra_actions=[_PAC_LIST_DECOY, _QUALITY_NC_DECOY],
    ),
    _pac_case(
        "PAC02",
        "Liste os planos de ação de qualidade abertos",
        action_id="pac-list-plans",
        path="/quality/action-plans",
        operation_id="list_quality_action_plans",
        summary="Lista paginada — plano de ação qualidade",
        extra_actions=[_PAC_DASHBOARD_DECOY, _QUALITY_NC_DECOY],
    ),
    _pac_case(
        "PAC03",
        "Quais planos PAC estão com ações atrasadas?",
        action_id="pac-overdue",
        path="/quality/action-plans/overdue",
        operation_id="list_quality_action_plans_overdue",
        summary="Lista paginada — plano de ação qualidade atrasado",
        extra_actions=[_PAC_LIST_DECOY, _PAC_DASHBOARD_DECOY],
    ),
    _pac_case(
        "PAC04",
        "Quais modos de falha estão se repetindo nos planos de ação?",
        action_id="pac-recurrence",
        path="/quality/action-plans/recurrence",
        operation_id="list_quality_action_plans_recurrence",
        summary="Lista paginada — recorrência plano de ação qualidade",
        extra_actions=[_PAC_LIST_DECOY, _QUALITY_NC_DECOY],
    ),
    _pac_case(
        "PAC05",
        "Busque casos similares no plano de ação de qualidade",
        action_id="pac-similar-cases",
        path="/quality/action-plans/{plan_id}/similar-cases",
        operation_id="get_quality_action_plan_similar_cases",
        summary="Análise consolidada — casos similares plano de ação qualidade",
        extra_actions=[_PAC_LIST_DECOY],
    ),
]

PAC_QUALITY_SELECTION_INDEX = [
    {
        "id": case["id"],
        "message": case["message"],
        "expected_action_id": case["expected_action_id"],
    }
    for case in PAC_QUALITY_SELECTION_CASES
]
