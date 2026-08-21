from app.application.services.chat_external_action_orchestration_service import (
    ChatExternalActionOrchestrationService,
)


def test_turn_analysis_action_ids_ordered_unique():
    ids = ChatExternalActionOrchestrationService._turn_analysis_action_ids(
        {"turnAnalysisActionIds": ["a", "b", "a", "", None]}
    )
    assert ids == ["a", "b"]


def test_merge_appends_analysis_actions_beyond_rest_route_single(monkeypatch):
    class FakeSelection:
        def select_action(self, message, *, allowed_action_ids=None, **kwargs):
            action_id = (allowed_action_ids or ["x"])[0]
            return {"actionId": action_id, "parameters": {}, "reason": "pick"}

    monkeypatch.setattr(
        "app.application.services.chat_intelligence_runtime_access.resolve_chat_intelligence_runtime",
        lambda: type("R", (), {"multi_action_enabled": True})(),
    )
    monkeypatch.setattr(
        ChatExternalActionOrchestrationService,
        "_resolve_max_calls",
        classmethod(lambda cls, max_calls: 4),
    )

    planned = [{"actionId": "production_schedule", "parameters": {}}]
    merged = ChatExternalActionOrchestrationService._merge_turn_analysis_action_ids(
        FakeSelection(),
        planned=planned,
        workspace_context={
            "turnAnalysisActionIds": ["production_schedule", "quality_kpi"],
        },
        allowed_action_ids=["production_schedule", "quality_kpi"],
        message="programação e qualidade",
        raw_message=None,
        conversation_context=None,
        previous_messages=None,
        memory_snapshot=None,
        max_calls=4,
    )

    assert [item["actionId"] for item in merged] == [
        "production_schedule",
        "quality_kpi",
    ]
    assert merged[1].get("fromTurnAnalysis") is True


def test_fast_budget_keeps_first_and_continuation_chips(monkeypatch):
    from app.application.services.chat_multi_intent_continuation_service import (
        ChatMultiIntentContinuationService,
    )

    class FakeSelection:
        def select_action(self, message, *, allowed_action_ids=None, **kwargs):
            action_id = (allowed_action_ids or ["x"])[0]
            return {
                "actionId": action_id,
                "arguments": {"path": f"/products/{{code}}/{action_id}"},
                "reason": "pick",
            }

    monkeypatch.setattr(
        "app.application.services.chat_intelligence_runtime_access.resolve_chat_intelligence_runtime",
        lambda: type("R", (), {"multi_action_enabled": True})(),
    )
    monkeypatch.setattr(
        ChatExternalActionOrchestrationService,
        "_resolve_max_calls",
        classmethod(lambda cls, max_calls: 1),
    )
    monkeypatch.setattr(
        ChatExternalActionOrchestrationService,
        "_mode_multi_action_cap",
        classmethod(lambda cls: 1),
    )

    merged = ChatExternalActionOrchestrationService._merge_turn_analysis_action_ids(
        FakeSelection(),
        planned=[{"actionId": "stock", "arguments": {"path": "/products/{code}/stock"}}],
        workspace_context={"turnAnalysisActionIds": ["stock", "suppliers"]},
        allowed_action_ids=["stock", "suppliers"],
        message="estoque e fornecedores 10080022",
        raw_message=None,
        conversation_context=None,
        previous_messages=None,
        memory_snapshot=None,
        max_calls=1,
    )
    executed, continuation = ChatMultiIntentContinuationService.apply_limit(
        merged,
        max_calls=1,
    )

    assert [item["actionId"] for item in executed] == ["stock"]
    assert continuation is not None
    assert continuation["deferredCount"] == 1
    chips = ChatMultiIntentContinuationService.build_follow_up_suggestions(continuation)
    assert chips
