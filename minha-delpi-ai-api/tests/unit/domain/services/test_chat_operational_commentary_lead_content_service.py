from app.composition.content_composer import configure_domain_infrastructure_ports
from app.domain.services.chat_operational_commentary_lead_content_service import (
    ChatOperationalCommentaryLeadContentService,
)

configure_domain_infrastructure_ports()


def test_depth_for_mode_loads_from_json():
    assert ChatOperationalCommentaryLeadContentService.depth_for_mode("fast") == "brief"
    assert ChatOperationalCommentaryLeadContentService.depth_for_mode("normal") == "standard"
    assert ChatOperationalCommentaryLeadContentService.depth_for_mode("thinker") == "expanded"


def test_profile_limits_load_from_json():
    brief = ChatOperationalCommentaryLeadContentService.profile("brief")
    expanded = ChatOperationalCommentaryLeadContentService.profile("expanded")

    assert brief["highlightLimit"] == 1
    assert brief["attentionLimit"] == 0
    assert expanded["highlightLimit"] == 6
    assert expanded["limitationsLimit"] == 4
    assert expanded["includeNarrativeInsight"] is True


def test_brief_direct_flag_and_synthesis_effect():
    assert (
        ChatOperationalCommentaryLeadContentService.brief_direct_tool_context_flag()
        == "commentaryBriefDirect"
    )
    assert (
        ChatOperationalCommentaryLeadContentService.synthesis_effect_for_depth("brief")
        == "llm_synthesis_brief"
    )
    assert (
        ChatOperationalCommentaryLeadContentService.synthesis_effect_for_depth("standard")
        == "llm_synthesis"
    )
