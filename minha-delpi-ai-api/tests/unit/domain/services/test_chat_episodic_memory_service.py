"""Testes — ChatEpisodicMemoryService (Fase 6)."""

from __future__ import annotations

from app.application.services.chat_session_memory_direct_answer_service import (
    ChatSessionMemoryDirectAnswerService,
)
from app.domain.services.chat_conversation_memory_service import (
    ChatConversationMemoryService,
)
from app.domain.services.chat_episodic_memory_service import ChatEpisodicMemoryService


def _assistant_with_episodes(episodes: list[dict]):
    return {
        "role": "assistant",
        "content": "ok",
        "metadata": {
            "contextSnapshot": {
                "episodicMemory": episodes,
                "conversationState": {
                    "activeTopic": "playbook",
                    "activeTask": {
                        "type": "playbook_creation",
                        "label": "playbook",
                        "status": "in_progress",
                    },
                },
            },
        },
    }


def test_recall_finds_playbook_episode():
    episodes = [
        {
            "episodeId": "e1",
            "taskType": "playbook_creation",
            "topic": "playbook",
            "summary": "Playbook memória e contexto em txt.",
        },
    ]
    snapshot = ChatEpisodicMemoryService.apply_pre_turn(
        {},
        message="Use o mesmo padrão do playbook anterior",
        previous_messages=[_assistant_with_episodes(episodes)],
    )

    assert snapshot.get("episodicRecall")
    assert "playbook" in str(snapshot["episodicRecall"].get("summary") or "").lower()


def test_recall_missing_sets_flag_and_direct_answer():
    snapshot = ChatEpisodicMemoryService.apply_pre_turn(
        {},
        message="Como fizemos no playbook anterior?",
        previous_messages=[],
    )

    assert snapshot.get("episodicRecallMissing")
    answer = ChatSessionMemoryDirectAnswerService.build(
        message="Como fizemos no playbook anterior?",
        workspace_context={"workingMemory": snapshot},
    )

    assert answer is not None
    assert "episódio" in answer.lower()


def test_post_turn_records_episode():
    snapshot = {
        "conversationState": {
            "activeTopic": "sql",
            "activeTask": {
                "type": "sql_task",
                "label": "SQL",
                "status": "in_progress",
                "objective": "consulta vendas",
            },
        },
    }
    updated = ChatEpisodicMemoryService.apply_post_turn(
        snapshot,
        message="monte a consulta",
        answer="SELECT 1 " + ("x" * 150),
    )

    assert updated.get("episodicMemory")
    assert updated.get("lastEpisodeRecorded")


def test_delete_episodes_clears_list():
    snapshot = ChatEpisodicMemoryService.apply_pre_turn(
        {"episodicMemory": [{"episodeId": "e1", "summary": "x"}]},
        message="Apague o histórico de episódio",
        previous_messages=[],
    )

    assert snapshot.get("episodicMemoryCleared")
    assert snapshot.get("episodicMemory") == []


def test_memory_pipeline_integrates_episodic_recall():
    previous = [
        _assistant_with_episodes(
            [
                {
                    "episodeId": "e1",
                    "taskType": "playbook_creation",
                    "topic": "playbook memória",
                    "summary": "Rascunho do playbook de memória.",
                },
            ]
        ),
    ]
    snapshot = ChatConversationMemoryService.build_pre_turn(
        message="Continue de onde paramos no playbook memória",
        previous_messages=previous,
    )

    assert snapshot.get("episodicRecall") or snapshot.get("episodicRecallMissing")
