"""Extrai pontos {label, value} de envelopes api-delpi (séries OEE/OTD/PPM)."""

from __future__ import annotations

from typing import Any


def extract_series_points(
    data: Any,
    series_field: str | None = None,
    *,
    branch: str | None = None,
) -> list[dict[str, Any]]:
    """Converte lista `points`/`series` do payload em pontos de gráfico TV."""
    if not isinstance(data, dict):
        return []
    key = series_field or "points"
    raw = data.get(key)
    if not isinstance(raw, list):
        raw = data.get("series")
    if not isinstance(raw, list):
        return []
    branch_code = str(branch).strip() if branch else ""
    points: list[dict[str, Any]] = []
    for row in raw:
        if not isinstance(row, dict):
            continue
        label = row.get("label") or row.get("bucket") or row.get("periodo") or row.get("date")
        value = row.get("value")
        if value is None and branch_code:
            branch_key = branch_code.zfill(2)
            value = (
                row.get(f"oee_filial_{branch_key}")
                or row.get(f"otd_filial_{branch_key}")
                or row.get(f"oee_pct_filial_{branch_key}")
                or row.get(f"ppm_filial_{branch_key}")
            )
        if value is None:
            for field_key, field_value in row.items():
                if not isinstance(field_key, str) or field_value is None:
                    continue
                if field_key.startswith(("oee_", "otd_", "ppm_")) and field_key not in {
                    "oee_pct",
                    "otd_pct",
                }:
                    value = field_value
                    break
        points.append({"label": label, "value": value})
    return points


def envelope_data(envelope: dict[str, Any] | Any) -> dict[str, Any]:
    if not isinstance(envelope, dict):
        return {}
    data = envelope.get("data")
    return data if isinstance(data, dict) else {}
