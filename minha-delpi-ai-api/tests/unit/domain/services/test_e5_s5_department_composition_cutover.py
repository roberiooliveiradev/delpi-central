"""E5.S5 — department composition cutover: goals + retrieval (sem routeId authority)."""

from __future__ import annotations

from app.domain.services.chat_department_meta_composition_planning_service import (
    ChatDepartmentMetaCompositionPlanningService,
)


def _action(
    action_id: str,
    *,
    when_to_use: str,
    summary: str,
    path: str,
) -> dict:
    return {
        "actionId": action_id,
        "whenToUse": when_to_use,
        "summary": summary,
        "description": summary,
        "path": path,
        "method": "GET",
    }


def _shared_catalog(*, indicators_path: str = "/dashboard/department-indicators") -> dict[str, dict]:
    return {
        "ext.dashboard.indicators": _action(
            "ext.dashboard.indicators",
            when_to_use="Use for «metas», «realizado» or department indicators.",
            summary="Metas e realizado",
            path=indicators_path,
        ),
        "ext.dashboard.idd": _action(
            "ext.dashboard.idd",
            when_to_use="Use for «idd» or «indicadores estrategicos».",
            summary="IDD estratégico",
            path="/dashboard/department-idd",
        ),
        "ext.kpi.financial_ebitda": _action(
            "ext.kpi.financial_ebitda",
            when_to_use="Use for financial «ebitda» KPI.",
            summary="Financial EBITDA",
            path="/kpi/financial/ebitda",
        ),
        "ext.kpi.commercial_rol": _action(
            "ext.kpi.commercial_rol",
            when_to_use="Use for commercial «rol» KPI.",
            summary="Commercial ROL",
            path="/kpi/commercial/rol",
        ),
        "ext.kpi.quality_ppm": _action(
            "ext.kpi.quality_ppm",
            when_to_use="Use for quality «ppm» KPI.",
            summary="Quality PPM",
            path="/kpi/quality/ppm",
        ),
        "ext.kpi.production_oee": _action(
            "ext.kpi.production_oee",
            when_to_use="Use for production «oee» KPI.",
            summary="Production OEE",
            path="/kpi/production/oee",
        ),
    }


_DEPT_CASES = (
    ("financial", "painel de indicadores do financeiro", "ext.kpi.financial_ebitda"),
    ("commercial", "painel de indicadores do comercial", "ext.kpi.commercial_rol"),
    ("quality", "painel de indicadores da qualidade", "ext.kpi.quality_ppm"),
    ("production", "painel de indicadores da produção", "ext.kpi.production_oee"),
)


def test_e5_s5_cutover_flags():
    goals = ChatDepartmentMetaCompositionPlanningService.goals_for_department(
        "financial",
        mode="compose",
    )
    assert goals
    assert goals[0].goal_id == "dept_meta_indicators"


def test_e5_s5_department_families_compose_without_route_ids():
    catalog = _shared_catalog()
    for department_id, message, flagship_action in _DEPT_CASES:
        planned = ChatDepartmentMetaCompositionPlanningService.plan_goal_driven(
            message=message,
            allowed_action_ids=list(catalog),
            actions_by_id=catalog,
            max_calls=5,
        )
        assert ChatDepartmentMetaCompositionPlanningService.resolve_department_id(
            message
        ) == department_id
        assert len(planned) >= 2
        action_ids = [item["arguments"]["actionId"] for item in planned]
        assert "ext.dashboard.indicators" in action_ids
        assert "ext.dashboard.idd" in action_ids
        assert flagship_action in action_ids
        assert all(item["metadata"].get("departmentMetaGoalDriven") for item in planned)
        assert all("routeId" not in (item.get("arguments") or {}) for item in planned)


def test_e5_s5_provider_path_rename_still_selects_by_semantics():
    renamed = _shared_catalog(
        indicators_path="/v2/providers/acme/dept-meta-panel",
    )
    renamed["ext.dashboard.indicators"]["actionId"] = "acme.dept.meta_panel"
    renamed["acme.dept.meta_panel"] = renamed.pop("ext.dashboard.indicators")

    planned = ChatDepartmentMetaCompositionPlanningService.plan_goal_driven(
        message="qual a meta para financeiro desse mês?",
        allowed_action_ids=list(renamed),
        actions_by_id=renamed,
        max_calls=3,
    )
    assert len(planned) == 1
    assert planned[0]["arguments"]["actionId"] == "acme.dept.meta_panel"
    assert planned[0]["metadata"]["path"] == "/v2/providers/acme/dept-meta-panel"
    assert planned[0]["arguments"]["parameters"]["department_id"] == "financial"


def test_e5_s5_does_not_use_legacy_route_id_authority():
    goals = ChatDepartmentMetaCompositionPlanningService.goals_for_department(
        "financial",
        mode="compose",
    )
    assert all(not hasattr(goal, "route_id") for goal in goals)
    assert "dashboardDepartmentIndicators" not in {
        hint for goal in goals for hint in goal.query_hints
    }
