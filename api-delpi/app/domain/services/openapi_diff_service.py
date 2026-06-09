"""Diff entre OpenAPI atual e baseline versionado."""

from __future__ import annotations

from typing import Any

from app.domain.services.openapi_baseline_service import (
    extract_operations_from_openapi,
    load_openapi_baseline,
)


def _index_operations(operations: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    indexed: dict[str, dict[str, Any]] = {}
    for row in operations:
        key = f"{row['method']} {row['path']}"
        indexed[key] = row
    return indexed


def diff_openapi_against_baseline(current_spec: dict[str, Any]) -> dict[str, Any]:
    baseline = load_openapi_baseline()
    current_ops = extract_operations_from_openapi(current_spec)
    baseline_ops = baseline.get("operations") or []

    current_index = _index_operations(current_ops)
    baseline_index = _index_operations(baseline_ops)

    added: list[dict[str, Any]] = []
    removed: list[dict[str, Any]] = []
    changed: list[dict[str, Any]] = []

    for key, row in current_index.items():
        if key not in baseline_index:
            added.append(row)
            continue
        previous = baseline_index[key]
        changes: dict[str, Any] = {}
        for field in ("operationId", "summary", "deprecated"):
            if row.get(field) != previous.get(field):
                changes[field] = {"before": previous.get(field), "after": row.get(field)}
        if sorted(row.get("tags") or []) != sorted(previous.get("tags") or []):
            changes["tags"] = {"before": previous.get("tags"), "after": row.get("tags")}
        if changes:
            changed.append({"method": row["method"], "path": row["path"], "changes": changes})

    for key, row in baseline_index.items():
        if key not in current_index:
            removed.append(row)

    return {
        "baseline_version": baseline.get("version"),
        "baseline_api_version": baseline.get("api_version"),
        "current_operation_count": len(current_ops),
        "baseline_operation_count": len(baseline_ops),
        "added_count": len(added),
        "removed_count": len(removed),
        "changed_count": len(changed),
        "added": added,
        "removed": removed,
        "changed": changed,
    }
