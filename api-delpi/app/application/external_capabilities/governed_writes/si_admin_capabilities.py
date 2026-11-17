"""Strategic Indicators administrative write capabilities for DAVI execute.

W013-ACT governed surface — same sealed-proposal contract as the W012
goal stack: every call carries the caller's own JWT and the owner API
stays the final authority on authorization and domain validation.

Capability surface (closed set — nothing else is executable):

  si.department.create        PREPARE+ACT — create department
  si.department.update        PREPARE+ACT — update (incl. rename)
  si.department.activate      PREPARE+ACT — activate department
  si.indicator.create         PREPARE+ACT — create structural indicator
  si.indicator.update         PREPARE+ACT — update (incl. rename)
  si.indicator.activate       PREPARE+ACT — activate indicator
  si.indicator.deactivate     PREPARE+ACT — deactivate indicator
  si.change_request.create    PREPARE+ACT — file a change request
  si.change_request.comment   PREPARE+ACT — add comment (idempotent)
  si.change_request.submit    PREPARE+ACT — draft → submitted

Concurrency model: identical to si.goal.* — PREPARE fingerprints the
authoritative owner state; ACT re-verifies the fingerprint AND forwards
the sealed optimistic precondition (``expected_row_xmin`` /
``expected_xmin`` / status guard) that the owner enforces atomically
inside the mutation transaction. Replay protection for change-request
creates/comments rides the owner-side ``idempotency_key`` (the sealed
proposal id).
"""

from __future__ import annotations

import logging
from typing import Any

from strategic_indicators_client import (
    StrategicIndicatorsApiClient,
    StrategicIndicatorsApiError,
)

from app.application.external_capabilities.governed_writes.errors import (
    INTERNAL,
    NOT_FOUND,
    OUTCOME_VERIFICATION_FAILED,
    VALIDATION,
    GovernedWriteError,
)
from app.application.external_capabilities.governed_writes.proposal import (
    canonical_json,
    fingerprint,
)
from app.application.external_capabilities.governed_writes.si_goal_capabilities import (
    _err,
    _reject_unknown_args,
    _require_occ_token,
    _require_str,
)

logger = logging.getLogger(__name__)

CAP_DEPT_CREATE = "si.department.create"
CAP_DEPT_UPDATE = "si.department.update"
CAP_DEPT_ACTIVATE = "si.department.activate"
CAP_IND_CREATE = "si.indicator.create"
CAP_IND_UPDATE = "si.indicator.update"
CAP_IND_ACTIVATE = "si.indicator.activate"
CAP_IND_DEACTIVATE = "si.indicator.deactivate"
CAP_CR_CREATE = "si.change_request.create"
CAP_CR_COMMENT = "si.change_request.comment"
CAP_CR_SUBMIT = "si.change_request.submit"

SI_ADMIN_WRITE_CAPABILITIES = frozenset(
    {
        CAP_DEPT_CREATE,
        CAP_DEPT_UPDATE,
        CAP_DEPT_ACTIVATE,
        CAP_IND_CREATE,
        CAP_IND_UPDATE,
        CAP_IND_ACTIVATE,
        CAP_IND_DEACTIVATE,
        CAP_CR_CREATE,
        CAP_CR_COMMENT,
        CAP_CR_SUBMIT,
    }
)

_VALID_AGGREGATION_MODES = frozenset({"consolidated", "average_of_units"})
_VALID_SCOPE_TYPES = frozenset({"consolidated", "per_unit"})
_VALID_PERFORMANCE_DIRECTIONS = frozenset(
    {"higher_is_better", "lower_is_better"}
)
_VALID_CR_BLOCKS = frozenset(
    {
        "departments",
        "department_indicators",
        "indicator_goals",
        "parameters.global",
        "governance.notes",
    }
)

_MAX_ID_LENGTH = 100
_MAX_CR_PAYLOAD_BYTES = 16 * 1024
_MAX_CR_PAYLOAD_DEPTH = 6
_MAX_CR_PAYLOAD_KEYS = 200
_MAX_TEXT_LENGTH = 2000
_CR_PAGE_LIMIT = 200
_CR_MAX_PAGES = 25

_DEPT_CREATE_ARGS = frozenset(
    {
        "department_id",
        "department_name",
        "short_name",
        "strategic_summary",
        "headline_goal",
        "supporting_focus",
        "weight_pct",
        "aggregation_mode",
        "display_order",
    }
)
_DEPT_UPDATE_ARGS = frozenset(
    {
        "department_id",
        "new_department_id",
        "department_name",
        "short_name",
        "strategic_summary",
        "headline_goal",
        "supporting_focus",
        "weight_pct",
        "aggregation_mode",
        "is_active",
        "display_order",
    }
)
_DEPT_REF_ARGS = frozenset({"department_id"})
_IND_CREATE_ARGS = frozenset(
    {
        "department_id",
        "indicator_id",
        "indicator_name",
        "weight_pct",
        "scope_type",
        "performance_direction",
        "strategic_description",
        "source_key",
        "value_unit",
        "value_prefix",
        "value_suffix",
        "value_decimals",
        "display_order",
    }
)
_IND_UPDATE_ARGS = frozenset(
    {
        "indicator_id",
        "new_indicator_id",
        "indicator_name",
        "weight_pct",
        "scope_type",
        "performance_direction",
        "strategic_description",
        "source_key",
        "value_unit",
        "value_prefix",
        "value_suffix",
        "value_decimals",
        "is_active",
        "display_order",
    }
)
_IND_REF_ARGS = frozenset({"indicator_id"})
_CR_CREATE_ARGS = frozenset(
    {"title", "description", "target_block", "proposed_payload"}
)
_CR_COMMENT_ARGS = frozenset({"change_request_id", "comment_text"})
_CR_REF_ARGS = frozenset({"change_request_id"})


def _require_id(args: dict, key: str) -> str:
    value = _require_str(args, key)
    if len(value) > _MAX_ID_LENGTH:
        raise _err(f"'{key}' exceeds {_MAX_ID_LENGTH} chars.", code=VALIDATION)
    return value


