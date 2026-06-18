from app.domain.services.chat_operational_follow_up_routing_service import (
    ChatOperationalFollowUpRoutingService,
)


def test_shipping_follow_up_grants_product_scope_and_inherits_date():
    assert ChatOperationalFollowUpRoutingService.grants_product_scope("shipping") is True
    assert (
        ChatOperationalFollowUpRoutingService.grants_specific_product_scope("shipping")
        is True
    )
    assert ChatOperationalFollowUpRoutingService.inherits_playbook_date("shipping") is True
    assert (
        ChatOperationalFollowUpRoutingService.preferred_route_id("shipping")
        == "productShippingStatus"
    )


def test_structure_exclusivity_grants_scope_without_date_inheritance():
    assert (
        ChatOperationalFollowUpRoutingService.grants_product_scope("structure_exclusivity")
        is True
    )
    assert (
        ChatOperationalFollowUpRoutingService.inherits_playbook_date("structure_exclusivity")
        is False
    )


def test_segment_from_message_expedition_follow_up():
    assert (
        ChatOperationalFollowUpRoutingService.segment_from_message("e a expedição?")
        == "shipping-status"
    )


def test_looks_like_playbook_date_follow_up_for_shipping_without_hoje():
    assert (
        ChatOperationalFollowUpRoutingService.looks_like_playbook_date_follow_up(
            "e a expedição?"
        )
        is True
    )


def test_blocks_capability_inquiry_on_operational_follow_up():
    assert (
        ChatOperationalFollowUpRoutingService.blocks_capability_inquiry(
            "e a expedição?",
            operational_data_topics=("expedicao", "expedição"),
        )
        is True
    )


def test_playbook_path_markers_include_factory_and_shipping():
    markers = ChatOperationalFollowUpRoutingService.playbook_path_markers()

    assert "/factory-status" in markers
    assert "/shipping-status" in markers
