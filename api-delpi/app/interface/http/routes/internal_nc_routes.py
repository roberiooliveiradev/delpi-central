# app/interface/http/routes/internal_nc_routes.py
from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query, status

from delpi_auth.authorization import require_any_permission, require_permission

from app.application.dto.internal_nc.create_internal_nonconformity_request import (
    CreateInternalNonconformityRequest,
)
from app.application.dto.internal_nc.list_internal_nonconformities_request import (
    ListInternalNonconformitiesRequest,
)
from app.application.dto.internal_nc.update_internal_nonconformity_request import (
    UpdateInternalNonconformityRequest,
)
from app.application.dto.internal_nc.transition_internal_nonconformity_status_request import (
    TransitionInternalNonconformityStatusRequest,
)
from app.application.dto.internal_nc.add_internal_nc_root_cause_request import (
    AddInternalNcRootCauseRequest,
)
from app.application.dto.internal_nc.create_internal_nc_action_request import (
    CreateInternalNcActionRequest,
)
from app.application.dto.internal_nc.update_internal_nc_action_request import (
    UpdateInternalNcActionRequest,
)
from app.application.dto.internal_nc.complete_internal_nc_action_request import (
    CompleteInternalNcActionRequest,
)
from app.composition.internal_nc_composer import (
    build_create_internal_nonconformity_use_case,
    build_get_internal_nonconformity_details_use_case,
    build_list_internal_nonconformities_use_case,
    build_update_internal_nonconformity_use_case,
    build_transition_internal_nonconformity_status_use_case,
    build_add_internal_nc_root_cause_use_case,
    build_list_internal_nc_root_causes_use_case,
    build_create_internal_nc_action_use_case,
    build_update_internal_nc_action_use_case,
    build_complete_internal_nc_action_use_case,
    build_list_internal_nc_actions_use_case,
)
from app.domain.entities.internal_nc.internal_nonconformity import (
    InternalNonconformity,
)
from app.domain.entities.internal_nc.internal_nonconformity_root_cause import (
    InternalNonconformityRootCause,
)
from app.domain.entities.internal_nc.internal_nonconformity_action import (
    InternalNonconformityAction,
)
from app.interface.http.schemas.internal_nc_schemas import (
    CreateInternalNonconformityBody,
    InternalNonconformityResponse,
    PaginatedInternalNonconformityResponse,
    UpdateInternalNonconformityBody,
    TransitionInternalNonconformityStatusBody,
    AddInternalNcRootCauseBody,
    InternalNcRootCauseResponse,
    CreateInternalNcActionBody,
    UpdateInternalNcActionBody,
    CompleteInternalNcActionBody,
    InternalNcActionResponse,
)

router = APIRouter()


