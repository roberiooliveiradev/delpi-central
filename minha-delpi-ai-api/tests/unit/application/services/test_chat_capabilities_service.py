from app.application.services.chat_capabilities_service import ChatCapabilitiesService


def test_is_capabilities_question():
    assert ChatCapabilitiesService.is_capabilities_question("o que você pode fazer?")
    assert ChatCapabilitiesService.is_capabilities_question("quais suas capacidades")
    assert not ChatCapabilitiesService.is_capabilities_question("estoque do 10080001")


def test_build_direct_answer_common_chat():
    text = ChatCapabilitiesService.build_direct_answer(
        workspace_context={"agent": None, "agentKey": None},
        allowed_action_ids=[],
        action_catalog=[],
    )
    assert text
    assert "chat comum" in text.lower() or "agente" in text.lower()
    assert "get_current_user" not in text


def test_build_direct_answer_with_agent_actions():
    text = ChatCapabilitiesService.build_direct_answer(
        workspace_context={"agent": {"name": "Especialista"}, "agentKey": "esp"},
        allowed_action_ids=["act.stock"],
        action_catalog=[
            {
                "actionId": "act.stock",
                "method": "GET",
                "path": "/products/{code}/stock",
                "summary": "Estoque do produto",
            },
        ],
    )
    assert "Especialista" in text
    assert "Estoque" in text
    assert "/products/" in text
