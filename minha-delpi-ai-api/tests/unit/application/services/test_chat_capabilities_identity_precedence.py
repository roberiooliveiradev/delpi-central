from app.application.services.chat_assistant_identity_service import (
    ChatAssistantIdentityService,
)
from app.application.services.chat_capabilities_service import ChatCapabilitiesService


def test_capabilities_question_skips_identity_role():
    message = "o que vc faz?"

    assert ChatCapabilitiesService.is_capabilities_question(message)
    assert ChatAssistantIdentityService.classify(message) is None


def test_common_chat_capabilities_intro():
    text = ChatCapabilitiesService.build_direct_answer(
        workspace_context={
            "agent": None,
            "userActivatedAgent": False,
        },
        allowed_action_ids=[],
        action_catalog=[],
    )

    assert text
    assert "chat comum" in text.lower()
    assert "sem agente ativo" in text.lower()


def test_agent_capabilities_intro_lists_agent_actions():
    text = ChatCapabilitiesService.build_direct_answer(
        workspace_context={
            "agent": {
                "name": "Agente Minha DELPI",
                "description": "Consultas operacionais de produto",
                "category": "engineering",
            },
            "userActivatedAgent": True,
        },
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

    assert "Agente Minha DELPI" in text
    assert "deste agente" in text.lower()
    assert "Estoque" in text
