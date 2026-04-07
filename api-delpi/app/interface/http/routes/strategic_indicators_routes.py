from fastapi import APIRouter, HTTPException, Request, Query

from delpi_auth.authorization import require_permission

from app.interface.http.schemas.strategic_indicators_settings_schema import (
    UpdateStrategicIndicatorsSettingsBodySchema,
    CreateChangeRequestBody,
    AddCommentBody,
)

from app.application.dto.strategic_indicators.update_settings_request import (
    UpdateStrategicIndicatorsSettingsRequest,
)
from app.application.dto.strategic_indicators.add_change_request_comment_request import (
    AddStrategicIndicatorsChangeRequestCommentRequest,
)
from app.application.dto.strategic_indicators.create_change_request_request import (
    CreateStrategicIndicatorsChangeRequestRequest,
)
from app.application.dto.strategic_indicators.get_executive_summary_real_request import (
    GetExecutiveSummaryRealRequest
)

from app.application.use_cases.strategic_indicators.update_settings_use_case import (
    StrategicIndicatorsSettingsValidationError,
)
from app.application.use_cases.strategic_indicators.get_department_details_use_case import (
    DepartmentNotFoundError,
)

from app.composition.strategic_indicators_composer import (
    build_get_strategic_indicators_executive_summary_use_case,
    build_get_strategic_indicators_settings_use_case,
    build_list_strategic_indicators_settings_audit_use_case,
    build_update_strategic_indicators_settings_use_case,
    build_add_strategic_indicators_change_request_comment_use_case,
    build_create_strategic_indicators_change_request_use_case,
    build_list_strategic_indicators_change_requests_use_case,
    build_submit_strategic_indicators_change_request_use_case,
    build_get_strategic_indicators_departments_use_case,
    build_get_strategic_indicators_department_details_use_case,
    build_get_strategic_indicators_use_case,
)

router = APIRouter(
    prefix="/strategic-indicators",
    tags=["Strategic Indicators"],
)


def _extract_actor(request: Request) -> tuple[str | None, str | None]:
    user_context = getattr(request.state, "user", None)
    actor_user_id = None
    actor_email = None

    if user_context is not None:
        actor_user_id = getattr(user_context, "id", None) or getattr(
            user_context, "sub", None
        )
        actor_email = getattr(user_context, "email", None)

    return actor_user_id, actor_email


@router.get("/health")
def strategic_indicators_health():
    return {
        "status": "online",
        "module": "strategic-indicators",
    }


@router.get("/executive-summary")
@require_permission("strategic-indicators.view")
def get_strategic_indicators_executive_summary(
    competence: str | None = Query(None),
    start_date: str | None = Query(None),
    end_date: str | None = Query(None),
):
    try:
        use_case = build_get_strategic_indicators_executive_summary_use_case()
        result = use_case.execute(
            GetExecutiveSummaryRealRequest(
                competence=competence,
                start_date=start_date,
                end_date=end_date,
            )
        )
        return result
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Falha ao carregar resumo executivo do Strategic Indicators: {exc}",
        ) from exc


@router.get("/settings")
@require_permission("strategic-indicators.settings.manage")
def get_strategic_indicators_settings():
    try:
        use_case = build_get_strategic_indicators_settings_use_case()
        result = use_case.execute()

        return {
            "weights": result.weights,
            "goals": result.goals,
            "parameters": result.parameters,
            "governance": result.governance,
            "meta": {
                "source": result.meta.source,
                "updated_at": result.meta.updated_at,
                "updated_by_email": result.meta.updated_by_email,
            },
        }
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Falha ao carregar configurações do Strategic Indicators: {exc}",
        ) from exc


@router.put("/settings")
@require_permission("strategic-indicators.settings.manage")
async def update_strategic_indicators_settings(
    body: UpdateStrategicIndicatorsSettingsBodySchema,
    request: Request,
):
    try:
        actor_user_id, actor_email = _extract_actor(request)

        dto = UpdateStrategicIndicatorsSettingsRequest(
            weights=body.weights.model_dump(),
            goals=body.goals.model_dump(),
            parameters=body.parameters.model_dump(),
            governance=body.governance.model_dump(),
            actor_user_id=actor_user_id,
            actor_email=actor_email,
        )

        use_case = build_update_strategic_indicators_settings_use_case()
        result = use_case.execute(dto)

        return result

    except StrategicIndicatorsSettingsValidationError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Falha ao atualizar configurações do Strategic Indicators: {exc}",
        ) from exc


@router.get("/settings/audit")
@require_permission("strategic-indicators.settings.manage")
def get_strategic_indicators_settings_audit(
    limit: int = Query(20, ge=1, le=200),
    entity_key: str | None = Query(None),
):
    try:
        use_case = build_list_strategic_indicators_settings_audit_use_case()
        rows = use_case.execute(
            limit=limit,
            entity_key=entity_key,
        )
        return {
            "items": rows,
        }
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Falha ao carregar auditoria do Strategic Indicators: {exc}",
        ) from exc


