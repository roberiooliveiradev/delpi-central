"""Strategic Indicators goal write capabilities for the DAVI execute tool.

Bounded adapter over the user-parity StrategicIndicatorsApiClient: every
call carries the caller's own JWT and the owner API stays the final
authority on authorization and domain validation.

Capability surface (closed set — nothing else is executable):

  si.goal.create       PREPARE+ACT — create a goal version for a scope
  si.goal.update       PREPARE+ACT — full-field update (incl. monthly curve)
  si.goal.activate     PREPARE+ACT — activate a version (deactivates scope)
  si.goal.deactivate   PREPARE+ACT — deactivate a version

Concurrency model: PREPARE fingerprints the authoritative state read from
the owner; ACT re-verifies the fingerprint AND forwards a sealed
optimistic precondition (``expected_max_version`` / ``expected_row_xmin``)
that the owner enforces inside the same atomic statement/transaction as
the mutation — a DAVI-only fingerprint could not close the check-to-write
gap on its own.
"""

from __future__ import annotations

import logging
from typing import Any

from strategic_indicators_client import (
    StrategicIndicatorsApiClient,
    StrategicIndicatorsApiError,
)

from app.application.external_capabilities.governed_writes.errors import (
    CONFLICT,
    FORBIDDEN,
    INTERNAL,
    NOT_FOUND,
    OWNER_UNAVAILABLE,
    OUTCOME_VERIFICATION_FAILED,
    UNAUTHENTICATED,
    UNKNOWN_RESULT,
    VALIDATION,
    GovernedWriteError,
)
from app.application.external_capabilities.governed_writes.proposal import (
    fingerprint,
)

logger = logging.getLogger(__name__)

CAP_GOAL_CREATE = "si.goal.create"
CAP_GOAL_UPDATE = "si.goal.update"
CAP_GOAL_ACTIVATE = "si.goal.activate"
CAP_GOAL_DEACTIVATE = "si.goal.deactivate"

SI_GOAL_WRITE_CAPABILITIES = frozenset(
    {
        CAP_GOAL_CREATE,
        CAP_GOAL_UPDATE,
        CAP_GOAL_ACTIVATE,
        CAP_GOAL_DEACTIVATE,
    }
)

_VALID_PERIODICITIES = frozenset({"monthly", "annual", "quarterly", "weekly"})
_VALID_GOAL_MODES = frozenset({"standard", "monthly_curve"})
_VALID_SCOPE_BRANCHES = frozenset({"", "01", "02"})

# Closed per-capability argument vocabularies — unknown keys are rejected
# so the model can never smuggle owner-contract fields past the catalog.
_CREATE_ARGS = frozenset(
    {
        "indicator_id",
        "goal_year",
        "goal_label",
        "goal_value",
        "goal_periodicity",
        "goal_mode",
        "goal_scope_branch",
        "monthly_targets",
        "valid_from",
        "valid_to",
        "notes",
    }
)
_UPDATE_ARGS = frozenset(
    {
        "goal_id",
        "indicator_id",
        "goal_year",
        "goal_scope_branch",
        "goal_label",
        "goal_value",
        "goal_periodicity",
        "goal_mode",
        "monthly_targets",
        "set_monthly_target",
        "valid_from",
        "valid_to",
        "notes",
    }
)
_GOAL_REF_ARGS = frozenset({"goal_id", "indicator_id", "goal_year"})


def _err(message: str, *, code: str, status_code: int = 400) -> GovernedWriteError:
    return GovernedWriteError(message, code=code, status_code=status_code)


def _require_occ_token(token: Any, capability: str) -> str:
    """Defense-in-depth at ACT: a sealed proposal must carry the owner OCC
    precondition — a missing token means the mutation would run unguarded."""
    if not token:
        raise _err(
            f"Sealed proposal for {capability} lacks the owner OCC "
            "precondition token; refusing an unguarded write.",
            code=VALIDATION,
            status_code=409,
        )
    return str(token)


def _reject_unknown_args(capability: str, args: dict, allowed: frozenset) -> None:
    unknown = sorted(set(args) - set(allowed))
    if unknown:
        raise _err(
            f"Unknown argument(s) for {capability}: {', '.join(unknown)}.",
            code=VALIDATION,
        )


def _require_str(args: dict, key: str) -> str:
    value = args.get(key)
    if not isinstance(value, str) or not value.strip():
        raise _err(f"'{key}' is required.", code=VALIDATION)
    return value.strip()


