"""Bounded planner loop, goal coverage, date coercion, KPI hint, Nebula retrieval."""

from __future__ import annotations

import json
from pathlib import Path

from app.application.services.openapi_first_selection_bridge_service import (
    OpenApiFirstSelectionBridgeService,
)
from app.application.services.openapi_llm_action_planner_service import (
    OpenApiLlmActionPlannerService,
)
from app.application.services.plan_external_actions_service import PlanExternalActionsService
from app.application.services.retrieve_action_candidates_service import (
    RetrieveActionCandidatesService,
)
from app.application.services.validate_action_arguments_service import (
    ValidateActionArgumentsService,
)
from app.domain.models.action_descriptor import ActionCandidate, ActionDescriptor
from app.domain.models.action_plan import ActionPlan, ActionPlanGoal, ActionPlanStep
from app.domain.services.chat_bounded_planner_mode_service import ChatBoundedPlannerModeService
from app.domain.services.chat_goal_coverage_service import ChatGoalCoverageService
from app.domain.services.chat_openapi_argument_coercion_service import (
    ChatOpenApiArgumentCoercionService,
)
from app.domain.services.chat_presentation_user_format_preference_service import (
    ChatPresentationUserFormatPreferenceService,
)
from app.domain.services.chat_presentation_decide_service import ChatPresentationDecideService
from app.domain.services.openapi_planner_mode_service import OpenApiPlannerModeDecision

_FIXTURES = Path(__file__).resolve().parents[3] / "fixtures"


class _CatalogRepository:
    def __init__(self, actions: list[dict]):
        self.actions = actions

    def find_candidate_actions(self, message, limit=80, allowed_action_ids=None):
        allowed = {str(item) for item in (allowed_action_ids or [])}
        query = str(message or "").lower()
        ranked = []
        for action in self.actions:
            if allowed and str(action.get("actionId")) not in allowed:
                continue
            hay = " ".join(
                str(action.get(key) or "")
                for key in ("summary", "description", "path", "operationId", "actionId")
            ).lower()
            score = sum(1 for token in query.split() if len(token) >= 4 and token in hay)
            ranked.append((score, action))
        ranked.sort(key=lambda item: -item[0])
        return [item[1] for item in ranked[:limit]]

    def list_actions(self, provider_key=None):
        return list(self.actions)

    def search_similar_actions(self, embedding, *, allowed_action_ids=None, limit=20):
        return []


class _FakeLlm:
    def __init__(self, payload: str):
        self.payload = payload
        self.calls = 0
        self.messages = []

    def generate(self, messages):
        self.calls += 1
        self.messages = messages
        return self.payload

    def stream(self, messages):
        yield self.payload


def _mode_on() -> OpenApiPlannerModeDecision:
    return OpenApiPlannerModeDecision(
        mode="on",
        use_openapi_selection=True,
        run_shadow_compare=False,
        canary_matched=False,
    )


def _candidate(action: dict, score: float = 1.0) -> ActionCandidate:
    return ActionCandidate(
        descriptor=ActionDescriptor.from_action_dict(action),
        score=score,
        lexical_score=score,
        vector_score=0.0,
        reasons=("lexical",),
    )


def _stock_action() -> dict:
    return {
        "actionId": "stock-action",
        "method": "GET",
        "path": "/products/{code}/stock",
        "operationId": "get_product_stock",
        "summary": "estoque do material",
        "description": "consulta estoque atual do produto",
        "enabled": True,
        "parametersSchema": [
            {"name": "code", "in": "path", "required": True, "schema": {"type": "string"}},
        ],
    }


def _schedule_action() -> dict:
    return {
        "actionId": "schedule-action",
        "method": "GET",
        "path": "/production/schedule/today",
        "operationId": "get_production_schedule_today",
        "summary": "produtos programados para produzir hoje",
        "description": "programação de produção do dia",
        "enabled": True,
        "parametersSchema": [],
    }


def _closing_rate_action() -> dict:
    return {
        "actionId": "closing-rate",
        "method": "GET",
        "path": "/commercial/closing-rate",
        "operationId": "get_commercial_closing_rate",
        "summary": "commercial closing rate conversion of quotes",
        "description": "Taxa de fechamento comercial",
        "enabled": True,
        "parametersSchema": [
            {
                "name": "start_date",
                "in": "query",
                "required": True,
                "schema": {"type": "string", "format": "date"},
            },
            {
                "name": "end_date",
                "in": "query",
                "required": True,
                "schema": {"type": "string", "format": "date"},
            },
            {"name": "branch", "in": "query", "required": False, "schema": {"type": "string"}},
        ],
    }


