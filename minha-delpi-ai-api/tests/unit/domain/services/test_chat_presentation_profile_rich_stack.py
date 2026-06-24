from app.composition.content_composer import configure_domain_infrastructure_ports
from app.domain.services.chat_presentation_profile_service import ChatPresentationProfileService
from app.domain.services.chat_presentation_rich_stack_policy_service import (
    ChatPresentationRichStackPolicyService,
)

configure_domain_infrastructure_ports()


def test_rich_stack_profiles_entity_set_loaded():
    profiles = ChatPresentationProfileService.entity_set("richStackProfiles")

    assert "stock" in profiles
    assert "structure_exclusivity" in profiles
    assert "tree_hierarchy" in profiles


def test_is_rich_stack_profile_uses_declarative_rules():
    assert ChatPresentationProfileService.is_rich_stack_profile("factory_status")
    assert ChatPresentationProfileService.is_rich_stack_profile("stock")
    assert ChatPresentationProfileService.is_rich_stack_profile("structure_exclusivity")
    assert not ChatPresentationProfileService.is_rich_stack_profile("generic")


def test_is_rich_playbook_route_resolves_from_profile_not_hardcoded_flags():
    assert ChatPresentationRichStackPolicyService.is_rich_playbook_route(
        "/products/90261805/structure/exclusivity",
        entity="product_structure_exclusivity",
    )
    assert ChatPresentationRichStackPolicyService.is_rich_playbook_route(
        "/products/90269001/stock",
        entity="product_stock",
    )
    assert not ChatPresentationRichStackPolicyService.is_rich_playbook_route(
        "/products/90269001/guide",
        entity="product_guide",
    )

