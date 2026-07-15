"""Extrai pontos {label, value} de envelopes api-delpi (séries OEE/OTD/PPM)."""

from __future__ import annotations

from typing import Any


def extract_series_points(
    data: Any,
    series_field: str | None = None,
    *,
    branch: str | None = None,
) -> list[dict[str, Any]]:
    """Converte lista `points`/`series`/`serie`/`ranking` do payload em pontos de gráfico TV."""
    if not isinstance(data, dict):
        return []
    candidates: list[str] = []
    if series_field and str(series_field).strip():
        candidates.append(str(series_field).strip())
    for key in ("points", "series", "serie", "ranking", "levelData", "statusData", "leadByLevel"):
        if key not in candidates:
            candidates.append(key)

    raw: list[Any] | None = None
    for key in candidates:
        value = data.get(key)
        if isinstance(value, list) and value:
            raw = value
            break
    if not isinstance(raw, list):
        return []
    branch_code = str(branch).strip() if branch else ""
    points: list[dict[str, Any]] = []
    for row in raw:
        if not isinstance(row, dict):
            continue
        label = (
            row.get("label")
            or row.get("bucket")
            or row.get("periodo")
            or row.get("date")
            or row.get("name")
            or row.get("centro_custo")
            or row.get("fornecedor")
            or row.get("level")
            or row.get("status")
        )
        value = row.get("value")
        if value is None:
            value = row.get("total") or row.get("qty") or row.get("quantidade") or row.get("count")
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
