"""Fail-closed eligibility classification for API DELPI operations (DAVI dynamic READ).

Canonical AuthZ policy (DAVI-READ-AUTHZ-REBASELINE-001):
  DAVI capability <= authenticated user capability
  DAVI has no independent business / branch / object AuthZ.
  Query filters (branch, code, …) ≠ DAVI authorization boundaries.

Eligibility is driven by trusted OpenAPI shape + governance metadata.
operationId is a technical lookup key only — never semantic authority.
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

# Structural shapes that require nested path projection metadata.
_NESTED_SHAPES = frozenset(
    {
        "product_snapshot",
        "hierarchy",
        "playbook_report",
        "composite_analysis",
        "nested_object",
    }
)

_DISPOSITION_STATUSES = frozenset(
    {
        STATUS_SEMANTICALLY_REDUNDANT,
        STATUS_NEEDS_NESTED_PROJECTION_SUPPORT,
        STATUS_NEEDS_MODEL_SAFE_PROJECTION,
        STATUS_EXPLICIT_PROCESSING_PROHIBITION,
    }
)


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


def _allowlist_operation_entry(
    allowlist: dict[str, Any] | None, operation_id: str
) -> dict[str, Any] | None:
    if not allowlist or not operation_id:
        return None
    for item in allowlist.get("operations") or []:
        if isinstance(item, dict) and (item.get("operationId") or "").strip() == operation_id:
            return item
    return None


def _coverage_disposition(
    allowlist: dict[str, Any] | None, operation_id: str
) -> str | None:
    """Trusted governance disposition for an operationId (lookup key only)."""
    if not allowlist or not operation_id:
        return None
    entry = _allowlist_operation_entry(allowlist, operation_id)
    if entry:
        disp = (entry.get("coverageDisposition") or "").strip()
        if disp in _DISPOSITION_STATUSES:
            return disp
    for item in allowlist.get("explicitlyNotApproved") or []:
        if not isinstance(item, dict):
            continue
        if (item.get("operationId") or "").strip() != operation_id:
            continue
        disp = (
            item.get("coverageDisposition") or item.get("primaryBlocker") or ""
        ).strip()
        if disp in _DISPOSITION_STATUSES:
            return disp
    return None


def _field_list(entry: dict[str, Any] | None, key: str) -> list[str]:
    if not entry:
        return []
    return [str(f) for f in (entry.get(key) or []) if f]


def _uses_nested_path_syntax(fields: list[str]) -> bool:
    return any(("." in f) or ("[]" in f) for f in fields)


def _shape_requires_nested(shape: str | None) -> bool:
    return (shape or "").strip().lower() in _NESTED_SHAPES


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
    """Return exactly one classification status (fail-closed).

    Order:
      hard technical exclusions
      → explicit processing prohibition
      → governance disposition
      → structural shape + projection validation
      → DAVI_ELIGIBLE_READ
    """
    method_u = (method or "").upper()
    path_l = (path or "").lower()
    oid = (operation_id or "").strip()
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

    if oid and oid in _explicit_prohibition_ids(allowlist):
        return STATUS_EXPLICIT_PROCESSING_PROHIBITION

    disposition = _coverage_disposition(allowlist, oid) if oid else None
    if disposition == STATUS_EXPLICIT_PROCESSING_PROHIBITION:
        return STATUS_EXPLICIT_PROCESSING_PROHIBITION
    if disposition == STATUS_SEMANTICALLY_REDUNDANT:
        return STATUS_SEMANTICALLY_REDUNDANT

    needs_nested = _shape_requires_nested(shape)
    entry = _allowlist_operation_entry(allowlist, oid) if oid else None
    inputs = _field_list(entry, "approvedInputFields")
    outputs = _field_list(entry, "approvedResponseFields")
    on_allowlist = bool(oid and oid in allowlisted_operation_ids and entry is not None)

    if on_allowlist:
        if not inputs or not outputs:
            if needs_nested:
                return STATUS_NEEDS_NESTED_PROJECTION_SUPPORT
            return STATUS_NEEDS_MODEL_SAFE_PROJECTION
        if needs_nested:
            if not _uses_nested_path_syntax(outputs):
                return STATUS_NEEDS_NESTED_PROJECTION_SUPPORT
            return STATUS_DAVI_ELIGIBLE_READ
        return STATUS_DAVI_ELIGIBLE_READ

    # Not allowlisted / no governed projection entry.
    if disposition == STATUS_NEEDS_NESTED_PROJECTION_SUPPORT:
        return STATUS_NEEDS_NESTED_PROJECTION_SUPPORT
    if disposition == STATUS_NEEDS_MODEL_SAFE_PROJECTION:
        return STATUS_NEEDS_MODEL_SAFE_PROJECTION
    if needs_nested:
        return STATUS_NEEDS_NESTED_PROJECTION_SUPPORT
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