def _require_weight(args: dict) -> float:
    value = args.get("weight_pct")
    if not isinstance(value, (int, float)) or isinstance(value, bool):
        raise _err("'weight_pct' is required (number).", code=VALIDATION)
    value = float(value)
    if value < 0 or value > 100:
        raise _err("weight_pct must be between 0 and 100.", code=VALIDATION)
    return value


def _validate_cr_payload(payload: Any) -> dict:
    """Bound the flexible CR proposed_payload: object-only, small, shallow."""
    if not isinstance(payload, dict):
        raise _err("'proposed_payload' must be an object.", code=VALIDATION)
    if len(canonical_json(payload).encode("utf-8")) > _MAX_CR_PAYLOAD_BYTES:
        raise _err(
            f"'proposed_payload' exceeds {_MAX_CR_PAYLOAD_BYTES} bytes.",
            code=VALIDATION,
        )

    keys = 0

    def _walk(node: Any, depth: int) -> None:
        nonlocal keys
        if depth > _MAX_CR_PAYLOAD_DEPTH:
            raise _err(
                f"'proposed_payload' exceeds depth {_MAX_CR_PAYLOAD_DEPTH}.",
                code=VALIDATION,
            )
        if isinstance(node, dict):
            keys += len(node)
            if keys > _MAX_CR_PAYLOAD_KEYS:
                raise _err(
                    f"'proposed_payload' exceeds {_MAX_CR_PAYLOAD_KEYS} keys.",
                    code=VALIDATION,
                )
            for value in node.values():
                _walk(value, depth + 1)
        elif isinstance(node, list):
            for item in node:
                _walk(item, depth + 1)

    _walk(payload, 0)
    return payload


def _require_bounded_text(args: dict, key: str) -> str:
    value = _require_str(args, key)
    if len(value) > _MAX_TEXT_LENGTH:
        raise _err(f"'{key}' exceeds {_MAX_TEXT_LENGTH} chars.", code=VALIDATION)
    return value


def _dept_snapshot(row: dict) -> dict:
    """Fingerprint basis for a department row — fields a mutation may touch
    plus the owner OCC token."""
    return {
        "department_id": row.get("department_id"),
        "department_name": row.get("department_name"),
        "short_name": row.get("short_name"),
        "strategic_summary": row.get("strategic_summary"),
        "headline_goal": row.get("headline_goal"),
        "supporting_focus": row.get("supporting_focus"),
        "weight_pct": row.get("weight_pct"),
        "aggregation_mode": row.get("aggregation_mode"),
        "is_active": row.get("is_active"),
        "display_order": row.get("display_order"),
        "row_xmin": row.get("row_xmin"),
    }


def _ind_snapshot(row: dict) -> dict:
    return {
        "indicator_id": row.get("indicator_id"),
        "department_id": row.get("department_id"),
        "indicator_name": row.get("indicator_name"),
        "weight_pct": row.get("weight_pct"),
        "scope_type": row.get("scope_type"),
        "performance_direction": row.get("performance_direction"),
        "strategic_description": row.get("strategic_description"),
        "source_key": row.get("source_key"),
        "value_unit": row.get("value_unit"),
        "value_prefix": row.get("value_prefix"),
        "value_suffix": row.get("value_suffix"),
        "value_decimals": row.get("value_decimals"),
        "branch_value_aggregation": row.get("branch_value_aggregation"),
        "is_active": row.get("is_active"),
        "display_order": row.get("display_order"),
        "row_xmin": row.get("row_xmin"),
    }


def _cr_snapshot(row: dict) -> dict:
    return {
        "id": row.get("id"),
        "request_code": row.get("request_code"),
        "title": row.get("title"),
        "description": row.get("description"),
        "target_block": row.get("target_block"),
        "proposed_payload": row.get("proposed_payload"),
        "status": row.get("status"),
        "row_xmin": row.get("row_xmin"),
    }


