from app.composition.content_composer import configure_domain_infrastructure_ports
from app.domain.services.chat_operational_llm_synthesis_context_content_service import (
    ChatOperationalLlmSynthesisContextContentService,
)

configure_domain_infrastructure_ports()


def test_max_chars_recalibrated():
    assert ChatOperationalLlmSynthesisContextContentService.max_chars() == 1200


def test_max_thinker_prose_chars_recalibrated():
    assert ChatOperationalLlmSynthesisContextContentService.max_thinker_prose_chars() == 2400


def test_enrich_insight_facts_budget_local_normal():
    budget = ChatOperationalLlmSynthesisContextContentService.enrich_insight_facts_budget(
        "normal",
        profile="local",
    )

    assert budget["base"] == 1200
    assert budget["perTool"] == 350
    assert budget["maxToolsCounted"] == 3
    assert budget["hardCap"] == 2800


def test_enrich_insight_facts_budget_cloud_thinker():
    budget = ChatOperationalLlmSynthesisContextContentService.enrich_insight_facts_budget(
        "thinker",
        profile="cloud",
    )

    assert budget["base"] == 3200
    assert budget["perTool"] == 800
    assert budget["maxToolsCounted"] == 6
    assert budget["hardCap"] == 7000


def test_resolve_enrich_insight_facts_max_chars_multi_tool():
    resolved = ChatOperationalLlmSynthesisContextContentService.resolve_enrich_insight_facts_max_chars(
        "normal",
        ok_tool_count=3,
        profile="local",
    )

    assert resolved == 1900