def test_llm_two_steps_without_joiner_are_kept():
    stock = _stock_action()
    schedule = _schedule_action()
    llm = _FakeLlm(
        json.dumps(
            {
                "planVersion": "2",
                "mode": "EXECUTE",
                "goals": [
                    {"goalId": "g1", "intent": "stock"},
                    {"goalId": "g2", "intent": "schedule"},
                ],
                "steps": [
                    {
                        "actionId": "stock-action",
                        "goalIds": ["g1"],
                        "arguments": {"parameters": {"code": "10080055"}},
                    },
                    {
                        "actionId": "schedule-action",
                        "goalIds": ["g2"],
                        "arguments": {"parameters": {}},
                    },
                ],
            }
        )
    )
    plan = PlanExternalActionsService(llm_planner=OpenApiLlmActionPlannerService(llm)).plan(
        "qual o estoque 10080055 e quais o produtos programados para produzir hj?",
        [_candidate(stock), _candidate(schedule)],
    )
    assert [step.action_id for step in plan.steps] == ["stock-action", "schedule-action"]
    coverage = ChatGoalCoverageService.evaluate(plan)
    assert coverage.pending_goal_ids == ()
    assert {item.status for item in coverage.results} == {"planned"}


def test_presentation_compound_still_caps_to_one_step():
    rol = {
        "actionId": "rol-action",
        "method": "GET",
        "path": "/commercial/rol",
        "operationId": "get_commercial_rol",
        "summary": "ROL comercial",
        "description": "Indicador ROL",
        "enabled": True,
        "parametersSchema": [],
    }
    series = {
        "actionId": "rol-series",
        "method": "GET",
        "path": "/commercial/rol/series",
        "operationId": "get_commercial_rol_series",
        "summary": "Série de ROL comercial",
        "description": "Série temporal",
        "enabled": True,
        "parametersSchema": [],
    }
    llm = _FakeLlm(
        json.dumps(
            {
                "steps": [
                    {"actionId": "rol-action", "arguments": {"parameters": {}}},
                    {"actionId": "rol-series", "arguments": {"parameters": {}}},
                ]
            }
        )
    )
    plan = PlanExternalActionsService(llm_planner=OpenApiLlmActionPlannerService(llm)).plan(
        "Mostre o ROL em KPI e série, tudo na mesma resposta.",
        [_candidate(rol), _candidate(series)],
    )
    assert len(plan.steps) == 1


def test_invalid_llm_dates_are_coerced_to_iso(monkeypatch):
    action = _closing_rate_action()
    llm = _FakeLlm(
        json.dumps(
            {
                "steps": [
                    {
                        "actionId": "closing-rate",
                        "arguments": {
                            "parameters": {
                                "start_date": "01-08-2026",
                                "end_date": "31-08-2026",
                                "branch": "01",
                            }
                        },
                    }
                ]
            }
        )
    )
    plan = PlanExternalActionsService(llm_planner=OpenApiLlmActionPlannerService(llm)).plan(
        "taxa de fechamento filial 01 agosto 2026",
        [_candidate(action)],
        execution_context={"referenceDate": "2026-09-09"},
    )
    params = plan.steps[0].arguments.get("parameters") or {}
    assert params["start_date"] == "2026-08-01"
    assert params["end_date"] == "2026-08-31"
    ValidateActionArgumentsService().validate(
        provider={"enabled": True},
        action=action,
        arguments=plan.steps[0].arguments,
    )


def test_planner_prompt_contains_conversation_context():
    llm = _FakeLlm('{"steps":[{"actionId":"stock-action","arguments":{"parameters":{}}}]}')
    adapter = OpenApiLlmActionPlannerService(llm)
    adapter(
        "e o estoque?",
        [{"actionId": "stock-action", "parameters": []}],
        conversation_context='{"operationalFocus":{"productCode":"10080055"}}',
        candidate_set_id="abc123",
    )
    user = llm.messages[1]["content"]
    assert "10080055" in user
    assert "abc123" in user


def test_normalize_from_message_detects_com_kpi():
    assert (
        ChatPresentationUserFormatPreferenceService.normalize_from_message(
            None,
            "Mostre o ROL comercial recente (agosto 2026) com KPI",
        )
        == "kpi"
    )


def test_normalize_from_message_negative_without_kpi():
    result = ChatPresentationUserFormatPreferenceService.normalize_from_message(
        None,
        "Mostre o ROL comercial recente de agosto 2026",
    )
    assert result != "kpi"