@router.post(
    "/nonconformities",
    response_model=InternalNonconformityResponse,
    status_code=status.HTTP_201_CREATED,
)
@require_permission("quality-nc.manage")
def create_internal_nonconformity(body: CreateInternalNonconformityBody):
    try:
        use_case = build_create_internal_nonconformity_use_case()
        result = use_case.execute(
            CreateInternalNonconformityRequest(
                source_type=body.source_type,
                detected_by_user_id=body.detected_by_user_id,
                detection_date=body.detection_date,
                item_code=body.item_code,
                item_description=body.item_description,
                sector=body.sector,
                defect_category=body.defect_category,
                defect_description=body.defect_description,
                severity=body.severity,
                priority=body.priority,
                source_inspection_id=body.source_inspection_id,
                production_order=body.production_order,
                lot_number=body.lot_number,
                operation_code=body.operation_code,
                operation_description=body.operation_description,
                defective_quantity=body.defective_quantity,
                inspected_quantity=body.inspected_quantity,
                containment_action_summary=body.containment_action_summary,
                disposition_type=body.disposition_type,
                immediate_cause_notes=body.immediate_cause_notes,
                root_cause_summary=body.root_cause_summary,
                responsible_user_id=body.responsible_user_id,
                due_date=body.due_date,
            )
        )
        return _to_response(result)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get(
    "/nonconformities",
    response_model=PaginatedInternalNonconformityResponse,
)
@require_any_permission(["quality-nc.view"])
def list_internal_nonconformities(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    current_status: str | None = Query(default=None),
    sector: str | None = Query(default=None),
    search: str | None = Query(default=None),
):
    try:
        use_case = build_list_internal_nonconformities_use_case()
        result = use_case.execute(
            ListInternalNonconformitiesRequest(
                page=page,
                page_size=page_size,
                current_status=current_status,
                sector=sector,
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
    response_model=InternalNonconformityResponse,
)
@require_permission("quality-nc.view")
def get_internal_nonconformity_details(nonconformity_id: str):
    try:
        use_case = build_get_internal_nonconformity_details_use_case()
        result = use_case.execute(nonconformity_id)
        return _to_response(result)
    except ValueError as exc:
        detail = str(exc)
        status_code = 404 if "não encontrada" in detail.lower() else 400
        raise HTTPException(status_code=status_code, detail=detail) from exc


@router.patch(
    "/nonconformities/{nonconformity_id}",
    response_model=InternalNonconformityResponse,
)
@require_permission("quality-nc.manage")
def update_internal_nonconformity(
    nonconformity_id: str,
    body: UpdateInternalNonconformityBody,
):
    try:
        use_case = build_update_internal_nonconformity_use_case()
        result = use_case.execute(
            UpdateInternalNonconformityRequest(
                nonconformity_id=nonconformity_id,
                source_type=body.source_type,
                detected_by_user_id=body.detected_by_user_id,
                detection_date=body.detection_date,
                item_code=body.item_code,
                item_description=body.item_description,
                sector=body.sector,
                defect_category=body.defect_category,
                defect_description=body.defect_description,
                severity=body.severity,
                priority=body.priority,
                current_status=body.current_status,
                source_inspection_id=body.source_inspection_id,
                production_order=body.production_order,
                lot_number=body.lot_number,
                operation_code=body.operation_code,
                operation_description=body.operation_description,
                defective_quantity=body.defective_quantity,
                inspected_quantity=body.inspected_quantity,
                containment_action_summary=body.containment_action_summary,
                disposition_type=body.disposition_type,
                immediate_cause_notes=body.immediate_cause_notes,
                root_cause_summary=body.root_cause_summary,
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
    response_model=InternalNonconformityResponse,
)
@require_permission("quality-nc.manage")
def transition_internal_nonconformity_status(
    nonconformity_id: str,
    body: TransitionInternalNonconformityStatusBody,
):
    try:
        use_case = build_transition_internal_nonconformity_status_use_case()
        result = use_case.execute(
            TransitionInternalNonconformityStatusRequest(
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
    "/nonconformities/{nonconformity_id}/root-causes",
    response_model=list[InternalNcRootCauseResponse],
)
@require_any_permission(["quality-nc.view"])
def list_internal_nc_root_causes(nonconformity_id: str):
    try:
        use_case = build_list_internal_nc_root_causes_use_case()
        result = use_case.execute(nonconformity_id)
        return [_to_root_cause_response(item) for item in result]
    except ValueError as exc:
        detail = str(exc)
        status_code = 404 if "não encontrada" in detail.lower() else 400
        raise HTTPException(status_code=status_code, detail=detail) from exc


@router.post(
    "/nonconformities/{nonconformity_id}/root-causes",
    response_model=InternalNcRootCauseResponse,
    status_code=status.HTTP_201_CREATED,
)
@require_any_permission(["quality-nc.manage"])
def add_internal_nc_root_cause(
    nonconformity_id: str,
    body: AddInternalNcRootCauseBody,
):
    try:
        use_case = build_add_internal_nc_root_cause_use_case()
        result = use_case.execute(
            AddInternalNcRootCauseRequest(
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
    response_model=list[InternalNcActionResponse],
)
@require_any_permission(["quality-nc.view"])
def list_internal_nc_actions(nonconformity_id: str):
    try:
        use_case = build_list_internal_nc_actions_use_case()
        result = use_case.execute(nonconformity_id)
        return [_to_action_response(item) for item in result]
    except ValueError as exc:
        detail = str(exc)
        status_code = 404 if "não encontrada" in detail.lower() else 400
        raise HTTPException(status_code=status_code, detail=detail) from exc


@router.post(
    "/nonconformities/{nonconformity_id}/actions",
    response_model=InternalNcActionResponse,
    status_code=status.HTTP_201_CREATED,
)
@require_any_permission(["quality-nc.manage"])
def create_internal_nc_action(nonconformity_id: str, body: CreateInternalNcActionBody):
    try:
        use_case = build_create_internal_nc_action_use_case()
        result = use_case.execute(
            CreateInternalNcActionRequest(
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
    response_model=InternalNcActionResponse,
)
@require_any_permission(["quality-nc.manage"])
def update_internal_nc_action(action_id: str, body: UpdateInternalNcActionBody):
    try:
        use_case = build_update_internal_nc_action_use_case()
        result = use_case.execute(
            UpdateInternalNcActionRequest(
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
    response_model=InternalNcActionResponse,
)
@require_any_permission(["quality-nc.manage"])
def complete_internal_nc_action(action_id: str, body: CompleteInternalNcActionBody):
    try:
        use_case = build_complete_internal_nc_action_use_case()
        result = use_case.execute(
            CompleteInternalNcActionRequest(
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


def _to_action_response(
    entity: InternalNonconformityAction,
) -> InternalNcActionResponse:
    return InternalNcActionResponse(
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


def _to_response(entity: InternalNonconformity) -> InternalNonconformityResponse:
    return InternalNonconformityResponse(
        id=entity.id,
        code=entity.code,
        source_type=entity.source_type,
        source_inspection_id=entity.source_inspection_id,
        production_order=entity.production_order,
        item_code=entity.item_code,
        item_description=entity.item_description,
        lot_number=entity.lot_number,
        sector=entity.sector,
        operation_code=entity.operation_code,
        operation_description=entity.operation_description,
        defect_category=entity.defect_category,
        defect_description=entity.defect_description,
        detected_by_user_id=entity.detected_by_user_id,
        detection_date=entity.detection_date,
        defective_quantity=entity.defective_quantity,
        inspected_quantity=entity.inspected_quantity,
        severity=entity.severity,
        priority=entity.priority,
        current_status=entity.current_status,
        containment_action_summary=entity.containment_action_summary,
        disposition_type=entity.disposition_type,
        immediate_cause_notes=entity.immediate_cause_notes,
        root_cause_summary=entity.root_cause_summary,
        responsible_user_id=entity.responsible_user_id,
        due_date=entity.due_date,
        closed_at=entity.closed_at,
        cancellation_reason=entity.cancellation_reason,
        created_at=entity.created_at,
        updated_at=entity.updated_at,
    )


def _to_root_cause_response(
    entity: InternalNonconformityRootCause,
) -> InternalNcRootCauseResponse:
    return InternalNcRootCauseResponse(
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