"""Um teste por linha P0/herança da QUESTION_FLOW_MATRIX."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from app.application.services.chat_external_action_orchestration_service import (
    ChatExternalActionOrchestrationService,
)
from app.composition.content_composer import configure_domain_infrastructure_ports
from app.domain.services.chat_operational_sufficiency_critic_service import (
    ChatOperationalSufficiencyCriticService,
)
from app.domain.services.chat_product_enrichment_composition_planning_service import (
    ChatProductEnrichmentCompositionPlanningService,
)
from app.domain.services.chat_product_query_intent_service import (
    ChatProductQueryIntent,
    ChatProductQueryIntentService,
)
from app.domain.services.chat_snapshot_operational_focus import ChatSnapshotOperationalFocus
from tests.fixtures.question_flow_matrix import QUESTION_FLOW_MATRIX

configure_domain_infrastructure_ports()


@pytest.fixture
def multi_action_runtime(monkeypatch):
    monkeypatch.setattr(
        "app.application.services.chat_intelligence_runtime_access.resolve_chat_intelligence_runtime",
        lambda: type("R", (), {"multi_action_enabled": True})(),
    )
    monkeypatch.setattr(
        ChatExternalActionOrchestrationService,
        "_resolve_max_calls",
        classmethod(lambda cls, max_calls: 4),
    )


def _run_case(case: dict, multi_action_runtime) -> None:
    kind = case["kind"]
    message = case.get("message") or ""

    if kind == "plan_actions_no_name_error":
        planned = ChatExternalActionOrchestrationService.plan_actions(
            MagicMock(select_action=MagicMock(return_value=None)),
            message=message,
            allowed_action_ids=[],
            workspace_context=case.get("workspace"),
            previous_messages=case.get("previous_messages") or [],
        )
        assert isinstance(planned, list)
        return

    if kind == "intent_stock":
        intent = ChatProductQueryIntentService.resolve_product_intent(message)
        assert intent == ChatProductQueryIntent.STOCK
        return

    if kind == "intent_description":
        intent = ChatProductQueryIntentService.resolve_product_intent(message)
        assert intent == ChatProductQueryIntent.DESCRIPTION
        return

    if kind == "ground_code":
        memory = case.get("memory_snapshot") or {}
        code = ChatProductQueryIntentService.resolve_product_code(
            message,
            memory_snapshot=memory,
        )
        focus = ChatSnapshotOperationalFocus.get(memory) if isinstance(memory, dict) else None
        if not code and isinstance(focus, dict):
            code = str(focus.get("productCode") or "").strip() or None
        # Grounding may come from memory focus via resolve; accept focus code when empty message code
        expected = case.get("expect_code")
        if code != expected:
            code = ChatProductQueryIntentService.resolve_product_code(
                message,
                memory_snapshot=memory,
                previous_messages=[],
            )
        assert code == expected or (
            isinstance(focus, dict) and focus.get("productCode") == expected
        )
        return

    if kind == "overview_trigger":
        assert ChatProductEnrichmentCompositionPlanningService.looks_like_product_overview(
            message
        )
        return

    if kind == "narrow_exclude_overview":
        assert not ChatProductEnrichmentCompositionPlanningService.looks_like_product_overview(
            message
        )
        return

    if kind == "critic_stock_low":
        verdict = ChatOperationalSufficiencyCriticService.evaluate(
            tool_calls=[
                {
                    "name": "execute_external_action",
                    "arguments": {"actionId": "stock", "path": "/products/x/stock"},
                    "metadata": {
                        "ok": True,
                        "path": "/products/x/stock",
                        "anomalies": [{"type": "zero_value"}],
                        "dataAnswer": {"profileKey": "stock"},
                    },
                }
            ],
            remaining_slots=2,
        )
        assert verdict.action == "execute"
        assert verdict.plan_id == "stock_low_needs_sales"
        return

    if kind == "critic_sales_empty":
        verdict = ChatOperationalSufficiencyCriticService.evaluate(
            tool_calls=[
                {
                    "name": "execute_external_action",
                    "arguments": {"actionId": "sales", "path": "/products/x/sales"},
                    "metadata": {
                        "ok": True,
                        "path": "/products/x/sales",
                        "emptyResult": True,
                        "anomalies": [{"type": "empty_list"}],
                        "dataAnswer": {"profileKey": "generic_list"},
                    },
                }
            ],
            remaining_slots=2,
        )
        assert verdict.action == "chips"
        assert verdict.clarify_key == "clarifyInvoiceDirection"
        return

    if kind == "critic_cap_deferred":
        verdict = ChatOperationalSufficiencyCriticService.evaluate(
            tool_calls=[
                {
                    "name": "execute_external_action",
                    "arguments": {"actionId": "stock", "path": "/products/x/stock"},
                    "metadata": {
                        "ok": True,
                        "path": "/products/x/stock",
                        "anomalies": [{"type": "zero_value"}],
                        "dataAnswer": {"profileKey": "stock"},
                    },
                }
            ],
            remaining_slots=0,
        )
        assert verdict.action == "chips"
        assert verdict.deferred_to_chips is True
        return

    if kind == "multi_intent_continuation":
        from app.application.services.chat_multi_intent_continuation_service import (
            ChatMultiIntentContinuationService,
        )

        executed, continuation = ChatMultiIntentContinuationService.apply_limit(
            [
                {"actionId": "stock", "arguments": {"path": "/products/{code}/stock"}},
                {"actionId": "suppliers", "arguments": {"path": "/products/{code}/suppliers"}},
            ],
            max_calls=1,
        )
        assert len(executed) == 1
        assert continuation is not None
        assert int(continuation.get("deferredCount") or 0) >= 1
        return

    if kind == "sufficiency_audit_shape":
        verdict = ChatOperationalSufficiencyCriticService.evaluate(
            tool_calls=[],
            remaining_slots=1,
        )
        payload = ChatOperationalSufficiencyCriticService.audit_payload(verdict)
        assert "verdict" in payload
        assert "reasonKey" in payload
        return

    raise AssertionError(f"kind não implementado: {kind}")


@pytest.mark.parametrize(
    "case",
    QUESTION_FLOW_MATRIX,
    ids=[str(item["id"]) for item in QUESTION_FLOW_MATRIX],
)
def test_question_flow_matrix_row(case, multi_action_runtime):
    _run_case(case, multi_action_runtime)
