from __future__ import annotations

from fastapi import APIRouter, Query
from fastapi.responses import JSONResponse

from production_pulse_app.application.services.work_center_catalog_service import (
    BindingValidationError,
    WorkCenterCatalogService,
    WorkCenterCatalogUnavailableError,
)
from production_pulse_app.core.responses import error, success
from production_pulse_app.infrastructure.http.auth_header import bearer_authorization_from_context

router = APIRouter(prefix="/catalog", tags=["Catalog"])
_catalog_service = WorkCenterCatalogService()


@router.get("/work-centers")
async def list_work_centers(
    branch: str = Query(..., min_length=1),
    search: str | None = Query(default=None),
):
    try:
        data = _catalog_service.list_work_centers(
            branch=branch,
            search=search,
            authorization=bearer_authorization_from_context(),
        )
        return success(data)
    except BindingValidationError as exc:
        payload = error(str(exc), code="validation_error", status_code=422)
        status_code = payload.pop("_status_code", 422)
        return JSONResponse(status_code=status_code, content=payload)
    except WorkCenterCatalogUnavailableError as exc:
        payload = error(str(exc), code="upstream_unavailable", status_code=503)
        status_code = payload.pop("_status_code", 503)
        return JSONResponse(status_code=status_code, content=payload)
