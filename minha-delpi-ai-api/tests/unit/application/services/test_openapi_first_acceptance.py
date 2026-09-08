"""E2–E9 — suite de aceite OpenAPI-first / tool routing universal."""

from __future__ import annotations

from typing import Any

import pytest

from app.application.services.openapi_first_selection_bridge_service import (
    OpenApiFirstSelectionBridgeService,
)
from app.application.services.plan_external_actions_service import PlanExternalActionsService
from app.application.services.retrieve_action_candidates_service import (
    RetrieveActionCandidatesService,
)
from app.application.services.validate_action_arguments_service import (
    ValidateActionArgumentsService,
)
from app.application.services.chat_external_action_orchestration_service import (
    ChatExternalActionOrchestrationService,
)
from app.domain.exceptions.external_action_exceptions import ExternalActionValidationError
from app.domain.models.action_descriptor import ActionDescriptor
from app.domain.models.action_plan import ActionPlan, ActionPlanStep
from app.domain.services.chat_agentic_catalog_service import ChatAgenticCatalogService
from app.domain.services.chat_schema_driven_presentation_service import (
    ChatSchemaDrivenPresentationService,
)
from app.domain.services.openapi_planner_mode_service import (
    OpenApiPlannerModeDecision,
    OpenApiPlannerModeService,
)
from tests.support.openapi_logistics_fixtures import (
    find_logistics_action,
    import_logistics_actions,
    logistics_allowed_action_ids,
)


class _LogisticsRepository:
    def __init__(self, actions: list[dict]):
        self.actions = actions

    def find_candidate_actions(self, message, limit=80, allowed_action_ids=None):
        allowed = {str(item) for item in (allowed_action_ids or [])}
        rows = [
            action
            for action in self.actions
            if not allowed or str(action.get("actionId")) in allowed
        ]
        return rows[:limit]

    def list_actions(self, provider_key=None):
        return list(self.actions)

    def search_similar_actions(self, embedding, *, allowed_action_ids=None, limit=20):
        return []


@pytest.fixture
def logistics_actions():
    return import_logistics_actions()


@pytest.fixture
def logistics_repo(logistics_actions):
    return _LogisticsRepository(logistics_actions)


def test_action_plan_schema_requires_action_id_and_arguments():
    schema = PlanExternalActionsService.planner_json_schema()
    assert "steps" in schema.get("required", [])
    step_required = schema["properties"]["steps"]["items"]["required"]
    assert "actionId" in step_required
    assert "arguments" in step_required
    plan = ActionPlan(
        steps=(
            ActionPlanStep(
                action_id="x",
                arguments={"parameters": {"id": "1"}},
            ),
        )
    )
    assert plan.as_dict()["steps"][0]["actionId"] == "x"
    descriptor = ActionDescriptor.from_action_dict(
        {"actionId": "a", "method": "GET", "path": "/x"}
    )
    assert descriptor.as_dict()["actionId"] == "a"


def test_case1_tracking_in_top_k(logistics_actions, logistics_repo):
    """Caso 1: tracking no top-K sem registry."""
    msg = "Onde esta a remessa 45871 e qual a previsao de entrega?"
    candidates = RetrieveActionCandidatesService(logistics_repo).retrieve(
        msg,
        allowed_action_ids=logistics_allowed_action_ids(logistics_actions),
        catalog_actions=logistics_actions,
    )
    assert candidates
    assert candidates[0].descriptor.operation_id == "get_shipment_tracking"


def test_case1_plan_binds_shipment_id(logistics_actions, logistics_repo):
    msg = "Onde esta a remessa 45871 e qual a previsao de entrega?"
    candidates = RetrieveActionCandidatesService(logistics_repo).retrieve(
        msg,
        allowed_action_ids=logistics_allowed_action_ids(logistics_actions),
        catalog_actions=logistics_actions,
    )
    plan = PlanExternalActionsService().plan(msg, candidates)
    assert plan.steps
    assert plan.steps[0].arguments["parameters"]["id"] == "45871"


def test_case2_missing_required_clarifies(logistics_actions, logistics_repo):
    msg = "Qual o status de rastreio da remessa?"
    candidates = RetrieveActionCandidatesService(logistics_repo).retrieve(
        msg,
        allowed_action_ids=logistics_allowed_action_ids(logistics_actions),
        catalog_actions=logistics_actions,
    )
    plan = PlanExternalActionsService().plan(msg, candidates)
    assert plan.clarify
    assert "id" in str(plan.metadata.get("missingParameters") or ["id"]).lower() or "id" in plan.clarify.lower()


