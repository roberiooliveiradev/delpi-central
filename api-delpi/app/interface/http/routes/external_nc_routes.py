# app/interface/http/routes/external_nc_routes.py
from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query, status

from delpi_auth.authorization import require_any_permission, require_permission

from app.application.dto.external_nc.create_external_nonconformity_request import (
    CreateExternalNonconformityRequest,
)
from app.application.dto.external_nc.list_external_nonconformities_request import (
    ListExternalNonconformitiesRequest,
)
from app.application.dto.external_nc.update_external_nonconformity_request import (
    UpdateExternalNonconformityRequest,
)
from app.application.dto.external_nc.transition_external_nonconformity_status_request import (
    TransitionExternalNonconformityStatusRequest,
)
from app.application.dto.external_nc.add_external_nc_comment_request import (
    AddExternalNcCommentRequest,
)
from app.application.dto.external_nc.upload_external_nc_attachment_request import (
    UploadExternalNcAttachmentRequest,
)
from app.composition.external_nc_composer import (
    build_create_external_nonconformity_use_case,
    build_get_external_nonconformity_details_use_case,
    build_list_external_nonconformities_use_case,
    build_update_external_nonconformity_use_case,
    build_transition_external_nonconformity_status_use_case,
    build_add_external_nc_comment_use_case,
    build_list_external_nc_comments_use_case,
    build_upload_external_nc_attachment_use_case,
)
from app.domain.entities.external_nc.external_nonconformity import (
    ExternalNonconformity,
)
from app.domain.entities.shared_quality.nonconformity_attachment import (
    NonconformityAttachment,
)
from app.domain.entities.shared_quality.nonconformity_comment import (
    NonconformityComment,
)
from app.interface.http.schemas.external_nc_schemas import (
    CreateExternalNonconformityBody,
    ExternalNonconformityResponse,
    PaginatedExternalNonconformityResponse,
    UpdateExternalNonconformityBody,
    TransitionExternalNonconformityStatusBody,
    AddExternalNcCommentBody,
    ExternalNcAttachmentResponse,
    ExternalNcCommentResponse,
    UploadExternalNcAttachmentBody,
)


router = APIRouter()


@router.post(
    "/nonconformities",
    response_model=ExternalNonconformityResponse,
    status_code=status.HTTP_201_CREATED,
)
@require_permission("quality-nc.manage")
def create_external_nonconformity(body: CreateExternalNonconformityBody):
    try:
        use_case = build_create_external_nonconformity_use_case()

        result = use_case.execute(
            CreateExternalNonconformityRequest(
                company_unit=body.company_unit,
                supplier_id=body.supplier_id,
                supplier_name_snapshot=body.supplier_name_snapshot,
                opened_by_user_id=body.opened_by_user_id,
                occurrence_date=body.occurrence_date,
                detection_date=body.detection_date,
                severity=body.severity,
                priority=body.priority,
                title=body.title,
                problem_description=body.problem_description,
                customer_name=body.customer_name,
                origin_type=body.origin_type,
                source_channel=body.source_channel,
                material_code=body.material_code,
                material_description=body.material_description,
                material_specification=body.material_specification,
                lot_number=body.lot_number,
                purchase_order=body.purchase_order,
                invoice_number=body.invoice_number,
                document_reference=body.document_reference,
                defective_quantity=body.defective_quantity,
                inspected_quantity=body.inspected_quantity,
                uom=body.uom,
                occurrence_type=body.occurrence_type,
                defect_category=body.defect_category,
                recurrence_flag=body.recurrence_flag,
                containment_required=body.containment_required,
                business_impact=body.business_impact,
                customer_impact=body.customer_impact,
                production_impact=body.production_impact,
                cost_estimate=body.cost_estimate,
                responsible_user_id=body.responsible_user_id,
                due_date=body.due_date,
            )
        )
        return _to_response(result)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get(
    "/nonconformities",
    response_model=PaginatedExternalNonconformityResponse,
)
@require_any_permission(["api-delpi.access", "quality-nc.manage"])
def list_external_nonconformities(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    current_status: str | None = Query(default=None),
    supplier_id: str | None = Query(default=None),
    search: str | None = Query(default=None),
):
    try:
        use_case = build_list_external_nonconformities_use_case()
        result = use_case.execute(
            ListExternalNonconformitiesRequest(
                page=page,
                page_size=page_size,
                current_status=current_status,
                supplier_id=supplier_id,
                search=search,
            )
        )

        return {
            "items": [_to_response(item) for item in result["items"]],
            "page": result["page"],
            "page_size": result["page_size"],
            "total": result["total"],
            "total_pages": result["total_pages"],
        }
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get(
    "/nonconformities/{nonconformity_id}",
    response_model=ExternalNonconformityResponse,
)
@require_any_permission(["api-delpi.access", "quality-nc.manage"])
def get_external_nonconformity_details(nonconformity_id: str):
    try:
        use_case = build_get_external_nonconformity_details_use_case()
        result = use_case.execute(nonconformity_id)
        return _to_response(result)
    except ValueError as exc:
        detail = str(exc)
        status_code = 404 if "não encontrada" in detail.lower() else 400
        raise HTTPException(status_code=status_code, detail=detail) from exc


