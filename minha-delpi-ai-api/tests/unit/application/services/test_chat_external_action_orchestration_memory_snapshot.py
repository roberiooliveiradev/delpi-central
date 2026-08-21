"""Regressão: plan_actions não levanta NameError em memory_snapshot (estoque)."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from app.application.services.chat_external_action_orchestration_service import (
    ChatExternalActionOrchestrationService,
)


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


def _selection_stub():
    sel = MagicMock()
    sel.select_action.return_value = None
    sel.select_action_for_product.return_value = None
    return sel


@pytest.mark.parametrize(
    "workspace_context",
    [
        {},
        {"workingMemory": {"operationalFocus": {"productCode": "10080047"}}},
        None,
    ],
)
def test_plan_actions_estoque_no_memory_snapshot_name_error(
    multi_action_runtime,
    workspace_context,
):
    planned = ChatExternalActionOrchestrationService.plan_actions(
        _selection_stub(),
        message="estoque",
        allowed_action_ids=[],
        workspace_context=workspace_context,
        previous_messages=[],
    )
    assert isinstance(planned, list)


def test_plan_actions_estoque_multiturn_after_clarify(multi_action_runtime):
    previous = [
        {"role": "user", "content": "estoque"},
        {
            "role": "assistant",
            "content": (
                "Não ficou claro o que você precisa. Pode reformular em uma "
                "frase o que deseja consultar ou fazer?"
            ),
        },
    ]
    planned = ChatExternalActionOrchestrationService.plan_actions(
        _selection_stub(),
        message="estoque",
        allowed_action_ids=[],
        workspace_context={"workingMemory": {}},
        previous_messages=previous,
    )
    assert isinstance(planned, list)


def test_plan_actions_estoque_with_turn_analysis_merge(multi_action_runtime, monkeypatch):
    class FakeSelection:
        def select_action(self, message, *, allowed_action_ids=None, **kwargs):
            action_id = (allowed_action_ids or ["stock"])[0]
            return {
                "actionId": action_id,
                "arguments": {"path": f"/products/{{code}}/{action_id}"},
                "reason": "pick",
            }

    monkeypatch.setattr(
        "app.domain.services.chat_analysis_intent_service.ChatAnalysisIntentService.is_data_interpretation_request",
        staticmethod(lambda *a, **k: False),
    )

    planned = ChatExternalActionOrchestrationService.plan_actions(
        FakeSelection(),
        message="estoque 10080047",
        allowed_action_ids=["stock"],
        workspace_context={
            "workingMemory": {"operationalFocus": {"productCode": "10080047"}},
            "turnAnalysisActionIds": ["stock"],
        },
        previous_messages=[],
    )
    assert isinstance(planned, list)