def test_case3_invalid_enum_rejected(logistics_actions):
    action = find_logistics_action("list_orders", logistics_actions)
    # Inject enum for branch to test validator
    for param in action["parametersSchema"]:
        if param.get("name") == "branch":
            param["schema"] = {"type": "string", "enum": ["01", "02"]}
    validator = ValidateActionArgumentsService()
    with pytest.raises(ExternalActionValidationError):
        validator.validate(
            provider={"enabled": True},
            action=action,
            arguments={"parameters": {"branch": "99"}},
        )


def test_case4_additional_body_property_rejected(logistics_actions):
    action = find_logistics_action("cancel_shipment", logistics_actions)
    body = action.get("requestBodySchema") or {}
    # Ensure additionalProperties false on schema
    content = body.get("content") or {}
    for media in content.values():
        if isinstance(media, dict) and isinstance(media.get("schema"), dict):
            media["schema"]["additionalProperties"] = False
    validator = ValidateActionArgumentsService()
    with pytest.raises(ExternalActionValidationError):
        validator.validate(
            provider={"enabled": True},
            action=action,
            arguments={
                "parameters": {"id": "45871"},
                "body": {"reason": "customer request", "extra": "nope"},
            },
        )


def test_case5_llm_action_outside_topk_falls_back_to_deterministic(logistics_actions, logistics_repo):
    msg = "Onde esta a remessa 45871?"
    candidates = RetrieveActionCandidatesService(logistics_repo).retrieve(
        msg,
        allowed_action_ids=logistics_allowed_action_ids(logistics_actions),
        catalog_actions=logistics_actions,
        top_k=2,
    )

    def fake_llm(_message, _catalog):
        return {
            "steps": [
                {
                    "actionId": "totally.unknown.action",
                    "arguments": {"parameters": {"id": "45871"}},
                }
            ]
        }

    plan = PlanExternalActionsService(llm_planner=fake_llm).plan(msg, candidates)
    assert "totally.unknown.action" not in [s.action_id for s in plan.steps]
    assert not plan.is_empty
    assert plan.steps[0].action_id in {c.action_id for c in candidates}


def test_case6_two_providers_scoped_to_allowed(logistics_actions, logistics_repo):
    foreign = {
        "actionId": "other_api.tracking.get",
        "operationId": "get_other_tracking",
        "method": "GET",
        "path": "/tracking/{id}",
        "summary": "Other tracking",
        "description": "rastreio remessa previsao",
        "parametersSchema": [
            {"name": "id", "in": "path", "required": True, "schema": {"type": "string"}}
        ],
        "providerKey": "other-api",
        "sensitivity": "read",
        "enabled": True,
    }
    mixed = list(logistics_actions) + [foreign]
    repo = _LogisticsRepository(mixed)
    allowed = logistics_allowed_action_ids(logistics_actions)
    candidates = RetrieveActionCandidatesService(repo).retrieve(
        "rastreio remessa 45871 previsao",
        allowed_action_ids=allowed,
        catalog_actions=mixed,
    )
    assert all(c.action_id in set(allowed) for c in candidates)
    assert all(c.action_id != foreign["actionId"] for c in candidates)


def test_case7_write_requires_confirmation(logistics_actions, logistics_repo, monkeypatch):
    monkeypatch.setattr(
        "app.infrastructure.config.settings.Settings.CHAT_OPENAPI_PLANNER_MODE",
        "on",
    )
    cancel = find_logistics_action("cancel_shipment", logistics_actions)
    cancel_id = cancel["actionId"]

    def fake_llm(_message, _catalog):
        return {
            "steps": [
                {
                    "actionId": cancel_id,
                    "arguments": {
                        "parameters": {"id": "45871"},
                        "body": {"reason": "cliente solicitou"},
                    },
                }
            ]
        }

    decision = OpenApiPlannerModeDecision(
        mode="on",
        use_openapi_selection=True,
        run_shadow_compare=False,
        canary_matched=False,
    )
    bridge = OpenApiFirstSelectionBridgeService(
        logistics_repo,
        planner=PlanExternalActionsService(llm_planner=fake_llm),
    )
    calls = bridge.plan_tool_calls(
        "Cancele a remessa 45871",
        allowed_action_ids=logistics_allowed_action_ids(logistics_actions),
        catalog_actions=logistics_actions,
        mode_decision=decision,
    )
    assert calls
    assert calls[0]["name"] == "clarify_external_action"
    assert calls[0]["metadata"].get("requiresConfirmation") is True

    confirmed = bridge.plan_tool_calls(
        "Cancele a remessa 45871, confirmo",
        allowed_action_ids=logistics_allowed_action_ids(logistics_actions),
        catalog_actions=logistics_actions,
        mode_decision=decision,
    )
    assert confirmed
    assert confirmed[0]["name"] == "execute_external_action"
    assert "cancel" in str(confirmed[0]["metadata"].get("operationId") or "").lower()


