"""OpenAPI-first: whenNotToUse quoted examples steer retrieval/planner.

Uses a fictional external catalog (no DELPI path/operationId hardcode).
"""

from app.application.services.plan_external_actions_service import PlanExternalActionsService
from app.application.services.retrieve_action_candidates_service import (
    RetrieveActionCandidatesService,
)
from app.domain.models.action_descriptor import ActionCandidate, ActionDescriptor


def _scalar(**overrides) -> dict:
    payload = {
        "actionId": "ext.metrics.scalar",
        "method": "GET",
        "path": "/metrics/scalar",
        "operationId": "get_metrics_scalar",
        "summary": "Scalar revenue KPI for one site",
        "description": (
            "KPI escalar de receita de um site. Use para «revenue of site X». "
            "Do not use for «revenue by site» tabular breakdown."
        ),
        "whenToUse": "Use for revenue of a specific site as a consolidated KPI.",
        "whenNotToUse": (
            "Do not use for «revenue by site» tabular ranking — prefer /metrics/by-site."
        ),
        "parametersSchema": [
            {"name": "site", "in": "query", "required": False, "schema": {"type": "string"}}
        ],
        "sensitivity": "read",
        "enabled": True,
    }
    payload.update(overrides)
    return payload


def _breakdown(**overrides) -> dict:
    payload = {
        "actionId": "ext.metrics.by-site",
        "method": "GET",
        "path": "/metrics/by-site",
        "operationId": "get_metrics_by_site",
        "summary": "Revenue breakdown by site",
        "description": (
            "Lista comparando sites. Use para «revenue by site». "
            "Do not use for «revenue of site X» or a single-site scalar KPI."
        ),
        "whenToUse": "Use when the user wants revenue broken down across sites.",
        "whenNotToUse": (
            "Do not use for «revenue of site X» or a single-site scalar KPI "
            "— prefer /metrics/scalar."
        ),
        "parametersSchema": [
            {
                "name": "period",
                "in": "query",
                "required": False,
                "schema": {"type": "string"},
            }
        ],
        "sensitivity": "read",
        "enabled": True,
    }
    payload.update(overrides)
    return payload


def _segment(**overrides) -> dict:
    payload = {
        "actionId": "ext.metrics.segment",
        "method": "GET",
        "path": "/metrics/segment",
        "operationId": "get_metrics_segment",
        "summary": "Segment revenue KPI for one brand line",
        "description": (
            "Receita de um segmento de marca no período, com meta. "
            "Filial opcional. Use para «segment revenue»."
        ),
        "whenToUse": "Use for one brand-line segment KPI, not site-wide consolidated revenue.",
        "parametersSchema": [
            {"name": "site", "in": "query", "required": False, "schema": {"type": "string"}}
        ],
        "sensitivity": "read",
        "enabled": True,
    }
    payload.update(overrides)
    return payload


def _stock() -> dict:
    return {
        "actionId": "ext.warehouses.stock",
        "method": "GET",
        "path": "/warehouses/{id}/stock",
        "operationId": "get_warehouse_stock",
        "summary": "Warehouse stock levels",
        "description": "Lists stock quantities for a warehouse.",
        "parametersSchema": [
            {"name": "id", "in": "path", "required": True, "schema": {"type": "string"}}
        ],
        "sensitivity": "read",
        "enabled": True,
    }


class _Repo:
    def __init__(self, actions: list[dict]):
        self.actions = actions

    def find_candidate_actions(self, message, limit=80, allowed_action_ids=None):
        allowed = {str(item) for item in (allowed_action_ids or [])}
        return [
            action
            for action in self.actions
            if not allowed or str(action.get("actionId")) in allowed
        ][:limit]

    def list_actions(self, provider_key=None):
        return list(self.actions)


def _allowed(actions: list[dict]) -> list[str]:
    return [str(item["actionId"]) for item in actions]


def test_single_site_kpi_does_not_select_breakdown():
    catalog = [_scalar(), _breakdown(), _stock()]
    message = "What is the revenue of site 01 as a consolidated KPI?"
    candidates = RetrieveActionCandidatesService(_Repo(catalog)).retrieve(
        message,
        allowed_action_ids=_allowed(catalog),
        catalog_actions=catalog,
    )
    ids = [item.action_id for item in candidates]
    assert "ext.metrics.scalar" in ids
    assert "ext.metrics.by-site" not in ids

    plan = PlanExternalActionsService(llm_planner=None).plan(message, candidates)
    assert plan.steps[0].action_id == "ext.metrics.scalar"


def test_breakdown_request_does_not_select_scalar():
    catalog = [_scalar(), _breakdown(), _stock()]
    message = "Show revenue by site ranking for this period"
    candidates = RetrieveActionCandidatesService(_Repo(catalog)).retrieve(
        message,
        allowed_action_ids=_allowed(catalog),
        catalog_actions=catalog,
        top_k=4,
    )
    ids = [item.action_id for item in candidates]
    assert "ext.metrics.by-site" in ids
    assert "ext.metrics.scalar" not in ids


def test_unrelated_stock_question_is_not_forced_to_revenue_actions():
    catalog = [_scalar(), _breakdown(), _stock()]
    message = "List warehouse stock for warehouse WH-1"
    candidates = RetrieveActionCandidatesService(_Repo(catalog)).retrieve(
        message,
        allowed_action_ids=_allowed(catalog),
        catalog_actions=catalog,
    )
    ids = [item.action_id for item in candidates]
    assert "ext.warehouses.stock" in ids
    assert ids[0] == "ext.warehouses.stock"
    plan = PlanExternalActionsService(llm_planner=None).plan(message, candidates)
    chosen = plan.steps[0].action_id if plan.steps else None
    assert chosen != "ext.metrics.scalar"
    assert chosen != "ext.metrics.by-site"


