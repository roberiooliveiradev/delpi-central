from app.application.services.chat_grounded_enrich_interactivity_service import (
    ChatGroundedEnrichInteractivityService,
)
from app.composition.content_composer import configure_domain_infrastructure_ports

configure_domain_infrastructure_ports()


def test_fast_enrich_insight_attaches_mode_suggestion_chip():
    metadata: dict = {}
    tool_context = {
        "responseMode": "fast",
        "turnGrounding": {"stage": "grounded_enrich_insight"},
    }

    ChatGroundedEnrichInteractivityService.attach_to_assistant_metadata(
        metadata,
        tool_context=tool_context,
        response_mode="fast",
    )

    suggestions = metadata.get("groundedEnrichModeSuggestions") or []

    assert suggestions
    assert "Normal" in suggestions[0]["label"] or "Pensador" in suggestions[0]["label"]


def test_fast_enrich_insight_skipped_for_normal_mode():
    metadata: dict = {}
    tool_context = {"turnGrounding": {"stage": "grounded_enrich_insight"}}

    ChatGroundedEnrichInteractivityService.attach_to_assistant_metadata(
        metadata,
        tool_context=tool_context,
        response_mode="normal",
    )

    assert "groundedEnrichModeSuggestions" not in metadata