@router.patch(
    "/nonconformities/{nonconformity_id}",
    response_model=ExternalNonconformityResponse,
)
@require_permission("quality-nc.manage")
def update_external_nonconformity(
    nonconformity_id: str,
    body: UpdateExternalNonconformityBody,
):
    try:
        use_case = build_update_external_nonconformity_use_case()
        result = use_case.execute(
            UpdateExternalNonconformityRequest(
                nonconformity_id=nonconformity_id,
                company_unit=body.company_unit,
                supplier_id=body.supplier_id,
                supplier_name_snapshot=body.supplier_name_snapshot,
                occurrence_date=body.occurrence_date,
                detection_date=body.detection_date,
                severity=body.severity,
                priority=body.priority,
                title=body.title,
                problem_description=body.problem_description,
                customer_name=body.customer_name,
                origin_type=body.origin_type,
                source_channel=body.source_channel,
                material_code=body.material_code,
                material_description=body.material_description,
                material_specification=body.material_specification,
                lot_number=body.lot_number,
                purchase_order=body.purchase_order,
                invoice_number=body.invoice_number,
                document_reference=body.document_reference,
                defective_quantity=body.defective_quantity,
                inspected_quantity=body.inspected_quantity,
                uom=body.uom,
                occurrence_type=body.occurrence_type,
                defect_category=body.defect_category,
                recurrence_flag=body.recurrence_flag,
                containment_required=body.containment_required,
                business_impact=body.business_impact,
                customer_impact=body.customer_impact,
                production_impact=body.production_impact,
                cost_estimate=body.cost_estimate,
                current_status=body.current_status,
                supplier_status=body.supplier_status,
                responsible_user_id=body.responsible_user_id,
                due_date=body.due_date,
                cancellation_reason=body.cancellation_reason,
            )
        )
        return _to_response(result)
    except ValueError as exc:
        detail = str(exc)
        status_code = 404 if "não encontrada" in detail.lower() else 400
        raise HTTPException(status_code=status_code, detail=detail) from exc


@router.post(
    "/nonconformities/{nonconformity_id}/transition",
    response_model=ExternalNonconformityResponse,
)
@require_permission("quality-nc.manage")
def transition_external_nonconformity_status(
    nonconformity_id: str,
    body: TransitionExternalNonconformityStatusBody,
):
    try:
        use_case = build_transition_external_nonconformity_status_use_case()
        result = use_case.execute(
            TransitionExternalNonconformityStatusRequest(
                nonconformity_id=nonconformity_id,
                target_status=body.target_status,
                actor_user_id=body.actor_user_id,
                justification=body.justification,
                effectiveness_approved=body.effectiveness_approved,
            )
        )
        return _to_response(result)
    except ValueError as exc:
        detail = str(exc)
        status_code = 404 if "não encontrada" in detail.lower() else 400
        raise HTTPException(status_code=status_code, detail=detail) from exc


@router.get(
    "/nonconformities/{nonconformity_id}/comments",
    response_model=list[ExternalNcCommentResponse],
)
def list_external_nc_comments(nonconformity_id: str):
    try:
        use_case = build_list_external_nc_comments_use_case()
        result = use_case.execute(nonconformity_id)
        return [_to_comment_response(item) for item in result]
    except ValueError as exc:
        detail = str(exc)
        status_code = 404 if "não encontrada" in detail.lower() else 400
        raise HTTPException(status_code=status_code, detail=detail) from exc


