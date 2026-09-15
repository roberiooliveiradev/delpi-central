"""Provider-neutral Product Master search for external adapters."""

from __future__ import annotations

import logging
import time
from typing import Any

from app.application.dto.product.list_products_requests import ListProductsRequest
from app.application.external_capabilities.constants import (
    PRODUCT_SEARCH_MAX_PAGE_SIZE,
)
from app.application.external_capabilities.product_search_auth import (
    require_product_search_access,
)
from app.application.external_capabilities.product_search_projection import (
    project_product_search_page,
)

logger = logging.getLogger(__name__)


def normalize_product_search_pagination(
    *,
    page: int | None,
    page_size: int | None,
) -> tuple[int, int]:
    raw_page = 1 if page is None else int(page)
    raw_size = (
        PRODUCT_SEARCH_MAX_PAGE_SIZE
        if page_size is None
        else int(page_size)
    )
    safe_page = max(1, raw_page)
    safe_size = min(max(1, raw_size), PRODUCT_SEARCH_MAX_PAGE_SIZE)
    return safe_page, safe_size


def search_products(
    *,
    code: str | None = None,
    description: str | None = None,
    group_code: str | None = None,
    page: int = 1,
    page_size: int = 50,
    enforce_authz: bool = True,
    tool_name: str = "search_products",
) -> dict[str, Any]:
    """Execute canonical SearchProducts and return the approved external projection.

    ``customer_reference`` is never accepted. AuthZ uses ENGINEERING_LMP_ACCESS
    via ``require_product_search_access`` when ``enforce_authz`` is True.
    """
    # Lazy import: avoids pulling pyodbc/TOTVS at module import time (tests/CI).
    from app.composition.product_composer import build_search_products_use_case

    if enforce_authz:
        require_product_search_access()

    safe_page, safe_size = normalize_product_search_pagination(
        page=page,
        page_size=page_size,
    )
    started = time.perf_counter()
    dto = ListProductsRequest(
        code=code,
        description=description,
        group_code=group_code,
        customer_reference=None,
        page=safe_page,
        page_size=safe_size,
    )
    result = build_search_products_use_case().execute(dto)
    projected = project_product_search_page(result.to_dict())
    latency_ms = int((time.perf_counter() - started) * 1000)

    user = None
    try:
        from delpi_auth.request_context import get_current_user

        user = get_current_user()
    except Exception:
        user = None

    logger.info(
        "external_capability_search_products",
        extra={
            "tool": tool_name,
            "actor_id": getattr(user, "id", None),
            "status": "ok",
            "latency_ms": latency_ms,
            "page": safe_page,
            "page_size": safe_size,
            "result_count": len(projected.get("items") or []),
        },
    )
    return projected
