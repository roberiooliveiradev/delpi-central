from app.composition.content_composer import configure_domain_infrastructure_ports
from app.domain.services.chat_operational_factual_verdict_content_service import (
    ChatOperationalFactualVerdictContentService,
)
from app.domain.services.chat_operational_narrative_synthesis_content_service import (
    ChatOperationalNarrativeSynthesisContentService,
)

configure_domain_infrastructure_ports()


def test_factual_profile_synthesis_kind_links_to_operational_factual_verdict():
    profile_key = "structure_exclusivity"
    synthesis_kind = ChatOperationalNarrativeSynthesisContentService.synthesis_kind_for_factual_profile(
        profile_key,
    )

    assert synthesis_kind == "structure_exclusivity"
    assert profile_key in ChatOperationalFactualVerdictContentService.profile_keys()
    assert ChatOperationalFactualVerdictContentService.path_markers(profile_key) == [
        "/structure/exclusivity",
    ]


def test_narrative_policy_synthesis_kind_maps_structure_exclusivity_summary():
    kind = ChatOperationalNarrativeSynthesisContentService.synthesis_kind_for_narrative_policy(
        "operational_structure_exclusivity_summary",
    )

    assert kind == "structure_exclusivity"
    assert ChatOperationalNarrativeSynthesisContentService.synthesis_policy(
        kind,
        "normal",
    ).endswith("operational-synthesis-structure-exclusivity.md")


def test_structure_exclusivity_path_markers_not_duplicated_in_bundle():
    node = ChatOperationalNarrativeSynthesisContentService.factual_profile_synthesis_kinds()

    assert "structure_exclusivity" in node
    assert not hasattr(
        ChatOperationalNarrativeSynthesisContentService,
        "structure_exclusivity_path_markers",
    )
