"""Regressão — playbook memória e contexto (§79 M1–M15)."""

from __future__ import annotations

import pytest

from app.application.services.chat_session_memory_direct_answer_service import (
    ChatSessionMemoryDirectAnswerService,
)
from app.domain.services.chat_conversation_memory_service import (
    ChatConversationMemoryService,
)
from app.domain.services.chat_conversation_state_service import (
    ChatConversationStateService,
)
from app.domain.services.chat_reference_resolution_service import (
    ChatReferenceResolutionService,
)
from tests.fixtures.memory_context_regression_cases import (
    MEMORY_CONTEXT_REGRESSION_CASES,
)


def _assistant_with_stock(product_code: str = "10080001"):
    return {
        "role": "assistant",
        "content": f"Estoque do produto {product_code}",
        "metadata": {
            "toolCalls": [
                {
                    "name": "execute_external_action",
                    "metadata": {
                        "ok": True,
                        "path": f"/products/{product_code}/stock",
                        "presentation": {"type": "table", "title": "Estoque"},
                    },
                }
            ],
            "contextSnapshot": {
                "lastEntities": {"productCode": product_code},
                "conversationState": {
                    "activeTopic": "estoque",
                    "activeTask": {
                        "type": "stock_lookup",
                        "label": "estoque",
                        "status": "in_progress",
                    },
                },
            },
        },
    }


@pytest.mark.parametrize("case", MEMORY_CONTEXT_REGRESSION_CASES, ids=lambda c: c["id"])
def test_memory_context_case_registered(case: dict):
    assert case["id"].startswith("M")


def test_m1_product_follow_up():
    snapshot = ChatConversationMemoryService.build_pre_turn(
        message="e os fornecedores?",
        previous_messages=[_assistant_with_stock()],
    )

    assert snapshot["lastEntities"].get("productCode") == "10080001"
    assert snapshot["followUpDetected"] is True


def test_m3_proximo_without_task_asks_clarification():
    snapshot = ChatConversationMemoryService.build_pre_turn(
        message="próximo",
        previous_messages=[],
    )

    assert snapshot.get("continuationMissingContext") is True
    answer = ChatSessionMemoryDirectAnswerService.build(
        message="próximo",
        workspace_context={"workingMemory": snapshot},
    )

    assert answer is not None
    assert "sequência" in answer.lower() or "tarefa" in answer.lower()


def test_m3_proximo_with_playbook_task_continues():
    previous = [
        {
            "role": "assistant",
            "content": "Playbook SQL",
            "metadata": {
                "contextSnapshot": {
                    "conversationState": {
                        "activeTopic": "playbook",
                        "activeTask": {
                            "type": "playbook_creation",
                            "label": "playbook",
                            "status": "in_progress",
                            "objective": "playbook SQL",
                        },
                    },
                },
            },
        }
    ]
    snapshot = ChatConversationMemoryService.build_pre_turn(
        message="próximo",
        previous_messages=previous,
    )

    assert snapshot.get("continuationRequested") is True
    assert snapshot.get("continuationMissingContext") is not True
    block = ChatConversationStateService.format_prompt_block(snapshot)

    assert block is not None
    assert "próximo" in block.lower() or "tarefa" in block.lower()


def test_m4_isso_resolves_single_table():
    snapshot = {
        "lastEntities": {},
        "lastPresentation": {"type": "table", "messageId": "msg-table"},
        "canvas": {"active": False},
    }
    resolved, used = ChatReferenceResolutionService.resolve_from_snapshot(
        "resuma isso em tópicos",
        snapshot,
    )

    assert not snapshot.get("memoryAmbiguity")
    assert used == ["lastPresentation"]
    assert resolved[0]["resolvedTo"] == "lastPresentation"


def test_m5_isso_ambiguous_when_multiple_artifacts():
    snapshot = {
        "lastPresentation": {"type": "table", "messageId": "msg-1"},
        "canvas": {"active": True, "lastUpdatedFromMessageId": "msg-2"},
        "lastAttachment": {"filename": "dados.pdf"},
    }
    resolved, used = ChatReferenceResolutionService.resolve_from_snapshot("explique isso", snapshot)

    assert snapshot.get("memoryAmbiguity", {}).get("reason") == "this_reference"
    assert len(resolved) == 0 or not used


def test_m6_user_correction_stored():
    snapshot = ChatConversationMemoryService.build_pre_turn(
        message="Não é DELPI Central, é Minha DELPI",
        previous_messages=[],
    )
    state = snapshot.get("conversationState") or {}
    corrections = state.get("userCorrections") or []

    assert len(corrections) >= 1
    assert "Minha DELPI" in corrections[-1].get("content", "")


def test_compare_previous_sets_ambiguity_when_two_products_in_history():
    previous = [
        {"role": "user", "content": "produto 10080001"},
        {
            "role": "assistant",
            "content": "Produto 10080001",
            "metadata": {
                "contextSnapshot": {
                    "lastEntities": {"productCode": "10080001"},
                    "previousProductCodes": [],
                }
            },
        },
        {"role": "user", "content": "agora produto 10080002"},
        {
            "role": "assistant",
            "content": "Estoque do produto",
            "metadata": {
                "contextSnapshot": {
                    "lastEntities": {"productCode": "10080002"},
                    "previousProductCodes": ["10080001"],
                }
            },
        },
    ]
    snapshot = ChatConversationMemoryService.build_pre_turn(
        message="compare com o anterior",
        previous_messages=previous,
    )

    ambiguity = snapshot.get("memoryAmbiguity") or {}

    assert ambiguity.get("reason") == "compare_previous"
    assert "10080001" in (ambiguity.get("candidates") or [])
    assert "10080002" in (ambiguity.get("candidates") or [])


