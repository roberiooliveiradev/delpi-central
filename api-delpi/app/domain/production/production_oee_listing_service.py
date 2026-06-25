"""Filtro, ordenação e resumo de linhas OEE (pós-materialização TOTVS)."""

from __future__ import annotations

from app.domain.production.production_efficiency_valid_range import (
    EFFICIENCY_BAND_VERIFY,
    PRODUCTION_EFFICIENCY_LOW_PCT_THRESHOLD,
    is_low_production_efficiency_pct,
    is_valid_production_efficiency_pct,
    parse_efficiency_bands,
)


def matches_production_list_status_filter(
    row: dict,
    *,
    status: str | None,
    efficiency_bands: str | list[str] | None,
) -> bool:
    bands = parse_efficiency_bands(efficiency_bands)
    row_status = str(row.get("status") or "").strip().lower()
    oee_pct = row.get("oee_pct")

    if bands:
        if EFFICIENCY_BAND_VERIFY in bands and row_status == "outlier":
            return True
        if "low" in bands and row_status == "valid" and is_low_production_efficiency_pct(oee_pct):
            return True
        if "ok" in bands and row_status == "valid" and is_valid_production_efficiency_pct(
            oee_pct
        ) and not is_low_production_efficiency_pct(oee_pct):
            return True
        return False

    normalized = (status or "").strip().lower()
    if normalized == "valid":
        return row_status == "valid"
    if normalized == "outlier":
        return row_status == "outlier"
    return True


def filter_production_appointment_rows(
    rows: list[dict],
    *,
    status: str | None,
    efficiency_bands: str | list[str] | None,
) -> list[dict]:
    return [
        row
        for row in rows
        if matches_production_list_status_filter(
            row,
            status=status,
            efficiency_bands=efficiency_bands,
        )
    ]


def _sort_key(row: dict, column: str):
    value = row.get(column)
    if column == "oee_pct":
        try:
            return float(value) if value is not None else float("-inf")
        except (TypeError, ValueError):
            return float("-inf")
    if value is None:
        return ""
    return value


def sort_production_appointment_rows(
    rows: list[dict],
    *,
    sort_by: str | None,
    sort_dir: str | None,
    status: str | None,
    efficiency_bands: str | list[str] | None,
) -> list[dict]:
    sort_columns = {
        "appointment_id": "appointment_id",
        "status": "status",
        "branch": "branch",
        "production_order": "production_order",
        "product_code": "product_code",
        "product_description": "product_description",
        "product_type": "product_type",
        "operator_code": "operator_code",
        "work_center": "work_center",
        "operation": "operation",
        "resource_code": "resource_code",
        "production_date": "production_date",
        "start_time": "start_time",
        "end_time": "end_time",
        "oee_pct": "oee_pct",
        "produced_qty": "produced_qty",
    }
    sort_key = (sort_by or "").strip().lower()
    sort_column = sort_columns.get(sort_key)
    reverse = str(sort_dir or "asc").lower() == "desc"

    if sort_column:
        return sorted(
            rows,
            key=lambda row: (
                _sort_key(row, sort_column),
                _sort_key(row, "production_date"),
                _sort_key(row, "production_order"),
                _sort_key(row, "operation"),
            ),
            reverse=reverse,
        )

    normalized = (status or "").strip().lower()
    bands = parse_efficiency_bands(efficiency_bands)
    if normalized == "outlier" or bands == [EFFICIENCY_BAND_VERIFY]:
        return sorted(
            rows,
            key=lambda row: (
                _sort_key(row, "oee_pct"),
                _sort_key(row, "production_date"),
                _sort_key(row, "production_order"),
                _sort_key(row, "operation"),
            ),
            reverse=True,
        )

    return sorted(
        rows,
        key=lambda row: (
            _sort_key(row, "production_date"),
            _sort_key(row, "production_order"),
            _sort_key(row, "operation"),
        ),
        reverse=True,
    )


def summarize_production_appointment_rows(rows: list[dict]) -> dict:
    total_appointments = len(rows)
    valid_rows = [row for row in rows if str(row.get("status") or "").lower() == "valid"]
    outlier_rows = [row for row in rows if str(row.get("status") or "").lower() == "outlier"]
    valid_values = [
        float(row["oee_pct"])
        for row in valid_rows
        if row.get("oee_pct") is not None
    ]
    avg_oee_pct = (
        round(sum(valid_values) / len(valid_values), 2) if valid_values else None
    )

    by_branch: dict[str, list[float]] = {}
    for row in valid_rows:
        branch = str(row.get("branch") or "").strip()
        if not branch or row.get("oee_pct") is None:
            continue
        by_branch.setdefault(branch, []).append(float(row["oee_pct"]))

    avg_oee_pct_by_branch = {
        branch: round(sum(values) / len(values), 2)
        for branch, values in by_branch.items()
        if values
    }

    return {
        "total_appointments": total_appointments,
        "valid_appointments": len(valid_rows),
        "outlier_appointments": len(outlier_rows),
        "avg_oee_pct": avg_oee_pct,
        "avg_oee_pct_by_branch": avg_oee_pct_by_branch,
    }


def paginate_production_appointment_rows(
    rows: list[dict],
    *,
    page: int,
    page_size: int,
) -> tuple[list[dict], int]:
    safe_page = max(int(page or 1), 1)
    safe_page_size = max(int(page_size or 20), 1)
    total = len(rows)
    offset = (safe_page - 1) * safe_page_size
    return rows[offset : offset + safe_page_size], total
