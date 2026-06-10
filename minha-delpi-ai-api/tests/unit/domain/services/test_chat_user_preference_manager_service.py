from app.domain.services.chat_behavior_instruction_service import (
    ChatBehaviorInstructionService,
)
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


def test_revoke_preferences_volte_ao_normal():
    snapshot = ChatUserPreferenceManagerService.apply_to_snapshot(
        {
            "behaviorInstructions": {"tone": "formal"},
            "userPreferences": {"behavior": {"tone": "formal"}},
        },
        message="volte ao normal",
    )

    assert snapshot.get("preferencesRevoked") is True
    assert snapshot.get("userPreferences") == {}


def test_revoke_ack_direct_answer():
    ack = ChatUserPreferenceManagerService.build_ack_direct_answer("volte ao normal")

    assert ack is not None
    assert "padrão" in ack

    ack2 = ChatUserPreferenceManagerService.build_ack_direct_answer(
        "esqueça essa preferência"
    )

    assert ack2 is not None


def test_text_only_preference_detected_and_labeled():
    detected = ChatBehaviorInstructionService.detect("sempre em txt")

    assert detected.get("responseFormat") == "text"
    assert detected.get("scope") == "session"

    snapshot = ChatUserPreferenceManagerService.apply_to_snapshot(
        {"behaviorInstructions": detected},
        message="sempre em txt",
    )
    labels = snapshot.get("preferencesAppliedLabels") or []

    assert "Respostas em texto puro" in labels


def test_table_preference_syncs_to_behavior_instructions_for_tools():
    post = ChatConversationMemoryService.build_post_turn(
        message="daqui pra frente responda em tabela",
        previous_messages=[],
        tool_calls=[],
        pre_snapshot=ChatConversationMemoryService.build_pre_turn(
            message="daqui pra frente responda em tabela",
            previous_messages=[],
        ),
        answer="Combinado.",
    )
    previous = [
        {
            "role": "assistant",
            "metadata": {"contextSnapshot": post},
        }
    ]
    turn = ChatConversationMemoryService.build_pre_turn(
        message="estoque do produto 10080001",
        previous_messages=previous,
    )

    behavior = turn.get("behaviorInstructions") or {}

    assert behavior.get("responseFormat") == "table"

    from app.application.services.chat_tool_context_format_service import (
        ChatToolContextFormatService,
    )

    assert (
        ChatToolContextFormatService.session_response_format(
            {"workingMemory": turn},
        )
        == "table"
    )


def test_tools_on_request_preference_is_persistent():
    detected = ChatBehaviorInstructionService.detect("não use ferramentas sem eu pedir")

    assert detected.get("toolsPolicy") == "on_request"
    assert detected.get("scope") == "session"

    snapshot = ChatUserPreferenceManagerService.apply_to_snapshot(
        {"behaviorInstructions": detected},
        message="não use ferramentas sem eu pedir",
    )
    labels = snapshot.get("preferencesAppliedLabels") or []

    assert "Não usar ferramentas sem pedir" in labels

    ack = ChatUserPreferenceManagerService.build_ack_direct_answer(
        "não use ferramentas sem eu pedir"
    )

    assert ack is not None
    assert "ferramentas" in ack


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
