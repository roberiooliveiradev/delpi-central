from app.application.services.chat_soft_agent_handoff_service import (
    ChatSoftAgentHandoffService,
)


def _active_workspace() -> dict:
    return {"userActivatedAgent": True, "actionsEnabled": True}


def test_should_offer_when_tools_miss_on_operational_query():
    assert ChatSoftAgentHandoffService.should_offer(
        message="qual o estoque 10080047",
        workspace_context=_active_workspace(),
        tool_calls=[],
        tool_context={"selectedExternalAction": None},
        pipeline_stages=["tools"],
        intent_route={"intent": "operational_query", "requiresTool": True},
    )


def test_should_not_offer_when_agent_inactive():
    assert not ChatSoftAgentHandoffService.should_offer(
        message="qual o estoque 10080047",
        workspace_context={"userActivatedAgent": False, "actionsEnabled": False},
        tool_calls=[],
        tool_context={},
        pipeline_stages=["tools"],
        intent_route={"intent": "operational_query", "requiresTool": True},
    )


def test_should_not_offer_when_external_action_selected():
    assert not ChatSoftAgentHandoffService.should_offer(
        message="qual o estoque 10080047",
        workspace_context=_active_workspace(),
        tool_calls=[],
        tool_context={"selectedExternalAction": {"actionId": "stock-action"}},
        pipeline_stages=["tools"],
        intent_route={"intent": "operational_query", "requiresTool": True},
    )


def test_should_not_offer_for_small_talk():
    assert not ChatSoftAgentHandoffService.should_offer(
        message="obrigado",
        workspace_context=_active_workspace(),
        tool_calls=[],
        tool_context={},
        pipeline_stages=["tools"],
        intent_route={"intent": "small_talk", "requiresTool": False},
    )


def test_build_follow_up_suggestions_uses_switch_action():
    items = ChatSoftAgentHandoffService.build_follow_up_suggestions(
        "qual o estoque 10080047"
    )
    assert len(items) == 1
    assert items[0]["query"] == "qual o estoque 10080047"
    assert items[0]["action"] == "switch_agent_and_resend"
    assert "trocar" in items[0]["label"].lower() or "agente" in items[0]["label"].lower()


def test_attach_sets_pending_and_soft_flag_without_auto_activate():
    metadata: dict = {
        "followUpSuggestions": [{"label": "Outro chip", "query": "outro"}],
    }
    ChatSoftAgentHandoffService.attach_to_assistant_metadata(
        metadata,
        message="qual o estoque 10080047",
        workspace_context=_active_workspace(),
        tool_calls=[],
        tool_context={"selectedExternalAction": None},
        pipeline_stages=["tools", "direct_answer"],
        intent_route={"intent": "operational_query", "requiresTool": True},
    )

    assert metadata["pendingOperationalQuery"] == "qual o estoque 10080047"
    assert metadata["softAgentHandoff"] is True
    assert metadata["followUpSuggestions"][0]["action"] == "switch_agent_and_resend"
    assert metadata["followUpSuggestions"][0]["query"] == "qual o estoque 10080047"
    # Não auto-ativa: só metadata de sugestão / pending.
    assert "agentId" not in metadata or metadata.get("agentId") is None


def test_attach_skips_when_not_applicable():
    metadata: dict = {}
    ChatSoftAgentHandoffService.attach_to_assistant_metadata(
        metadata,
        message="qual o estoque 10080047",
        workspace_context=_active_workspace(),
        tool_calls=[{"name": "execute_external_action", "metadata": {"path": "/stock"}}],
        tool_context={"selectedExternalAction": {"actionId": "x"}},
        pipeline_stages=["tools"],
        intent_route={"intent": "operational_query", "requiresTool": True},
    )
    assert "softAgentHandoff" not in metadata
    assert "pendingOperationalQuery" not in metadata
