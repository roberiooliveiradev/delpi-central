"""E3.S7 — follow-up routing cutover (follow_up_type → routeSegment)."""

from __future__ import annotations

from app.domain.services.chat_operational_follow_up_routing_service import (
    ChatOperationalFollowUpRoutingService,
)


def test_e3_s7_cutover_enabled_by_default():
    assert ChatOperationalFollowUpRoutingService.authority_shadow_enabled() is True
    assert ChatOperationalFollowUpRoutingService.cutover_enabled() is True


def test_e3_s7_shipping_authority_from_follow_up_type():
    message = "e a expedição?"
    legacy = ChatOperationalFollowUpRoutingService.segment_from_message_terms(message)
    candidate = ChatOperationalFollowUpRoutingService.segment_from_follow_up_type(message)
    authority = ChatOperationalFollowUpRoutingService.segment_from_message(message)
    assert legacy is None  # E9.S12.A — terms deletados
    assert candidate == "shipping-status"
    assert authority == "shipping-status"


def test_e3_s7_structure_exclusivity_candidate_without_terms():
    message = (
        "quais matérias-primas exclusivas existem na estrutura desse produto?"
    )
    legacy = ChatOperationalFollowUpRoutingService.segment_from_message_terms(message)
    candidate = ChatOperationalFollowUpRoutingService.segment_from_follow_up_type(message)
    authority = ChatOperationalFollowUpRoutingService.segment_from_message(message)
    assert legacy is None
    assert candidate == "structure/exclusivity"
    assert authority == "structure/exclusivity"


def test_e3_s7_topic_switch_has_no_route_segment():
    message = "agora fale sobre política de férias"
    assert ChatOperationalFollowUpRoutingService.segment_from_message(message) is None
    assert ChatOperationalFollowUpRoutingService.segment_from_follow_up_type(message) is None


def test_e3_s7_sibling_preferred_route_id_from_type():
    assert (
        ChatOperationalFollowUpRoutingService.preferred_route_id("shipping")
        == "productShippingStatus"
    )
    assert (
        ChatOperationalFollowUpRoutingService.preferred_route_id("structure_exclusivity")
        == "productStructureExclusivity"
    )


def test_e3_s7_message_segment_terms_api_empty_after_delete():
    assert ChatOperationalFollowUpRoutingService.message_segment_terms() == ()
    assert ChatOperationalFollowUpRoutingService.segment_from_message_terms("e a expedição?") is None
