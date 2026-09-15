"""HTTP surface for OpenAI Custom GPT Actions (LEGACY_TRANSITIONAL)."""

from __future__ import annotations

import logging
from typing import Optional

from fastapi import APIRouter, Query
from fastapi.responses import JSONResponse

from app.application.external_capabilities.constants import (
    EXTERNAL_INTERNAL_ERROR_MESSAGE,
)
from app.application.gpt_actions.constants import (
    GPT_ACTIONS_BASE_PATH,
    GPT_PRODUCT_SEARCH_DEFAULT_PAGE_SIZE,
    GPT_PRODUCT_SEARCH_MAX_PAGE_SIZE,
)
from app.application.gpt_actions.dispatch_service import GptActionsDispatchService
from app.application.gpt_actions.openapi_builder import build_gpt_actions_openapi
from app.application.security.api_delpi_permissions import ENGINEERING_LMP_ACCESS
from app.config import settings
from app.utils.logger import log_error
from app.core.responses import error_response
from app.interface.http.route_response_helpers import api_delpi_success
from delpi_auth.authorization import require_any_permission, require_auth

router = APIRouter(
    prefix=GPT_ACTIONS_BASE_PATH,
    tags=["API DELPI GPT Actions (legacy)"],
)
logger = logging.getLogger(__name__)
_dispatch = GptActionsDispatchService()


@router.get(
    "/openapi.json",
    operation_id="gpt_get_openapi_schema",
    summary="Public OpenAPI schema for Custom GPT import (legacy)",
    include_in_schema=False,
)
def gpt_get_openapi_schema():
    return JSONResponse(
        build_gpt_actions_openapi(
            public_base_url=getattr(settings, "PUBLIC_BASE_URL", None),
            root_path="/apps/api-delpi",
        )
    )


@router.get(
    "/catalog",
    operation_id="gpt_get_catalog",
    summary="List V1 GPT capabilities and field allowlist (legacy)",
)
@require_auth()
def gpt_get_catalog():
    try:
        data = _dispatch.get_catalog()
        return api_delpi_success(
            data,
            operation_id="gpt_get_catalog",
            message="GPT Actions catalog loaded.",
        )
    except Exception as exc:
        log_error(f"gpt_get_catalog failed: {exc}")
        return error_response(
            EXTERNAL_INTERNAL_ERROR_MESSAGE,
            status_code=500,
            code="INTERNAL_ERROR",
            recoverable=True,
        )


@router.get(
    "/products/search",
    operation_id="gpt_search_products",
    summary="Search products with minimal projection (legacy)",
)
@require_any_permission(ENGINEERING_LMP_ACCESS)
def gpt_search_products(
    code: Optional[str] = Query(None),
    description: Optional[str] = Query(None),
    group_code: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(
        GPT_PRODUCT_SEARCH_DEFAULT_PAGE_SIZE,
        ge=1,
        le=GPT_PRODUCT_SEARCH_MAX_PAGE_SIZE,
    ),
):
    try:
        data = _dispatch.search_products(
            code=code,
            description=description,
            group_code=group_code,
            page=page,
            page_size=page_size,
        )
        return api_delpi_success(
            data,
            operation_id="gpt_search_products",
            message="Product search completed.",
        )
    except Exception as exc:
        log_error(f"gpt_search_products failed: {exc}")
        return error_response(
            EXTERNAL_INTERNAL_ERROR_MESSAGE,
            status_code=500,
            code="INTERNAL_ERROR",
            recoverable=True,
        )
