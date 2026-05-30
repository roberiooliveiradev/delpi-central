from app.domain.services.admin_rbac_profile_catalog_service import (
    AdminRbacProfileCatalogService,
)


class GetAdminRbacProfilesUseCase:
    def execute(self) -> dict:
        return {
            "profiles": AdminRbacProfileCatalogService.list_profiles(),
            "contract": AdminRbacProfileCatalogService.build_contract(),
        }