def _normalize_scope_branch(value: Any) -> str:
    return ("" if value is None else str(value)).strip()


def _normalize_targets(targets: Any) -> list[dict]:
    if targets is None:
        return []
    if not isinstance(targets, list):
        raise _err("'monthly_targets' must be a list.", code=VALIDATION)
    normalized = []
    for item in targets:
        if not isinstance(item, dict):
            raise _err("Each monthly target must be an object.", code=VALIDATION)
        month = item.get("month_number")
        value = item.get("target_value")
        if not isinstance(month, int) or isinstance(month, bool):
            raise _err("monthly_targets[].month_number must be an integer.", code=VALIDATION)
        if not isinstance(value, (int, float)) or isinstance(value, bool):
            raise _err("monthly_targets[].target_value must be a number.", code=VALIDATION)
        normalized.append({"month_number": month, "target_value": float(value)})
    return normalized


def _validate_curve(targets: list[dict]) -> None:
    months = sorted(t["month_number"] for t in targets)
    if months != list(range(1, 13)):
        raise _err(
            "monthly_curve requires monthly_targets for months 1-12, no duplicates.",
            code=VALIDATION,
        )


def _validate_goal_value_and_mode(args: dict) -> str:
    mode = str(args.get("goal_mode") or "standard").strip()
    if mode not in _VALID_GOAL_MODES:
        raise _err("goal_mode must be 'standard' or 'monthly_curve'.", code=VALIDATION)
    periodicity = str(args.get("goal_periodicity") or "").strip()
    if periodicity not in _VALID_PERIODICITIES:
        raise _err(
            "goal_periodicity must be one of monthly|annual|quarterly|weekly.",
            code=VALIDATION,
        )
    if mode != "monthly_curve":
        value = args.get("goal_value")
        if isinstance(value, (int, float)) and float(value) < 0:
            raise _err("goal_value cannot be negative.", code=VALIDATION)
    return mode


def _snapshot_row(item: dict) -> dict:
    """Fields a goal mutation may touch — the fingerprint basis."""
    return {
        "id": item.get("id"),
        "indicator_id": item.get("indicator_id"),
        "goal_year": item.get("goal_year"),
        "goal_label": item.get("goal_label"),
        "goal_value": item.get("goal_value"),
        "goal_periodicity": item.get("goal_periodicity"),
        "goal_mode": item.get("goal_mode"),
        "goal_scope_branch": item.get("goal_scope_branch") or "",
        "version": item.get("version"),
        "is_active": item.get("is_active"),
        "valid_from": item.get("valid_from"),
        "valid_to": item.get("valid_to"),
        "notes": item.get("notes"),
        "row_xmin": item.get("row_xmin"),
        "monthly_targets": [
            {"month_number": t.get("month_number"), "target_value": t.get("target_value")}
            for t in sorted(
                item.get("monthly_targets") or [],
                key=lambda t: t.get("month_number") or 0,
            )
        ],
    }


