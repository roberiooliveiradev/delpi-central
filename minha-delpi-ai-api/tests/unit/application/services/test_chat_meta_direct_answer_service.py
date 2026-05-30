from unittest.mock import MagicMock
from uuid import uuid4

from app.application.services.chat_assistant_identity_service import (
    ChatAssistantIdentityService,
)
from app.application.services.chat_capabilities_service import ChatCapabilitiesService
from app.application.services.chat_meta_direct_answer_service import (
    ChatMetaDirectAnswerService,
)
from app.application.services.chat_turn.chat_turn_preparation_service import (
    ChatTurnPreparationService,
)
from app.application.services.chat_user_context_service import ChatUserContextService


def test_detect_compound_meta_intents():
    message = "me diga quem sou eu e o que consigo fazer aqui, quem é você?"

    intents = ChatMetaDirectAnswerService.detect_intents(message)

    assert intents.user_profile is True
    assert intents.capabilities is True
    assert intents.assistant_identity is True
    assert intents.count == 3


def test_assistant_identity_classifies_in_compound_question():
    category = ChatAssistantIdentityService.classify(
        "me diga quem sou eu e o que consigo fazer aqui, quem é você?"
    )

    assert category == "who"


def test_capabilities_detects_consigo_fazer_aqui():
    assert ChatCapabilitiesService.is_capability_inquiry(
        "o que consigo fazer aqui"
    )


def test_meta_direct_answer_composes_three_sections():
    message = "me diga quem sou eu e o que consigo fazer aqui, quem é você?"
    workspace_context = {"agent": None, "agentId": None, "skills": {}}

    answer = ChatMetaDirectAnswerService.build(
        message=message,
        workspace_context=workspace_context,
        resolve_user_identity_answer=lambda _msg: (
            "**Seu perfil na Minha DELPI:**\n\n- **Nome:** Robério"
        ),
        resolve_capabilities_answer=lambda _msg: (
            "Posso ajudar você nestes formatos:\n\n- Documentação autorizada."
        ),
    )

    assert answer
    assert "Organizei sua pergunta" in answer
    assert "## Seu perfil na Minha DELPI" in answer
    assert "## O que você pode fazer aqui" in answer
    assert "## Sobre o assistente" in answer
    assert "Robério" in answer
    assert "Documentação autorizada" in answer
    assert "Minha DELPI" in answer


def test_turn_preparation_uses_meta_direct_answer_for_compound_question():
    session = MagicMock()
    session.id = uuid4()
    request = MagicMock()
    request.attachment_ids = None

    rag_context_service = MagicMock()
    message = "me diga quem sou eu e o que consigo fazer aqui, quem é você?"

    prepared = ChatTurnPreparationService(rag_context_service=rag_context_service).prepare(
        message=message,
        request=request,
        session=session,
        user_id=uuid4(),
        workspace_context={"skills": {"companyKnowledge": True}},
        attachments=[],
        previous_messages=[],
        history_source=[],
        build_tool_context=MagicMock(
            return_value={
                "context": "",
                "toolCalls": [],
                "nativeToolCalling": {},
            }
        ),
        maybe_extend_tool_context=lambda **kwargs: kwargs["tool_context"],
        prepare_history=lambda history: ("", list(history)),
        history_keep=12,
        fast_path_enabled=True,
        fast_path_max_chars=30,
        resolve_user_identity_answer=lambda _msg: "- **Nome:** Robério",
        resolve_capabilities_answer=lambda _msg: "- Documentação autorizada.",
    )

    assert prepared.direct_answer
    assert prepared.skip_rag is True
    assert "meta_direct_answer" in prepared.pipeline_stages
    assert "## Seu perfil na Minha DELPI" in prepared.direct_answer
    assert "## O que você pode fazer aqui" in prepared.direct_answer
    assert "## Sobre o assistente" in prepared.direct_answer
    rag_context_service.build_context.assert_not_called()