def test_decide_com_kpi_selects_kpi_when_slot_available():
    decision = ChatPresentationDecideService.decide(
        user_message="Mostre o ROL comercial recente (agosto 2026) com KPI",
        available_formats=["table", "kpi", "text"],
        rows=[{"value": 10}],
    )
    assert decision.get("selected") == "kpi"


def test_decide_com_kpi_falls_back_when_schema_has_no_kpi_slot():
    decision = ChatPresentationDecideService.decide(
        user_message="Mostre o ROL comercial recente (agosto 2026) com KPI",
        available_formats=["table", "text"],
        rows=[{"value": 10}],
    )
    assert decision.get("selected") != "kpi"


def test_goal_coverage_pending_when_second_goal_missing():
    plan = ActionPlan(
        goals=(
            ActionPlanGoal(goal_id="g1", intent="stock"),
            ActionPlanGoal(goal_id="g2", intent="schedule"),
        ),
        steps=(
            ActionPlanStep(action_id="stock-action", goal_ids=("g1",), arguments={}),
        ),
    )
    report = ChatGoalCoverageService.evaluate(plan)
    assert "g2" in report.pending_goal_ids
    assert report.complete is False


def test_membership_rejects_action_outside_candidate_set():
    llm = _FakeLlm(
        json.dumps(
            {
                "steps": [
                    {"actionId": "unknown-action", "arguments": {"parameters": {}}},
                    {"actionId": "stock-action", "arguments": {"parameters": {"code": "1"}}},
                ]
            }
        )
    )
    plan = PlanExternalActionsService(llm_planner=OpenApiLlmActionPlannerService(llm)).plan(
        "estoque 1",
        [_candidate(_stock_action())],
    )
    assert [step.action_id for step in plan.steps] == ["stock-action"]
    assert "unknown-action" in (plan.metadata.get("rejectedOutsideCandidateSet") or [])


def test_bounded_loop_second_search_merges_candidates(monkeypatch):
    monkeypatch.setattr(ChatBoundedPlannerModeService, "resolve_mode", lambda: "on")
    stock = _stock_action()
    schedule = _schedule_action()
    payloads = [
        json.dumps(
            {
                "mode": "SEARCH_ACTIONS",
                "steps": [],
                "searchRequests": {
                    "actions": [
                        {
                            "goalId": "g2",
                            "query": "production schedule planned today",
                            "reason": "compound_goal",
                        }
                    ]
                },
            }
        ),
        json.dumps(
            {
                "mode": "EXECUTE",
                "steps": [
                    {"actionId": "stock-action", "arguments": {"parameters": {"code": "10080055"}}},
                    {"actionId": "schedule-action", "arguments": {"parameters": {}}},
                ],
            }
        ),
    ]

    class _SequencedLlm:
        def __init__(self):
            self.calls = 0

        def generate(self, messages):
            payload = payloads[min(self.calls, len(payloads) - 1)]
            self.calls += 1
            return payload

        def stream(self, messages):
            yield self.generate(messages)

    repo = _CatalogRepository([stock, schedule])
    planner = PlanExternalActionsService(
        llm_planner=OpenApiLlmActionPlannerService(_SequencedLlm())
    )
    bridge = OpenApiFirstSelectionBridgeService(repo, planner=planner)
    planned = bridge.plan_tool_calls(
        "estoque 10080055 e programação de hoje",
        allowed_action_ids=["stock-action", "schedule-action"],
        catalog_actions=[stock, schedule],
        mode_decision=_mode_on(),
    )
    action_ids = [
        str((item.get("arguments") or {}).get("actionId") or "")
        for item in planned
        if item.get("name") == "execute_external_action"
    ]
    assert "stock-action" in action_ids
    assert "schedule-action" in action_ids
    assert planned[0]["metadata"].get("plannerRoundCount") == 2


def test_nebula_retrieval_prefers_specialized_over_generic():
    fixture = json.loads(
        (_FIXTURES / "nebula_factory_openapi_actions.json").read_text(encoding="utf-8")
    )
    actions = fixture["actions"]
    allowed = [str(item["actionId"]) for item in actions]
    repo = _CatalogRepository(actions)
    candidates = RetrieveActionCandidatesService(repo).retrieve(
        "export the product structure to excel",
        allowed_action_ids=allowed,
        catalog_actions=actions,
    )
    assert candidates
    assert "export" in candidates[0].action_id


def test_nebula_metamorphic_renames_still_rank_export():
    fixture = json.loads(
        (_FIXTURES / "nebula_factory_openapi_actions_metamorphic.json").read_text(
            encoding="utf-8"
        )
    )
    actions = fixture["actions"]
    allowed = [str(item["actionId"]) for item in actions]
    repo = _CatalogRepository(actions)
    candidates = RetrieveActionCandidatesService(repo).retrieve(
        "export the product structure to excel",
        allowed_action_ids=allowed,
        catalog_actions=actions,
    )
    assert candidates
    assert "spreadsheet" in candidates[0].action_id or "dump" in candidates[0].action_id