class SiGoalWriteStack:
    """Composition-bound adapter: SI client + capability implementations."""

    def __init__(self, client: StrategicIndicatorsApiClient | None = None) -> None:
        self._client = client or StrategicIndicatorsApiClient()

    # ------------------------------------------------------------ owner reads

    def _list_scope_rows(
        self,
        authorization: str,
        *,
        indicator_id: str | None = None,
        goal_year: int | None = None,
    ) -> list[dict]:
        payload = self._client.list_user_indicator_goals(
            authorization=authorization,
            indicator_id=indicator_id,
            goal_year=goal_year,
        )
        items = payload.get("items")
        if not isinstance(items, list):
            raise _err(
                "Owner returned an unexpected goal list payload.",
                code=INTERNAL,
                status_code=502,
            )
        return items

    def _find_goal_row(
        self,
        authorization: str,
        *,
        goal_id: str,
        indicator_id: str | None = None,
        goal_year: int | None = None,
    ) -> dict:
        items = self._list_scope_rows(
            authorization, indicator_id=indicator_id, goal_year=goal_year
        )
        for item in items:
            if str(item.get("id")) == goal_id:
                return item
        raise _err(
            f"Indicator goal '{goal_id}' not found (or not visible to the caller).",
            code=NOT_FOUND,
            status_code=404,
        )

    def _scope_fingerprint(
        self,
        authorization: str,
        *,
        indicator_id: str,
        goal_year: int,
        scope_branch: str,
    ) -> tuple[str, list[dict], int]:
        """Fingerprint of the whole (indicator, year, scope) bucket plus the
        current MAX(version) used as the owner's create precondition."""
        rows = [
            row
            for row in self._list_scope_rows(
                authorization, indicator_id=indicator_id, goal_year=goal_year
            )
            if _normalize_scope_branch(row.get("goal_scope_branch")) == scope_branch
        ]
        snapshots = sorted(
            (_snapshot_row(row) for row in rows),
            key=lambda r: str(r["id"]),
        )
        max_version = max((int(row.get("version") or 0) for row in rows), default=0)
        return (
            fingerprint(
                {
                    "scope": [indicator_id, goal_year, scope_branch],
                    "rows": snapshots,
                }
            ),
            rows,
            max_version,
        )

    # ------------------------------------------------------------ PREPARE

    def prepare(self, authorization: str, capability: str, args: dict) -> dict:
        args = dict(args or {})
        if capability == CAP_GOAL_CREATE:
            return self._prepare_create(authorization, args)
        if capability == CAP_GOAL_UPDATE:
            return self._prepare_update(authorization, args)
        if capability == CAP_GOAL_ACTIVATE:
            return self._prepare_toggle(authorization, args, activate=True)
        if capability == CAP_GOAL_DEACTIVATE:
            return self._prepare_toggle(authorization, args, activate=False)
        raise _err(
            f"Unknown write capability '{capability}'.",
            code=VALIDATION,
        )

    def _prepare_create(self, authorization: str, args: dict) -> dict:
        _reject_unknown_args(CAP_GOAL_CREATE, args, _CREATE_ARGS)
        indicator_id = _require_str(args, "indicator_id")
        goal_year = args.get("goal_year")
        if not isinstance(goal_year, int) or isinstance(goal_year, bool):
            raise _err("'goal_year' is required (integer).", code=VALIDATION)
        if goal_year < 2020 or goal_year > 2100:
            raise _err("goal_year must be between 2020 and 2100.", code=VALIDATION)
        goal_label = _require_str(args, "goal_label")
        mode = _validate_goal_value_and_mode(args)
        scope_branch = _normalize_scope_branch(args.get("goal_scope_branch"))
        if scope_branch not in _VALID_SCOPE_BRANCHES:
            raise _err(
                "goal_scope_branch must be '' (consolidated), '01' or '02'.",
                code=VALIDATION,
            )
        targets = _normalize_targets(args.get("monthly_targets"))
        if mode == "monthly_curve":
            _validate_curve(targets)
        elif targets:
            raise _err(
                "monthly_targets is only allowed when goal_mode='monthly_curve'.",
                code=VALIDATION,
            )

        fp, scope_rows, max_version = self._scope_fingerprint(
            authorization,
            indicator_id=indicator_id,
            goal_year=goal_year,
            scope_branch=scope_branch,
        )

        exact_change: dict[str, Any] = {
            "indicator_id": indicator_id,
            "goal_year": goal_year,
            "goal_label": goal_label,
            "goal_value": float(args.get("goal_value") or 0),
            "goal_periodicity": str(args["goal_periodicity"]).strip(),
            "goal_mode": mode,
            "goal_scope_branch": scope_branch,
            "monthly_targets": targets,
            "valid_from": args.get("valid_from"),
            "valid_to": args.get("valid_to"),
            "notes": args.get("notes"),
            # Sealed owner-side precondition for ACT.
            "expected_max_version": max_version,
        }

        deactivated = [
            {"id": row.get("id"), "version": row.get("version")}
            for row in scope_rows
            if row.get("is_active")
        ]
        return {
            "resource_type": "si_indicator_goal",
            "resource_id": None,
            "current_state_fingerprint": fp,
            "exact_change": exact_change,
            "validation_result": {"ready": True, "checks": ["args", "scope_state"]},
            "consequential_impact": {
                "deactivates_existing_versions": deactivated,
                "note": (
                    "Creating this goal deactivates the current active "
                    "version(s) of the same indicator/year/scope."
                    if deactivated
                    else "No active version exists in this scope."
                ),
            },
            "confirmation_requirement": {
                "kind": "confirm_before_act",
                "summary": {
                    "action": "create_indicator_goal",
                    "indicator_id": indicator_id,
                    "goal_year": goal_year,
                    "goal_scope_branch": scope_branch,
                    "goal_label": goal_label,
                    "goal_mode": mode,
                    "expected_new_version": max_version + 1,
                },
            },
            "expected_postcondition": {
                "indicator_id": indicator_id,
                "goal_year": goal_year,
                "goal_scope_branch": scope_branch,
                "version": max_version + 1,
                "is_active": True,
            },
        }

    def _prepare_update(self, authorization: str, args: dict) -> dict:
        _reject_unknown_args(CAP_GOAL_UPDATE, args, _UPDATE_ARGS)
        goal_id = _require_str(args, "goal_id")
        current = self._find_goal_row(
            authorization,
            goal_id=goal_id,
            indicator_id=args.get("indicator_id"),
            goal_year=args.get("goal_year"),
        )

        # Hydrate the full-form PUT contract from the owner's current row:
        # the model only sends intended deltas; absent fields keep the
        # current values (PUT would otherwise clear/reset them).
        merged: dict[str, Any] = {
            "goal_id": goal_id,
            "indicator_id": str(
                args.get("indicator_id") or current.get("indicator_id") or ""
            ),
            "goal_year": int(
                args.get("goal_year")
                if args.get("goal_year") is not None
                else (current.get("goal_year") or 0)
            ),
            "goal_scope_branch": _normalize_scope_branch(
                args.get("goal_scope_branch")
                if args.get("goal_scope_branch") is not None
                else current.get("goal_scope_branch")
            ),
            "goal_label": str(
                args.get("goal_label")
                if args.get("goal_label") is not None
                else current.get("goal_label") or ""
            ),
            "goal_value": float(
                args.get("goal_value")
                if args.get("goal_value") is not None
                else (current.get("goal_value") or 0)
            ),
            "goal_periodicity": str(
                args.get("goal_periodicity") or current.get("goal_periodicity") or ""
            ).strip(),
            "goal_mode": str(
                args.get("goal_mode") or current.get("goal_mode") or "standard"
            ).strip(),
            "valid_from": (
                args.get("valid_from")
                if "valid_from" in args
                else current.get("valid_from")
            ),
            "valid_to": (
                args.get("valid_to")
                if "valid_to" in args
                else current.get("valid_to")
            ),
            "notes": (
                args.get("notes")
                if "notes" in args
                else current.get("notes")
            ),
            "expected_row_xmin": current.get("row_xmin"),
        }

        # Fail-closed: without the owner's OCC token the update would run
        # unguarded — refuse to seal an unprotected proposal.
        if not merged["expected_row_xmin"]:
            raise _err(
                "Owner read contract did not expose the OCC token "
                "(row_xmin); cannot seal a guarded update.",
                code=INTERNAL,
                status_code=502,
            )

        mode = merged["goal_mode"]
        if mode not in _VALID_GOAL_MODES:
            raise _err("goal_mode must be 'standard' or 'monthly_curve'.", code=VALIDATION)
        if merged["goal_periodicity"] not in _VALID_PERIODICITIES:
            raise _err(
                "goal_periodicity must be one of monthly|annual|quarterly|weekly.",
                code=VALIDATION,
            )
        if mode != "monthly_curve" and merged["goal_value"] < 0:
            raise _err("goal_value cannot be negative.", code=VALIDATION)
        if merged["goal_scope_branch"] not in _VALID_SCOPE_BRANCHES:
            raise _err(
                "goal_scope_branch must be '' (consolidated), '01' or '02'.",
                code=VALIDATION,
            )
        if not merged["goal_label"].strip():
            raise _err("goal_label cannot be empty.", code=VALIDATION)

        if mode == "monthly_curve":
            if args.get("monthly_targets") is not None:
                targets = _normalize_targets(args["monthly_targets"])
            else:
                targets = _normalize_targets(current.get("monthly_targets"))
                patch = args.get("set_monthly_target")
                if patch is not None:
                    if not isinstance(patch, dict):
                        raise _err(
                            "'set_monthly_target' must be an object with "
                            "month_number and target_value.",
                            code=VALIDATION,
                        )
                    month = patch.get("month_number")
                    value = patch.get("target_value")
                    if not isinstance(month, int) or not (1 <= month <= 12):
                        raise _err(
                            "set_monthly_target.month_number must be 1-12.",
                            code=VALIDATION,
                        )
                    if not isinstance(value, (int, float)) or isinstance(value, bool):
                        raise _err(
                            "set_monthly_target.target_value must be a number.",
                            code=VALIDATION,
                        )
                    for target in targets:
                        if target["month_number"] == month:
                            target["target_value"] = float(value)
                            break
                    else:
                        targets.append(
                            {"month_number": month, "target_value": float(value)}
                        )
            _validate_curve(targets)
            merged["monthly_targets"] = targets
        else:
            if args.get("monthly_targets") is not None or args.get("set_monthly_target"):
                raise _err(
                    "monthly_targets/set_monthly_target require "
                    "goal_mode='monthly_curve'.",
                    code=VALIDATION,
                )
            merged["monthly_targets"] = []

        # exact_change seals goal_id (recompute/execute/verify need it);
        # it is stripped again when the owner PUT body is built.
        exact_change = dict(merged)
        diff = _diff_fields(current, merged)

        return {
            "resource_type": "si_indicator_goal",
            "resource_id": goal_id,
            "current_state_fingerprint": fingerprint(_snapshot_row(current)),
            "exact_change": exact_change,
            "validation_result": {"ready": True, "checks": ["args", "row_state"]},
            "consequential_impact": {
                "changed_fields": diff,
                "note": (
                    "monthly_targets are replaced wholesale (full 12-point "
                    "curve); other months were carried from the current state."
                    if mode == "monthly_curve"
                    else "Scalar goal update; monthly targets are removed."
                ),
            },
            "confirmation_requirement": {
                "kind": "confirm_before_act",
                "summary": {
                    "action": "update_indicator_goal",
                    "goal_id": goal_id,
                    "changed_fields": diff,
                },
            },
            "expected_postcondition": {
                "goal_id": goal_id,
                "fields": {
                    k: v for k, v in merged.items() if k != "goal_id"
                },
            },
        }

    def _prepare_toggle(
        self, authorization: str, args: dict, *, activate: bool
    ) -> dict:
        capability = CAP_GOAL_ACTIVATE if activate else CAP_GOAL_DEACTIVATE
        _reject_unknown_args(capability, args, _GOAL_REF_ARGS)
        goal_id = _require_str(args, "goal_id")
        indicator_id = args.get("indicator_id")
        goal_year = args.get("goal_year")
        current = self._find_goal_row(
            authorization,
            goal_id=goal_id,
            indicator_id=indicator_id,
            goal_year=goal_year,
        )

        scope_branch = _normalize_scope_branch(current.get("goal_scope_branch"))
        # Fail-closed: activate/deactivate must carry the owner's OCC token.
        if not current.get("row_xmin"):
            raise _err(
                "Owner read contract did not expose the OCC token "
                "(row_xmin); cannot seal a guarded state change.",
                code=INTERNAL,
                status_code=502,
            )
        if activate:
            # Fingerprint covers the whole scope: activating supersedes
            # siblings, so a concurrent scope change must force re-prepare.
            fp, scope_rows, _max_version = self._scope_fingerprint(
                authorization,
                indicator_id=str(current.get("indicator_id") or ""),
                goal_year=int(current.get("goal_year") or 0),
                scope_branch=scope_branch,
            )
            superseded = [
                {"id": row.get("id"), "version": row.get("version")}
                for row in scope_rows
                if row.get("is_active") and str(row.get("id")) != goal_id
            ]
        else:
            fp = fingerprint(_snapshot_row(current))
            superseded = []

        return {
            "resource_type": "si_indicator_goal",
            "resource_id": goal_id,
            "current_state_fingerprint": fp,
            "exact_change": {
                "goal_id": goal_id,
                "is_active": activate,
                "expected_xmin": current.get("row_xmin"),
            },
            "validation_result": {"ready": True, "checks": ["args", "row_state"]},
            "consequential_impact": {
                "supersedes_active_versions": superseded,
                "note": (
                    "Activating supersedes the currently active version(s) "
                    "in the same indicator/year/scope."
                    if activate and superseded
                    else (
                        "Activation leaves no other active version."
                        if activate
                        else "Deactivation leaves the scope without an active goal."
                    )
                ),
            },
            "confirmation_requirement": {
                "kind": "confirm_before_act",
                "summary": {
                    "action": (
                        "activate_indicator_goal"
                        if activate
                        else "deactivate_indicator_goal"
                    ),
                    "goal_id": goal_id,
                    "indicator_id": current.get("indicator_id"),
                    "goal_year": current.get("goal_year"),
                    "version": current.get("version"),
                    "goal_scope_branch": scope_branch,
                },
            },
            "expected_postcondition": {
                "goal_id": goal_id,
                "is_active": activate,
            },
        }

    # ------------------------------------------------------------ fingerprint

    def recompute_fingerprint(
        self, authorization: str, capability: str, exact_change: dict
    ) -> str:
        if capability == CAP_GOAL_CREATE:
            fp, _rows, _max = self._scope_fingerprint(
                authorization,
                indicator_id=str(exact_change["indicator_id"]),
                goal_year=int(exact_change["goal_year"]),
                scope_branch=_normalize_scope_branch(
                    exact_change.get("goal_scope_branch")
                ),
            )
            return fp
        if capability == CAP_GOAL_UPDATE:
            row = self._find_goal_row(
                authorization, goal_id=str(exact_change["goal_id"])
            )
            return fingerprint(_snapshot_row(row))
        if capability == CAP_GOAL_ACTIVATE:
            row = self._find_goal_row(
                authorization, goal_id=str(exact_change["goal_id"])
            )
            fp, _rows, _max = self._scope_fingerprint(
                authorization,
                indicator_id=str(row.get("indicator_id") or ""),
                goal_year=int(row.get("goal_year") or 0),
                scope_branch=_normalize_scope_branch(row.get("goal_scope_branch")),
            )
            return fp
        if capability == CAP_GOAL_DEACTIVATE:
            row = self._find_goal_row(
                authorization, goal_id=str(exact_change["goal_id"])
            )
            return fingerprint(_snapshot_row(row))
        raise _err(
            "Fingerprint recompute unsupported.",
            code=INTERNAL,
            status_code=500,
        )

    # ------------------------------------------------------------ ACT

    def execute(
        self, authorization: str, capability: str, exact_change: dict
    ) -> dict[str, Any]:
        if capability == CAP_GOAL_CREATE:
            return self._client.create_user_indicator_goal(
                authorization=authorization,
                body=exact_change,
            )
        if capability == CAP_GOAL_UPDATE:
            body = {k: v for k, v in exact_change.items() if k != "goal_id"}
            _require_occ_token(body.get("expected_row_xmin"), capability)
            return self._client.update_user_indicator_goal(
                authorization=authorization,
                goal_id=str(exact_change["goal_id"]),
                body=body,
            )
        if capability == CAP_GOAL_ACTIVATE:
            return self._client.activate_user_indicator_goal(
                authorization=authorization,
                goal_id=str(exact_change["goal_id"]),
                expected_xmin=_require_occ_token(
                    exact_change.get("expected_xmin"), capability
                ),
            )
        if capability == CAP_GOAL_DEACTIVATE:
            return self._client.deactivate_user_indicator_goal(
                authorization=authorization,
                goal_id=str(exact_change["goal_id"]),
                expected_xmin=_require_occ_token(
                    exact_change.get("expected_xmin"), capability
                ),
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
        goal_id = expected_postcondition.get("goal_id")
        if capability == CAP_GOAL_CREATE:
            indicator_id = str(expected_postcondition["indicator_id"])
            goal_year = int(expected_postcondition["goal_year"])
            scope = _normalize_scope_branch(
                expected_postcondition.get("goal_scope_branch")
            )
            version = int(expected_postcondition["version"])
            rows = self._list_scope_rows(
                authorization, indicator_id=indicator_id, goal_year=goal_year
            )
            match = next(
                (
                    row
                    for row in rows
                    if _normalize_scope_branch(row.get("goal_scope_branch")) == scope
                    and int(row.get("version") or 0) == version
                ),
                None,
            )
            if match is None or match.get("is_active") is not True:
                raise GovernedWriteError(
                    "Postcondition failed: expected active goal version not "
                    "found after create.",
                    code=OUTCOME_VERIFICATION_FAILED,
                    status_code=409,
                )
            return {"goal": _snapshot_row(match)}

        row = self._find_goal_row(authorization, goal_id=str(goal_id))
        if capability in (CAP_GOAL_ACTIVATE, CAP_GOAL_DEACTIVATE):
            expected_active = bool(expected_postcondition.get("is_active"))
            if bool(row.get("is_active")) != expected_active:
                raise GovernedWriteError(
                    "Postcondition failed: goal active state does not match "
                    "the expected outcome.",
                    code=OUTCOME_VERIFICATION_FAILED,
                    status_code=409,
                )
            return {"goal": _snapshot_row(row)}

        if capability == CAP_GOAL_UPDATE:
            fields = expected_postcondition.get("fields") or {}
            mismatches: list[str] = []
            for key, expected in fields.items():
                if key == "expected_row_xmin":
                    continue
                if key == "monthly_targets":
                    actual = [
                        {
                            "month_number": t.get("month_number"),
                            "target_value": float(t.get("target_value") or 0),
                        }
                        for t in sorted(
                            row.get("monthly_targets") or [],
                            key=lambda t: t.get("month_number") or 0,
                        )
                    ]
                    wanted = sorted(
                        (
                            {
                                "month_number": t["month_number"],
                                "target_value": float(t["target_value"]),
                            }
                            for t in (expected or [])
                        ),
                        key=lambda t: t["month_number"],
                    )
                    if actual != wanted:
                        mismatches.append(key)
                    continue
                actual_value = row.get(key)
                if key == "goal_scope_branch":
                    actual_value = _normalize_scope_branch(actual_value)
                if key == "goal_value":
                    actual_value = float(actual_value or 0)
                    expected = float(expected or 0)
                if actual_value != expected:
                    mismatches.append(key)
            if mismatches:
                raise GovernedWriteError(
                    "Postcondition failed: fields differ after update: "
                    + ", ".join(sorted(mismatches)),
                    code=OUTCOME_VERIFICATION_FAILED,
                    status_code=409,
                    data={"mismatched_fields": sorted(mismatches)},
                )
            return {"goal": _snapshot_row(row)}

        raise _err(
            f"Verify not implemented for '{capability}'.",
            code=INTERNAL,
            status_code=500,
        )


def _diff_fields(current: dict, merged: dict) -> dict[str, dict[str, Any]]:
    diff: dict[str, dict[str, Any]] = {}
    for key in (
        "indicator_id",
        "goal_year",
        "goal_scope_branch",
        "goal_label",
        "goal_value",
        "goal_periodicity",
        "goal_mode",
        "valid_from",
        "valid_to",
        "notes",
    ):
        before = current.get(key)
        after = merged.get(key)
        if key == "goal_scope_branch":
            before = _normalize_scope_branch(before)
            after = _normalize_scope_branch(after)
        if key == "goal_value":
            before = float(before or 0)
            after = float(after or 0)
        if before != after:
            diff[key] = {"from": before, "to": after}
    current_targets = [
        {"month_number": t.get("month_number"), "target_value": t.get("target_value")}
        for t in sorted(
            current.get("monthly_targets") or [],
            key=lambda t: t.get("month_number") or 0,
        )
    ]
    new_targets = [
        {"month_number": t["month_number"], "target_value": t["target_value"]}
        for t in sorted(
            merged.get("monthly_targets") or [],
            key=lambda t: t["month_number"],
        )
    ]
    if current_targets != new_targets:
        diff["monthly_targets"] = {"from": current_targets, "to": new_targets}
    return diff


def owner_error_to_governed(exc: StrategicIndicatorsApiError) -> GovernedWriteError:
    """Map owner HTTP semantics into the stable governed error contract."""
    status = exc.status_code
    if status == 401:
        return GovernedWriteError(
            "Owner rejected the caller token.",
            code=UNAUTHENTICATED,
            status_code=401,
        )
    if status == 403:
        return GovernedWriteError(
            "Owner denied the write (backend authorization).",
            code=FORBIDDEN,
            status_code=403,
        )
    if status == 404:
        return GovernedWriteError(
            "Owner could not find the target resource.",
            code=NOT_FOUND,
            status_code=404,
        )
    if status == 409:
        return GovernedWriteError(
            "Owner refused the write: concurrent state changed since PREPARE.",
            code=CONFLICT,
            status_code=409,
        )
    if status is not None and 400 <= status < 500:
        return GovernedWriteError(
            "Owner rejected the write payload.",
            code=VALIDATION,
            status_code=status,
        )
    # Network failure or owner 5xx: the write may have committed — do NOT
    # flag it as safe-to-retry; the orchestrator reconciles by read-back.
    return GovernedWriteError(
        "Owner unavailable or transport failed; outcome unknown.",
        code=UNKNOWN_RESULT,
        status_code=503,
        data={"owner_error": str(exc)[:300]},
    )