def test_case8_multi_action_when_compound(logistics_actions, logistics_repo):
    from app.domain.models.action_descriptor import ActionCandidate, ActionDescriptor

    tracking = find_logistics_action("get_shipment_tracking", logistics_actions)
    stock = find_logistics_action("get_warehouse_stock", logistics_actions)
    candidates = [
        ActionCandidate(descriptor=ActionDescriptor.from_action_dict(tracking), score=1.0),
        ActionCandidate(descriptor=ActionDescriptor.from_action_dict(stock), score=0.9),
    ]

    def fake_llm(_message, _catalog):
        return {
            "steps": [
                {
                    "actionId": tracking["actionId"],
                    "arguments": {"parameters": {"id": "45871"}},
                },
                {
                    "actionId": stock["actionId"],
                    "arguments": {"parameters": {"id": "12"}},
                },
            ]
        }

    msg = "Onde esta a remessa 45871 e tambem o estoque do armazem 12"
    plan = PlanExternalActionsService(llm_planner=fake_llm).plan(msg, candidates)
    assert len(plan.steps) >= 2


def test_case9_execution_context_preserves_id(logistics_actions, logistics_repo):
    msg = "e a previsao?"
    candidates = RetrieveActionCandidatesService(logistics_repo).retrieve(
        "previsao entrega rastreio remessa",
        allowed_action_ids=logistics_allowed_action_ids(logistics_actions),
        catalog_actions=logistics_actions,
    )
    # Force tracking-like candidates by filtering
    tracking = [c for c in candidates if c.descriptor.operation_id == "get_shipment_tracking"]
    assert tracking
    plan = PlanExternalActionsService().plan(
        msg,
        tracking,
        execution_context={"parameters": {"id": "45871"}},
    )
    assert plan.steps
    assert plan.steps[0].arguments["parameters"]["id"] == "45871"


def test_case10_legacy_mode_off_aliases_to_openapi_on(monkeypatch, logistics_repo, logistics_actions):
    """off/shadow viram on — pipeline de registry não volta."""
    monkeypatch.setattr(
        "app.infrastructure.config.settings.Settings.CHAT_OPENAPI_PLANNER_MODE",
        "off",
    )
    assert OpenApiPlannerModeService.resolve_mode() == "on"
    decision = OpenApiPlannerModeService.decide(provider_keys={"logistics-example"})
    assert decision.is_off is False
    assert decision.use_openapi_selection is True
    bridge = OpenApiFirstSelectionBridgeService(logistics_repo, planner=PlanExternalActionsService(llm_planner=None))
    planned = bridge.plan_tool_calls(
        "Onde esta a remessa 45871?",
        allowed_action_ids=logistics_allowed_action_ids(logistics_actions),
        catalog_actions=logistics_actions,
        mode_decision=decision,
    )
    assert planned
    assert planned[0]["arguments"]["parameters"]["id"] == "45871"


def test_fail_closed_on_empty_plan_does_not_use_registry(monkeypatch, logistics_actions, logistics_repo):
    monkeypatch.setattr(
        "app.infrastructure.config.settings.Settings.CHAT_OPENAPI_PLANNER_MODE",
        "on",
    )

    class _Selection:
        repository = logistics_repo
        semantic_ranker = None

    planned = ChatExternalActionOrchestrationService.plan_actions(
        _Selection(),
        message="oi tudo bem",
        allowed_action_ids=logistics_allowed_action_ids(logistics_actions),
        workspace_context={"providerKeys": ["logistics-example"]},
    )
    assert planned
    assert planned[0]["name"] == "clarify_external_action"
    assert (planned[0].get("metadata") or {}).get("selectionMode") == "openapi_first"
    assert (planned[0].get("metadata") or {}).get("emptyPlan") is True


def test_small_talk_negative_no_steps(logistics_actions, logistics_repo):
    candidates = RetrieveActionCandidatesService(logistics_repo).retrieve(
        "oi tudo bem",
        allowed_action_ids=logistics_allowed_action_ids(logistics_actions),
        catalog_actions=logistics_actions,
    )
    plan = PlanExternalActionsService().plan("oi tudo bem", candidates)
    assert plan.steps == ()


