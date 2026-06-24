from __future__ import annotations

from app.application.services.supplies.stock_value_hybrid_content_service import (
    note,
    process_warehouse_locations,
)


def build_register_snapshot_estimation_meta(
    *,
    period_end: str,
    breakdown_rows: list[dict],
    em_estoque_value: float,
    em_processo_proxy_value: float,
    by_branch_wip: list[dict] | None = None,
) -> dict:
    locations = process_warehouse_locations()
    stale_closure = False
    closing_base_date = None
    if breakdown_rows:
        closing_base_date = breakdown_rows[0].get("closing_base_date")
        if period_end and closing_base_date:
            stale_closure = str(closing_base_date) < period_end

    return {
        "closing_base_date": closing_base_date,
        "closing_base_value": sum(float(row.get("closing_base_value") or 0) for row in breakdown_rows)
        if breakdown_rows
        else None,
        "bridge_value": None,
        "period_net_value": None,
        "official_closure_available": False,
        "official_closure_date": None,
        "official_closure_value": None,
        "official_closure_on_period_end": False,
        "register_snapshot": {
            "em_estoque_value": em_estoque_value,
            "em_processo_proxy_value": em_processo_proxy_value,
            "em_processo_proxy_method": "sb2_process_locations",
            "process_locations": list(locations),
            "total_geral_proxy_value": em_estoque_value + em_processo_proxy_value,
            "snapshot_at_query_time": True,
            "period_end_requested": period_end,
            "by_branch": by_branch_wip or [],
        },
        "data_quality_warning": note(
            "registerSnapshotHistoricalWarning",
            period_end=period_end,
        )
        if stale_closure
        else None,
        "by_branch_breakdown": breakdown_rows,
    }
