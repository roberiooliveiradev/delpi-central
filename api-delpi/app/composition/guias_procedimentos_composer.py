from __future__ import annotations

from app.application.use_cases.guias_procedimentos.admin_guias_use_cases import (
    ArchiveProcedureUseCase,
    CreateDepartmentUseCase,
    CreateProcedureUseCase,
    GetAdminDepartmentUseCase,
    GetAdminProcedureUseCase,
    ListAdminDepartmentsUseCase,
    ListAdminProceduresUseCase,
    PublishProcedureUseCase,
    RestoreProcedureUseCase,
    UnpublishProcedureUseCase,
    UpdateDepartmentUseCase,
    UpdateProcedureUseCase,
)
from app.application.use_cases.guias_procedimentos.media_guias_use_cases import (
    ArchiveAttachmentUseCase,
    ArchiveMediaUseCase,
    CreateExternalVideoUseCase,
    ListAdminProcedureAttachmentsUseCase,
    ListAdminProcedureMediaUseCase,
    ListReadableProcedureAttachmentsUseCase,
    ListReadableProcedureMediaUseCase,
    ResolveAttachmentFileUseCase,
    ResolveMediaFileUseCase,
    UpdateAttachmentMetadataUseCase,
    UpdateMediaMetadataUseCase,
    UploadProcedureAttachmentUseCase,
    UploadProcedureImageUseCase,
    UploadProcedureVideoUseCase,
)
from app.application.use_cases.guias_procedimentos.public_guias_use_cases import (
    GetGuiasDepartmentBySlugUseCase,
    GetGuiasProcedureBySlugUseCase,
    ListGuiasDepartmentsUseCase,
)
from app.infrastructure.persistence.plugins.repositories.guias_procedimentos.postgres_guias_procedimentos_repository import (
    PostgresGuiasProcedimentosRepository,
)


def build_guias_procedimentos_repository() -> PostgresGuiasProcedimentosRepository:
    return PostgresGuiasProcedimentosRepository()


def build_list_guias_departments_use_case() -> ListGuiasDepartmentsUseCase:
    return ListGuiasDepartmentsUseCase(build_guias_procedimentos_repository())


def build_get_guias_department_by_slug_use_case() -> GetGuiasDepartmentBySlugUseCase:
    return GetGuiasDepartmentBySlugUseCase(build_guias_procedimentos_repository())


def build_get_guias_procedure_by_slug_use_case() -> GetGuiasProcedureBySlugUseCase:
    return GetGuiasProcedureBySlugUseCase(build_guias_procedimentos_repository())


def build_list_admin_departments_use_case() -> ListAdminDepartmentsUseCase:
    return ListAdminDepartmentsUseCase(build_guias_procedimentos_repository())


def build_get_admin_department_use_case() -> GetAdminDepartmentUseCase:
    return GetAdminDepartmentUseCase(build_guias_procedimentos_repository())


def build_create_department_use_case() -> CreateDepartmentUseCase:
    return CreateDepartmentUseCase(build_guias_procedimentos_repository())


def build_update_department_use_case() -> UpdateDepartmentUseCase:
    return UpdateDepartmentUseCase(build_guias_procedimentos_repository())


def build_list_admin_procedures_use_case() -> ListAdminProceduresUseCase:
    return ListAdminProceduresUseCase(build_guias_procedimentos_repository())


def build_get_admin_procedure_use_case() -> GetAdminProcedureUseCase:
    return GetAdminProcedureUseCase(build_guias_procedimentos_repository())


def build_create_procedure_use_case() -> CreateProcedureUseCase:
    return CreateProcedureUseCase(build_guias_procedimentos_repository())


def build_update_procedure_use_case() -> UpdateProcedureUseCase:
    return UpdateProcedureUseCase(build_guias_procedimentos_repository())


def build_publish_procedure_use_case() -> PublishProcedureUseCase:
    return PublishProcedureUseCase(build_guias_procedimentos_repository())


def build_unpublish_procedure_use_case() -> UnpublishProcedureUseCase:
    return UnpublishProcedureUseCase(build_guias_procedimentos_repository())


def build_archive_procedure_use_case() -> ArchiveProcedureUseCase:
    return ArchiveProcedureUseCase(build_guias_procedimentos_repository())


def build_restore_procedure_use_case() -> RestoreProcedureUseCase:
    return RestoreProcedureUseCase(build_guias_procedimentos_repository())


def build_list_admin_procedure_media_use_case() -> ListAdminProcedureMediaUseCase:
    return ListAdminProcedureMediaUseCase(build_guias_procedimentos_repository())


def build_list_admin_procedure_attachments_use_case() -> (
    ListAdminProcedureAttachmentsUseCase
):
    return ListAdminProcedureAttachmentsUseCase(build_guias_procedimentos_repository())


def build_list_readable_procedure_media_use_case() -> ListReadableProcedureMediaUseCase:
    return ListReadableProcedureMediaUseCase(build_guias_procedimentos_repository())


def build_list_readable_procedure_attachments_use_case() -> (
    ListReadableProcedureAttachmentsUseCase
):
    return ListReadableProcedureAttachmentsUseCase(
        build_guias_procedimentos_repository()
    )


def build_upload_procedure_image_use_case() -> UploadProcedureImageUseCase:
    return UploadProcedureImageUseCase(build_guias_procedimentos_repository())


def build_upload_procedure_video_use_case() -> UploadProcedureVideoUseCase:
    return UploadProcedureVideoUseCase(build_guias_procedimentos_repository())


def build_create_external_video_use_case() -> CreateExternalVideoUseCase:
    return CreateExternalVideoUseCase(build_guias_procedimentos_repository())


def build_upload_procedure_attachment_use_case() -> UploadProcedureAttachmentUseCase:
    return UploadProcedureAttachmentUseCase(build_guias_procedimentos_repository())


def build_update_media_metadata_use_case() -> UpdateMediaMetadataUseCase:
    return UpdateMediaMetadataUseCase(build_guias_procedimentos_repository())


def build_archive_media_use_case() -> ArchiveMediaUseCase:
    return ArchiveMediaUseCase(build_guias_procedimentos_repository())


def build_update_attachment_metadata_use_case() -> UpdateAttachmentMetadataUseCase:
    return UpdateAttachmentMetadataUseCase(build_guias_procedimentos_repository())


def build_archive_attachment_use_case() -> ArchiveAttachmentUseCase:
    return ArchiveAttachmentUseCase(build_guias_procedimentos_repository())


def build_resolve_media_file_use_case() -> ResolveMediaFileUseCase:
    return ResolveMediaFileUseCase(build_guias_procedimentos_repository())


def build_resolve_attachment_file_use_case() -> ResolveAttachmentFileUseCase:
    return ResolveAttachmentFileUseCase(build_guias_procedimentos_repository())