def test_m1_fornecedores_reference_hint():
    snapshot = ChatConversationMemoryService.build_pre_turn(
        message="e os fornecedores?",
        previous_messages=[_assistant_with_stock("10080022")],
    )

    hints = snapshot.get("referenceHints") or {}

    assert "fornecedores" in hints
    assert "10080022" in hints["fornecedores"]


def test_m8_resume_sql_task_from_stack():
    previous = [
        {
            "role": "assistant",
            "metadata": {
                "contextSnapshot": {
                    "conversationState": {
                        "activeTask": None,
                        "taskStack": [
                            {
                                "type": "sql_task",
                                "label": "SQL",
                                "status": "paused",
                                "objective": "consulta vendas",
                            }
                        ],
                    },
                },
            },
        }
    ]
    snapshot = ChatConversationMemoryService.build_pre_turn(
        message="retome a consulta SQL",
        previous_messages=previous,
    )
    task = (snapshot.get("conversationState") or {}).get("activeTask") or {}

    assert task.get("type") == "sql_task"
    assert task.get("status") == "in_progress"


def test_m12_sql_column_edit_resolves_last_sql():
    previous = [
        {
            "role": "assistant",
            "content": "SELECT id, nome FROM produtos",
            "metadata": {"sqlAdvanced": {"workspace": {"currentSql": "SELECT id, nome FROM produtos"}}},
        }
    ]
    snapshot = ChatConversationMemoryService.build_pre_turn(
        message="adicione coluna preco na consulta",
        previous_messages=previous,
    )

    assert "lastSqlSnippet" in (snapshot.get("activeEntities") or {})
    resolved, used = ChatReferenceResolutionService.resolve_from_snapshot(
        "adicione coluna preco",
        snapshot,
    )

    assert "lastSqlSnippet" in used


def test_m7_topic_change_pauses_task():
    previous = [
        {
            "role": "assistant",
            "metadata": {
                "contextSnapshot": {
                    "conversationState": {
                        "activeTask": {
                            "type": "playbook_creation",
                            "label": "SQL",
                            "status": "in_progress",
                        },
                    },
                },
            },
        }
    ]
    snapshot = ChatConversationMemoryService.build_pre_turn(
        message="agora vamos falar de estoque do produto 10080001",
        previous_messages=previous,
    )
    state = snapshot.get("conversationState") or {}

    assert len(state.get("taskStack") or []) >= 1
    assert state.get("activeTopic")


def test_m10_correction_in_prompt_block():
    snapshot = ChatConversationMemoryService.build_pre_turn(
        message="Não é DELPI Central, é Minha DELPI",
        previous_messages=[],
    )
    block = ChatConversationStateService.format_prompt_block(snapshot)

    assert block is not None
    assert "Correção do usuário" in block


def test_m14_sensitive_skips_memory_write_flag():
    snapshot = ChatConversationMemoryService.build_pre_turn(
        message="minha senha é abc123",
        previous_messages=[],
    )

    assert snapshot.get("conversationState", {}).get("skipMemoryWrite") is True


def test_m15_clear_context_wipes_conversation_state():
    snapshot = ChatConversationMemoryService.build_pre_turn(
        message="limpe o contexto",
        previous_messages=[
            {
                "role": "assistant",
                "metadata": {
                    "contextSnapshot": {
                        "conversationState": {
                            "activeTopic": "x",
                            "activeTask": {"type": "t"},
                        },
                    },
                },
            }
        ],
    )

    state = snapshot.get("conversationState") or {}

    assert state.get("activeTask") is None
    assert state.get("activeTopic") is None


def test_m16_semantic_memory_requested_for_documentation():
    snapshot = ChatConversationMemoryService.build_pre_turn(
        message="Como funciona a autorização RBAC?",
        previous_messages=[],
    )

    assert snapshot.get("semanticMemoryRequested") is True
    assert snapshot.get("semanticMemoryQuery")
    assert snapshot.get("proceduralMemoryHints") or snapshot.get("semanticMemoryIntent")


def test_m17_episodic_recall_from_prior_snapshot():
    previous = [
        {
            "role": "assistant",
            "content": "ok",
            "metadata": {
                "contextSnapshot": {
                    "episodicMemory": [
                        {
                            "episodeId": "e1",
                            "taskType": "playbook_creation",
                            "topic": "playbook memória",
                            "summary": "Rascunho do playbook.",
                        },
                    ],
                },
            },
        },
    ]
    snapshot = ChatConversationMemoryService.build_pre_turn(
        message="Use o mesmo padrão do playbook anterior",
        previous_messages=previous,
    )

    assert snapshot.get("episodicRecall") or snapshot.get("episodicRecallMissing")


def test_m10_memory_contradiction_via_pipeline():
    snapshot = ChatConversationMemoryService.build_pre_turn(
        message="Agora quero respostas completas e detalhadas",
        previous_messages=[
            {"role": "user", "content": "daqui pra frente respostas curtas"},
            {"role": "assistant", "content": "Combinado."},
        ],
    )

    assert snapshot.get("memoryContradictionResolved") or snapshot.get("supersededMemory")


def test_post_turn_preserves_snippet():
    pre = {
        "conversationState": {
            "activeTask": {"type": "playbook_creation", "status": "in_progress"},
        }
    }
    post = ChatConversationMemoryService.build_post_turn(
        message="continue",
        previous_messages=[],
        tool_calls=[],
        pre_snapshot=pre,
        answer="Segue a seção de métricas do playbook.",
    )

    assert "métricas" in (post.get("conversationState") or {}).get(
        "lastUsefulAssistantSnippet", ""
    )
