from app.composition.content_composer import configure_domain_infrastructure_ports
from app.domain.services.chat_user_query_improvement_content_service import (
    ChatUserQueryImprovementContentService,
)


def test_user_query_improvement_bundle_loaded():
    configure_domain_infrastructure_ports()

    assert ChatUserQueryImprovementContentService.enabled() is True
    assert ChatUserQueryImprovementContentService.limit_int("maxTokens", 64) == 128
    assert "digitação" in ChatUserQueryImprovementContentService.system_prompt().lower()
    assert "descriao" in ChatUserQueryImprovementContentService.broken_operational_stems()
    assert ChatUserQueryImprovementContentService.compile_skip_pattern("corrijaPrefix")
    assert ChatUserQueryImprovementContentService.reason("llmApplied") == "llm_applied"


def test_format_user_prompt_includes_message():
    configure_domain_infrastructure_ports()

    prompt = ChatUserQueryImprovementContentService.format_user_prompt(
        message="qual a descrião do 10050078?"
    )
    assert "10050078" in prompt
    assert "descrião" in prompt
