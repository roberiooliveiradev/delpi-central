from app.domain.services.chat_conversation_memory_service import (
    ChatConversationMemoryService,
)
from app.domain.services.chat_user_preference_manager_service import (
    ChatUserPreferenceManagerService,
)


def test_m2_correction_preference_persists_across_turn():
    turn1 = ChatConversationMemoryService.build_pre_turn(
        message="daqui pra frente corrija sem explicar",
        previous_messages=[],
    )
    post1 = ChatConversationMemoryService.build_post_turn(
        message="daqui pra frente corrija sem explicar",
        previous_messages=[],
        tool_calls=[],
        pre_snapshot=turn1,
        answer="Combinado.",
    )
    previous = [
        {
            "role": "assistant",
            "content": "ok",
            "metadata": {"contextSnapshot": post1},
        }
    ]
    turn2 = ChatConversationMemoryService.build_pre_turn(
        message="corrija: o produto esta bloqueado",
        previous_messages=previous,
    )
    prefs = turn2.get("userPreferences") or {}
    correction = prefs.get("textCorrection") or {}
    behavior = prefs.get("behavior") or {}

    assert (
        correction.get("deliverFinalOnly")
        or (turn2.get("textCorrectionPreferences") or {}).get("deliverFinalOnly")
        or behavior.get("finalVersionOnly") == "true"
    )


def test_m9_topic_change_clears_session_preferences():
    post_short = ChatConversationMemoryService.build_post_turn(
        message="daqui pra frente responda curto",
        previous_messages=[],
        tool_calls=[],
        pre_snapshot=ChatConversationMemoryService.build_pre_turn(
            message="daqui pra frente responda curto",
            previous_messages=[],
        ),
        answer="ok",
    )
    previous = [
        {
            "role": "assistant",
            "metadata": {
                "contextSnapshot": {
                    **post_short,
                    "userPreferences": {
                        "scope": "session",
                        "behavior": {"answerLength": "short"},
                    },
                },
            },
        }
    ]
    snapshot = ChatConversationMemoryService.build_pre_turn(
        message="agora vamos falar de outro assunto: estoque",
        previous_messages=previous,
    )

    assert snapshot.get("preferencesTopicChanged") is True
    behavior = (snapshot.get("userPreferences") or {}).get("behavior") or {}

    assert behavior.get("answerLength") != "short"


def test_revoke_preferences():
    snapshot = ChatUserPreferenceManagerService.apply_to_snapshot(
        {
            "behaviorInstructions": {"tone": "formal"},
            "userPreferences": {"behavior": {"tone": "formal"}},
        },
        message="não use mais preferências de tom",
    )

    assert snapshot.get("preferencesRevoked") is True
    assert snapshot.get("userPreferences") == {}


def test_unified_prompt_block():
    snapshot = {
        "userPreferences": {
            "behavior": {"answerLength": "short", "tone": "formal"},
        },
        "preferencesAppliedLabels": ["Respostas curtas", "Tom formal"],
    }
    block = ChatUserPreferenceManagerService.format_prompt_block(snapshot)

    assert block is not None
    assert "Preferências ativas" in block
