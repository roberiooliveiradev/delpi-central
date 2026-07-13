from app.domain.services.prompt_policy_service import PromptPolicyService


def test_build_system_prompt_includes_context_engineering():
    service = PromptPolicyService()

    prompt = service.build_system_prompt()

    assert "Você é o assistente Minha DELPI" in prompt
    assert "Engenharia de contexto" in prompt
    assert "Decisões" in prompt
    assert "não invente" in prompt.lower()
    assert "Memória de contexto" in prompt or "memória ativa" in prompt.lower()


def test_contextual_prompt_includes_administrative_writing_in_text_mode():
    service = PromptPolicyService()

    prompt = service.build_contextual_prompt(
        rag_context="",
        tool_context="",
        text_task_mode=True,
    )

    assert "modo de redação" in prompt.lower() or "modo textual" in prompt.lower()


def test_contextual_prompt_includes_email_writing_policy():
    service = PromptPolicyService()

    prompt = service.build_contextual_prompt(
        rag_context="",
        tool_context="",
        text_task_mode=True,
        email_writing_mode=True,
    )

    assert "e-mails corporativos" in prompt.lower() or "e-mail" in prompt.lower()
    assert "[seu nome]" in prompt.lower() or "seu nome" in prompt.lower()


def test_contextual_prompt_always_includes_base_and_response_style():
    service = PromptPolicyService()

    prompt = service.build_contextual_prompt(
        rag_context="Documento relevante",
        tool_context="",
    )

    assert "Você é o assistente Minha DELPI" in prompt
    assert "Engenharia de contexto" in prompt
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


def test_contextual_prompt_includes_data_interpretation_policy():
    service = PromptPolicyService()

    prompt = service.build_contextual_prompt(
        rag_context="",
        tool_context="",
        analysis_mode=True,
        data_interpretation_mode=True,
    )

    assert "interpretação de dados" in prompt.lower()
    assert "perfil do usuário" in prompt.lower()


def test_contextual_prompt_includes_analysis_policy_when_analysis_mode_enabled():
    service = PromptPolicyService()

    prompt = service.build_contextual_prompt(
        rag_context="",
        tool_context="",
        analysis_mode=True,
    )

    assert "análise comparativa" in prompt.lower()


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


def test_contextual_prompt_includes_text_correction_policy():
    service = PromptPolicyService()

    prompt = service.build_contextual_prompt(
        rag_context="",
        tool_context="",
        text_task_mode=True,
        text_correction_mode=True,
    )

    assert "correção" in prompt.lower() or "Correção de texto" in prompt


def test_contextual_prompt_includes_session_knowledge_policy_for_attachment_context():
    service = PromptPolicyService()

    prompt = service.build_contextual_prompt(
        rag_context="[Fonte 1]\nTítulo: manual.pdf\nEscopo: session_source\nArquivo: manual.pdf\nTrecho: conteúdo do arquivo",
        tool_context="",
    )

    assert "Instruções para fontes anexadas à conversa" in prompt
    assert "fontes de conhecimento da sessão atual" in prompt


def test_contextual_prompt_includes_humanized_data_policy_when_commentary_present():
    service = PromptPolicyService()

    prompt = service.build_contextual_prompt(
        rag_context="",
        tool_context='{"dataCommentary": {"summary": "Saldo confortável", "alertLevel": "ok"}}',
    )

    assert "Modo resposta humanizada com dados" in prompt
    assert "dataCommentary" in prompt or "conclusão" in prompt.lower()


def test_contextual_prompt_includes_humanized_data_policy_when_data_answer_present():
    service = PromptPolicyService()

    prompt = service.build_contextual_prompt(
        rag_context="",
        tool_context='{"dataAnswer": {"summary": {"answer": "Saldo confortável", "riskLevel": "ok"}}}',
    )

    assert "Modo resposta humanizada com dados" in prompt
    assert "dataAnswer" in prompt or "conclusão" in prompt.lower()


def test_contextual_prompt_includes_project_sources_policy():
    service = PromptPolicyService()

    prompt = service.build_contextual_prompt(
        rag_context="[Fonte 1]\nEscopo: project_source\nTrecho: conteúdo do treinamento",
        tool_context="",
    )

    assert "fontes do projeto" in prompt.lower()
    assert "nunca" in prompt.lower() and "acessar arquivos" in prompt.lower()