def test_date_coercion_sibling_month_name():
    schema = [
        {"name": "start_date", "schema": {"format": "date"}},
        {"name": "end_date", "schema": {"format": "date"}},
    ]
    coerced = ChatOpenApiArgumentCoercionService.coerce_parameters(
        {},
        schema,
        message="agosto de 2026",
        execution_context={"referenceDate": "2026-09-09"},
    )
    assert coerced["start_date"] == "2026-08-01"
    assert coerced["end_date"] == "2026-08-31"


def _product_action(action_id: str, path: str, summary: str) -> dict:
    return {
        "actionId": action_id,
        "method": "GET",
        "path": path,
        "operationId": f"get_{action_id.replace('-', '_')}",
        "summary": summary,
        "description": summary,
        "enabled": True,
        "parametersSchema": [
            {"name": "code", "in": "path", "required": True, "schema": {"type": "string"}}
        ],
    }


def test_bounded_loop_numbered_compound_covers_two_goals_not_siblings(monkeypatch):
    monkeypatch.setattr(ChatBoundedPlannerModeService, "resolve_mode", lambda: "on")
    catalog = [
        _product_action("stock", "/products/{code}/stock", "Estoque do produto"),
        _product_action("structure", "/products/{code}/structure", "Estrutura BOM do produto"),
        _product_action("guide", "/products/{code}/guide", "Roteiro de fabricação do produto"),
        _product_action(
            "open-orders",
            "/products/{code}/sales/open-orders",
            "Pedidos em aberto do produto",
        ),
    ]
    repo = _CatalogRepository(catalog)
    bridge = OpenApiFirstSelectionBridgeService(
        repo,
        planner=PlanExternalActionsService(llm_planner=None),
    )
    planned = bridge.plan_tool_calls(
        "para o produto 90260149 traga (1) a estrutura BOM e (2) o roteiro de fabricação",
        allowed_action_ids=[item["actionId"] for item in catalog],
        catalog_actions=catalog,
        mode_decision=_mode_on(),
    )
    ids = [
        str((item.get("arguments") or {}).get("actionId") or "")
        for item in planned
        if item.get("name") == "execute_external_action"
    ]
    assert ids == ["structure", "guide"]
    assert (planned[0].get("metadata") or {}).get("path") == "/products/{code}/structure"
    coverage = (planned[0].get("metadata") or {}).get("goalCoverage") or {}
    assert coverage.get("complete") is True


def test_bounded_loop_sets_requested_presentation_from_com_kpi(monkeypatch):
    monkeypatch.setattr(ChatBoundedPlannerModeService, "resolve_mode", lambda: "on")
    action = {
        "actionId": "rol-action",
        "method": "GET",
        "path": "/commercial/rol",
        "operationId": "get_commercial_rol",
        "summary": "ROL comercial",
        "description": "Indicador ROL",
        "enabled": True,
        "parametersSchema": [],
    }
    repo = _CatalogRepository([action])
    bridge = OpenApiFirstSelectionBridgeService(
        repo,
        planner=PlanExternalActionsService(llm_planner=None),
    )
    planned = bridge.plan_tool_calls(
        "Mostre o ROL comercial recente (agosto 2026) com KPI",
        allowed_action_ids=["rol-action"],
        catalog_actions=[action],
        mode_decision=_mode_on(),
    )
    assert planned
    assert (planned[0].get("metadata") or {}).get("requestedPresentation") == "kpi"


def test_e8_session_a_compound_turn_has_no_joiner_gate():
    fixture = json.loads(
        (_FIXTURES / "chat_conversation_context_quality.json").read_text(encoding="utf-8")
    )
    turn = next(item for item in fixture["turns"] if item["id"] == "T2")
    lowered = str(turn["message"]).lower()
    assert " e tambem " not in lowered
    assert " e também " not in lowered
    assert turn["expectFamily"] == ["stock", "schedule"]


def test_e8_session_b_sibling_also_omits_joiner_gate():
    fixture = json.loads(
        (_FIXTURES / "chat_conversation_context_quality_session_b.json").read_text(
            encoding="utf-8"
        )
    )
    turn = next(item for item in fixture["turns"] if item["id"] == "T2")
    lowered = str(turn["message"]).lower()
    assert " e tambem " not in lowered
    assert " e quais " not in lowered
