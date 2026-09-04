"""E3.S1 — entendimento do turno em shadow (decomposição em subtarefas)."""

from __future__ import annotations

import pytest

from app.domain.services.chat_conversational_intelligence_flag_service import (
    ChatConversationalIntelligenceFlagService,
)
from app.domain.services.chat_turn_understanding_service import (
    ChatTurnUnderstandingService,
)

_FIVE_SUBTASK_MESSAGE = (
    "1. qual o estoque do 10080001\n"
    "2. quais fornecedores desse produto\n"
    "3. mostra a estrutura dele\n"
    "4. compara com o mes passado\n"
    "5. envia um resumo por e-mail"
)


def test_enumerated_message_with_five_items_yields_five_subtasks():
    understanding = ChatTurnUnderstandingService.analyze(_FIVE_SUBTASK_MESSAGE)

    assert understanding.subtask_count >= 5
    assert [item.id for item in understanding.subtasks[:5]] == [
        "st-1",
        "st-2",
        "st-3",
        "st-4",
        "st-5",
    ]


def test_subtasks_keep_their_own_goal_text():
    understanding = ChatTurnUnderstandingService.analyze(_FIVE_SUBTASK_MESSAGE)
    goals = [item.goal for item in understanding.subtasks]

    assert any("10080001" in goal for goal in goals)
    assert any("fornecedores" in goal for goal in goals)
    assert any("e-mail" in goal for goal in goals)


def test_dependent_subtask_declares_previous_dependency():
    understanding = ChatTurnUnderstandingService.analyze(_FIVE_SUBTASK_MESSAGE)
    dependent = understanding.subtasks[1]

    assert dependent.goal.startswith("quais fornecedores desse")
    assert dependent.depends_on == ("st-1",)


def test_hard_separator_splits_compound_request():
    understanding = ChatTurnUnderstandingService.analyze(
        "estoque do 10080001; fornecedores do 10080001; vendas do 10080001"
    )

    assert understanding.subtask_count == 3


def test_action_subtask_is_typed_as_action():
    understanding = ChatTurnUnderstandingService.analyze(
        "1. qual o estoque do 10080001\n2. envia o resultado por e-mail"
    )

    assert {item.type for item in understanding.subtasks} >= {"action"}


def test_single_intent_message_stays_with_one_subtask():
    understanding = ChatTurnUnderstandingService.analyze(
        "qual o estoque do produto 10080001?"
    )

    assert understanding.subtask_count == 1


def test_fast_mode_keeps_a_single_subtask():
    understanding = ChatTurnUnderstandingService.analyze(
        _FIVE_SUBTASK_MESSAGE,
        response_mode="fast",
    )

    assert understanding.subtask_count == 1


def test_empty_message_falls_back_to_placeholder_subtask():
    understanding = ChatTurnUnderstandingService.analyze("   ")

    assert understanding.subtask_count == 1
    assert understanding.subtasks[0].type == "unknown"


def test_shadow_is_none_when_flag_is_off(monkeypatch):
    monkeypatch.setattr(
        ChatConversationalIntelligenceFlagService,
        "turn_understanding_shadow_enabled",
        classmethod(lambda cls: False),
    )

    assert ChatTurnUnderstandingService.analyze_shadow(_FIVE_SUBTASK_MESSAGE) is None


def test_shadow_metadata_exposes_subtasks_without_driving_execution():
    understanding = ChatTurnUnderstandingService.analyze_shadow(
        _FIVE_SUBTASK_MESSAGE,
        enabled=True,
    )

    assert understanding is not None
    payload = understanding.as_admin_debug()
    assert payload["subtaskCount"] >= 5
    assert payload["source"] == "heuristic"
    assert len(payload["subtasks"]) >= 5


def test_continuation_hint_comes_from_last_user_message():
    understanding = ChatTurnUnderstandingService.analyze(
        "e o estoque?",
        previous_messages=[{"role": "user", "content": "quem fornece o 10080001?"}],
    )

    assert understanding.continuation_of == "quem fornece o 10080001?"


@pytest.mark.parametrize(
    "flag_key",
    ["turnUnderstandingShadow", "taskPlannerEnabled"],
)
def test_conversational_intelligence_flags_have_json_default(flag_key):
    assert isinstance(
        ChatConversationalIntelligenceFlagService.json_default(flag_key),
        bool,
    )


def test_task_planner_flag_is_off_by_default_until_cutover():
    assert (
        ChatConversationalIntelligenceFlagService.json_default("taskPlannerEnabled")
        is False
    )