def test_contextual_prompt_includes_drawing_render_only_when_analysis_in_tool_context():
    service = PromptPolicyService()

    prompt = service.build_contextual_prompt(
        rag_context="",
        tool_context=(
            '{"drawingAnalysisMode": true, "drawingAnalysis": {"items": ['
            '{"item": "Revisão", "status": "ok", "templateKey": "revision_cross_ok"}]}}'
        ),
        skills={"drawingAnalysis": True},
    )

    assert "Modo render-only" in prompt
    assert "não altere" in prompt.lower()
    assert "drawingAnalysis.items" in prompt or "drawingAnalysisExport" in prompt


def test_contextual_prompt_includes_drawing_rag_normative_when_rag_and_analysis():
    service = PromptPolicyService()

    prompt = service.build_contextual_prompt(
        rag_context="Normas_Tecnicas_DELPI: decape de cabo ±1 mm quando indicado.",
        tool_context='{"drawingAnalysisMode": true, "drawingAnalysis": {"items": []}}',
        skills={"drawingAnalysis": True},
    )

    assert "RAG normativo" in prompt
    assert "não" in prompt.lower() and "status" in prompt.lower()
    assert "Ordem de autoridade" in prompt or "API DELPI" in prompt


def test_contextual_prompt_omits_drawing_rag_normative_without_rag_context():
    service = PromptPolicyService()

    prompt = service.build_contextual_prompt(
        rag_context="",
        tool_context='{"drawingAnalysisMode": true, "drawingAnalysis": {"items": []}}',
        skills={"drawingAnalysis": True},
    )

    assert "Modo render-only" in prompt
    assert "RAG normativo" not in prompt


def test_document_vision_policy_excludes_validation_checklist():
    policy_path = PromptPolicyService.POLICY_DIR / "document-vision-delpi-skill.md"
    content = policy_path.read_text(encoding="utf-8").lower()

    assert "fora de escopo" in content
    assert "drawinganalysis" in content.replace("-", "")
    assert "erro crítico" not in content or "não" in content


def test_drawing_skill_policy_is_decoupled_from_validation_rules():
    policy_path = PromptPolicyService.POLICY_DIR / "drawing-analysis-delpi-skill.md"
    content = policy_path.read_text(encoding="utf-8").lower()

    assert "pipeline" in content
    assert "revisão divergente: erro crítico" not in content
    assert "componente faltante ou extra na bom: erro crítico" not in content


def test_build_skill_policy_sections_includes_quality_action_plans_when_enabled():
    service = PromptPolicyService()

    sections = service.build_active_skill_policy_sections(skills={"qualityActionPlans": True})

    assert sections
    assert any("PAC" in section or "8D" in section for section in sections)


def test_build_skill_policy_sections_includes_technical_description_when_enabled():
    service = PromptPolicyService()

    sections = service.build_active_skill_policy_sections(
        skills={"technicalDescription": True}
    )

    assert sections
    assert any("matérias-primas" in section.lower() or "1008" in section for section in sections)


def test_technical_description_skill_policy_covers_create_and_analyze():
    policy_path = PromptPolicyService.POLICY_DIR / "technical-description-delpi-skill.md"
    content = policy_path.read_text(encoding="utf-8").lower()

    assert "criar" in content
    assert "analisar" in content
    assert "normas" in content
    assert "vdar" in content
    assert "drawing-analysis-delpi" in content


def test_quality_action_plans_skill_policy_requires_confirmation_before_writes():
    policy_path = PromptPolicyService.POLICY_DIR / "quality-action-plans-delpi-skill.md"
    content = policy_path.read_text(encoding="utf-8").lower()

    assert "confirmação" in content
    assert "branch_code" in content
    assert "nonconformity_scope" in content


def test_build_active_skill_policy_includes_readonly_section_when_flag_set():
    service = PromptPolicyService()

    sections = service.build_active_skill_policy_sections(
        skills={
            "qualityActionPlans": True,
            "qualityActionPlansReadOnly": True,
        }
    )

    combined = "\n".join(sections).lower()

    assert "modo só consulta" in combined
    assert "allowwrite" in combined or "modo consulta" in combined