class SiAdminWriteStack:
    """Composition-bound adapter: SI client + admin capability impls."""

    def __init__(self, client: StrategicIndicatorsApiClient | None = None) -> None:
        self._client = client or StrategicIndicatorsApiClient()

    # ------------------------------------------------------------ owner reads

    def _list_departments(self, authorization: str) -> list[dict]:
        payload = self._client.list_user_admin_departments(
            authorization=authorization
        )
        items = payload.get("items")
        if not isinstance(items, list):
            raise _err(
                "Owner returned an unexpected departments payload.",
                code=INTERNAL,
                status_code=502,
            )
        return items

    def _find_department(self, authorization: str, department_id: str) -> dict:
        for row in self._list_departments(authorization):
            if str(row.get("department_id")) == department_id:
                return row
        raise _err(
            f"Department '{department_id}' not found (or not visible to the caller).",
            code=NOT_FOUND,
            status_code=404,
        )

    def _list_indicators(
        self, authorization: str, department_id: str
    ) -> list[dict]:
        payload = self._client.list_user_admin_department_indicators(
            authorization=authorization, department_id=department_id
        )
        items = payload.get("items")
        if not isinstance(items, list):
            raise _err(
                "Owner returned an unexpected indicators payload.",
                code=INTERNAL,
                status_code=502,
            )
        return items

    def _find_indicator(
        self, authorization: str, indicator_id: str
    ) -> tuple[dict, list[dict]]:
        """Locate an indicator row by scanning every department — the owner
        has no global indicator get-by-id read."""
        for dept in self._list_departments(authorization):
            rows = self._list_indicators(
                authorization, str(dept.get("department_id") or "")
            )
            for row in rows:
                if str(row.get("indicator_id")) == indicator_id:
                    return row, rows
        raise _err(
            f"Indicator '{indicator_id}' not found (or not visible to the caller).",
            code=NOT_FOUND,
            status_code=404,
        )

    def _list_change_requests(self, authorization: str) -> list[dict]:
        rows: list[dict] = []
        for page in range(_CR_MAX_PAGES):
            payload = self._client.list_user_change_requests(
                authorization=authorization,
                limit=_CR_PAGE_LIMIT,
                offset=page * _CR_PAGE_LIMIT,
            )
            items = payload.get("items")
            if not isinstance(items, list):
                raise _err(
                    "Owner returned an unexpected change-requests payload.",
                    code=INTERNAL,
                    status_code=502,
                )
            rows.extend(items)
            if len(items) < _CR_PAGE_LIMIT:
                break
        return rows

    def _find_change_request(self, authorization: str, cr_id: str) -> dict:
        for row in self._list_change_requests(authorization):
            if str(row.get("id")) == cr_id or str(row.get("request_code")) == cr_id:
                return row
        raise _err(
            f"Change request '{cr_id}' not found (or not visible to the caller).",
            code=NOT_FOUND,
            status_code=404,
        )

    def _depts_fingerprint(self, authorization: str) -> str:
        rows = sorted(
            (_dept_snapshot(row) for row in self._list_departments(authorization)),
            key=lambda r: str(r["department_id"]),
        )
        return fingerprint({"departments": rows})

    def _indicators_fingerprint(
        self, authorization: str, department_id: str
    ) -> str:
        rows = sorted(
            (
                _ind_snapshot(row)
                for row in self._list_indicators(authorization, department_id)
            ),
            key=lambda r: str(r["indicator_id"]),
        )
        return fingerprint({"department_id": department_id, "indicators": rows})

    def _crs_fingerprint(self, authorization: str) -> str:
        rows = sorted(
            (_cr_snapshot(row) for row in self._list_change_requests(authorization)),
            key=lambda r: str(r["id"]),
        )
        return fingerprint({"change_requests": rows})

    # ------------------------------------------------------------ PREPARE

    def prepare(self, authorization: str, capability: str, args: dict) -> dict:
        args = dict(args or {})
        if capability == CAP_DEPT_CREATE:
            return self._prepare_dept_create(authorization, args)
        if capability == CAP_DEPT_UPDATE:
            return self._prepare_dept_update(authorization, args)
        if capability == CAP_DEPT_ACTIVATE:
            return self._prepare_dept_activate(authorization, args)
        if capability == CAP_IND_CREATE:
            return self._prepare_ind_create(authorization, args)
        if capability == CAP_IND_UPDATE:
            return self._prepare_ind_update(authorization, args)
        if capability in (CAP_IND_ACTIVATE, CAP_IND_DEACTIVATE):
            return self._prepare_ind_toggle(
                authorization, args, activate=(capability == CAP_IND_ACTIVATE)
            )
        if capability == CAP_CR_CREATE:
            return self._prepare_cr_create(authorization, args)
        if capability == CAP_CR_COMMENT:
            return self._prepare_cr_comment(authorization, args)
        if capability == CAP_CR_SUBMIT:
            return self._prepare_cr_submit(authorization, args)
        raise _err(f"Unknown write capability '{capability}'.", code=VALIDATION)

    def _prepare_dept_create(self, authorization: str, args: dict) -> dict:
        _reject_unknown_args(CAP_DEPT_CREATE, args, _DEPT_CREATE_ARGS)
        department_id = _require_id(args, "department_id")
        department_name = _require_str(args, "department_name")
        short_name = _require_str(args, "short_name")
        aggregation_mode = str(args.get("aggregation_mode") or "").strip()
        if aggregation_mode not in _VALID_AGGREGATION_MODES:
            raise _err(
                "aggregation_mode must be 'consolidated' or 'average_of_units'.",
                code=VALIDATION,
            )
        weight_pct = _require_weight(args)
        display_order = int(args.get("display_order") or 0)

        body: dict[str, Any] = {
            "department_id": department_id,
            "department_name": department_name,
            "short_name": short_name,
            "strategic_summary": str(args.get("strategic_summary") or ""),
            "headline_goal": str(args.get("headline_goal") or ""),
            "supporting_focus": str(args.get("supporting_focus") or ""),
            "weight_pct": weight_pct,
            "aggregation_mode": aggregation_mode,
            "display_order": display_order,
        }

        fp = self._depts_fingerprint(authorization)
        return {
            "resource_type": "si_department",
            "resource_id": department_id,
            "current_state_fingerprint": fp,
            "exact_change": {"body": body},
            "validation_result": {"ready": True, "checks": ["args", "depts_state"]},
            "consequential_impact": {
                "note": (
                    "Creates an active department; its weight participates "
                    "in the IGD aggregate alongside existing departments."
                ),
            },
            "confirmation_requirement": {
                "kind": "confirm_before_act",
                "summary": {
                    "action": "create_department",
                    "department_id": department_id,
                    "department_name": department_name,
                    "aggregation_mode": aggregation_mode,
                    "weight_pct": weight_pct,
                },
            },
            "expected_postcondition": {
                "department_id": department_id,
                "fields": body,
            },
        }

    def _prepare_dept_update(self, authorization: str, args: dict) -> dict:
        _reject_unknown_args(CAP_DEPT_UPDATE, args, _DEPT_UPDATE_ARGS)
        department_id = _require_id(args, "department_id")
        current = self._find_department(authorization, department_id)

        # Hydrate the full-replace PUT body from the owner row: the model
        # only sends intended deltas; absent fields keep current values.
        merged: dict[str, Any] = {
            "department_name": str(
                args.get("department_name")
                if args.get("department_name") is not None
                else current.get("department_name") or ""
            ),
            "short_name": str(
                args.get("short_name")
                if args.get("short_name") is not None
                else current.get("short_name") or ""
            ),
            "strategic_summary": str(
                args.get("strategic_summary")
                if args.get("strategic_summary") is not None
                else current.get("strategic_summary") or ""
            ),
            "headline_goal": str(
                args.get("headline_goal")
                if args.get("headline_goal") is not None
                else current.get("headline_goal") or ""
            ),
            "supporting_focus": str(
                args.get("supporting_focus")
                if args.get("supporting_focus") is not None
                else current.get("supporting_focus") or ""
            ),
            "weight_pct": float(
                args.get("weight_pct")
                if args.get("weight_pct") is not None
                else (current.get("weight_pct") or 0)
            ),
            "aggregation_mode": str(
                args.get("aggregation_mode") or current.get("aggregation_mode") or ""
            ).strip(),
            "is_active": bool(
                args.get("is_active")
                if args.get("is_active") is not None
                else current.get("is_active")
            ),
            "display_order": int(
                args.get("display_order")
                if args.get("display_order") is not None
                else (current.get("display_order") or 0)
            ),
        }
        new_department_id = (
            str(args.get("new_department_id")).strip()
            if args.get("new_department_id") is not None
            else None
        ) or None
        if new_department_id:
            if len(new_department_id) > _MAX_ID_LENGTH:
                raise _err(
                    f"'new_department_id' exceeds {_MAX_ID_LENGTH} chars.",
                    code=VALIDATION,
                )
            if new_department_id == department_id:
                raise _err(
                    "new_department_id equals the current id (no-op rename).",
                    code=VALIDATION,
                )
            merged["new_department_id"] = new_department_id

        if merged["aggregation_mode"] not in _VALID_AGGREGATION_MODES:
            raise _err(
                "aggregation_mode must be 'consolidated' or 'average_of_units'.",
                code=VALIDATION,
            )
        if not (0 <= merged["weight_pct"] <= 100):
            raise _err("weight_pct must be between 0 and 100.", code=VALIDATION)
        if not merged["department_name"].strip():
            raise _err("department_name cannot be empty.", code=VALIDATION)
        if not merged["short_name"].strip():
            raise _err("short_name cannot be empty.", code=VALIDATION)

        # Fail-closed: without the owner OCC token the update would run
        # unguarded — refuse to seal an unprotected proposal.
        row_xmin = current.get("row_xmin")
        if not row_xmin:
            raise _err(
                "Owner read contract did not expose the OCC token "
                "(row_xmin); cannot seal a guarded update.",
                code=INTERNAL,
                status_code=502,
            )
        merged["expected_row_xmin"] = row_xmin

        diff = _diff_dept_fields(current, merged, new_department_id)
        impact: dict[str, Any] = {"changed_fields": diff}
        if new_department_id:
            impact["rename"] = {
                "from": department_id,
                "to": new_department_id,
                "migrated_references": [
                    "department_indicators.department_id",
                    "period_scores.scope_department_id",
                ],
                "note": (
                    "Renaming repoints structural indicators and stored "
                    "period scores to the new id (owner-migrated)."
                ),
            }

        return {
            "resource_type": "si_department",
            "resource_id": department_id,
            "current_state_fingerprint": fingerprint(_dept_snapshot(current)),
            "exact_change": {"department_id": department_id, "body": merged},
            "validation_result": {"ready": True, "checks": ["args", "row_state"]},
            "consequential_impact": impact,
            "confirmation_requirement": {
                "kind": "confirm_before_act",
                "summary": {
                    "action": "update_department",
                    "department_id": department_id,
                    "changed_fields": diff,
                    **(
                        {"rename_to": new_department_id}
                        if new_department_id
                        else {}
                    ),
                },
            },
            "expected_postcondition": {
                "department_id": new_department_id or department_id,
                "fields": {
                    k: v
                    for k, v in merged.items()
                    if k not in ("expected_row_xmin", "new_department_id")
                },
            },
        }

    def _prepare_dept_activate(self, authorization: str, args: dict) -> dict:
        _reject_unknown_args(CAP_DEPT_ACTIVATE, args, _DEPT_REF_ARGS)
        department_id = _require_id(args, "department_id")
        current = self._find_department(authorization, department_id)

        row_xmin = current.get("row_xmin")
        if not row_xmin:
            raise _err(
                "Owner read contract did not expose the OCC token "
                "(row_xmin); cannot seal a guarded state change.",
                code=INTERNAL,
                status_code=502,
            )
        if current.get("is_active") is True:
            raise _err(
                f"Department '{department_id}' is already active.",
                code=VALIDATION,
                status_code=409,
            )

        return {
            "resource_type": "si_department",
            "resource_id": department_id,
            "current_state_fingerprint": fingerprint(_dept_snapshot(current)),
            "exact_change": {
                "department_id": department_id,
                "expected_xmin": row_xmin,
            },
            "validation_result": {"ready": True, "checks": ["args", "row_state"]},
            "consequential_impact": {
                "note": (
                    "Activating makes the department count again in the "
                    "IGD aggregate and the admin trees."
                ),
            },
            "confirmation_requirement": {
                "kind": "confirm_before_act",
                "summary": {
                    "action": "activate_department",
                    "department_id": department_id,
                    "department_name": current.get("department_name"),
                },
            },
            "expected_postcondition": {
                "department_id": department_id,
                "is_active": True,
            },
        }

    def _prepare_ind_create(self, authorization: str, args: dict) -> dict:
        _reject_unknown_args(CAP_IND_CREATE, args, _IND_CREATE_ARGS)
        department_id = _require_id(args, "department_id")
        indicator_id = _require_id(args, "indicator_id")
        indicator_name = _require_str(args, "indicator_name")
        scope_type = str(args.get("scope_type") or "").strip()
        if scope_type not in _VALID_SCOPE_TYPES:
            raise _err(
                "scope_type must be 'consolidated' or 'per_unit'.",
                code=VALIDATION,
            )
        performance_direction = str(
            args.get("performance_direction") or "higher_is_better"
        ).strip()
        if performance_direction not in _VALID_PERFORMANCE_DIRECTIONS:
            raise _err("performance_direction inválido.", code=VALIDATION)
        weight_pct = _require_weight(args)
        value_decimals = args.get("value_decimals", 2)
        if not isinstance(value_decimals, int) or isinstance(value_decimals, bool):
            raise _err("value_decimals must be an integer.", code=VALIDATION)
        if value_decimals < 0 or value_decimals > 6:
            raise _err("value_decimals must be between 0 and 6.", code=VALIDATION)
        display_order = int(args.get("display_order") or 0)

        # The owner creates indicators under an existing department — the
        # read itself enforces visibility/authorization of the parent.
        self._find_department(authorization, department_id)

        body: dict[str, Any] = {
            "indicator_id": indicator_id,
            "indicator_name": indicator_name,
            "weight_pct": weight_pct,
            "scope_type": scope_type,
            "performance_direction": performance_direction,
            "strategic_description": str(args.get("strategic_description") or ""),
            "source_key": args.get("source_key"),
            "value_unit": args.get("value_unit"),
            "value_prefix": args.get("value_prefix"),
            "value_suffix": args.get("value_suffix"),
            "value_decimals": value_decimals,
            "display_order": display_order,
        }

        fp = self._indicators_fingerprint(authorization, department_id)
        return {
            "resource_type": "si_department_indicator",
            "resource_id": indicator_id,
            "current_state_fingerprint": fp,
            "exact_change": {"department_id": department_id, "body": body},
            "validation_result": {
                "ready": True,
                "checks": ["args", "parent_department", "indicators_state"],
            },
            "consequential_impact": {
                "note": (
                    "Creates an active structural indicator under "
                    f"'{department_id}'; its weight participates in the "
                    "department aggregate."
                ),
            },
            "confirmation_requirement": {
                "kind": "confirm_before_act",
                "summary": {
                    "action": "create_indicator",
                    "department_id": department_id,
                    "indicator_id": indicator_id,
                    "indicator_name": indicator_name,
                    "scope_type": scope_type,
                    "weight_pct": weight_pct,
                },
            },
            "expected_postcondition": {
                "indicator_id": indicator_id,
                "department_id": department_id,
                "fields": body,
            },
        }

    def _prepare_ind_update(self, authorization: str, args: dict) -> dict:
        _reject_unknown_args(CAP_IND_UPDATE, args, _IND_UPDATE_ARGS)
        indicator_id = _require_id(args, "indicator_id")
        current, _rows = self._find_indicator(authorization, indicator_id)

        merged: dict[str, Any] = {
            "indicator_name": str(
                args.get("indicator_name")
                if args.get("indicator_name") is not None
                else current.get("indicator_name") or ""
            ),
            "weight_pct": float(
                args.get("weight_pct")
                if args.get("weight_pct") is not None
                else (current.get("weight_pct") or 0)
            ),
            "scope_type": str(
                args.get("scope_type") or current.get("scope_type") or ""
            ).strip(),
            "performance_direction": str(
                args.get("performance_direction")
                or current.get("performance_direction")
                or "higher_is_better"
            ).strip(),
            "strategic_description": str(
                args.get("strategic_description")
                if args.get("strategic_description") is not None
                else current.get("strategic_description") or ""
            ),
            "source_key": (
                args.get("source_key")
                if "source_key" in args
                else current.get("source_key")
            ),
            "value_unit": (
                args.get("value_unit")
                if "value_unit" in args
                else current.get("value_unit")
            ),
            "value_prefix": (
                args.get("value_prefix")
                if "value_prefix" in args
                else current.get("value_prefix")
            ),
            "value_suffix": (
                args.get("value_suffix")
                if "value_suffix" in args
                else current.get("value_suffix")
            ),
            "value_decimals": int(
                args.get("value_decimals")
                if args.get("value_decimals") is not None
                else (current.get("value_decimals") or 0)
            ),
            "is_active": bool(
                args.get("is_active")
                if args.get("is_active") is not None
                else current.get("is_active")
            ),
            "display_order": int(
                args.get("display_order")
                if args.get("display_order") is not None
                else (current.get("display_order") or 0)
            ),
        }
        # Full-replace PUT resets fields not sent; carry the owner's
        # aggregation mode forward so a plain update does not silently
        # reset it (the HTTP contract does not expose it as an arg).
        merged["branch_value_aggregation"] = current.get(
            "branch_value_aggregation"
        )

        new_indicator_id = (
            str(args.get("new_indicator_id")).strip()
            if args.get("new_indicator_id") is not None
            else None
        ) or None
        if new_indicator_id:
            if len(new_indicator_id) > _MAX_ID_LENGTH:
                raise _err(
                    f"'new_indicator_id' exceeds {_MAX_ID_LENGTH} chars.",
                    code=VALIDATION,
                )
            if new_indicator_id == indicator_id:
                raise _err(
                    "new_indicator_id equals the current id (no-op rename).",
                    code=VALIDATION,
                )
            merged["new_indicator_id"] = new_indicator_id

        if merged["scope_type"] not in _VALID_SCOPE_TYPES:
            raise _err(
                "scope_type must be 'consolidated' or 'per_unit'.",
                code=VALIDATION,
            )
        if merged["performance_direction"] not in _VALID_PERFORMANCE_DIRECTIONS:
            raise _err("performance_direction inválido.", code=VALIDATION)
        if not (0 <= merged["weight_pct"] <= 100):
            raise _err("weight_pct must be between 0 and 100.", code=VALIDATION)
        if not (0 <= merged["value_decimals"] <= 6):
            raise _err("value_decimals must be between 0 and 6.", code=VALIDATION)
        if not merged["indicator_name"].strip():
            raise _err("indicator_name cannot be empty.", code=VALIDATION)

        row_xmin = current.get("row_xmin")
        if not row_xmin:
            raise _err(
                "Owner read contract did not expose the OCC token "
                "(row_xmin); cannot seal a guarded update.",
                code=INTERNAL,
                status_code=502,
            )
        merged["expected_row_xmin"] = row_xmin

        diff = _diff_ind_fields(current, merged, new_indicator_id)
        impact: dict[str, Any] = {"changed_fields": diff}
        if new_indicator_id:
            impact["rename"] = {
                "from": indicator_id,
                "to": new_indicator_id,
                "migrated_references": ["indicator_goals.indicator_id"],
                "note": (
                    "Renaming repoints analytical goals to the new "
                    "indicator id (owner-migrated)."
                ),
            }

        return {
            "resource_type": "si_department_indicator",
            "resource_id": indicator_id,
            "current_state_fingerprint": fingerprint(_ind_snapshot(current)),
            "exact_change": {"indicator_id": indicator_id, "body": merged},
            "validation_result": {"ready": True, "checks": ["args", "row_state"]},
            "consequential_impact": impact,
            "confirmation_requirement": {
                "kind": "confirm_before_act",
                "summary": {
                    "action": "update_indicator",
                    "indicator_id": indicator_id,
                    "changed_fields": diff,
                    **(
                        {"rename_to": new_indicator_id}
                        if new_indicator_id
                        else {}
                    ),
                },
            },
            "expected_postcondition": {
                "indicator_id": new_indicator_id or indicator_id,
                "fields": {
                    k: v
                    for k, v in merged.items()
                    if k not in ("expected_row_xmin", "new_indicator_id")
                },
            },
        }

    def _prepare_ind_toggle(
        self, authorization: str, args: dict, *, activate: bool
    ) -> dict:
        capability = CAP_IND_ACTIVATE if activate else CAP_IND_DEACTIVATE
        _reject_unknown_args(capability, args, _IND_REF_ARGS)
        indicator_id = _require_id(args, "indicator_id")
        current, _rows = self._find_indicator(authorization, indicator_id)

        row_xmin = current.get("row_xmin")
        if not row_xmin:
            raise _err(
                "Owner read contract did not expose the OCC token "
                "(row_xmin); cannot seal a guarded state change.",
                code=INTERNAL,
                status_code=502,
            )
        if bool(current.get("is_active")) == activate:
            raise _err(
                f"Indicator '{indicator_id}' is already "
                f"{'active' if activate else 'inactive'}.",
                code=VALIDATION,
                status_code=409,
            )

        return {
            "resource_type": "si_department_indicator",
            "resource_id": indicator_id,
            "current_state_fingerprint": fingerprint(_ind_snapshot(current)),
            "exact_change": {
                "indicator_id": indicator_id,
                "expected_xmin": row_xmin,
            },
            "validation_result": {"ready": True, "checks": ["args", "row_state"]},
            "consequential_impact": {
                "note": (
                    "Activating makes the indicator count again in the "
                    "department aggregate."
                    if activate
                    else "Deactivating removes the indicator from the "
                    "department aggregate and active trees."
                ),
            },
            "confirmation_requirement": {
                "kind": "confirm_before_act",
                "summary": {
                    "action": (
                        "activate_indicator" if activate else "deactivate_indicator"
                    ),
                    "indicator_id": indicator_id,
                    "indicator_name": current.get("indicator_name"),
                    "department_id": current.get("department_id"),
                },
            },
            "expected_postcondition": {
                "indicator_id": indicator_id,
                "is_active": activate,
            },
        }

    def _prepare_cr_create(self, authorization: str, args: dict) -> dict:
        _reject_unknown_args(CAP_CR_CREATE, args, _CR_CREATE_ARGS)
        title = _require_bounded_text(args, "title")
        description = _require_bounded_text(args, "description")
        target_block = str(args.get("target_block") or "").strip()
        if target_block not in _VALID_CR_BLOCKS:
            raise _err(
                "target_block must be one of: "
                + ", ".join(sorted(_VALID_CR_BLOCKS)),
                code=VALIDATION,
            )
        payload = _validate_cr_payload(args.get("proposed_payload"))

        body = {
            "title": title,
            "description": description,
            "target_block": target_block,
            "proposed_payload": payload,
        }

        fp = self._crs_fingerprint(authorization)
        return {
            "resource_type": "si_change_request",
            "resource_id": None,
            "current_state_fingerprint": fp,
            "exact_change": {"body": body},
            "validation_result": {"ready": True, "checks": ["args", "crs_state"]},
            "consequential_impact": {
                "note": (
                    "Creates a draft change request for review — it does "
                    "NOT apply the proposed payload to live configuration."
                ),
            },
            "confirmation_requirement": {
                "kind": "confirm_before_act",
                "summary": {
                    "action": "create_change_request",
                    "title": title,
                    "target_block": target_block,
                },
            },
            "expected_postcondition": {
                "title": title,
                "target_block": target_block,
                "status": "draft",
            },
        }

    def _prepare_cr_comment(self, authorization: str, args: dict) -> dict:
        _reject_unknown_args(CAP_CR_COMMENT, args, _CR_COMMENT_ARGS)
        cr_id = _require_id(args, "change_request_id")
        comment_text = _require_bounded_text(args, "comment_text")
        current = self._find_change_request(authorization, cr_id)

        return {
            "resource_type": "si_change_request",
            "resource_id": str(current.get("id")),
            "current_state_fingerprint": fingerprint(_cr_snapshot(current)),
            "exact_change": {
                "change_request_id": str(current.get("id")),
                "body": {"comment_text": comment_text},
            },
            "validation_result": {"ready": True, "checks": ["args", "row_state"]},
            "consequential_impact": {
                "note": (
                    "Adds a comment to the change request; idempotent "
                    "replay returns the same comment."
                ),
            },
            "confirmation_requirement": {
                "kind": "confirm_before_act",
                "summary": {
                    "action": "comment_change_request",
                    "change_request_id": current.get("id"),
                    "request_code": current.get("request_code"),
                    "comment_text": comment_text[:120],
                },
            },
            "expected_postcondition": {
                "change_request_id": str(current.get("id")),
                "comment_text": comment_text,
            },
        }

    def _prepare_cr_submit(self, authorization: str, args: dict) -> dict:
        _reject_unknown_args(CAP_CR_SUBMIT, args, _CR_REF_ARGS)
        cr_id = _require_id(args, "change_request_id")
        current = self._find_change_request(authorization, cr_id)

        if current.get("status") != "draft":
            raise _err(
                f"Change request '{cr_id}' is not a draft "
                f"(status: {current.get('status')}).",
                code=VALIDATION,
                status_code=409,
            )
        row_xmin = current.get("row_xmin")
        if not row_xmin:
            raise _err(
                "Owner read contract did not expose the OCC token "
                "(row_xmin); cannot seal a guarded transition.",
                code=INTERNAL,
                status_code=502,
            )

        return {
            "resource_type": "si_change_request",
            "resource_id": str(current.get("id")),
            "current_state_fingerprint": fingerprint(_cr_snapshot(current)),
            "exact_change": {
                "change_request_id": str(current.get("id")),
                "expected_xmin": row_xmin,
            },
            "validation_result": {"ready": True, "checks": ["args", "row_state"]},
            "consequential_impact": {
                "note": (
                    "Submits the change request for review — submitting "
                    "does NOT approve or apply the proposed change."
                ),
            },
            "confirmation_requirement": {
                "kind": "confirm_before_act",
                "summary": {
                    "action": "submit_change_request",
                    "change_request_id": current.get("id"),
                    "request_code": current.get("request_code"),
                    "title": current.get("title"),
                    "target_block": current.get("target_block"),
                },
            },
            "expected_postcondition": {
                "change_request_id": str(current.get("id")),
                "status": "submitted",
            },
        }

    # ------------------------------------------------------------ fingerprint

    def recompute_fingerprint(
        self, authorization: str, capability: str, exact_change: dict
    ) -> str:
        if capability == CAP_DEPT_CREATE:
            return self._depts_fingerprint(authorization)
        if capability in (CAP_DEPT_UPDATE, CAP_DEPT_ACTIVATE):
            row = self._find_department(
                authorization, str(exact_change["department_id"])
            )
            return fingerprint(_dept_snapshot(row))
        if capability == CAP_IND_CREATE:
            return self._indicators_fingerprint(
                authorization, str(exact_change["department_id"])
            )
        if capability in (CAP_IND_UPDATE, CAP_IND_ACTIVATE, CAP_IND_DEACTIVATE):
            row, _rows = self._find_indicator(
                authorization, str(exact_change["indicator_id"])
            )
            return fingerprint(_ind_snapshot(row))
        if capability == CAP_CR_CREATE:
            return self._crs_fingerprint(authorization)
        if capability in (CAP_CR_COMMENT, CAP_CR_SUBMIT):
            row = self._find_change_request(
                authorization, str(exact_change["change_request_id"])
            )
            return fingerprint(_cr_snapshot(row))
        raise _err(
            "Fingerprint recompute unsupported.",
            code=INTERNAL,
            status_code=500,
        )

    # ------------------------------------------------------------ ACT

    def execute(
        self,
        authorization: str,
        capability: str,
        exact_change: dict,
        *,
        correlation_id: str | None = None,
    ) -> dict[str, Any]:
        # Audit correlation: the sealed proposal id doubles as the owner
        # idempotency key for replay-protected CR creates/comments.
        audit_kwargs = {
            "write_origin": "davi-mcp",
            "correlation_id": correlation_id,
        }
        if capability == CAP_DEPT_CREATE:
            return self._client.create_user_admin_department(
                authorization=authorization,
                body=exact_change["body"],
                **audit_kwargs,
            )
        if capability == CAP_DEPT_UPDATE:
            body = dict(exact_change["body"])
            _require_occ_token(body.get("expected_row_xmin"), capability)
            return self._client.update_user_admin_department(
                authorization=authorization,
                department_id=str(exact_change["department_id"]),
                body=body,
                **audit_kwargs,
            )
        if capability == CAP_DEPT_ACTIVATE:
            return self._client.activate_user_admin_department(
                authorization=authorization,
                department_id=str(exact_change["department_id"]),
                expected_xmin=_require_occ_token(
                    exact_change.get("expected_xmin"), capability
                ),
                **audit_kwargs,
            )
        if capability == CAP_IND_CREATE:
            return self._client.create_user_admin_department_indicator(
                authorization=authorization,
                department_id=str(exact_change["department_id"]),
                body=exact_change["body"],
                **audit_kwargs,
            )
        if capability == CAP_IND_UPDATE:
            body = dict(exact_change["body"])
            _require_occ_token(body.get("expected_row_xmin"), capability)
            return self._client.update_user_admin_indicator(
                authorization=authorization,
                indicator_id=str(exact_change["indicator_id"]),
                body=body,
                **audit_kwargs,
            )
        if capability == CAP_IND_ACTIVATE:
            return self._client.activate_user_admin_indicator(
                authorization=authorization,
                indicator_id=str(exact_change["indicator_id"]),
                expected_xmin=_require_occ_token(
                    exact_change.get("expected_xmin"), capability
                ),
                **audit_kwargs,
            )
        if capability == CAP_IND_DEACTIVATE:
            return self._client.deactivate_user_admin_indicator(
                authorization=authorization,
                indicator_id=str(exact_change["indicator_id"]),
                expected_xmin=_require_occ_token(
                    exact_change.get("expected_xmin"), capability
                ),
                **audit_kwargs,
            )
        if capability == CAP_CR_CREATE:
            return self._client.create_user_change_request(
                authorization=authorization,
                body=exact_change["body"],
                idempotency_key=correlation_id,
                **audit_kwargs,
            )
        if capability == CAP_CR_COMMENT:
            return self._client.add_user_change_request_comment(
                authorization=authorization,
                change_request_id=str(exact_change["change_request_id"]),
                body=exact_change["body"],
                idempotency_key=correlation_id,
                **audit_kwargs,
            )
        if capability == CAP_CR_SUBMIT:
            return self._client.submit_user_change_request(
                authorization=authorization,
                change_request_id=str(exact_change["change_request_id"]),
                expected_xmin=_require_occ_token(
                    exact_change.get("expected_xmin"), capability
                ),
                **audit_kwargs,
            )
        raise _err(
            f"ACT not implemented for '{capability}'.",
            code=INTERNAL,
            status_code=500,
        )

    # ------------------------------------------------------------ verify

    def verify(
        self,
        authorization: str,
        capability: str,
        exact_change: dict,
        expected_postcondition: dict,
        write_result: dict[str, Any] | None,
    ) -> dict[str, Any]:
        """Authoritative read-back against the owner API."""
        if capability == CAP_DEPT_CREATE:
            row = self._find_department(
                authorization, str(expected_postcondition["department_id"])
            )
            self._assert_fields(row, expected_postcondition.get("fields") or {})
            return {"department": _dept_snapshot(row)}

        if capability == CAP_DEPT_UPDATE:
            row = self._find_department(
                authorization, str(expected_postcondition["department_id"])
            )
            self._assert_fields(row, expected_postcondition.get("fields") or {})
            return {"department": _dept_snapshot(row)}

        if capability == CAP_DEPT_ACTIVATE:
            row = self._find_department(
                authorization, str(expected_postcondition["department_id"])
            )
            if row.get("is_active") is not True:
                raise GovernedWriteError(
                    "Postcondition failed: department is not active.",
                    code=OUTCOME_VERIFICATION_FAILED,
                    status_code=409,
                )
            return {"department": _dept_snapshot(row)}

        if capability == CAP_IND_CREATE:
            row = self._find_indicator_in_dept(
                authorization,
                str(expected_postcondition["department_id"]),
                str(expected_postcondition["indicator_id"]),
            )
            self._assert_fields(row, expected_postcondition.get("fields") or {})
            return {"indicator": _ind_snapshot(row)}

        if capability in (CAP_IND_UPDATE,):
            row, _rows = self._find_indicator(
                authorization, str(expected_postcondition["indicator_id"])
            )
            self._assert_fields(row, expected_postcondition.get("fields") or {})
            return {"indicator": _ind_snapshot(row)}

        if capability in (CAP_IND_ACTIVATE, CAP_IND_DEACTIVATE):
            row, _rows = self._find_indicator(
                authorization, str(expected_postcondition["indicator_id"])
            )
            if bool(row.get("is_active")) != bool(
                expected_postcondition.get("is_active")
            ):
                raise GovernedWriteError(
                    "Postcondition failed: indicator active state does not "
                    "match the expected outcome.",
                    code=OUTCOME_VERIFICATION_FAILED,
                    status_code=409,
                )
            return {"indicator": _ind_snapshot(row)}

        if capability == CAP_CR_CREATE:
            cr = (write_result or {})
            cr_id = cr.get("id")
            if not cr_id:
                raise GovernedWriteError(
                    "Postcondition failed: create returned no request id.",
                    code=OUTCOME_VERIFICATION_FAILED,
                    status_code=409,
                )
            row = self._find_change_request(authorization, str(cr_id))
            if row.get("status") != "draft":
                raise GovernedWriteError(
                    "Postcondition failed: change request is not a draft.",
                    code=OUTCOME_VERIFICATION_FAILED,
                    status_code=409,
                )
            return {"change_request": _cr_snapshot(row)}

        if capability == CAP_CR_COMMENT:
            # Comments have no owner read endpoint: the authoritative
            # proof is the mutation row itself (id + target + actor +
            # created_at), idempotency-protected by the sealed key.
            comment = write_result or {}
            if (
                not comment.get("id")
                or str(comment.get("change_request_id"))
                != str(expected_postcondition.get("change_request_id"))
                or not comment.get("created_at")
            ):
                raise GovernedWriteError(
                    "Postcondition failed: comment row not confirmed.",
                    code=OUTCOME_VERIFICATION_FAILED,
                    status_code=409,
                )
            parent = self._find_change_request(
                authorization, str(expected_postcondition["change_request_id"])
            )
            return {
                "comment": {
                    "id": comment.get("id"),
                    "change_request_id": comment.get("change_request_id"),
                    "comment_text": comment.get("comment_text"),
                    "created_at": comment.get("created_at"),
                },
                "change_request": _cr_snapshot(parent),
            }

        if capability == CAP_CR_SUBMIT:
            row = self._find_change_request(
                authorization, str(expected_postcondition["change_request_id"])
            )
            if row.get("status") != "submitted":
                raise GovernedWriteError(
                    "Postcondition failed: change request is not submitted.",
                    code=OUTCOME_VERIFICATION_FAILED,
                    status_code=409,
                )
            return {"change_request": _cr_snapshot(row)}

        raise _err(
            f"Verify not implemented for '{capability}'.",
            code=INTERNAL,
            status_code=500,
        )

    def _find_indicator_in_dept(
        self, authorization: str, department_id: str, indicator_id: str
    ) -> dict:
        for row in self._list_indicators(authorization, department_id):
            if str(row.get("indicator_id")) == indicator_id:
                return row
        raise _err(
            f"Indicator '{indicator_id}' not found after write.",
            code=OUTCOME_VERIFICATION_FAILED,
            status_code=409,
        )

    def _assert_fields(self, row: dict, fields: dict) -> None:
        mismatches: list[str] = []
        for key, expected in fields.items():
            actual = row.get(key)
            if key == "weight_pct":
                actual = float(actual or 0)
                expected = float(expected or 0)
            if actual != expected:
                mismatches.append(key)
        if mismatches:
            raise GovernedWriteError(
                "Postcondition failed: fields differ after write: "
                + ", ".join(sorted(mismatches)),
                code=OUTCOME_VERIFICATION_FAILED,
                status_code=409,
                data={"mismatched_fields": sorted(mismatches)},
            )


