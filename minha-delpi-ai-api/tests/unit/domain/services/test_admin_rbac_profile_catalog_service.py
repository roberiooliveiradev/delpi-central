from app.domain.services.admin_rbac_profile_catalog_service import (
    AdminRbacProfileCatalogService,
)


def test_list_profiles_has_four_formal_profiles():
    profiles = AdminRbacProfileCatalogService.list_profiles()

    assert len(profiles) == 4
    assert {item["key"] for item in profiles} == {
        "admin",
        "operator",
        "auditor",
        "viewer",
    }


def test_resolve_active_profile_keys_from_roles():
    active = AdminRbacProfileCatalogService.resolve_active_profile_keys(
        ["admin", "viewer"]
    )

    assert active == ["admin", "viewer"]
