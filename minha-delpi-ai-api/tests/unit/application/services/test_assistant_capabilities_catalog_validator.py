from app.application.services.assistant_capabilities_catalog_validator import (
    AssistantCapabilitiesCatalogValidator,
)


def test_validate_catalog_passes():
    errors = AssistantCapabilitiesCatalogValidator.validate()

    assert errors == []