def _diff_dept_fields(
    current: dict, merged: dict, new_id: str | None
) -> dict[str, dict[str, Any]]:
    diff: dict[str, dict[str, Any]] = {}
    if new_id:
        diff["department_id"] = {"from": current.get("department_id"), "to": new_id}
    for key in (
        "department_name",
        "short_name",
        "strategic_summary",
        "headline_goal",
        "supporting_focus",
        "aggregation_mode",
        "is_active",
        "display_order",
    ):
        before = current.get(key)
        after = merged.get(key)
        if before != after:
            diff[key] = {"from": before, "to": after}
    before_w = float(current.get("weight_pct") or 0)
    after_w = float(merged.get("weight_pct") or 0)
    if before_w != after_w:
        diff["weight_pct"] = {"from": before_w, "to": after_w}
    return diff


def _diff_ind_fields(
    current: dict, merged: dict, new_id: str | None
) -> dict[str, dict[str, Any]]:
    diff: dict[str, dict[str, Any]] = {}
    if new_id:
        diff["indicator_id"] = {"from": current.get("indicator_id"), "to": new_id}
    for key in (
        "indicator_name",
        "scope_type",
        "performance_direction",
        "strategic_description",
        "source_key",
        "value_unit",
        "value_prefix",
        "value_suffix",
        "value_decimals",
        "is_active",
        "display_order",
    ):
        before = current.get(key)
        after = merged.get(key)
        if before != after:
            diff[key] = {"from": before, "to": after}
    before_w = float(current.get("weight_pct") or 0)
    after_w = float(merged.get("weight_pct") or 0)
    if before_w != after_w:
        diff["weight_pct"] = {"from": before_w, "to": after_w}
    return diff
