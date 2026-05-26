from app.domain.services.prompt_policy_service import PromptPolicyService


def test_contextual_prompt_always_includes_base_and_response_style():
    service = PromptPolicyService()

    prompt = service.build_contextual_prompt(
        rag_context="Documento relevante",
        tool_context="",
    )

    assert "Você é o assistente Minha DELPI" in prompt
    assert "Contexto documental autorizado" in prompt
    assert "Documento relevante" in prompt
    assert "Estilo e formatação" in prompt or "Instruções gerais para resposta" in prompt


def test_contextual_prompt_does_not_include_external_action_policy_without_tool_context():
    service = PromptPolicyService()

    prompt = service.build_contextual_prompt(
        rag_context="Documento relevante",
        tool_context="",
    )

    assert "Instruções para resultados de `execute_external_action`" not in prompt


def test_contextual_prompt_includes_external_action_policy_when_tool_context_mentions_action():
    service = PromptPolicyService()

    prompt = service.build_contextual_prompt(
        rag_context="",
        tool_context="tool=execute_external_action statusCode=200 ok=true",
    )

    assert "APIs externas" in prompt or "execute_external_action" in prompt
    assert "200" in prompt or "sucesso" in prompt


def test_contextual_prompt_includes_platform_tools_policy_when_tool_context_mentions_allowed_apps():
    service = PromptPolicyService()

    prompt = service.build_contextual_prompt(
        rag_context="",
        tool_context="tool=get_allowed_apps result=...",
    )

    assert "Instruções para ferramentas internas da plataforma" in prompt
    assert "liste os aplicativos autorizados" in prompt


def test_contextual_prompt_includes_product_policy_when_tool_context_mentions_products():
    service = PromptPolicyService()

    prompt = service.build_contextual_prompt(
        rag_context="",
        tool_context="Consulta de produtos em estoque com NCM",
    )

    assert "produto" in prompt.lower()
    assert "código" in prompt or "descrição" in prompt


def test_contextual_prompt_includes_sql_policy_when_rag_context_has_sql():
    service = PromptPolicyService()

    prompt = service.build_contextual_prompt(
        rag_context="SELECT * FROM SD4010 WHERE D4_PRODUTO = '10080014'",
        tool_context="",
    )

    assert "Instruções para contexto documental com SQL" in prompt
    assert "Não reproduza SQL bruto" in prompt


def test_contextual_prompt_includes_operational_policy_when_operational_mode_enabled():
    service = PromptPolicyService()

    prompt = service.build_contextual_prompt(
        rag_context="",
        tool_context="",
        operational_mode=True,
    )

    assert "Modo operacional" in prompt


def test_contextual_prompt_includes_api_delpi_routes_policy_when_tool_context_mentions_api_delpi():
    service = PromptPolicyService()

    prompt = service.build_contextual_prompt(
        rag_context="",
        tool_context=(
            "execute_external_action provider=api_delpi "
            "path=/products/{code}/stock statusCode=200"
        ),
    )

    assert "Instruções para consultas via API DELPI" in prompt
    assert "get_product_stock" in prompt or "/products/{code}/stock" in prompt


def test_contextual_prompt_includes_session_knowledge_policy_for_attachment_context():
    service = PromptPolicyService()

    prompt = service.build_contextual_prompt(
        rag_context="[Fonte 1]\nTítulo: manual.pdf\nEscopo: session_source\nArquivo: manual.pdf\nTrecho: conteúdo do arquivo",
        tool_context="",
    )

    assert "Instruções para fontes anexadas à conversa" in prompt
    assert "fontes de conhecimento da sessão atual" in prompt
