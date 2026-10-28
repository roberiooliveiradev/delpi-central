"""Comex configurable analysis — BFF composition (PROC-0076.COMEX.S2/S3).

Owns the Portal-side business rules:
  - product catalog proxy (api-delpi is the TOTVS owner);
  - NCM homologation lifecycle + audit (supplies schema);
  - operational allowlist sync into external-data-api on approve/deactivate;
  - personal saved views with server-side ownership.
"""

from __future__ import annotations

import logging
import re
import uuid
from datetime import date
from typing import Any

from app.application.security.supplies_permissions import (
    has_canonical_manage,
)
from app.domain.comex_analysis.lifecycle import (
    GovernanceTransitionError,
    STATUSES,
    required_capability,
)
from app.domain.entities import EffectiveUser
from app.infrastructure.gateways.delpi_api_gateway import (
    DelpiApiGatewayError,
)
from app.infrastructure.gateways.delpi_envelope import unwrap_delpi_envelope
from app.infrastructure.gateways.delpi_s2s_gateway import DelpiS2SApiGateway
from app.infrastructure.gateways.market_data_gateway import (
    MarketDataGateway,
    MarketDataGatewayError,
)
from app.infrastructure.persistence.comex_analysis_repository import (
    ComexAnalysisRepository,
    GovernanceRevisionConflictError,
)

logger = logging.getLogger("supplies-api.comex_analysis")

_NCM_RE = re.compile(r"^[0-9]{8}$")

_PRODUCT_SEARCH_KEYS = (
    "code",
    "description",
    "product_type",
    "group_code",
    "subgroup",
    "page",
    "page_size",
    "sort",
    "direction",
)

SELECTABLE_METRICS = (
    "fob_usd_total",
    "net_weight_kg_total",
    "unit_value_usd_per_t",
)
GRANULARITIES = ("month", "year")
VIEW_MODES = ("chart", "table")
MAX_SELECTION = 200
MAX_NAME = 120


class ComexValidationError(RuntimeError):
    """422 — malformed client input."""

    def __init__(self, message: str, *, code: str = "invalid_request"):
        self.code = code
        super().__init__(message)


class ComexNotFoundError(RuntimeError):
    """404 — governance record or view not found for the caller."""


class ComexForbiddenError(RuntimeError):
    """403 — capability below the transition's requirement."""


class ComexConflictError(RuntimeError):
    """409 — illegal transition or revision conflict."""

    def __init__(self, message: str, *, code: str = "conflict"):
        self.code = code
        super().__init__(message)


def _require_ncm(raw: Any) -> str:
    code = str(raw or "").strip()
    if not _NCM_RE.match(code):
        raise ComexValidationError(
            "ncm_code must be an 8-digit NCM", code="invalid_ncm"
        )
    return code


def _clean_str(value: Any, field: str, *, max_len: int, required=False) -> str | None:
    if value is None:
        if required:
            raise ComexValidationError(f"{field} is required")
        return None
    text = str(value).strip()
    if required and not text:
        raise ComexValidationError(f"{field} is required")
    if len(text) > max_len:
        raise ComexValidationError(f"{field} exceeds {max_len} characters")
    return text or None


def _clean_str_list(value: Any, field: str, *, max_items=MAX_SELECTION) -> list[str]:
    if value is None:
        return []
    if not isinstance(value, list):
        raise ComexValidationError(f"{field} must be a list")
    if len(value) > max_items:
        raise ComexValidationError(f"{field} exceeds {max_items} items")
    items = []
    for entry in value:
        text = str(entry).strip()
        if text:
            items.append(text[:64])
    return items


def _user_uuid(user: EffectiveUser) -> str:
    try:
        return str(uuid.UUID(str(user.id)))
    except (ValueError, AttributeError, TypeError) as exc:
        raise ComexValidationError(
            "authenticated user id is not a UUID", code="invalid_actor"
        ) from exc


