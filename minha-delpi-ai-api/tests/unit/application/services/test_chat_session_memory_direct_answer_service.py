from app.application.services.chat_session_memory_direct_answer_service import (
    ChatSessionMemoryDirectAnswerService,
)


def test_preference_ack_short_answers():
    answer = ChatSessionMemoryDirectAnswerService.build(
        message="daqui pra frente responda curto",
        workspace_context={"workingMemory": {}},
    )

    assert answer is not None
    assert "Combinado" in answer
    assert "curta" in answer.lower()


def test_no_ack_on_operational_follow_up():
    answer = ChatSessionMemoryDirectAnswerService.build(
        message="agora estoque",
        workspace_context={
            "workingMemory": {"lastEntities": {"productCode": "10080001"}},
        },
    )

    assert answer is None


def test_ambiguity_answer():
    answer = ChatSessionMemoryDirectAnswerService.build(
        message="compare com o anterior",
        workspace_context={
            "workingMemory": {
                "memoryAmbiguity": {
                    "candidates": ["10080001", "20090002"],
                },
            },
        },
    )

    assert answer is not None
    assert "10080001" in answer
    assert "20090002" in answer


def test_memory_introspection_m20():
    answer = ChatSessionMemoryDirectAnswerService.build(
        message="quais informações você está usando?",
        workspace_context={
            "workingMemory": {
                "lastEntities": {"productCode": "10080001"},
            },
            "memoryUx": {
                "summary": "Produto 10080001",
                "usage": {
                    "preferences": ["Respostas curtas"],
                    "entities": ["Produto 10080001"],
                },
            },
        },
    )

    assert answer is not None
    assert "10080001" in answer or "Produto" in answer
