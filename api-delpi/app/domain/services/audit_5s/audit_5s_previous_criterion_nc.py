"""NCs da auditoria imediatamente anterior — chave estável = criterion_code."""

from __future__ import annotations

from typing import Any


def index_previous_ncs_by_criterion_code(
    rows: list[dict[str, Any]],
) -> dict[str, dict[str, Any]]:
    """Uma NC por código de critério (primeira ocorrência; SQL já ordena)."""
    indexed: dict[str, dict[str, Any]] = {}
    for row in rows:
        code = str(row.get("criterion_code") or "").strip().upper()
        if not code or code in indexed:
            continue
        indexed[code] = row
    return indexed


def build_previous_criterion_ncs_payload(
    *,
    previous_audit: dict[str, Any] | None,
    nc_rows: list[dict[str, Any]],
) -> dict[str, Any]:
    by_code = index_previous_ncs_by_criterion_code(nc_rows)
    return {
        "previous_audit": (
            {
                "id": str(previous_audit["id"]),
                "audit_code": previous_audit.get("audit_code"),
                "audit_date": (
                    previous_audit["audit_date"].isoformat()
                    if hasattr(previous_audit.get("audit_date"), "isoformat")
                    else previous_audit.get("audit_date")
                ),
                "shift": previous_audit.get("shift"),
            }
            if previous_audit
            else None
        ),
        "by_criterion_code": by_code,
        "items": list(by_code.values()),
    }
