"""Comex NCM allowlist administration (PROC-0076.COMEX.S2).

The allowlist remains the feed's operational source of truth — this is
the only write path, reachable exclusively via the supplies-api S2S
credential after the Portal governance workflow homologates an NCM.
Upserts are idempotent and deactivation is soft (``active=false``):
rows are never deleted because observations reference the NCM.
"""

from __future__ import annotations

import re
from datetime import datetime, timezone
from typing import Any

from app.application.contracts import InvalidQueryError
from app.application.market_data_queries import _repo, _require_storage
from app.infrastructure.persistence.market_contract_readiness import (
    check_market_contract_ready,
)
from app.infrastructure.persistence.plugins_db import get_connection

_NCM_RE = re.compile(r"^[0-9]{8}$")
_MAX_TEXT = 200

# NCM revision in force for Comex Stat publications — callers may
# override with an explicit ``ncm_version``; the governance layer
# does not track nomenclature revisions.
_CURRENT_NCM_VERSION = "2022"


def _clean_text(value: Any, field: str, *, max_len: int = _MAX_TEXT) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    if len(text) > max_len:
        raise InvalidQueryError(f"{field} exceeds {max_len} characters")
    return text or None


def upsert_ncm_allowlist(
    *,
    ncm_code: str,
    body: dict[str, Any] | None,
    actor: str,
) -> dict[str, Any]:
    """operationId: upsertComexNcmAllowlistV1.

    ``actor`` is the authenticated S2S client id — recorded in the event
    metadata the caller's governance layer already audits. Creation
    requires ``description``; ``ncm_version`` defaults to the NCM
    revision currently in force when the caller does not track
    nomenclature versions. Updates may toggle ``active`` alone
    (deactivation never renames or re-describes).
    """
    code = (ncm_code or "").strip()
    if not _NCM_RE.match(code):
        raise InvalidQueryError("ncm_code must be an 8-digit NCM")
    payload = body if isinstance(body, dict) else {}

    description = _clean_text(payload.get("description"), "description")
    ncm_version = _clean_text(payload.get("ncm_version"), "ncm_version", max_len=40)
    family_code = _clean_text(payload.get("family_code"), "family_code", max_len=64)
    approved_by = _clean_text(payload.get("approved_by"), "approved_by")
    active = payload.get("active")
    if active is not None and not isinstance(active, bool):
        raise InvalidQueryError("active must be a boolean")

    _require_storage()
    with get_connection() as conn:
        check_market_contract_ready(conn)
        repo = _repo(conn)
        existing = repo.get_ncm_allowlist(code)
        if existing is None and not description:
            raise InvalidQueryError("description is required on create")
        row = repo.upsert_ncm_allowlist(
            ncm_code=code,
            ncm_version=(
                ncm_version
                or (existing or {}).get("ncm_version")
                or _CURRENT_NCM_VERSION
            ),
            description=description or (existing or {}).get("description"),
            family_code=(
                family_code
                if family_code is not None
                else (existing or {}).get("family_code")
            ),
            approved_by=approved_by or (existing or {}).get("approved_by"),
            approved_at=(
                datetime.now(timezone.utc)
                if existing is None or approved_by
                else (existing or {}).get("approved_at")
            ),
            active=(
                active
                if active is not None
                else ((existing or {}).get("active", True))
            ),
        )
        conn.commit()

    return {
        "allowlist_entry": _allowlist_dto(row),
        "created": existing is None,
        "synced_by": actor,
    }


def _allowlist_dto(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "ncm_code": row["ncm_code"],
        "ncm_version": row["ncm_version"],
        "description": row["description"],
        "family_code": row.get("family_code"),
        "approved_by": row.get("approved_by"),
        "approved_at": (
            row["approved_at"].isoformat()
            if row.get("approved_at") is not None
            else None
        ),
        "active": row["active"],
    }
