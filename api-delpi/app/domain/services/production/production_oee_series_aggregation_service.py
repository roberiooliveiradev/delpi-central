from __future__ import annotations

from datetime import date


def _parse_iso_date(value: str) -> date:
    return date.fromisoformat(value.strip())


def resolve_bucket_oee_pct(
    daily_rows: list[dict],
    *,
    branch: str,
    date_start: str,
    date_end: str,
) -> float | None:
    """Média ponderada por apontamentos — equivalente ao AVG do período inteiro."""
    start = _parse_iso_date(date_start)
    end = _parse_iso_date(date_end)
    target_branch = branch.strip()

    weighted_sum = 0.0
    total_count = 0

    for row in daily_rows:
        row_branch = str(row.get("branch") or "").strip()
        if row_branch != target_branch:
            continue

        production_date = str(row.get("production_date") or "").strip()
        if not production_date:
            continue

        row_date = _parse_iso_date(production_date)
        if row_date < start or row_date > end:
            continue

        count = int(row.get("appointment_count") or 0)
        if count <= 0:
            continue

        oee_raw = row.get("oee_pct")
        if oee_raw is None or oee_raw == "":
            continue

        try:
            oee_value = float(oee_raw)
        except (TypeError, ValueError):
            continue

        weighted_sum += oee_value * count
        total_count += count

    if total_count == 0:
        return None

    return round(weighted_sum / total_count, 2)
