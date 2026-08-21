from app.domain.services.chat_assistant_content_service import ChatAssistantContentService
from app.domain.services.chat_conversation_state_service import ChatConversationStateService


def test_conversation_state_task_patterns_from_json():
    patterns = ChatAssistantContentService.get_node("conversation_state", "taskPatterns")

    assert isinstance(patterns, list)
    types = {str(row.get("type")) for row in patterns if isinstance(row, dict)}
    assert "drawing_analysis" in types
    assert "documentation" in types


def test_revisao_manual_is_drawing_analysis_not_documentation():
    snapshot = ChatConversationStateService.apply_pre_turn(
        {},
        message="confirmar revisão manual do item pendente no relatório do desenho 90261899",
    )
    task = (snapshot.get("conversationState") or {}).get("activeTask") or {}

    assert task.get("type") == "drawing_analysis"


def test_manual_de_procedimento_still_documentation():
    snapshot = ChatConversationStateService.apply_pre_turn(
        {},
        message="escreva o manual de procedimento de qualidade",
    )
    task = (snapshot.get("conversationState") or {}).get("activeTask") or {}

    assert task.get("type") == "documentation"
