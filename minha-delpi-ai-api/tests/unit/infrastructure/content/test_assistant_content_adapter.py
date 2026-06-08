from app.domain.services.chat_assistant_content_service import ChatAssistantContentService
from app.infrastructure.content.assistant_content_adapter import (
    InfrastructureAssistantContentAdapter,
)


def test_adapter_loads_assistant_bundle():
    adapter = InfrastructureAssistantContentAdapter()
    ChatAssistantContentService.configure(adapter)

    labels = ChatAssistantContentService.get_mapping("stream", "activity", "phaseGroups")

    assert labels.get("tools") == "Consultando"


def test_adapter_loads_personality_playbook():
    adapter = InfrastructureAssistantContentAdapter()
    data = adapter.load_personality_playbook()

    assert isinstance(data.get("feedbackReasons"), list)
