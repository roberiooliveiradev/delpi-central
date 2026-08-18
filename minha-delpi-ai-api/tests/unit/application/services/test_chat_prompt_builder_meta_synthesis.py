from app.application.services.chat_prompt_builder_service import ChatPromptBuilderService
from app.composition.content_composer import configure_domain_infrastructure_ports
from app.domain.services.chat_meta_llm_synthesis_service import ChatMetaLlmSynthesisService
from app.domain.services.prompt_policy_service import PromptPolicyService

configure_domain_infrastructure_ports()


def test_meta_synthesis_omits_skill_wall_and_email_placeholder():
    builder = ChatPromptBuilderService(PromptPolicyService())
    messages = builder.build_messages(
        history=[],
        current_message="quem é vc?",
        rag_context="",
        tool_context="",
        skills={"sqlAuthoring": True, "qualityActionPlans": True},
        email_writing_mode=True,
        email_prompt_supplement="Assinatura: [Seu nome]",
        meta_synthesis_tool_context={
            ChatMetaLlmSynthesisService.TOOL_CONTEXT_META_LLM_SYNTHESIS: True,
        },
    )

    system = messages[0]["content"]

    assert "[Seu nome]" not in system
    assert "Especialista SQL" not in system
    assert "PAC Qualidade" not in system


def test_profile_meta_synthesis_omits_email_placeholder():
    builder = ChatPromptBuilderService(PromptPolicyService())
    messages = builder.build_messages(
        history=[],
        current_message="quem sou eu?",
        rag_context="",
        tool_context="",
        skills={"sqlAuthoring": True},
        email_writing_mode=True,
        email_prompt_supplement="Assinatura: [Seu nome]",
        meta_synthesis_tool_context={"userProfileLlmSynthesis": True},
    )

    system = messages[0]["content"]

    assert "[Seu nome]" not in system
    assert "Especialista SQL" not in system
    assert "perfil" in system.lower()


def test_profile_meta_synthesis_omits_prompt_user_context_block():
    builder = ChatPromptBuilderService(PromptPolicyService())
    messages = builder.build_messages(
        history=[],
        current_message="quem sou eu?",
        rag_context="",
        tool_context="",
        user_context=(
            "[Dados do usuário que está conversando com você]\n"
            "REGRA: quando o usuário perguntar sobre si mesmo, use os dados abaixo."
        ),
        meta_synthesis_tool_context={"userProfileLlmSynthesis": True},
    )

    system = messages[0]["content"]

    assert "REGRA: quando o usuário" not in system
    assert "[Dados do usuário que está conversando com você]" not in system
