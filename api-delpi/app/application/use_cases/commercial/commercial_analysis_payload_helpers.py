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
