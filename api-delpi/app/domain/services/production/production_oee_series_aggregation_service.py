from __future__ import annotations

from datetime import date


def _parse_iso_date(value: str) -> date:
    return date.fromisoformat(value.strip())


def _coerce_float(value: object) -> float:
    if value is None or value == "":
        return 0.0
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def resolve_period_oee_by_branch(daily_rows: list[dict]) -> list[dict]:
    """Deriva o OEE médio por filial no período a partir das linhas diárias.

    Equivale exatamente a ``ROUND(AVG(EFICIENCIA_PERCENTUAL), 2)`` por filial:
    soma os componentes brutos (``efficiency_sum`` / ``efficiency_sample_count``)
    de cada dia e arredonda uma única vez. Evita um segundo scan da view fabril,
    reaproveitando a agregação diária já cacheada.
    """
    totals: dict[str, dict[str, float]] = {}

    for row in daily_rows:
        branch = str(row.get("branch") or "").strip()
        if not branch:
            continue
        bucket = totals.setdefault(branch, {"sum": 0.0, "count": 0.0})
        bucket["sum"] += _coerce_float(row.get("efficiency_sum"))
        bucket["count"] += _coerce_float(row.get("efficiency_sample_count"))

    rows: list[dict] = []
    for branch in sorted(totals):
        sample_count = totals[branch]["count"]
        oee_pct = (
            round(totals[branch]["sum"] / sample_count, 2)
            if sample_count > 0
            else None
        )
        rows.append({"branch": branch, "oee_pct": oee_pct})

    return rows


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
