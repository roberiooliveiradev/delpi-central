"""Mapa de entrega público — leitura anônima do snapshot congelado e progresso limitado."""

from __future__ import annotations

from fastapi import APIRouter, Query

from production_control_app.composition.pc_composer import (
    build_delivery_map_service,
    build_public_delivery_map_access_service,
)
from production_control_app.core.responses import fail, ok
from production_control_app.domain.errors import DelpiGatewayError, InvalidBranch, SnapshotNotFound

router = APIRouter(prefix="/public/delivery-map", tags=["Public delivery map"])

_MAX_PROGRESS_ORDERS = 40


def _handle_public_errors(exc: Exception):
    if isinstance(exc, InvalidBranch):
        return fail(str(exc), 422)
    if isinstance(exc, SnapshotNotFound):
        return fail(str(exc), 404)
    if isinstance(exc, ValueError):
        return fail(str(exc), 422)
    if isinstance(exc, DelpiGatewayError):
        return fail(str(exc), 502)
    raise exc


@router.get("/{token}")
def get_public_delivery_map(
    token: str,
    branch: str = Query(..., description="Filial TOTVS (01 ou 02)"),
    search: str = Query("", description="Filtra OP, produto ou observação"),
):
    """Snapshot congelado do mapa de entrega, somente leitura (sem seed do TOTVS)."""
    access = build_public_delivery_map_access_service()
    if not access.is_valid_token(token):
        return fail(access.message("invalidToken", "Link do mapa de entrega inválido ou desativado."), 404)
    try:
        data = build_delivery_map_service().build_public(branch=branch, search=search)
    except Exception as exc:  # noqa: BLE001
        return _handle_public_errors(exc)
    return ok(data)


@router.get("/{token}/progress")
def get_public_delivery_map_progress(
    token: str,
    branch: str = Query(..., description="Filial TOTVS (01 ou 02)"),
    orders: str = Query(
        "",
        description="Lista de OPs mãe separadas por vírgula (progresso por conjunto)",
    ),
):
    """Progresso vivo por conjunto — limitado a lotes pequenos para uso anônimo."""
    access = build_public_delivery_map_access_service()
    if not access.is_valid_token(token):
        return fail(access.message("invalidToken", "Link do mapa de entrega inválido ou desativado."), 404)

    production_orders = [
        part.strip()
        for part in str(orders or "").split(",")
        if part.strip()
    ]
    if len(production_orders) > _MAX_PROGRESS_ORDERS:
        return fail(
            access.message(
                "progressBatchTooLarge",
                f"Máximo de {_MAX_PROGRESS_ORDERS} OPs por consulta de progresso.",
            ),
            422,
        )

    try:
        data = build_delivery_map_service().build_public_progress(
            branch=branch,
            production_orders=production_orders,
        )
    except Exception as exc:  # noqa: BLE001
        return _handle_public_errors(exc)
    return ok(data)