def test_metamorphic_path_rename_preserves_when_not_semantics():
    scalar = _scalar(
        actionId="vendor.alpha.one",
        path="/alpha/one",
        operationId="get_alpha_one",
    )
    breakdown = _breakdown(
        actionId="vendor.beta.two",
        path="/beta/two",
        operationId="get_beta_two",
    )
    catalog = [scalar, breakdown]
    message = "What is the revenue of site 01 as a consolidated KPI?"
    candidates = RetrieveActionCandidatesService(_Repo(catalog)).retrieve(
        message,
        allowed_action_ids=_allowed(catalog),
        catalog_actions=catalog,
    )
    assert [item.action_id for item in candidates] == ["vendor.alpha.one"]

    def fake_llm(_message, _catalog):
        return {
            "steps": [
                {
                    "actionId": "vendor.beta.two",
                    "arguments": {"parameters": {}},
                }
            ]
        }

    plan = PlanExternalActionsService(llm_planner=fake_llm).plan(message, candidates)
    assert plan.steps[0].action_id == "vendor.alpha.one"


def test_llm_cannot_pick_when_not_candidate_still_in_unfiltered_list():
    scalar = _scalar()
    breakdown = _breakdown()
    message = "What is the revenue of site 01 as a consolidated KPI?"
    candidates = [
        ActionCandidate(
            descriptor=ActionDescriptor.from_action_dict(breakdown),
            score=9.0,
        ),
        ActionCandidate(
            descriptor=ActionDescriptor.from_action_dict(scalar),
            score=1.0,
        ),
    ]

    def fake_llm(_message, catalog):
        ids = {str(item.get("actionId")) for item in catalog}
        assert "ext.metrics.by-site" not in ids
        return {
            "steps": [
                {
                    "actionId": "ext.metrics.by-site",
                    "arguments": {"parameters": {}},
                }
            ]
        }

    plan = PlanExternalActionsService(llm_planner=fake_llm).plan(message, candidates)
    assert plan.steps[0].action_id == "ext.metrics.scalar"


def test_llm_clarify_only_falls_back_to_deterministic_scalar():
    scalar = _scalar()
    breakdown = _breakdown()
    message = "What is the revenue of site 01 as a consolidated KPI?"
    candidates = [
        ActionCandidate(
            descriptor=ActionDescriptor.from_action_dict(breakdown),
            score=9.0,
        ),
        ActionCandidate(
            descriptor=ActionDescriptor.from_action_dict(scalar),
            score=1.0,
        ),
    ]

    def fake_llm(_message, catalog):
        ids = {str(item.get("actionId")) for item in catalog}
        assert "ext.metrics.by-site" not in ids
        return {
            "steps": [],
            "clarify": (
                "I returned WEG revenue. Do you also want new-business revenue?"
            ),
        }

    plan = PlanExternalActionsService(llm_planner=fake_llm).plan(message, candidates)
    assert plan.steps
    assert plan.steps[0].action_id == "ext.metrics.scalar"
    assert not plan.clarify


def test_llm_step_plus_clarify_still_executes_scalar():
    scalar = _scalar()
    message = "What is the revenue of site 01 as a consolidated KPI?"
    candidates = [
        ActionCandidate(
            descriptor=ActionDescriptor.from_action_dict(scalar),
            score=1.0,
        ),
    ]

    def fake_llm(_message, _catalog):
        return {
            "steps": [
                {
                    "actionId": "ext.metrics.scalar",
                    "arguments": {"parameters": {"site": "01"}},
                }
            ],
            "clarify": "Want the by-site ranking as well?",
        }

    plan = PlanExternalActionsService(llm_planner=fake_llm).plan(message, candidates)
    assert plan.steps[0].action_id == "ext.metrics.scalar"
    assert not plan.clarify


def test_llm_weaker_sibling_loses_to_deterministic_scalar():
    scalar = _scalar()
    segment = _segment()
    message = "What is the revenue of site 01 as a consolidated KPI?"
    candidates = [
        ActionCandidate(
            descriptor=ActionDescriptor.from_action_dict(segment),
            score=8.0,
        ),
        ActionCandidate(
            descriptor=ActionDescriptor.from_action_dict(scalar),
            score=1.2,
        ),
    ]

    def fake_llm(_message, _catalog):
        return {
            "steps": [
                {
                    "actionId": "ext.metrics.segment",
                    "arguments": {"parameters": {"site": "01"}},
                }
            ]
        }

    plan = PlanExternalActionsService(llm_planner=fake_llm).plan(message, candidates)
    assert plan.steps[0].action_id == "ext.metrics.scalar"


def test_quoted_positive_survives_large_catalog_pool():
    fillers = [
        {
            "actionId": f"ext.noise.item-{index}",
            "method": "GET",
            "path": f"/noise/{index}",
            "operationId": f"get_noise_{index}",
            "summary": "Unrelated operational listing",
            "description": "Generic listing without revenue quotes.",
            "sensitivity": "read",
            "enabled": True,
        }
        for index in range(130)
    ]
    catalog = [*fillers, _scalar(), _segment()]
    message = "What is the revenue of site 01 as a consolidated KPI?"
    candidates = RetrieveActionCandidatesService(_Repo(catalog)).retrieve(
        message,
        allowed_action_ids=_allowed(catalog),
        catalog_actions=catalog,
    )
    ids = [item.action_id for item in candidates]
    assert "ext.metrics.scalar" in ids
    assert ids[0] == "ext.metrics.scalar"