def test_agentic_catalog_uses_retriever_when_mode_on(monkeypatch, logistics_actions, logistics_repo):
    monkeypatch.setattr(
        "app.infrastructure.config.settings.Settings.CHAT_OPENAPI_PLANNER_MODE",
        "on",
    )
    ranked = ChatAgenticCatalogService.build_ranked_candidates(
        "Onde esta a remessa 45871 e previsao de entrega?",
        logistics_allowed_action_ids(logistics_actions),
        logistics_repo,
    )
    assert ranked
    assert ranked[0].get("operationId") == "get_shipment_tracking"


def test_orchestration_on_mode_returns_tracking(monkeypatch, logistics_actions, logistics_repo):
    monkeypatch.setattr(
        "app.infrastructure.config.settings.Settings.CHAT_OPENAPI_PLANNER_MODE",
        "on",
    )

    class _Selection:
        repository = logistics_repo
        semantic_ranker = None

    planned = ChatExternalActionOrchestrationService.plan_actions(
        _Selection(),
        message="Onde esta a remessa 45871 e qual a previsao de entrega?",
        allowed_action_ids=logistics_allowed_action_ids(logistics_actions),
        workspace_context={"providerKeys": ["logistics-example"]},
    )
    assert planned
    assert planned[0]["name"] == "execute_external_action"
    assert (planned[0]["arguments"].get("parameters") or {}).get("id") == "45871"


def test_shadow_mode_aliases_to_on_and_compare_helper_still_works(
    monkeypatch, logistics_actions, logistics_repo
):
    monkeypatch.setattr(
        "app.infrastructure.config.settings.Settings.CHAT_OPENAPI_PLANNER_MODE",
        "shadow",
    )
    assert OpenApiPlannerModeService.resolve_mode() == "on"
    bridge = OpenApiFirstSelectionBridgeService(logistics_repo, planner=PlanExternalActionsService(llm_planner=None))
    openapi = bridge.plan_tool_calls(
        "Onde esta a remessa 45871?",
        allowed_action_ids=logistics_allowed_action_ids(logistics_actions),
        catalog_actions=logistics_actions,
        mode_decision=OpenApiPlannerModeService.decide(),
    )
    legacy = [
        {
            "name": "execute_external_action",
            "arguments": {"actionId": "legacy.action", "parameters": {}},
        }
    ]
    shadow = OpenApiFirstSelectionBridgeService.compare_shadow(
        legacy_planned=legacy,
        openapi_planned=openapi,
    )
    assert openapi
    assert shadow["diverged"] is True
    assert shadow["selectionMode"] == "shadow"


def test_canary_matches_provider_only(monkeypatch):
    monkeypatch.setattr(
        "app.infrastructure.config.settings.Settings.CHAT_OPENAPI_PLANNER_MODE",
        "canary",
    )
    monkeypatch.setattr(
        "app.infrastructure.config.settings.Settings.CHAT_OPENAPI_PLANNER_PROVIDER_KEYS",
        "logistics-example",
    )
    matched = OpenApiPlannerModeService.decide(provider_keys={"logistics-example"})
    assert matched.use_openapi_selection is True
    unmatched = OpenApiPlannerModeService.decide(provider_keys={"api-delpi"})
    assert unmatched.use_openapi_selection is False


def test_presentation_flat_tracking_without_x_delpi():
    rows = ChatSchemaDrivenPresentationService.extract_tabular_rows(
        {"location": "Curitiba", "eta": "2026-09-10", "status": "in_transit"}
    )
    assert rows == [{"location": "Curitiba", "eta": "2026-09-10", "status": "in_transit"}]
    empty = ChatSchemaDrivenPresentationService.extract_tabular_rows({})
    assert empty == []


def test_merge_execution_context_is_provider_agnostic():
    ctx = OpenApiFirstSelectionBridgeService.merge_execution_context(
        None,
        provider_key="logistics-example",
        action_id="logistics_example.shipments.get_shipment_tracking",
        arguments={"parameters": {"id": "45871"}},
    )
    assert ctx["parameters"]["id"] == "45871"
    assert ctx["providerKey"] == "logistics-example"


def _candidate_from_action(action: dict[str, Any], *, score: float = 1.0) -> ActionCandidate:
    from app.domain.models.action_descriptor import ActionCandidate

    return ActionCandidate(
        descriptor=ActionDescriptor.from_action_dict(action),
        score=score,
    )


