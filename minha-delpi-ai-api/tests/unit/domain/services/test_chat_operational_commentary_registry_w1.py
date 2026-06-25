"""Regressão W1b — registry declarativo de commentaryProfiles."""

from app.composition.content_composer import configure_domain_infrastructure_ports
from app.domain.services.chat_operational_commentary_builder_registry_service import (
    ChatOperationalCommentaryBuilderRegistryService,
)
from app.domain.services.chat_operational_commentary_profile_service import (
    ChatOperationalCommentaryProfileService,
)
from app.domain.services.chat_operational_data_commentary_service import (
    ChatOperationalDataCommentaryService,
)

configure_domain_infrastructure_ports()

_OPERATIONAL_PROFILES = frozenset(
    {
        "factory_status",
        "stock",
        "production_status",
        "shipping_status",
        "directives",
        "structure_exclusivity",
        "sale_pricing",
        "analyser",
    }
)


def test_operational_commentary_profiles_registered_in_json():
    registered = ChatOperationalCommentaryProfileService.registered_profile_keys()

    assert _OPERATIONAL_PROFILES <= registered


def test_each_operational_profile_has_builder_strategy_and_content_section():
    for profile_key in sorted(_OPERATIONAL_PROFILES):
        config = ChatOperationalCommentaryProfileService.profile_config(profile_key)

        assert config.get("contentSection"), profile_key
        assert config.get("builderStrategy"), profile_key
        assert (
            config["builderStrategy"]
            in ChatOperationalCommentaryBuilderRegistryService.registered_strategies()
        )


def test_orchestration_rejects_unknown_profile_key():
    assert ChatOperationalDataCommentaryService.build("unknown_profile_xyz", {"items": []}) is None


def test_structure_exclusivity_uses_metadata_only_path():
    root = {
        "product": {"product_code": "90260255"},
        "summary": {"total_exclusive_raw_materials": 0, "total_raw_materials": 2},
        "items": [{"component_type": "MP"}],
    }

    commentary = ChatOperationalDataCommentaryService.build("structure_exclusivity", root)

    assert commentary is not None
    assert commentary.get("metadataOnly") is True
    assert commentary.get("highlights") == []
