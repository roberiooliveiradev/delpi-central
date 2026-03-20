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
from app.application.dto.external_nc.add_external_nc_root_cause_request import (
    AddExternalNcRootCauseRequest,
)
from app.application.dto.external_nc.create_external_nc_action_request import (
    CreateExternalNcActionRequest,
)
from app.application.dto.external_nc.update_external_nc_action_request import (
    UpdateExternalNcActionRequest,
)
from app.application.dto.external_nc.complete_external_nc_action_request import (
    CompleteExternalNcActionRequest,
)
from app.application.dto.external_nc.register_external_nc_effectiveness_check_request import (
    RegisterExternalNcEffectivenessCheckRequest,
)
from app.application.dto.external_nc.upload_external_nc_action_attachment_request import (
    UploadExternalNcActionAttachmentRequest,
)
from app.application.dto.external_nc.add_external_nc_team_member_request import (
    AddExternalNcTeamMemberRequest,
)
from app.application.dto.external_nc.remove_external_nc_team_member_request import (
    RemoveExternalNcTeamMemberRequest,
)
from app.application.dto.external_nc.update_external_supplier_status_request import (
    UpdateExternalSupplierStatusRequest,
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
    build_add_external_nc_root_cause_use_case,
    build_list_external_nc_root_causes_use_case,
    build_create_external_nc_action_use_case,
    build_update_external_nc_action_use_case,
    build_complete_external_nc_action_use_case,
    build_list_external_nc_actions_use_case,
    build_list_external_nc_effectiveness_checks_use_case,
    build_register_external_nc_effectiveness_check_use_case,
    build_upload_external_nc_action_attachment_use_case,
    build_add_external_nc_team_member_use_case,
    build_list_external_nc_team_members_use_case,
    build_remove_external_nc_team_member_use_case,
    build_update_external_supplier_status_use_case,
    build_get_external_nc_dashboard_by_cause_use_case,
    build_get_external_nc_dashboard_by_supplier_use_case,
    build_get_external_nc_dashboard_overdue_actions_use_case,
    build_get_external_nc_dashboard_summary_use_case,
    build_export_nonconformity_report_use_case,
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
from app.domain.entities.external_nc.external_nonconformity_root_cause import (
    ExternalNonconformityRootCause,
)
from app.domain.entities.external_nc.external_nonconformity_action import (
    ExternalNonconformityAction,
)
from app.domain.entities.external_nc.external_nonconformity_effectiveness_check import (
    ExternalNonconformityEffectivenessCheck,
)
from app.domain.entities.external_nc.external_nc_team_member import (
    ExternalNcTeamMember,
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
    AddExternalNcRootCauseBody,
    ExternalNcRootCauseResponse,
    CreateExternalNcActionBody,
    UpdateExternalNcActionBody,
    CompleteExternalNcActionBody,
    ExternalNcActionResponse,
    ExternalNcEffectivenessCheckResponse,
    RegisterExternalNcEffectivenessCheckBody,
    UploadExternalNcActionAttachmentBody,
    AddExternalNcTeamMemberBody,
    ExternalNcTeamMemberResponse,
    UpdateExternalSupplierStatusBody,
    ExternalNcDashboardByCauseResponse,
    ExternalNcDashboardBySupplierResponse,
    ExternalNcDashboardOverdueActionResponse,
    ExternalNcDashboardSummaryResponse,
    ExternalNcExportResponse,
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
@require_any_permission(["api-delpi.access","quality-nc.manage"])
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
@require_permission("quality-nc.manage")
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
@require_permission("quality-nc.manage")
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


@router.get(
    "/nonconformities/{nonconformity_id}/root-causes",
    response_model=list[ExternalNcRootCauseResponse],
)
@require_any_permission(["api-delpi.access","quality-nc.manage"])
def list_external_nc_root_causes(nonconformity_id: str):
    try:
        use_case = build_list_external_nc_root_causes_use_case()
        result = use_case.execute(nonconformity_id)
        return [_to_root_cause_response(item) for item in result]
    except ValueError as exc:
        detail = str(exc)
        status_code = 404 if "não encontrada" in detail.lower() else 400
        raise HTTPException(status_code=status_code, detail=detail) from exc


@router.post(
    "/nonconformities/{nonconformity_id}/root-causes",
    response_model=ExternalNcRootCauseResponse,
    status_code=status.HTTP_201_CREATED,
)
@require_permission("quality-nc.manage")
def add_external_nc_root_cause(
    nonconformity_id: str,
    body: AddExternalNcRootCauseBody,
):
    try:
        use_case = build_add_external_nc_root_cause_use_case()
        result = use_case.execute(
            AddExternalNcRootCauseRequest(
                nonconformity_id=nonconformity_id,
                analysis_method=body.analysis_method,
                cause_dimension=body.cause_dimension,
                category=body.category,
                why_level=body.why_level,
                description=body.description,
                is_root_cause=body.is_root_cause,
                created_by_user_id=body.created_by_user_id,
            )
        )
        return _to_root_cause_response(result)
    except ValueError as exc:
        detail = str(exc)
        status_code = 404 if "não encontrada" in detail.lower() else 400
        raise HTTPException(status_code=status_code, detail=detail) from exc


@router.get(
    "/nonconformities/{nonconformity_id}/actions",
    response_model=list[ExternalNcActionResponse],
)
@require_any_permission(["api-delpi.access","quality-nc.manage"])
def list_external_nc_actions(nonconformity_id: str):
    try:
        use_case = build_list_external_nc_actions_use_case()
        result = use_case.execute(nonconformity_id)
        return [_to_action_response(item) for item in result]
    except ValueError as exc:
        detail = str(exc)
        status_code = 404 if "não encontrada" in detail.lower() else 400
        raise HTTPException(status_code=status_code, detail=detail) from exc


@router.post(
    "/nonconformities/{nonconformity_id}/actions",
    response_model=ExternalNcActionResponse,
    status_code=status.HTTP_201_CREATED,
)
@require_permission("quality-nc.manage")
def create_external_nc_action(nonconformity_id: str, body: CreateExternalNcActionBody):
    try:
        use_case = build_create_external_nc_action_use_case()
        result = use_case.execute(
            CreateExternalNcActionRequest(
                nonconformity_id=nonconformity_id,
                root_cause_id=body.root_cause_id,
                action_type=body.action_type,
                title=body.title,
                description=body.description,
                responsible_user_id=body.responsible_user_id,
                responsible_external_name=body.responsible_external_name,
                responsible_external_email=body.responsible_external_email,
                start_date=body.start_date,
                due_date=body.due_date,
                verification_required=body.verification_required,
                effectiveness_due_date=body.effectiveness_due_date,
                created_by_user_id=body.created_by_user_id,
            )
        )
        return _to_action_response(result)
    except ValueError as exc:
        detail = str(exc)
        status_code = 404 if "não encontrada" in detail.lower() else 400
        raise HTTPException(status_code=status_code, detail=detail) from exc


@router.patch(
    "/actions/{action_id}",
    response_model=ExternalNcActionResponse,
)
@require_permission("quality-nc.manage")
def update_external_nc_action(action_id: str, body: UpdateExternalNcActionBody):
    try:
        use_case = build_update_external_nc_action_use_case()
        result = use_case.execute(
            UpdateExternalNcActionRequest(
                action_id=action_id,
                root_cause_id=body.root_cause_id,
                action_type=body.action_type,
                title=body.title,
                description=body.description,
                responsible_user_id=body.responsible_user_id,
                responsible_external_name=body.responsible_external_name,
                responsible_external_email=body.responsible_external_email,
                start_date=body.start_date,
                due_date=body.due_date,
                verification_required=body.verification_required,
                effectiveness_due_date=body.effectiveness_due_date,
            )
        )
        return _to_action_response(result)
    except ValueError as exc:
        detail = str(exc)
        status_code = 404 if "não encontrada" in detail.lower() else 400
        raise HTTPException(status_code=status_code, detail=detail) from exc


@router.post(
    "/actions/{action_id}/complete",
    response_model=ExternalNcActionResponse,
)
@require_permission("quality-nc.manage")
def complete_external_nc_action(action_id: str, body: CompleteExternalNcActionBody):
    try:
        use_case = build_complete_external_nc_action_use_case()
        result = use_case.execute(
            CompleteExternalNcActionRequest(
                action_id=action_id,
                actor_user_id=body.actor_user_id,
                completion_notes=body.completion_notes,
            )
        )
        return _to_action_response(result)
    except ValueError as exc:
        detail = str(exc)
        status_code = 404 if "não encontrada" in detail.lower() else 400
        raise HTTPException(status_code=status_code, detail=detail) from exc


@router.get(
    "/nonconformities/{nonconformity_id}/effectiveness-checks",
    response_model=list[ExternalNcEffectivenessCheckResponse],
)
@require_any_permission(["api-delpi.access","quality-nc.manage"])
def list_external_nc_effectiveness_checks(nonconformity_id: str):
    try:
        use_case = build_list_external_nc_effectiveness_checks_use_case()
        result = use_case.execute(nonconformity_id)
        return [_to_effectiveness_check_response(item) for item in result]
    except ValueError as exc:
        detail = str(exc)
        status_code = 404 if "não encontrada" in detail.lower() else 400
        raise HTTPException(status_code=status_code, detail=detail) from exc


@router.post(
    "/nonconformities/{nonconformity_id}/effectiveness-checks",
    response_model=ExternalNcEffectivenessCheckResponse,
    status_code=status.HTTP_201_CREATED,
)
@require_permission("quality-nc.manage")
def register_external_nc_effectiveness_check(
    nonconformity_id: str,
    body: RegisterExternalNcEffectivenessCheckBody,
):
    try:
        use_case = build_register_external_nc_effectiveness_check_use_case()
        result = use_case.execute(
            RegisterExternalNcEffectivenessCheckRequest(
                nonconformity_id=nonconformity_id,
                action_id=body.action_id,
                checked_by_user_id=body.checked_by_user_id,
                checked_at=body.checked_at,
                criteria=body.criteria,
                result=body.result,
                notes=body.notes,
                next_action=body.next_action,
            )
        )
        return _to_effectiveness_check_response(result)
    except ValueError as exc:
        detail = str(exc)
        status_code = 404 if "não encontrada" in detail.lower() else 400
        raise HTTPException(status_code=status_code, detail=detail) from exc


@router.post(
    "/actions/{action_id}/attachments",
    response_model=ExternalNcAttachmentResponse,
    status_code=status.HTTP_201_CREATED,
)
@require_permission("quality-nc.manage")
def upload_external_nc_action_attachment(
    action_id: str,
    body: UploadExternalNcActionAttachmentBody,
):
    try:
        use_case = build_upload_external_nc_action_attachment_use_case()
        result = use_case.execute(
            UploadExternalNcActionAttachmentRequest(
                action_id=action_id,
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

@router.get(
    "/nonconformities/{nonconformity_id}/team-members",
    response_model=list[ExternalNcTeamMemberResponse],
)
@require_permission("quality-nc.manage")
def list_external_nc_team_members(nonconformity_id: str):
    try:
        use_case = build_list_external_nc_team_members_use_case()
        result = use_case.execute(nonconformity_id)
        return [_to_team_member_response(item) for item in result]
    except ValueError as exc:
        detail = str(exc)
        status_code = 404 if "não encontrada" in detail.lower() else 400
        raise HTTPException(status_code=status_code, detail=detail) from exc


@router.post(
    "/nonconformities/{nonconformity_id}/team-members",
    response_model=ExternalNcTeamMemberResponse,
    status_code=status.HTTP_201_CREATED,
)
@require_permission("quality-nc.manage")
def add_external_nc_team_member(
    nonconformity_id: str,
    body: AddExternalNcTeamMemberBody,
):
    try:
        use_case = build_add_external_nc_team_member_use_case()
        result = use_case.execute(
            AddExternalNcTeamMemberRequest(
                nonconformity_id=nonconformity_id,
                user_id=body.user_id,
                role_in_case=body.role_in_case,
                actor_user_id=body.actor_user_id,
            )
        )
        return _to_team_member_response(result)
    except ValueError as exc:
        detail = str(exc)
        status_code = 404 if "não encontrada" in detail.lower() else 400
        raise HTTPException(status_code=status_code, detail=detail) from exc


@router.delete(
    "/nonconformities/{nonconformity_id}/team-members/{member_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
@require_permission("quality-nc.manage")
def remove_external_nc_team_member(
    nonconformity_id: str,
    member_id: str,
    actor_user_id: str = Query(...),
):
    try:
        use_case = build_remove_external_nc_team_member_use_case()
        use_case.execute(
            RemoveExternalNcTeamMemberRequest(
                nonconformity_id=nonconformity_id,
                member_id=member_id,
                actor_user_id=actor_user_id,
            )
        )
        return None
    except ValueError as exc:
        detail = str(exc)
        status_code = 404 if "não encontrada" in detail.lower() else 400
        raise HTTPException(status_code=status_code, detail=detail) from exc


@router.post(
    "/nonconformities/{nonconformity_id}/supplier-status",
    response_model=ExternalNonconformityResponse,
)
@require_permission("quality-nc.manage")
def update_external_supplier_status(
    nonconformity_id: str,
    body: UpdateExternalSupplierStatusBody,
):
    try:
        use_case = build_update_external_supplier_status_use_case()
        result = use_case.execute(
            UpdateExternalSupplierStatusRequest(
                nonconformity_id=nonconformity_id,
                supplier_status=body.supplier_status,
                actor_user_id=body.actor_user_id,
                justification=body.justification,
            )
        )
        return _to_response(result)
    except ValueError as exc:
        detail = str(exc)
        status_code = 404 if "não encontrada" in detail.lower() else 400
        raise HTTPException(status_code=status_code, detail=detail) from exc


@router.get(
    "/dashboard/summary",
    response_model=ExternalNcDashboardSummaryResponse,
)
@require_permission("api-delpi.access")
def get_external_nc_dashboard_summary():
    use_case = build_get_external_nc_dashboard_summary_use_case()
    return use_case.execute()


@router.get(
    "/dashboard/by-supplier",
    response_model=list[ExternalNcDashboardBySupplierResponse],
)
@require_permission("api-delpi.access")
def get_external_nc_dashboard_by_supplier():
    use_case = build_get_external_nc_dashboard_by_supplier_use_case()
    return use_case.execute()


@router.get(
    "/dashboard/by-cause",
    response_model=list[ExternalNcDashboardByCauseResponse],
)
@require_permission("api-delpi.access")
def get_external_nc_dashboard_by_cause():
    use_case = build_get_external_nc_dashboard_by_cause_use_case()
    return use_case.execute()


@router.get(
    "/dashboard/overdue-actions",
    response_model=list[ExternalNcDashboardOverdueActionResponse],
)
@require_permission("api-delpi.access")
def get_external_nc_dashboard_overdue_actions():
    use_case = build_get_external_nc_dashboard_overdue_actions_use_case()
    return use_case.execute()

@router.get(
    "/nonconformities/{nonconformity_id}/export",
    response_model=ExternalNcExportResponse,
)
@require_permission("api-delpi.access")
def export_external_nonconformity_report(nonconformity_id: str):
    try:
        use_case = build_export_nonconformity_report_use_case()
        return use_case.execute(nonconformity_id)
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


def _to_root_cause_response(
    entity: ExternalNonconformityRootCause,
) -> ExternalNcRootCauseResponse:
    return ExternalNcRootCauseResponse(
        id=entity.id,
        nonconformity_id=entity.nonconformity_id,
        analysis_method=entity.analysis_method,
        cause_dimension=entity.cause_dimension,
        category=entity.category,
        why_level=entity.why_level,
        description=entity.description,
        is_root_cause=entity.is_root_cause,
        created_by_user_id=entity.created_by_user_id,
        created_at=entity.created_at,
    )


def _to_action_response(
    entity: ExternalNonconformityAction,
) -> ExternalNcActionResponse:
    return ExternalNcActionResponse(
        id=entity.id,
        nonconformity_id=entity.nonconformity_id,
        root_cause_id=entity.root_cause_id,
        action_type=entity.action_type,
        title=entity.title,
        description=entity.description,
        responsible_user_id=entity.responsible_user_id,
        responsible_external_name=entity.responsible_external_name,
        responsible_external_email=entity.responsible_external_email,
        start_date=entity.start_date,
        due_date=entity.due_date,
        completed_at=entity.completed_at,
        status=entity.status,
        verification_required=entity.verification_required,
        effectiveness_due_date=entity.effectiveness_due_date,
        completion_notes=entity.completion_notes,
        created_by_user_id=entity.created_by_user_id,
        created_at=entity.created_at,
        updated_at=entity.updated_at,
    )


def _to_effectiveness_check_response(
    entity: ExternalNonconformityEffectivenessCheck,
) -> ExternalNcEffectivenessCheckResponse:
    return ExternalNcEffectivenessCheckResponse(
        id=entity.id,
        nonconformity_id=entity.nonconformity_id,
        action_id=entity.action_id,
        checked_by_user_id=entity.checked_by_user_id,
        checked_at=entity.checked_at,
        criteria=entity.criteria,
        result=entity.result,
        notes=entity.notes,
        next_action=entity.next_action,
        created_at=entity.created_at,
    )


def _to_team_member_response(
    entity: ExternalNcTeamMember,
) -> ExternalNcTeamMemberResponse:
    return ExternalNcTeamMemberResponse(
        id=entity.id,
        nonconformity_id=entity.nonconformity_id,
        user_id=entity.user_id,
        role_in_case=entity.role_in_case,
        joined_at=entity.joined_at,
    )