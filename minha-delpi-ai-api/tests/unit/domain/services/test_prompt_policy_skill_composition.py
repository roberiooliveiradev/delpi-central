from app.composition.content_composer import configure_domain_infrastructure_ports
from app.domain.services.prompt_policy_service import PromptPolicyService

configure_domain_infrastructure_ports()


def test_prompt_loads_only_requested_skill_when_analysis_ran():
    policy = PromptPolicyService()
    sections = policy.build_active_skill_policy_sections(
        {"sqlAuthoring": True, "companyKnowledge": True, "drawingAnalysis": True},
        skills_to_load=["sql"],
        analysis_ran=True,
    )
    joined = "\n".join(sections).lower()
    assert sections
    assert "sql" in joined or "protheus" in joined or "select" in joined
    # Company knowledge policy should not be present when only sql was loaded.
    assert "conhecimento da empresa" not in joined
    assert "company knowledge" not in joined


def test_prompt_loads_all_enabled_without_analysis():
    policy = PromptPolicyService()
    sections = policy.build_active_skill_policy_sections(
        {"sqlAuthoring": True, "companyKnowledge": True},
        analysis_ran=False,
    )
    assert len(sections) >= 2