@router.post(
    "/nonconformities/{nonconformity_id}/comments",
    response_model=ExternalNcCommentResponse,
    status_code=status.HTTP_201_CREATED,
)
def add_external_nc_comment(
    nonconformity_id: str,
    body: AddExternalNcCommentBody,
):
    try:
        use_case = build_add_external_nc_comment_use_case()
        result = use_case.execute(
            AddExternalNcCommentRequest(
                nonconformity_id=nonconformity_id,
                comment_type=body.comment_type,
                content=body.content,
                is_internal=body.is_internal,
                created_by_user_id=body.created_by_user_id,
            )
        )
        return _to_comment_response(result)
    except ValueError as exc:
        detail = str(exc)
        status_code = 404 if "não encontrada" in detail.lower() else 400
        raise HTTPException(status_code=status_code, detail=detail) from exc


@router.post(
    "/nonconformities/{nonconformity_id}/attachments",
    response_model=ExternalNcAttachmentResponse,
    status_code=status.HTTP_201_CREATED,
)
def upload_external_nc_attachment(
    nonconformity_id: str,
    body: UploadExternalNcAttachmentBody,
):
    try:
        use_case = build_upload_external_nc_attachment_use_case()
        result = use_case.execute(
            UploadExternalNcAttachmentRequest(
                nonconformity_id=nonconformity_id,
                file_name=body.file_name,
                original_name=body.original_name,
                mime_type=body.mime_type,
                size_bytes=body.size_bytes,
                storage_provider=body.storage_provider,
                storage_path=body.storage_path,
                checksum=body.checksum,
                uploaded_by_user_id=body.uploaded_by_user_id,
            )
        )
        return _to_attachment_response(result)
    except ValueError as exc:
        detail = str(exc)
        status_code = 404 if "não encontrada" in detail.lower() else 400
        raise HTTPException(status_code=status_code, detail=detail) from exc



def _to_comment_response(comment: NonconformityComment) -> ExternalNcCommentResponse:
    return ExternalNcCommentResponse(
        id=comment.id,
        nc_type=comment.nc_type,
        nc_id=comment.nc_id,
        comment_type=comment.comment_type,
        content=comment.content,
        is_internal=comment.is_internal,
        created_by_user_id=comment.created_by_user_id,
        created_at=comment.created_at,
    )


def _to_attachment_response(
    attachment: NonconformityAttachment,
) -> ExternalNcAttachmentResponse:
    return ExternalNcAttachmentResponse(
        id=attachment.id,
        nc_type=attachment.nc_type,
        nc_id=attachment.nc_id,
        action_id=attachment.action_id,
        effectiveness_check_id=attachment.effectiveness_check_id,
        file_name=attachment.file_name,
        original_name=attachment.original_name,
        mime_type=attachment.mime_type,
        size_bytes=attachment.size_bytes,
        storage_provider=attachment.storage_provider,
        storage_path=attachment.storage_path,
        checksum=attachment.checksum,
        uploaded_by_user_id=attachment.uploaded_by_user_id,
        uploaded_at=attachment.uploaded_at,
    )


def _to_response(entity: ExternalNonconformity) -> ExternalNonconformityResponse:
    return ExternalNonconformityResponse(
        id=entity.id,
        code=entity.code,
        company_unit=entity.company_unit,
        supplier_id=entity.supplier_id,
        supplier_name_snapshot=entity.supplier_name_snapshot,
        customer_name=entity.customer_name,
        origin_type=entity.origin_type,
        source_channel=entity.source_channel,
        material_code=entity.material_code,
        material_description=entity.material_description,
        material_specification=entity.material_specification,
        lot_number=entity.lot_number,
        purchase_order=entity.purchase_order,
        invoice_number=entity.invoice_number,
        document_reference=entity.document_reference,
        occurrence_date=entity.occurrence_date,
        detection_date=entity.detection_date,
        defective_quantity=entity.defective_quantity,
        inspected_quantity=entity.inspected_quantity,
        uom=entity.uom,
        severity=entity.severity,
        priority=entity.priority,
        occurrence_type=entity.occurrence_type,
        defect_category=entity.defect_category,
        recurrence_flag=entity.recurrence_flag,
        containment_required=entity.containment_required,
        title=entity.title,
        problem_description=entity.problem_description,
        business_impact=entity.business_impact,
        customer_impact=entity.customer_impact,
        production_impact=entity.production_impact,
        cost_estimate=entity.cost_estimate,
        current_status=entity.current_status,
        supplier_status=entity.supplier_status,
        responsible_user_id=entity.responsible_user_id,
        opened_by_user_id=entity.opened_by_user_id,
        due_date=entity.due_date,
        closed_at=entity.closed_at,
        cancellation_reason=entity.cancellation_reason,
        created_at=entity.created_at,
        updated_at=entity.updated_at,
    )