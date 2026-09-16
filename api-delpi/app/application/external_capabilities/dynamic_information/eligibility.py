"""Fail-closed eligibility classification for API DELPI operations (DAVI dynamic READ).

Canonical AuthZ policy (DAVI-READ-AUTHZ-REBASELINE-001):
  DAVI capability <= authenticated user capability
  DAVI has no independent business / branch / object AuthZ.
  Query filters (branch, code, …) ≠ DAVI authorization boundaries.
  Backend-authorized internal READ may be processed unless explicitly prohibited.
  Model-safe projection / minimization remains mandatory for eligibility.
"""

from __future__ import annotations

from typing import Any

from app.application.external_capabilities.dynamic_information.constants import (
    STATUS_ADMIN_OUT_OF_SCOPE,
    STATUS_DAVI_ELIGIBLE_READ,
    STATUS_DESTRUCTIVE_OUT_OF_SCOPE,
    STATUS_EXPLICIT_PROCESSING_PROHIBITION,
    STATUS_GENERIC_SQL_FORBIDDEN,
    STATUS_LEGACY_UNSAFE,
    STATUS_NEEDS_MODEL_SAFE_PROJECTION,
    STATUS_NEEDS_NESTED_PROJECTION_SUPPORT,
    STATUS_NOT_RELEVANT,
    STATUS_SEMANTICALLY_REDUNDANT,
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
_ADMIN_MARKERS = ("/admin", "/system", "/internal/", "gpt-actions")
_SQL_MARKERS = ("/data/sql", "/sql", "execute_sql", "raw_sql")

# Nested / hierarchy shapes that cannot be sanitized by flat items[] field lists.
_NESTED_SHAPES = frozenset(
    {
        "product_snapshot",
        "hierarchy",
        "playbook_report",
        "composite_analysis",
        "nested_object",
    }
)

# Known nested ops; still need path-based approvedResponseFields to become eligible.
_NESTED_PROJECTION_CANDIDATES = frozenset(
    {
        "get_product_detail",
        "get_product_structure",
        "get_product_structure_exclusivity",
        "get_product_production_status",
        "get_product_factory_status",
        "get_product_playbook",
        "get_product_guide",
        "get_product_summary",
    }
)

# Same Product Master slice already covered by search_products — do not expand coverage
# with a redundant detail action unless governance adds distinct fields.
_SEMANTICALLY_REDUNDANT = frozenset({"get_product_detail"})


def _explicit_prohibition_ids(allowlist: dict[str, Any] | None) -> set[str]:
    if not allowlist:
        return set()
    ids: set[str] = set()
    for item in allowlist.get("explicitProcessingProhibitions") or []:
        if isinstance(item, dict):
            oid = (item.get("operationId") or "").strip()
            if oid:
                ids.add(oid)
        elif isinstance(item, str) and item.strip():
            ids.add(item.strip())
    return ids


def _allowlist_has_safe_projection(allowlist: dict[str, Any] | None, operation_id: str) -> bool:
    if not allowlist or not operation_id:
        return False
    for item in allowlist.get("operations") or []:
        if not isinstance(item, dict):
            continue
        if (item.get("operationId") or "").strip() != operation_id:
            continue
        fields = item.get("approvedResponseFields") or []
        inputs = item.get("approvedInputFields") or []
        return bool(fields) and bool(inputs)
    return False


def _uses_nested_paths(allowlist: dict[str, Any] | None, operation_id: str) -> bool:
    if not allowlist:
        return False
    for item in allowlist.get("operations") or []:
        if not isinstance(item, dict):
            continue
        if (item.get("operationId") or "").strip() != operation_id:
            continue
        for field in item.get("approvedResponseFields") or []:
            text = str(field)
            if "." in text or "[]" in text:
                return True
        return False
    return False


def classify_operation(
    *,
    method: str,
    path: str,
    operation_id: str | None,
    allowlisted_operation_ids: set[str],
    summary: str = "",
    tags: list[str] | None = None,
    shape: str | None = None,
    allowlist: dict[str, Any] | None = None,
) -> str:
    """Return exactly one classification status (fail-closed)."""
    method_u = (method or "").upper()
    path_l = (path or "").lower()
    oid = (operation_id or "").strip()
    shape_l = (shape or "").strip().lower()
    _ = tags
    _ = summary

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

    prohibited = _explicit_prohibition_ids(allowlist)
    if oid and oid in prohibited:
        return STATUS_EXPLICIT_PROCESSING_PROHIBITION

    # Governance allowlist with model-safe projection = eligible.
    if oid and oid in allowlisted_operation_ids and _allowlist_has_safe_projection(
        allowlist, oid
    ):
        return STATUS_DAVI_ELIGIBLE_READ

    if oid in _SEMANTICALLY_REDUNDANT:
        return STATUS_SEMANTICALLY_REDUNDANT

    needs_nested = oid in _NESTED_PROJECTION_CANDIDATES or shape_l in _NESTED_SHAPES
    if needs_nested:
        # Nested ops become eligible only via path-based approvedResponseFields.
        if oid and oid in allowlisted_operation_ids and _uses_nested_paths(allowlist, oid):
            return STATUS_DAVI_ELIGIBLE_READ
        return STATUS_NEEDS_NESTED_PROJECTION_SUPPORT

    # Flat GETs without governed projection metadata.
    if not oid:
        return STATUS_NEEDS_MODEL_SAFE_PROJECTION

    return STATUS_NEEDS_MODEL_SAFE_PROJECTION


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
