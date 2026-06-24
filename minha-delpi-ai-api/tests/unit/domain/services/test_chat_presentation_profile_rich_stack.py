from app.composition.content_composer import configure_domain_infrastructure_ports
from app.domain.services.chat_presentation_profile_service import ChatPresentationProfileService
from app.domain.services.chat_presentation_rich_stack_policy_service import (
    ChatPresentationRichStackPolicyService,
)

configure_domain_infrastructure_ports()


def test_rich_stack_profiles_entity_set_empty_for_delivered_pure():
    profiles = ChatPresentationProfileService.entity_set("richStackProfiles")

    assert len(profiles) == 0


def test_is_rich_stack_profile_false_for_as_delivered_profiles():
    assert not ChatPresentationProfileService.is_rich_stack_profile("factory_status")
    assert not ChatPresentationProfileService.is_rich_stack_profile("stock")
    assert not ChatPresentationProfileService.is_rich_stack_profile("structure_exclusivity")
    assert not ChatPresentationProfileService.is_rich_stack_profile("generic")


def test_is_rich_playbook_route_false_for_as_delivered_profiles():
    assert not ChatPresentationRichStackPolicyService.is_rich_playbook_route(
        "/products/90261805/structure/exclusivity",
        entity="product_structure_exclusivity",
    )
    assert not ChatPresentationRichStackPolicyService.is_rich_playbook_route(
        "/products/90269001/stock",
        entity="product_stock",
    )
    assert not ChatPresentationRichStackPolicyService.is_rich_playbook_route(
        "/products/90269001/guide",
        entity="product_guide",
    )

