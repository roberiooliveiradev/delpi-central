from app.application.services.chat_agent_skills_service import ChatAgentSkillsService


def test_sql_authoring_default_for_common_chat(monkeypatch):
    monkeypatch.setattr(
        "app.application.services.chat_agent_skills_service.Settings.CHAT_DEFAULT_SQL_AUTHORING_SKILL",
        True,
    )

    skills = ChatAgentSkillsService.resolve(
        agent_metadata={},
        allowed_action_ids=[],
        has_agent=False,
    )

    assert skills["sqlAuthoring"] is True
    assert skills["sqlExecutionAvailable"] is False
    assert skills["companyKnowledge"] is True


def test_sql_authoring_from_agent_metadata():
    skills = ChatAgentSkillsService.resolve(
        agent_metadata={"skills": {"sql": {"authoring": True}}},
        allowed_action_ids=[],
        has_agent=True,
    )

    assert skills["sqlAuthoring"] is True


def test_sql_authoring_off_for_agent_without_skill():
    skills = ChatAgentSkillsService.resolve(
        agent_metadata={"skills": {"sql": {"authoring": False}}},
        allowed_action_ids=[],
        has_agent=True,
    )

    assert skills["sqlAuthoring"] is False


def test_prompt_includes_sql_skill_policy():
    from app.domain.services.prompt_policy_service import PromptPolicyService

    prompt = PromptPolicyService().build_contextual_prompt(
        rag_context="",
        tool_context="",
        skills={"sqlAuthoring": True},
    )

    assert "Skill — Especialista SQL" in prompt or "Especialista SQL" in prompt
    assert "```sql" in prompt


def test_prompt_includes_company_knowledge_skill_policy():
    from app.domain.services.prompt_policy_service import PromptPolicyService

    prompt = PromptPolicyService().build_contextual_prompt(
        rag_context="",
        tool_context="",
        skills={"companyKnowledge": True},
    )

    assert "Conhecimento da empresa" in prompt
    assert "search_knowledge_base" in prompt


def test_preserves_rag_on_fast_path_when_company_knowledge_enabled():
    assert ChatAgentSkillsService.preserves_rag_on_fast_path(
        {"companyKnowledge": True},
    )
    assert not ChatAgentSkillsService.preserves_rag_on_fast_path(
        {"companyKnowledge": False},
    )


def test_fast_path_messages_include_sql_skill_policy():
    from app.application.services.chat_prompt_builder_service import (
        ChatPromptBuilderService,
    )
    from app.domain.services.prompt_policy_service import PromptPolicyService

    messages = ChatPromptBuilderService(PromptPolicyService()).build_fast_path_messages(
        current_message="oi",
        skills={"sqlAuthoring": True},
    )

    system = messages[0]["content"]
    assert "```sql" in system


def test_company_knowledge_default_for_common_chat(monkeypatch):
    monkeypatch.setattr(
        "app.application.services.chat_agent_skills_service.Settings.CHAT_DEFAULT_COMPANY_KNOWLEDGE_SKILL",
        True,
    )

    skills = ChatAgentSkillsService.resolve(
        agent_metadata={},
        allowed_action_ids=[],
        has_agent=False,
    )

    assert skills["companyKnowledge"] is True


def test_company_knowledge_default_for_agent_without_explicit_skill(monkeypatch):
    monkeypatch.setattr(
        "app.application.services.chat_agent_skills_service.Settings.CHAT_DEFAULT_COMPANY_KNOWLEDGE_SKILL",
        True,
    )

    skills = ChatAgentSkillsService.resolve(
        agent_metadata={},
        allowed_action_ids=[],
        has_agent=True,
    )

    assert skills["companyKnowledge"] is True


def test_company_knowledge_respects_agent_explicit_disable():
    skills = ChatAgentSkillsService.resolve(
        agent_metadata={
            "skills": {
                "company-knowledge": {"enabled": False},
            },
        },
        allowed_action_ids=[],
        has_agent=True,
    )

    assert skills["companyKnowledge"] is False
