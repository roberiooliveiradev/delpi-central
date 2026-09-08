"""Testes do planner LLM OpenAPI-first (fail-soft + wiring)."""

from __future__ import annotations

from app.application.services.openapi_llm_action_planner_service import (
    OpenApiLlmActionPlannerService,
)
from app.application.services.plan_external_actions_service import PlanExternalActionsService
from app.domain.models.action_descriptor import ActionCandidate, ActionDescriptor


class _FakeLlm:
    def __init__(self, payload: str):
        self.payload = payload
        self.calls = 0

    def generate(self, messages):
        self.calls += 1
        return self.payload

    def stream(self, messages):
        yield self.payload


def test_llm_planner_returns_structured_plan():
    llm = _FakeLlm(
        '{"steps":[{"actionId":"a1","arguments":{"parameters":{"code":"1"}},'
        '"reason":"match","confidence":0.9}]}'
    )
    adapter = OpenApiLlmActionPlannerService(llm)
    payload = adapter("estoque 1", [{"actionId": "a1", "parameters": []}])
    assert payload["steps"][0]["actionId"] == "a1"
    assert llm.calls == 1


def test_llm_planner_fail_soft_on_invalid_json():
    adapter = OpenApiLlmActionPlannerService(_FakeLlm("not-json"))
    assert adapter("msg", [{"actionId": "a1"}]) is None


def test_plan_service_prefers_llm_then_falls_back():
    action = {
        "actionId": "stock-action",
        "method": "GET",
        "path": "/products/{code}/stock",
        "operationId": "get_product_stock",
        "summary": "estoque",
        "description": "consulta estoque",
        "enabled": True,
        "parametersSchema": [
            {"name": "code", "in": "path", "required": True, "schema": {"type": "string"}},
        ],
    }
    candidate = ActionCandidate(
        descriptor=ActionDescriptor.from_action_dict(action),
        score=1.0,
        lexical_score=1.0,
        vector_score=0.0,
        reasons=("lexical",),
    )

    llm = _FakeLlm(
        '{"steps":[{"actionId":"stock-action","arguments":'
        '{"actionId":"stock-action","parameters":{"code":"10080022"}},"reason":"llm"}]}'
    )
    plan = PlanExternalActionsService(llm_planner=OpenApiLlmActionPlannerService(llm)).plan(
        "estoque do produto 10080022",
        [candidate],
    )
    assert not plan.is_empty
    assert plan.steps[0].action_id == "stock-action"
    assert llm.calls == 1