class ComexAnalysisService:
    def __init__(
        self,
        *,
        repository: ComexAnalysisRepository | None = None,
        delpi_gateway: DelpiS2SApiGateway | None = None,
        market_gateway: MarketDataGateway | None = None,
    ) -> None:
        self._repo = repository or ComexAnalysisRepository()
        self._delpi = delpi_gateway or DelpiS2SApiGateway()
        self._market = market_gateway or MarketDataGateway()

    # -- product catalog (api-delpi proxy) --------------------------------

    def search_products(
        self, *, user: EffectiveUser, args: dict[str, Any]
    ) -> dict[str, Any]:
        params = {
            key: args[key]
            for key in _PRODUCT_SEARCH_KEYS
            if args.get(key) not in (None, "")
        }
        payload = self._delpi.get(
            "/supplies/products/search",
            access_token=user.access_token or "",
            params=params,
        )
        data = unwrap_delpi_envelope(payload)
        if not isinstance(data, dict):
            raise DelpiApiGatewayError("product catalog invalid envelope")
        return data

    # -- governance ---------------------------------------------------------

    def list_governance(
        self, *, status: str | None = None, limit: int = 200
    ) -> list[dict[str, Any]]:
        if status is not None and status not in STATUSES:
            raise ComexValidationError(
                f"status must be one of {sorted(STATUSES)}",
                code="invalid_status",
            )
        return self._repo.list_governance(status=status, limit=limit)

    def get_governance(self, governance_id: str) -> dict[str, Any]:
        record = self._repo.get_governance(_require_uuid(governance_id))
        if record is None:
            raise ComexNotFoundError("governance record not found")
        record["events"] = self._repo.list_governance_events(
            record["governance_id"]
        )
        return record

    def request_ncm(
        self,
        *,
        user: EffectiveUser,
        ncm_code: Any,
        description: Any = None,
        ncm_version: Any = None,
        family_code: Any = None,
        product_codes: Any = None,
        notes: Any = None,
        initial_status: Any = None,
    ) -> dict[str, Any]:
        """Create the governance row or resubmit an existing one.

        ``initial_status`` may be ``candidate`` (discovered, not yet
        submitted) or ``pending_fiscal_review`` (formal request).
        """
        code = _require_ncm(ncm_code)
        status = (initial_status or "pending_fiscal_review").strip()
        if status not in ("candidate", "pending_fiscal_review"):
            raise ComexValidationError(
                "initial_status must be 'candidate' or 'pending_fiscal_review'",
                code="invalid_status",
            )
        actor = _user_uuid(user)
        record = self._repo.create_governance(
            record={
                "ncm_code": code,
                "ncm_version": _clean_str(ncm_version, "ncm_version", max_len=40),
                "description": _clean_str(description, "description", max_len=400),
                "family_code": _clean_str(family_code, "family_code", max_len=64),
                "product_codes": _clean_str_list(
                    product_codes, "product_codes"
                ),
                "status": status,
                "notes": _clean_str(notes, "notes", max_len=400),
                "requested_by": actor,
            }
        )
        if record.pop("_existing", False):
            # S7 shared-catalog add (``candidate``) is idempotent — the
            # existing row is returned untouched, whatever its status.
            if status == "candidate":
                record["already_registered"] = True
                return record
            # Resubmit path — only from candidate/rejected.
            if record["status"] not in ("candidate", "rejected"):
                raise ComexConflictError(
                    f"NCM {code} already has status '{record['status']}'",
                    code="ncm_already_registered",
                )
            record = self.transition(
                user=user,
                governance_id=record["governance_id"],
                to_status="pending_fiscal_review",
                notes=notes,
                expected_revision=record["revision"],
            )
        return record

    def transition(
        self,
        *,
        user: EffectiveUser,
        governance_id: Any,
        to_status: Any,
        notes: Any = None,
        expected_revision: Any = None,
    ) -> dict[str, Any]:
        target = str(to_status or "").strip()
        if target not in STATUSES:
            raise ComexValidationError(
                f"to_status must be one of {sorted(STATUSES)}",
                code="invalid_status",
            )
        record = self._repo.get_governance(_require_uuid(governance_id))
        if record is None:
            raise ComexNotFoundError("governance record not found")

        capability = required_capability(record["status"], target)
        if capability == "manage" and not has_canonical_manage(user):
            raise ComexForbiddenError(
                f"transition {record['status']} → {target} requires "
                "supplies.manage"
            )

        try:
            revision = int(
                expected_revision
                if expected_revision is not None
                else record["revision"]
            )
        except (TypeError, ValueError) as exc:
            raise ComexValidationError(
                "expected_revision must be an integer"
            ) from exc

        actor = _user_uuid(user)
        try:
            updated = self._repo.transition_governance(
                governance_id=record["governance_id"],
                expected_revision=revision,
                to_status=target,
                actor=actor,
                notes=_clean_str(notes, "notes", max_len=400),
                event_type=_event_for(target),
                extra_columns={"from_status": record["status"]},
            )
        except GovernanceRevisionConflictError as exc:
            raise ComexConflictError(
                "record changed concurrently — reload and retry",
                code="revision_conflict",
            ) from exc
        except GovernanceTransitionError as exc:
            raise ComexConflictError(str(exc), code=exc.code) from exc

        updated["allowlist_sync"] = self._sync_allowlist(
            record=updated, target=target, user=user
        )
        return updated

    # -- allowlist sync -----------------------------------------------------

    def _sync_allowlist(
        self, *, record: dict[str, Any], target: str, user: EffectiveUser
    ) -> str:
        """Propagate approved/inactive to the feed's operational allowlist.

        The governance commit is authoritative; sync is best-effort with
        an audit trail — a failed sync is explicit, never silent.
        """
        if target not in ("approved", "inactive"):
            return "not_applicable"
        try:
            self._market.put_ncm_allowlist(
                record["ncm_code"],
                {
                    "description": record.get("description"),
                    "ncm_version": record.get("ncm_version"),
                    "family_code": record.get("family_code"),
                    "approved_by": user.email or str(user.id),
                    "active": target == "approved",
                },
            )
        except MarketDataGatewayError as exc:
            logger.error(
                "comex_allowlist_sync_failed ncm=%s status=%s",
                record["ncm_code"],
                exc.status_code,
            )
            self._repo.record_sync_event(
                governance_id=record["governance_id"],
                actor=_user_uuid(user),
                event_type="allowlist_sync_failed",
                metadata={
                    "target": target,
                    "upstream_status": exc.status_code,
                    "upstream_code": exc.code,
                },
            )
            return "failed"
        self._repo.record_sync_event(
            governance_id=record["governance_id"],
            actor=_user_uuid(user),
            event_type="allowlist_synced",
            metadata={"target": target},
        )
        return "synced"

    # -- saved views ----------------------------------------------------------

    def list_views(self, *, user: EffectiveUser) -> list[dict[str, Any]]:
        return self._repo.list_views(owner_user_id=_user_uuid(user))

    def get_view(self, view_id: Any, *, user: EffectiveUser) -> dict[str, Any]:
        view = self._repo.get_view(
            _require_uuid(view_id), owner_user_id=_user_uuid(user)
        )
        if view is None:
            # Same 404 for "not theirs" — no existence leak.
            raise ComexNotFoundError("saved view not found")
        return view

    def create_view(
        self, *, user: EffectiveUser, body: dict[str, Any]
    ) -> dict[str, Any]:
        record = self._view_payload(body)
        record["owner_user_id"] = _user_uuid(user)
        return self._repo.create_view(record=record)

    def update_view(
        self, view_id: Any, *, user: EffectiveUser, body: dict[str, Any]
    ) -> dict[str, Any]:
        record = self._view_payload(body)
        updated = self._repo.update_view(
            _require_uuid(view_id),
            owner_user_id=_user_uuid(user),
            record=record,
        )
        if updated is None:
            raise ComexNotFoundError("saved view not found")
        return updated

    def delete_view(self, view_id: Any, *, user: EffectiveUser) -> None:
        deleted = self._repo.delete_view(
            _require_uuid(view_id), owner_user_id=_user_uuid(user)
        )
        if not deleted:
            raise ComexNotFoundError("saved view not found")

    @staticmethod
    def _view_payload(body: dict[str, Any]) -> dict[str, Any]:
        body = body if isinstance(body, dict) else {}
        granularity = (body.get("granularity") or "month").strip()
        if granularity not in GRANULARITIES:
            raise ComexValidationError(
                f"granularity must be one of {GRANULARITIES}",
                code="invalid_granularity",
            )
        view_mode = (body.get("view_mode") or "chart").strip()
        if view_mode not in VIEW_MODES:
            raise ComexValidationError(
                f"view_mode must be one of {VIEW_MODES}",
                code="invalid_view_mode",
            )
        metrics = _clean_str_list(body.get("selected_metrics"), "selected_metrics")
        unknown = [m for m in metrics if m not in SELECTABLE_METRICS]
        if unknown:
            raise ComexValidationError(
                f"unknown metrics: {', '.join(unknown)}",
                code="invalid_metric",
            )
        ncms = _clean_str_list(
            body.get("approved_ncm_references"), "approved_ncm_references"
        )
        for ncm in ncms:
            _require_ncm(ncm)

        date_range = body.get("date_range")
        if date_range is not None:
            if not isinstance(date_range, dict):
                raise ComexValidationError("date_range must be an object")
            date_range = {
                "date_from": _require_iso_date(date_range.get("date_from"), "date_from"),
                "date_to": _require_iso_date(date_range.get("date_to"), "date_to"),
            }

        return {
            "name": _clean_str(body.get("name"), "name", max_len=MAX_NAME, required=True),
            "unit_scope": _clean_str(body.get("unit_scope"), "unit_scope", max_len=2),
            "selected_product_codes": _clean_str_list(
                body.get("selected_product_codes"), "selected_product_codes"
            ),
            "selected_materials": _clean_str_list(
                body.get("selected_materials"), "selected_materials"
            ),
            "approved_ncm_references": ncms,
            "selected_metrics": metrics,
            "date_range": date_range,
            "granularity": granularity,
            "view_mode": view_mode,
        }


def _require_uuid(raw: Any) -> str:
    try:
        return str(uuid.UUID(str(raw)))
    except (ValueError, TypeError) as exc:
        raise ComexValidationError("id must be a UUID", code="invalid_id") from exc


def _require_iso_date(raw: Any, field: str) -> str:
    text = str(raw or "").strip()
    try:
        return date.fromisoformat(text).isoformat()
    except ValueError as exc:
        raise ComexValidationError(
            f"{field} must be an ISO date", code="invalid_date"
        ) from exc


def _event_for(to_status: str) -> str:
    return {
        "pending_fiscal_review": "submitted_for_review",
        "approved": "approved",
        "rejected": "rejected",
        "inactive": "deactivated",
    }.get(to_status, "transitioned")
