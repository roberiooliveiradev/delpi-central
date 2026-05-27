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
