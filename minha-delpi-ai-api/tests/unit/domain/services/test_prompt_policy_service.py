from app.domain.services.prompt_policy_service import PromptPolicyService


def test_contextual_prompt_includes_rag_and_tool_sections():
    service = PromptPolicyService()

    prompt = service.build_contextual_prompt(
        rag_context="[Fonte 1] Minha DELPI é uma plataforma.",
        tool_context="[Ferramenta: get_allowed_apps] Resultado autorizado: []",
    )

    assert "Contexto documental autorizado" in prompt
    assert "Resultados de ferramentas internas autorizadas" in prompt
    assert "Não extrapole" in prompt
