"""BFF production / products — proxy api-delpi com RBAC commercial."""

from __future__ import annotations

import logging
from urllib.parse import quote

from fastapi import APIRouter, Query, Request

from commercial_app.application.security.auth_dependencies import require_any_permission
from commercial_app.application.security.commercial_permissions import (
    COMMERCIAL_ANALYTICS_PERMISSIONS,
    COMMERCIAL_READ_PERMISSIONS,
)
from commercial_app.composition.commercial_composer import build_delpi_commercial_gateway
from commercial_app.core.responses import fail, ok
from commercial_app.interface.http.routes.totvs_bff_helpers import unwrap_gateway_data

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Production BFF"])

_PERM = (*COMMERCIAL_READ_PERMISSIONS, *COMMERCIAL_ANALYTICS_PERMISSIONS)


@router.get(
    "/production/orders/by-op/{production_order}",
    operation_id="bff_get_production_order_by_op",
)
@require_any_permission(*_PERM)
def production_order_by_op(
    _request: Request,
    production_order: str,
    branch: str | None = None,
):
    op_id = "bff_get_production_order_by_op"
    try:
        encoded = quote(production_order.strip(), safe="")
        payload = build_delpi_commercial_gateway().get_production(
            f"/orders/by-op/{encoded}",
            params={"branch": branch},
        )
        return ok(unwrap_gateway_data(payload), message="OP carregada.", operation_id=op_id)
    except RuntimeError as exc:
        return fail(str(exc), 502, operation_id=op_id)
    except Exception:
        logger.exception("%s_failed", op_id)
        return fail("Erro interno ao carregar OP.", 500, operation_id=op_id)


@router.get(
    "/production/appointments/by-op",
    operation_id="bff_get_production_appointments_by_op",
)
@require_any_permission(*_PERM)
def production_appointments_by_op(
    _request: Request,
    op: str = Query(...),
    branch: str | None = None,
    page: int = Query(default=1),
    page_size: int = Query(default=50),
):
    op_id = "bff_get_production_appointments_by_op"
    try:
        payload = build_delpi_commercial_gateway().get_production(
            "/appointments/by-op",
            params={"op": op, "branch": branch, "page": page, "page_size": page_size},
        )
        return ok(
            unwrap_gateway_data(payload),
            message="Apontamentos carregados.",
            operation_id=op_id,
        )
    except RuntimeError as exc:
        return fail(str(exc), 502, operation_id=op_id)
    except Exception:
        logger.exception("%s_failed", op_id)
        return fail("Erro interno ao carregar apontamentos.", 500, operation_id=op_id)


@router.get(
    "/products/{product_code}/factory-status",
    operation_id="bff_get_product_factory_status",
)
@require_any_permission(*_PERM)
def product_factory_status(
    _request: Request,
    product_code: str,
    branch: str | None = None,
):
    op_id = "bff_get_product_factory_status"
    try:
        encoded = quote(product_code.strip(), safe="")
        payload = build_delpi_commercial_gateway().get_product(
            f"/{encoded}/factory-status",
            params={"branch": branch},
        )
        return ok(
            unwrap_gateway_data(payload),
            message="Status fabril carregado.",
            operation_id=op_id,
        )
    except RuntimeError as exc:
        return fail(str(exc), 502, operation_id=op_id)
    except Exception:
        logger.exception("%s_failed", op_id)
        return fail("Erro interno ao carregar status fabril.", 500, operation_id=op_id)


@router.get(
    "/products/{product_code}/structure",
    operation_id="bff_get_product_structure",
)
@require_any_permission(*_PERM)
def product_structure(
    _request: Request,
    product_code: str,
    max_depth: int = Query(default=6),
    page_size: int = Query(default=200),
):
    op_id = "bff_get_product_structure"
    try:
        encoded = quote(product_code.strip(), safe="")
        payload = build_delpi_commercial_gateway().get_product(
            f"/{encoded}/structure",
            params={"max_depth": max_depth, "page_size": page_size},
        )
        return ok(
            unwrap_gateway_data(payload),
            message="Estrutura do produto carregada.",
            operation_id=op_id,
        )
    except RuntimeError as exc:
        return fail(str(exc), 502, operation_id=op_id)
    except Exception:
        logger.exception("%s_failed", op_id)
        return fail("Erro interno ao carregar estrutura.", 500, operation_id=op_id)
