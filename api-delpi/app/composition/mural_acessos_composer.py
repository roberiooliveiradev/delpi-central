from __future__ import annotations

from app.application.services.mural_acessos.mural_acessos_image_storage import (
    MuralAcessosImageStorage,
)
from app.application.use_cases.mural_acessos.mural_acessos_use_cases import (
    CreateHubUseCase,
    CreateLinkUseCase,
    DeleteHubUseCase,
    DeleteLinkImageUseCase,
    DeleteLinkUseCase,
    GetHubUseCase,
    ListHubsUseCase,
    ListLinksUseCase,
    ListPublicMenuUseCase,
    ReorderLinksUseCase,
    RenderHubQrUseCase,
    ResolveLinkImageUseCase,
    UpdateHubUseCase,
    UpdateLinkUseCase,
    UploadLinkImageUseCase,
)
from app.infrastructure.persistence.plugins.repositories.mural_acessos.postgres_mural_acessos_repository import (
    PostgresMuralAcessosRepository,
)


def build_mural_acessos_repository() -> PostgresMuralAcessosRepository:
    return PostgresMuralAcessosRepository()


def build_mural_acessos_image_storage() -> MuralAcessosImageStorage:
    return MuralAcessosImageStorage()


def build_list_hubs_use_case() -> ListHubsUseCase:
    return ListHubsUseCase(build_mural_acessos_repository())


def build_create_hub_use_case() -> CreateHubUseCase:
    return CreateHubUseCase(build_mural_acessos_repository())


def build_get_hub_use_case() -> GetHubUseCase:
    return GetHubUseCase(build_mural_acessos_repository())


def build_update_hub_use_case() -> UpdateHubUseCase:
    return UpdateHubUseCase(build_mural_acessos_repository())


def build_delete_hub_use_case() -> DeleteHubUseCase:
    return DeleteHubUseCase(
        build_mural_acessos_repository(),
        build_mural_acessos_image_storage(),
    )


def build_render_hub_qr_use_case() -> RenderHubQrUseCase:
    return RenderHubQrUseCase(build_mural_acessos_repository())


def build_list_links_use_case() -> ListLinksUseCase:
    return ListLinksUseCase(build_mural_acessos_repository())


def build_create_link_use_case() -> CreateLinkUseCase:
    return CreateLinkUseCase(build_mural_acessos_repository())


def build_update_link_use_case() -> UpdateLinkUseCase:
    return UpdateLinkUseCase(build_mural_acessos_repository())


def build_delete_link_use_case() -> DeleteLinkUseCase:
    return DeleteLinkUseCase(
        build_mural_acessos_repository(),
        build_mural_acessos_image_storage(),
    )


def build_reorder_links_use_case() -> ReorderLinksUseCase:
    return ReorderLinksUseCase(build_mural_acessos_repository())


def build_upload_link_image_use_case() -> UploadLinkImageUseCase:
    return UploadLinkImageUseCase(
        build_mural_acessos_repository(),
        build_mural_acessos_image_storage(),
    )


def build_delete_link_image_use_case() -> DeleteLinkImageUseCase:
    return DeleteLinkImageUseCase(
        build_mural_acessos_repository(),
        build_mural_acessos_image_storage(),
    )


def build_resolve_link_image_use_case() -> ResolveLinkImageUseCase:
    return ResolveLinkImageUseCase(
        build_mural_acessos_repository(),
        build_mural_acessos_image_storage(),
    )


def build_list_public_menu_use_case() -> ListPublicMenuUseCase:
    return ListPublicMenuUseCase(build_mural_acessos_repository())
