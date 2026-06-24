from __future__ import annotations

from app.application.dto.supplies.get_stock_value_request import GetStockValueRequest
from app.application.services.supplies.stock_value_method_service import (
    STOCK_METHOD_RESOLVED_OFFICIAL,
)


def build_stock_estimation_payload(
    *,
    request: GetStockValueRequest,
    bundle: dict,
    period_start: str,
    period_end: str,
    period_end_exclusive: str,
) -> dict:
    estimation_meta = bundle.get("estimation_meta") or {}
    stock_method_resolved = bundle.get("stock_method_resolved") or "estimated"
    stock_method_requested = (request.stock_method or "auto").strip().lower()

    if stock_method_resolved == STOCK_METHOD_RESOLVED_OFFICIAL:
        method = "sb9_closure_on_end_date"
        note = (
            "Valor do fechamento oficial SB9010 na data final do período. "
            "Corresponde ao inventário contábil quando registrado na SB9."
        )
        data_quality_warning = None
    else:
        method = "sb9_last_closure_plus_sd3_movements"
        note = (
            "Valor estimado a partir do último fechamento real em SB9010 "
            "somado às movimentações líquidas em SD3010 (entrada se D3_TM < '500', "
            "saída caso contrário). Não substitui fechamento oficial da SB9."
        )
        data_quality_warning = None
        stale_closure = False
        if period_end and estimation_meta.get("closing_base_date"):
            stale_closure = str(estimation_meta.get("closing_base_date")) < period_end
        if stale_closure and not estimation_meta.get("official_closure_on_period_end"):
            data_quality_warning = (
                "Último fechamento SB9 anterior ao fim do período; a estimativa SD3 pode "
                "divergir do Registro de Inventário até existir fechamento SB9 na data."
            )

    payload = {
        "enabled": True,
        "method": method,
        "stock_method": stock_method_requested,
        "stock_method_resolved": stock_method_resolved,
        "start_date": period_start,
        "end_date": period_end,
        "end_date_exclusive": period_end_exclusive,
        "closing_base_date": estimation_meta.get("closing_base_date"),
        "closing_base_value": estimation_meta.get("closing_base_value"),
        "bridge_value": estimation_meta.get("bridge_value"),
        "period_net_value": estimation_meta.get("period_net_value"),
        "official_closure_available": estimation_meta.get("official_closure_available", False),
        "official_closure_date": estimation_meta.get("official_closure_date"),
        "official_closure_value": estimation_meta.get("official_closure_value"),
        "official_closure_on_period_end": estimation_meta.get(
            "official_closure_on_period_end", False
        ),
        "note": note,
    }
    if data_quality_warning:
        payload["data_quality_warning"] = data_quality_warning
    return payload
