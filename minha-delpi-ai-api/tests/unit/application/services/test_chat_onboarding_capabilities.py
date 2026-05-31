from app.application.services.chat_capabilities_service import ChatCapabilitiesService


def test_resolve_capability_answer_training_mode():
    answer = ChatCapabilitiesService.resolve_capability_answer(
        message="me ensine a usar",
        workspace_context={},
        allowed_action_ids=[],
        action_catalog=[],
    )

    assert answer
    assert "Guia rápido" in answer
