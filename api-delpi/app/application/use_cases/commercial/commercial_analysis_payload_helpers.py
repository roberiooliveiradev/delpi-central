from __future__ import annotations

from typing import Any


def branch_breakdown_rows(by_branch: dict[str, Any] | None) -> list[dict[str, Any]]:
    """Converte mapa branch_XX → métricas em linhas tabulares para TV/tabelas."""
    if not isinstance(by_branch, dict):
        return []
    rows: list[dict[str, Any]] = []
    for key, metrics in by_branch.items():
        if not isinstance(metrics, dict):
            continue
        branch_key = str(key).strip()
        branch_code = branch_key.replace("branch_", "", 1) if branch_key.startswith("branch_") else branch_key
        rows.append({"branch": branch_code, **metrics})
    return rows


def branch_series_scalar_fields(
    metrics_01: dict[str, Any] | None,
    metrics_02: dict[str, Any] | None,
    *metric_keys: str,
) -> dict[str, Any]:
    """Espalha métricas por filial em chaves escalares (ex.: otd_pct_filial_01)."""
    fields: dict[str, Any] = {}
    for key in metric_keys:
        metric_key = str(key).strip()
        if not metric_key:
            continue
        fields[f"{metric_key}_filial_01"] = (
            metrics_01.get(metric_key) if isinstance(metrics_01, dict) else None
        )
        fields[f"{metric_key}_filial_02"] = (
            metrics_02.get(metric_key) if isinstance(metrics_02, dict) else None
        )
    return fields
