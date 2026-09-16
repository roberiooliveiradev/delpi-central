"""Fail-closed eligibility classification for API DELPI operations (DAVI dynamic READ)."""

from __future__ import annotations

from typing import Any

from app.application.external_capabilities.dynamic_information.constants import (
    STATUS_ADMIN_OUT_OF_SCOPE,
    STATUS_DAVI_ELIGIBLE_READ,
    STATUS_DESTRUCTIVE_OUT_OF_SCOPE,
    STATUS_GENERIC_SQL_FORBIDDEN,
    STATUS_LEGACY_UNSAFE,
    STATUS_NEEDS_BRANCH_AUTHZ_EVIDENCE,
    STATUS_NEEDS_DATA_CLASSIFICATION,
    STATUS_NEEDS_EXTERNAL_PROCESSING_APPROVAL,
    STATUS_NEEDS_EXTERNAL_PROJECTION,
    STATUS_NEEDS_NESTED_PROJECTION_SUPPORT,
    STATUS_NOT_RELEVANT,
    STATUS_STREAM_BINARY_OUT_OF_SCOPE,
    STATUS_WRITE_OUT_OF_SCOPE,
)

_BINARY_MARKERS = (
    "/download",
    "/export",
    "/excel",
    "/pdf",
    "/drawing/pdf",
    "/stream",
    "/file",
    "/attachment",
    "/binary",
)
_SENSITIVE_MARKERS = (
    "pricing",
    "price",
    "cost",
    "salary",
    "payroll",
    "finance",
    "freight",
    "rol",
)
_ADMIN_MARKERS = ("/admin", "/system", "/internal/", "gpt-actions")
_SQL_MARKERS = ("/data/sql", "/sql", "execute_sql", "raw_sql")

# Stock lacks independent branch AuthZ on the current route (optional filter only).
_BRANCH_AUTHZ_PENDING = frozenset({"get_product_stock"})

# Flat items[] field projection cannot sanitize these shapes/composites today.
# Primary technical blocker when external-processing is also missing.
_NESTED_PROJECTION_PENDING = frozenset(
    {
        "get_product_detail",
        "get_product_structure",
        "get_product_structure_exclusivity",
        "get_product_production_status",
        "get_product_factory_status",
        "get_product_playbook",
        "get_product_guide",
    }
)

# Nested/composite shapes from x-delpi (when operationId not in the set above).
_NESTED_SHAPES = frozenset(
    {
        "product_snapshot",
        "hierarchy",
        "playbook_report",
        "composite_analysis",
        "nested_object",
    }
)


def classify_operation(
    *,
    method: str,
    path: str,
    operation_id: str | None,
    allowlisted_operation_ids: set[str],
    summary: str = "",
    tags: list[str] | None = None,
    shape: str | None = None,
) -> str:
    """Return exactly one classification status (fail-closed)."""
    method_u = (method or "").upper()
    path_l = (path or "").lower()
    oid = (operation_id or "").strip()
    blob = f"{path_l} {oid.lower()} {(summary or '').lower()}"
    shape_l = (shape or "").strip().lower()

    if path_l.startswith("/mcp") or oid.startswith("mcp_"):
        return STATUS_NOT_RELEVANT

    if any(m in path_l or m in oid.lower() for m in _SQL_MARKERS):
        return STATUS_GENERIC_SQL_FORBIDDEN

    if any(m in path_l for m in _ADMIN_MARKERS) or "gpt_actions" in path_l or path_l.startswith(
        "/gpt-actions"
    ):
        return STATUS_LEGACY_UNSAFE if "gpt" in path_l else STATUS_ADMIN_OUT_OF_SCOPE

    if any(m in path_l for m in _BINARY_MARKERS):
        return STATUS_STREAM_BINARY_OUT_OF_SCOPE

    if method_u in {"DELETE"}:
        return STATUS_DESTRUCTIVE_OUT_OF_SCOPE

    if method_u in {"POST", "PUT", "PATCH"}:
        return STATUS_WRITE_OUT_OF_SCOPE

    if method_u != "GET":
        return STATUS_NOT_RELEVANT

    # Explicit governance allowlist wins over heuristic sensitivity markers.
    if oid and oid in allowlisted_operation_ids:
        return STATUS_DAVI_ELIGIBLE_READ

    if oid in _BRANCH_AUTHZ_PENDING:
        return STATUS_NEEDS_BRANCH_AUTHZ_EVIDENCE

    if any(m in blob for m in _SENSITIVE_MARKERS):
        return STATUS_NEEDS_DATA_CLASSIFICATION

    if oid in _NESTED_PROJECTION_PENDING or shape_l in _NESTED_SHAPES:
        return STATUS_NEEDS_NESTED_PROJECTION_SUPPORT

    # GET without explicit external-processing approval stays quarantined.
    # Presence of x-delpi entity/shape alone does not approve external projection.
    tags = tags or []
    if not oid:
        return STATUS_NEEDS_EXTERNAL_PROJECTION

    _ = tags
    return STATUS_NEEDS_EXTERNAL_PROCESSING_APPROVAL


def is_dynamically_executable(status: str) -> bool:
    return status == STATUS_DAVI_ELIGIBLE_READ


def load_allowlist_operation_ids(payload: dict[str, Any]) -> set[str]:
    ops = payload.get("operations") or []
    ids: set[str] = set()
    for item in ops:
        if isinstance(item, dict):
            oid = (item.get("operationId") or "").strip()
            if oid:
                ids.add(oid)
        elif isinstance(item, str) and item.strip():
            ids.add(item.strip())
    return ids