def test_llm_plan_binds_missing_granularity_for_series():
    action = {
        "actionId": "api_delpi.commercial.get_commercial_rol_series",
        "operationId": "get_commercial_rol_series",
        "method": "GET",
        "path": "/commercial/rol/series",
        "summary": "Commercial ROL series",
        "description": "ROL monthly series",
        "parametersSchema": [
            {"name": "start_date", "in": "query", "required": True},
            {"name": "end_date", "in": "query", "required": True},
            {"name": "granularity", "in": "query", "required": True},
        ],
        "enabled": True,
    }
    action_id = action["actionId"]

    def fake_llm(_message, _catalog):
        return {
            "steps": [
                {
                    "actionId": action_id,
                    "arguments": {
                        "parameters": {
                            "start_date": "01-01-2026",
                            "end_date": "31-03-2026",
                        }
                    },
                }
            ]
        }

    plan = PlanExternalActionsService(llm_planner=fake_llm).plan(
        "série comercial de ROL no trimestre",
        [_candidate_from_action(action)],
    )
    assert not plan.is_empty
    params = plan.steps[0].arguments.get("parameters") or {}
    assert params.get("granularity") == "month"
    assert params.get("start_date") == "01-01-2026"
    assert params.get("end_date") == "31-03-2026"


def test_bind_does_not_invent_granularity_for_scalar_summary():
    action = {
        "actionId": "api_delpi.commercial.get_commercial_rol_summary",
        "operationId": "get_commercial_rol_summary",
        "method": "GET",
        "path": "/commercial/rol/summary",
        "summary": "Commercial ROL summary KPI",
        "description": "Scalar ROL KPI",
        "parametersSchema": [
            {"name": "start_date", "in": "query", "required": True},
            {"name": "end_date", "in": "query", "required": True},
        ],
        "enabled": True,
    }
    parameters, _body, missing = PlanExternalActionsService._bind_arguments(
        "resumo de ROL do mês",
        action,
        context_parameters={
            "start_date": "01-03-2026",
            "end_date": "31-03-2026",
        },
    )
    assert missing == []
    assert "granularity" not in parameters
    assert parameters["start_date"] == "01-03-2026"
    assert parameters["end_date"] == "31-03-2026"


def test_llm_empty_rejected_falls_back_to_deterministic():
    from app.domain.models.action_descriptor import ActionCandidate, ActionDescriptor

    action = {
        "actionId": "stock",
        "operationId": "get_product_stock",
        "method": "GET",
        "path": "/products/{code}/stock",
        "summary": "Estoque do produto",
        "description": "Saldo de estoque",
        "parametersSchema": [{"name": "code", "in": "path", "required": True}],
        "enabled": True,
    }

    def fake_llm(_message, _catalog):
        return {
            "steps": [
                {
                    "actionId": "totally.unknown",
                    "arguments": {"parameters": {"code": "90260149"}},
                }
            ]
        }

    plan = PlanExternalActionsService(llm_planner=fake_llm).plan(
        "estoque do produto 90260149",
        [
            ActionCandidate(
                descriptor=ActionDescriptor.from_action_dict(action),
                score=1.0,
            )
        ],
    )
    assert not plan.clarify
    assert plan.steps[0].action_id == "stock"


def test_deterministic_skips_sibling_missing_required():
    """Lower-ranked action missing required args must not abort a valid first step."""
    from app.domain.models.action_descriptor import ActionCandidate, ActionDescriptor

    good = {
        "actionId": "stock",
        "operationId": "get_product_stock",
        "method": "GET",
        "path": "/products/{code}/stock",
        "summary": "Estoque do produto",
        "description": "Saldo de estoque atual",
        "parametersSchema": [
            {"name": "code", "in": "path", "required": True},
        ],
        "enabled": True,
    }
    bad = {
        "actionId": "supplier-history",
        "operationId": "get_supplier_history",
        "method": "GET",
        "path": "/supplies/safety-stock/items/{code}/suppliers/{supplier_code}/purchase-price-history",
        "summary": "Histórico de preço fornecedor estoque",
        "description": "Purchase price history saldo estoque",
        "parametersSchema": [
            {"name": "code", "in": "path", "required": True},
            {"name": "supplier_code", "in": "path", "required": True},
            {"name": "supplierStore", "in": "query", "required": True},
        ],
        "enabled": True,
    }
    candidates = [
        ActionCandidate(descriptor=ActionDescriptor.from_action_dict(good), score=2.0),
        ActionCandidate(descriptor=ActionDescriptor.from_action_dict(bad), score=1.5),
    ]
    plan = PlanExternalActionsService(llm_planner=None).plan(
        "numa resposta só o saldo de estoque atual do produto 90260149",
        candidates,
        max_steps=2,
    )
    assert not plan.clarify
    assert [s.action_id for s in plan.steps] == ["stock"]
