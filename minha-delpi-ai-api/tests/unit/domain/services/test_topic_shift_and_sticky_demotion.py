"""Topic shift demotes sticky authority; resume keeps ledger referenciável."""

from __future__ import annotations

from app.domain.services.chat_conversation_state_service import ChatConversationStateService
from app.domain.services.chat_planner_conversation_context_service import (
    ChatPlannerConversationContextService,
)


def test_topic_change_marks_sticky_inactive_and_keeps_ledger():
    pre = ChatConversationStateService.apply_pre_turn(
        {
            "conversationState": {
                "activeTopic": "estoque",
                "activeTopicId": "topic-1",
                "topics": [
                    {
                        "topicId": "topic-1",
                        "label": "estoque",
                        "entities": {"code": "10080055"},
                        "resolvedArguments": {},
                        "lastSuccessfulActionIds": ["stock-action"],
                        "timeRange": {},
                    }
                ],
                "activeTask": {"type": "ops", "label": "estoque"},
                "taskStack": [],
            }
        },
        message="agora vamos falar de programação",
        previous_messages=[],
    )
    state = pre["conversationState"]
    assert pre.get("preferencesTopicChanged") is True
    assert state.get("stickyContextActive") is False
    assert state.get("topics")  # previous topic remains referenciável


def test_planner_context_omits_last_action_parameters():
    previous = [
        {
            "role": "assistant",
            "metadata": {
                "toolCalls": [
                    {
                        "name": "execute_external_action",
                        "arguments": {
                            "actionId": "stock-action",
                            "parameters": {"code": "OLD"},
                        },
                        "metadata": {"ok": True, "path": "/products/1/stock"},
                    }
                ]
            },
        }
    ]
    ctx = ChatPlannerConversationContextService.build(
        previous_messages=previous,
        workspace_context={
            "workingMemory": {
                "operationalFocus": {"entities": {"code": "OLD"}},
                "conversationState": {"preferencesTopicChanged": True, "stickyContextActive": False},
            }
        },
        execution_context=None,
    )
    assert "OLD" not in ctx or '"parameters"' not in ctx
    assert '"role": "evidence"' in ctx or '"role":"evidence"' in ctx
    assert "contextPrecedence" in ctx
