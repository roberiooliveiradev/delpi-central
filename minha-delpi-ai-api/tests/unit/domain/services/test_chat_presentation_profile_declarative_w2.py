from app.domain.services.chat_operational_refinement.chat_operational_refinement_vocabulary import (
    ChatOperationalRefinementVocabulary,
)
from app.domain.services.chat_presentation_profile_service import ChatPresentationProfileService
from app.domain.services.chat_presentation_table_profile_inference_service import (
    ChatPresentationTableProfileInferenceService,
)
from app.domain.services.chat_presentation_text_first_policy_service import (
    ChatPresentationTextFirstPolicyService,
)
from app.domain.services.chat_presentation_visual_ui_hint_service import (
    ChatPresentationVisualUiHintService,
)
from app.domain.services.chat_presentation_vocabulary_service import (
    ChatPresentationVocabularyService,
)
from app.domain.services.operational_route_registry_service import (
    OperationalRouteRegistryService,
)


def test_text_first_profiles_loaded_from_entity_set():
    keys = ChatPresentationProfileService.text_first_profile_keys()

    assert "sale_pricing" in keys
    assert "structure_exclusivity" in keys
    assert ChatPresentationProfileService.is_text_first_profile("sale_pricing")
    assert not ChatPresentationProfileService.is_text_first_profile("stock")


def test_tier_a_profile_keys_and_path_fragments_from_path_rules():
    tier_a = ChatPresentationProfileService.tier_a_profile_keys()

    assert "analyser" in tier_a
    assert "purchase_list" in tier_a

    fragments = ChatPresentationProfileService.tier_a_table_assembly_path_fragments()

    assert "/analyser" in fragments
    assert "/stock" in fragments
    assert "/purchases" in fragments


def test_vocabulary_service_delegates_tier_a_to_profiles():
    profile_keys = frozenset(ChatPresentationProfileService.tier_a_profile_keys())
    vocab_keys = frozenset(ChatPresentationVocabularyService.playbook12_tier_a_profile_keys())

    assert profile_keys == vocab_keys

    derived_fragments = ChatPresentationVocabularyService.playbook12_table_assembly_path_fragments()
    profile_fragments = ChatPresentationProfileService.tier_a_table_assembly_path_fragments()

    assert derived_fragments == profile_fragments


def test_route_namespace_from_profile_declarative():
    namespace = ChatPresentationProfileService.route_namespace(
        path="/products/10080001/factory-status",
        entity="product_factory_status",
    )

    assert namespace == "factoryStatus"
    assert (
        ChatPresentationVisualUiHintService.resolve_namespace(
            path="/products/10080001/factory-status",
            profile_key="factory_status",
        )
        == "factoryStatus"
    )


def test_table_profile_for_entity_from_json():
    assert (
        ChatPresentationProfileService.table_profile_for_entity("product_stock")
        == "stockProductPositions"
    )
    assert (
        ChatPresentationTableProfileInferenceService.infer_profile_name(
            entity="product_stock",
        )
        == "stockProductPositions"
    )


def test_paginated_path_fragments_from_registry():
    registry_fragments = OperationalRouteRegistryService.paginated_path_fragments()
    vocab_fragments = ChatOperationalRefinementVocabulary.paginated_path_fragments()

    assert registry_fragments
    assert vocab_fragments == registry_fragments
    assert "/stock" in vocab_fragments


def test_factory_status_builds_visual_bundle_via_stack_layout_not_hardcoded_profile():
    assert ChatPresentationTextFirstPolicyService.should_build_visual_bundle(
        path="/products/10080001/factory-status",
        entity="product_factory_status",
    )