@router.get("/change-requests")
@require_permission("strategic-indicators.settings.manage")
def list_change_requests():
    try:
        use_case = build_list_strategic_indicators_change_requests_use_case()
        return {"items": use_case.execute()}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.post("/change-requests")
@require_permission("strategic-indicators.settings.manage")
def create_change_request(body: CreateChangeRequestBody, request: Request):
    try:
        actor_user_id, actor_email = _extract_actor(request)

        use_case = build_create_strategic_indicators_change_request_use_case()
        result = use_case.execute(
            CreateStrategicIndicatorsChangeRequestRequest(
                title=body.title,
                description=body.description,
                target_block=body.target_block,
                proposed_payload=body.proposed_payload,
                actor_user_id=actor_user_id,
                actor_email=actor_email,
            )
        )
        return result
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.post("/change-requests/{change_request_id}/comments")
@require_permission("strategic-indicators.settings.manage")
def add_comment(change_request_id: str, body: AddCommentBody, request: Request):
    try:
        actor_user_id, actor_email = _extract_actor(request)

        use_case = build_add_strategic_indicators_change_request_comment_use_case()
        result = use_case.execute(
            AddStrategicIndicatorsChangeRequestCommentRequest(
                change_request_id=change_request_id,
                comment_text=body.comment_text,
                actor_user_id=actor_user_id,
                actor_email=actor_email,
            )
        )
        return result
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.post("/change-requests/{change_request_id}/submit")
@require_permission("strategic-indicators.settings.manage")
def submit_change_request(change_request_id: str, request: Request):
    try:
        actor_user_id, actor_email = _extract_actor(request)

        use_case = build_submit_strategic_indicators_change_request_use_case()
        result = use_case.execute(change_request_id, actor_user_id, actor_email)
        return result
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.get("/departments")
@require_permission("strategic-indicators.view")
def get_strategic_indicators_departments():
    try:
        use_case = build_get_strategic_indicators_departments_use_case()
        result = use_case.execute()

        return {
            "items": [
                {
                    "id": item.id,
                    "name": item.name,
                    "short_name": item.short_name,
                    "weight_pct": item.weight_pct,
                    "score": item.score,
                    "classification": item.classification,
                    "contribution": item.contribution,
                    "aggregation_mode": item.aggregation_mode,
                    "strategic_summary": item.strategic_summary,
                    "variation": {
                        "value": item.variation.value,
                        "direction": item.variation.direction,
                    },
                }
                for item in result.items
            ]
        }
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Falha ao carregar departamentos do Strategic Indicators: {exc}",
        ) from exc


@router.get("/departments/{department_id}")
@require_permission("strategic-indicators.view")
def get_strategic_indicators_department_details(department_id: str):
    try:
        use_case = build_get_strategic_indicators_department_details_use_case()
        result = use_case.execute(department_id)

        return {
            "id": result.id,
            "name": result.name,
            "short_name": result.short_name,
            "weight_pct": result.weight_pct,
            "score": result.score,
            "classification": result.classification,
            "contribution": result.contribution,
            "aggregation_mode": result.aggregation_mode,
            "strategic_summary": result.strategic_summary,
            "variation": {
                "value": result.variation.value,
                "direction": result.variation.direction,
            },
            "units": [
                {
                    "unit_id": unit.unit_id,
                    "unit_name": unit.unit_name,
                    "score": unit.score,
                    "classification": unit.classification,
                }
                for unit in result.units
            ],
            "indicators": [
                {
                    "id": indicator.id,
                    "name": indicator.name,
                    "weight_pct": indicator.weight_pct,
                    "goal_2026": indicator.goal_2026,
                    "strategic_description": indicator.strategic_description,
                    "scope_type": indicator.scope_type,
                    "realized": indicator.realized,
                    "score": indicator.score,
                    "gap": indicator.gap,
                    "trend": indicator.trend,
                }
                for indicator in result.indicators
            ],
        }
    except DepartmentNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Falha ao carregar detalhe do departamento: {exc}",
        ) from exc


@router.get("/indicators")
@require_permission("strategic-indicators.view")
def get_strategic_indicators(
    department_id: str | None = Query(None),
    start_date: str | None = Query(None),
    end_date: str | None = Query(None),
):
    try:
        use_case = build_get_strategic_indicators_use_case()
        result = use_case.execute(
            department_id=department_id,
            start_date=start_date,
            end_date=end_date,
        )

        return {
            "items": [
                {
                    "department_id": item.department_id,
                    "department_name": item.department_name,
                    "indicator_id": item.indicator_id,
                    "indicator_name": item.indicator_name,
                    "weight_pct": item.weight_pct,
                    "goal_2026": item.goal_2026,
                    "scope_type": item.scope_type,
                    "value": item.value,
                    "score": item.score,
                    "gap": item.gap,
                    "trend": item.trend,
                    "classification": item.classification,
                    "source": item.source,
                }
                for item in result.items
            ],
            "errors": [
                {
                    "department_id": error.department_id,
                    "source": error.source,
                    "message": error.message,
                }
                for error in result.errors
            ],
            "partial_success": result.partial_success,
        }
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Falha ao carregar indicadores do Strategic Indicators: {exc}",
        ) from exc