"""Strategic Indicators W015 capabilities — governed destructive surface.

Same sealed-proposal contract as W012/W013/W014, extended to destructive
operations. The three hard deletes run exclusively through the ``delete``
MCP tool (separate capability family — never executable via ``execute``);
``si.config.import_replace`` stays a bounded execute capability because
the owner treats it as a catalog apply, not a record delete.

Capability surface (closed set):

  si.goal.delete           PREPARE+ACT — hard-delete one goal (targets
                           cascade; copied_from refs SET NULL)
  si.indicator.delete      PREPARE+ACT — cascade-delete an indicator and
                           every goal version/target under it
  si.department.delete     PREPARE+ACT — cascade-delete a department, all
                           its indicators (active or not) and goals
  si.config.import_replace PREPARE+ACT — wipe-and-rebuild the whole
                           catalog from a bundle (owner transaction)

Owner-side safety now enforced atomically inside the mutation
transaction: ``expected_xmin`` guarded deletes, ``FOR UPDATE`` row locks,
``expected_*_count`` dependent-set guards (FK RESTRICT is the hard
backstop — silent loss is impossible, drift becomes a typed 409), and
``settings_audit`` events written in the same transaction with cascade
counts + ``_audit_meta`` provenance.

Recovery: PREPARE for ``si.config.import_replace`` runs the owner export
and seals its digest inside the proposal — the pre-state artifact is
bound to the authorized operation. The disclosure is honest: the owner
export only carries *active* goals, so superseded versions and row
metadata (created_at/xmin/surrogate ids) are NOT restorable; a replaced
catalog can only be rebuilt to the exported subset.
"""

from __future__ import annotations

import hashlib
import json
import logging
from typing import Any

from strategic_indicators_client import (
    StrategicIndicatorsApiClient,
)

from app.application.external_capabilities.governed_writes.errors import (
    INTERNAL,
    NOT_FOUND,
    VALIDATION,
    GovernedWriteError,
)
from app.application.external_capabilities.governed_writes.proposal import (
    fingerprint,
)
from app.application.external_capabilities.governed_writes.si_goal_capabilities import (
    _err,
    _reject_unknown_args,
    _require_str,
)

logger = logging.getLogger(__name__)

CAP_GOAL_DELETE = "si.goal.delete"
CAP_INDICATOR_DELETE = "si.indicator.delete"
CAP_DEPARTMENT_DELETE = "si.department.delete"
CAP_CONFIG_IMPORT_REPLACE = "si.config.import_replace"

# Destructive family — executable ONLY via the ``delete`` tool.
SI_W015_DELETE_CAPABILITIES = frozenset(
    {
        CAP_GOAL_DELETE,
        CAP_INDICATOR_DELETE,
        CAP_DEPARTMENT_DELETE,
    }
)

# Destructive-but-bounded apply — stays on the ``execute`` tool.
SI_W015_WRITE_CAPABILITIES = frozenset({CAP_CONFIG_IMPORT_REPLACE})

_DELETE_ARGS = {
    CAP_GOAL_DELETE: frozenset({"goal_id"}),
    CAP_INDICATOR_DELETE: frozenset({"indicator_id"}),
    CAP_DEPARTMENT_DELETE: frozenset({"department_id"}),
}
_ID_ARG = {
    CAP_GOAL_DELETE: "goal_id",
    CAP_INDICATOR_DELETE: "indicator_id",
    CAP_DEPARTMENT_DELETE: "department_id",
}
_IMPORT_REPLACE_ARGS = frozenset({"bundle"})

_MAX_BUNDLE_BYTES = 2 * 1024 * 1024


def _canonical_bundle_digest(bundle: Any) -> str:
    canonical = json.dumps(bundle, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _export_state_digest(export: Any) -> str:
    # ``exported_at`` is a per-response timestamp — including it in the
    # fingerprint makes every ACT-time recompute diverge and the proposal
    # can never execute. Digest only the catalog state.
    if isinstance(export, dict):
        export = {k: v for k, v in export.items() if k != "exported_at"}
    return _canonical_bundle_digest(export)


class SiW015WriteStack:
    """PREPARE/re-fingerprint/ACT/verify for the W015 destructive set."""

    def __init__(self, client: StrategicIndicatorsApiClient | None = None) -> None:
        self._client = client or StrategicIndicatorsApiClient()

    # ------------------------------------------------------------- reads

    def _all_goals(self, authorization: str) -> list[dict]:
        page = self._client.list_user_indicator_goals(
            authorization=authorization, active_only=False
        )
        return list((page or {}).get("items") or [])

    def _indicator_goals(self, authorization: str, indicator_id: str) -> list[dict]:
        page = self._client.list_user_indicator_goals(
            authorization=authorization,
            indicator_id=indicator_id,
            active_only=False,
        )
        return list((page or {}).get("items") or [])

    def _department_goals(self, authorization: str, department_id: str) -> list[dict]:
        page = self._client.list_user_indicator_goals(
            authorization=authorization,
            department_id=department_id,
            active_only=False,
        )
        return list((page or {}).get("items") or [])

    def _export(self, authorization: str) -> dict:
        return self._client.export_user_admin_config(
            authorization=authorization
        ) or {}

    # ------------------------------------------------------------- PREPARE

    def prepare(self, authorization: str, capability: str, args: dict) -> dict:
        args = dict(args or {})
        if capability in _DELETE_ARGS:
            return self._prepare_delete(authorization, capability, args)
        if capability == CAP_CONFIG_IMPORT_REPLACE:
            return self._prepare_import_replace(authorization, args)
        raise _err(
            f"PREPARE not implemented for '{capability}'.",
            code=INTERNAL,
            status_code=500,
        )

    def _prepare_delete(
        self, authorization: str, capability: str, args: dict
    ) -> dict:
        _reject_unknown_args(capability, args, _DELETE_ARGS[capability])
        id_key = _ID_ARG[capability]
        target_id = _require_str(args, id_key)

        if capability == CAP_GOAL_DELETE:
            goals = self._all_goals(authorization)
            goal = next(
                (g for g in goals if str(g.get("id")) == target_id), None
            )
            if goal is None:
                raise _err(
                    "Meta não encontrada.",
                    code=NOT_FOUND,
                    status_code=404,
                )
            monthly = len(goal.get("monthly_targets") or [])
            copied_refs = [
                str(g.get("id"))
                for g in goals
                if str(g.get("copied_from_goal_id") or "") == target_id
            ]
            xmin = goal.get("row_xmin")
            if xmin is None:
                raise _err(
                    "Não foi possível selar a versão da meta "
                    "(row_xmin indisponível) — PREPARE abortado.",
                    code=INTERNAL,
                    status_code=500,
                )
            exact_change = {
                "goal_id": target_id,
                "expected_xmin": xmin,
            }
            impact = {
                "record_type": "indicator_goal",
                "identifier": target_id,
                "name": goal.get("goal_label") or goal.get("indicator_id"),
                "current_state": {
                    "indicator_id": goal.get("indicator_id"),
                    "goal_year": goal.get("goal_year"),
                    "goal_scope_branch": goal.get("goal_scope_branch"),
                    "version": goal.get("version"),
                    "is_active": goal.get("is_active"),
                },
                "dependents": {
                    "monthly_targets": monthly,
                    "copied_from_references": len(copied_refs),
                    "copied_from_goal_ids": copied_refs,
                },
                "delete_semantics": (
                    "HARD DELETE — physical removal of the goal row and its "
                    "monthly targets (FK cascade); other goals referencing "
                    "it via copied_from_goal_id lose that link (SET NULL)."
                ),
                "reversibility": (
                    "IRREVERSIBLE — no soft delete. The row must be "
                    "recreated manually; prior versions are not restored."
                ),
            }
            resource = {
                "resource_type": "si_indicator_goal",
                "resource_id": target_id,
            }
            summary_action = "hard_delete_goal"
            fp_state = {
                "goal_id": target_id,
                "row_xmin": xmin,
            }
        else:
            export = self._export(authorization)
            if capability == CAP_INDICATOR_DELETE:
                indicator = next(
                    (
                        i
                        for i in export.get("department_indicators") or []
                        if str(i.get("indicator_id")) == target_id
                    ),
                    None,
                )
                if indicator is None:
                    raise _err(
                        "Indicador estrutural não encontrado.",
                        code=NOT_FOUND,
                        status_code=404,
                    )
                goals = self._indicator_goals(authorization, target_id)
                monthly = sum(
                    len(g.get("monthly_targets") or []) for g in goals
                )
                xmin = self._indicator_row_xmin(
                    authorization, indicator
                )
                if xmin is None:
                    raise _err(
                        "Não foi possível selar a versão do indicador "
                        "(row_xmin indisponível) — PREPARE abortado.",
                        code=INTERNAL,
                        status_code=500,
                    )
                exact_change = {
                    "indicator_id": target_id,
                    "expected_xmin": xmin,
                    "expected_goal_count": len(goals),
                }
                impact = {
                    "record_type": "department_indicator",
                    "identifier": target_id,
                    "name": indicator.get("indicator_name"),
                    "current_state": {
                        "department_id": indicator.get("department_id"),
                        "is_active": indicator.get("is_active"),
                    },
                    "dependents": {
                        "indicator_goals": len(goals),
                        "monthly_targets": monthly,
                        "goal_versions": [
                            str(g.get("id")) for g in goals
                        ],
                    },
                    "delete_semantics": (
                        "HARD DELETE — cascade removes every goal version "
                        "and monthly target of this indicator, then the "
                        "indicator row. FK RESTRICT prevents silent loss: "
                        "a concurrent dependent blocks the delete."
                    ),
                    "reversibility": "IRREVERSIBLE — no soft delete.",
                }
                resource = {
                    "resource_type": "si_department_indicator",
                    "resource_id": target_id,
                }
                summary_action = "hard_delete_indicator"
                fp_state = {
                    "indicator_id": target_id,
                    "row_xmin": xmin,
                    "goal_count": len(goals),
                }
            else:  # CAP_DEPARTMENT_DELETE
                department = next(
                    (
                        d
                        for d in export.get("departments") or []
                        if str(d.get("department_id")) == target_id
                    ),
                    None,
                )
                if department is None:
                    raise _err(
                        "Departamento não encontrado.",
                        code=NOT_FOUND,
                        status_code=404,
                    )
                indicators = [
                    i
                    for i in export.get("department_indicators") or []
                    if str(i.get("department_id")) == target_id
                ]
                goals = self._department_goals(authorization, target_id)
                monthly = sum(
                    len(g.get("monthly_targets") or []) for g in goals
                )
                xmin = self._department_row_xmin(
                    authorization, department
                )
                if xmin is None:
                    raise _err(
                        "Não foi possível selar a versão do departamento "
                        "(row_xmin indisponível) — PREPARE abortado.",
                        code=INTERNAL,
                        status_code=500,
                    )
                exact_change = {
                    "department_id": target_id,
                    "expected_xmin": xmin,
                    "expected_indicator_count": len(indicators),
                    "expected_goal_count": len(goals),
                }
                impact = {
                    "record_type": "department",
                    "identifier": target_id,
                    "name": department.get("department_name"),
                    "current_state": {
                        "is_active": department.get("is_active"),
                    },
                    "dependents": {
                        "indicators": len(indicators),
                        "indicator_ids": [
                            str(i.get("indicator_id")) for i in indicators
                        ],
                        "indicator_goals": len(goals),
                        "monthly_targets": monthly,
                    },
                    "delete_semantics": (
                        "HARD DELETE — cascade removes every indicator of "
                        "this department (active or not), every goal "
                        "version and monthly target, then the department "
                        "row. FK RESTRICT prevents silent loss."
                    ),
                    "reversibility": "IRREVERSIBLE — no soft delete.",
                    "kpi_impact": (
                        "IGD/tree/dashboard aggregates recompute without "
                        "this department once snapshots refresh."
                    ),
                }
                resource = {
                    "resource_type": "si_department",
                    "resource_id": target_id,
                }
                summary_action = "hard_delete_department"
                fp_state = {
                    "department_id": target_id,
                    "row_xmin": xmin,
                    "indicator_count": len(indicators),
                    "goal_count": len(goals),
                }

        fp = fingerprint(
            {"capability": capability, "state": fp_state}
        )
        return {
            **resource,
            "current_state_fingerprint": fp,
            "exact_change": exact_change,
            "validation_result": {"ready": True, "checks": ["exists", "args"]},
            "consequential_impact": impact,
            "confirmation_requirement": {
                "kind": "confirm_before_act",
                "destructive": True,
                "summary": {
                    "action": summary_action,
                    **{k: impact[k] for k in ("identifier", "name", "dependents")},
                },
            },
            "expected_postcondition": {"deleted": target_id},
        }

    def _indicator_row_xmin(
        self, authorization: str, indicator: dict
    ) -> str | None:
        """xmin for the indicator row. Export does not carry row_xmin;
        the admin indicators list does — read it for the seal."""
        department_id = str(indicator.get("department_id") or "")
        if not department_id:
            return None
        page = self._client.list_user_admin_department_indicators(
            authorization=authorization, department_id=department_id
        )
        for item in (page or {}).get("items") or []:
            if str(item.get("indicator_id")) == str(
                indicator.get("indicator_id")
            ):
                return item.get("row_xmin")
        return None

    def _department_row_xmin(
        self, authorization: str, department: dict
    ) -> str | None:
        page = self._client.list_user_admin_departments(
            authorization=authorization
        )
        for item in (page or {}).get("items") or []:
            if str(item.get("department_id")) == str(
                department.get("department_id")
            ):
                return item.get("row_xmin")
        return None

    def _prepare_import_replace(
        self, authorization: str, args: dict
    ) -> dict:
        _reject_unknown_args(CAP_CONFIG_IMPORT_REPLACE, args, _IMPORT_REPLACE_ARGS)
        bundle = args.get("bundle")
        if not isinstance(bundle, dict):
            raise _err(
                "bundle é obrigatório e deve ser um objeto.",
                code=VALIDATION,
            )
        raw = json.dumps(bundle)
        if len(raw.encode("utf-8")) > _MAX_BUNDLE_BYTES:
            raise _err(
                "bundle excede o limite de 2 MiB.",
                code=VALIDATION,
            )

        sealed_body = dict(bundle)
        sealed_body["mode"] = "replace"
        # The owner ``/admin/config/import/*`` contract is the flat
        # ``ImportAdminConfigBodySchema`` (schema_version / departments /
        # department_indicators / indicator_goals / module_settings /
        # include_goals / mode at body top level). Wrapping the payload in
        # ``{"bundle": ...}`` makes the owner reject every PREPARE and ACT.
        body = sealed_body
        preview = self._client.preview_user_admin_config_import(
            authorization=authorization, body=body
        )
        if not preview.get("valid"):
            raise _err(
                "Preview do owner rejeitou o pacote: "
                + "; ".join(str(e) for e in preview.get("errors") or []),
                code=VALIDATION,
            )

        # Recovery artifact: the authoritative export at PREPARE time.
        # Its digest is sealed in the fingerprint so a drifted catalog
        # invalidates the proposal; the payload stays in exact_change so
        # the sealed proposal itself carries the pre-state for restore.
        export = self._export(authorization)
        export_digest = _export_state_digest(export)

        exact_change = {
            "body": body,
            "expected_counts": preview.get("current_counts") or {},
            "bundle_digest": _canonical_bundle_digest(sealed_body),
            "recovery_export_digest": export_digest,
            "recovery_export": export,
        }
        planned = preview.get("planned") or {}
        current = preview.get("current_counts") or {}
        fp = fingerprint(
            {
                "capability": CAP_CONFIG_IMPORT_REPLACE,
                "bundle_digest": exact_change["bundle_digest"],
                "current_counts": current,
                "export_digest": export_digest,
            }
        )
        return {
            "resource_type": "si_admin_config",
            "resource_id": None,
            "current_state_fingerprint": fp,
            "exact_change": exact_change,
            "validation_result": {
                "ready": True,
                "checks": ["envelope", "owner_preview"],
            },
            "consequential_impact": {
                "record_type": "admin_config",
                "mode": "replace",
                "current_counts": current,
                "planned": planned,
                "delete_semantics": (
                    "DESTRUCTIVE — the owner deletes EVERY department, "
                    "indicator and goal (active or not, with monthly "
                    "targets) inside one transaction, then rebuilds the "
                    "catalog from the bundle."
                ),
                "reversibility": (
                    "PARTIAL — the sealed PREPARE export restores only "
                    "active goals; superseded versions and row metadata "
                    "are permanently lost."
                ),
            },
            "confirmation_requirement": {
                "kind": "confirm_before_act",
                "destructive": True,
                "summary": {
                    "action": "replace_admin_config",
                    "delete": {k: v.get("delete") for k, v in planned.items() if isinstance(v, dict) and v.get("delete") is not None},
                    "insert": {k: v.get("insert") for k, v in planned.items() if isinstance(v, dict) and v.get("insert") is not None},
                },
            },
            "expected_postcondition": {
                "catalog_counts": {
                    k: v.get("insert")
                    for k, v in planned.items()
                    if k in ("departments", "department_indicators", "indicator_goals")
                    and isinstance(v, dict) and v.get("insert") is not None
                },
            },
        }

    # ------------------------------------------------------- fingerprint re-read

    def recompute_fingerprint(
        self, authorization: str, capability: str, exact_change: dict
    ) -> str:
        ec = dict(exact_change or {})
        if capability == CAP_GOAL_DELETE:
            goals = self._all_goals(authorization)
            goal = next(
                (g for g in goals if str(g.get("id")) == ec.get("goal_id")),
                None,
            )
            return fingerprint(
                {
                    "capability": capability,
                    "state": {
                        "goal_id": ec.get("goal_id"),
                        "row_xmin": (goal or {}).get("row_xmin"),
                    },
                }
            )
        if capability == CAP_INDICATOR_DELETE:
            export = self._export(authorization)
            indicator = next(
                (
                    i
                    for i in export.get("department_indicators") or []
                    if str(i.get("indicator_id")) == ec.get("indicator_id")
                ),
                None,
            )
            xmin = (
                self._indicator_row_xmin(authorization, indicator)
                if indicator
                else None
            )
            goals = (
                self._indicator_goals(authorization, str(ec.get("indicator_id")))
                if indicator
                else []
            )
            return fingerprint(
                {
                    "capability": capability,
                    "state": {
                        "indicator_id": ec.get("indicator_id"),
                        "row_xmin": xmin,
                        "goal_count": len(goals),
                    },
                }
            )
        if capability == CAP_DEPARTMENT_DELETE:
            export = self._export(authorization)
            department = next(
                (
                    d
                    for d in export.get("departments") or []
                    if str(d.get("department_id")) == ec.get("department_id")
                ),
                None,
            )
            xmin = (
                self._department_row_xmin(authorization, department)
                if department
                else None
            )
            indicators = (
                [
                    i
                    for i in export.get("department_indicators") or []
                    if str(i.get("department_id"))
                    == str(ec.get("department_id"))
                ]
                if department
                else []
            )
            goals = (
                self._department_goals(
                    authorization, str(ec.get("department_id"))
                )
                if department
                else []
            )
            return fingerprint(
                {
                    "capability": capability,
                    "state": {
                        "department_id": ec.get("department_id"),
                        "row_xmin": xmin,
                        "indicator_count": len(indicators),
                        "goal_count": len(goals),
                    },
                }
            )
        if capability == CAP_CONFIG_IMPORT_REPLACE:
            export = self._export(authorization)
            export_digest = _export_state_digest(export)
            return fingerprint(
                {
                    "capability": CAP_CONFIG_IMPORT_REPLACE,
                    "bundle_digest": ec.get("bundle_digest"),
                    "current_counts": ec.get("expected_counts") or {},
                    "export_digest": export_digest,
                }
            )
        raise _err(
            f"Fingerprint recompute not implemented for '{capability}'.",
            code=INTERNAL,
            status_code=500,
        )

    # ---------------------------------------------------------------- ACT

    def execute(
        self,
        authorization: str,
        capability: str,
        exact_change: dict,
        *,
        correlation_id: str | None = None,
    ) -> dict[str, Any]:
        audit_kwargs = {
            "write_origin": "davi-mcp",
            "correlation_id": correlation_id,
        }
        ec = dict(exact_change or {})
        if capability == CAP_GOAL_DELETE:
            return self._client.delete_user_indicator_goal(
                authorization=authorization,
                goal_id=str(ec.get("goal_id") or ""),
                expected_xmin=ec.get("expected_xmin"),
                **audit_kwargs,
            )
        if capability == CAP_INDICATOR_DELETE:
            return self._client.delete_user_admin_indicator(
                authorization=authorization,
                indicator_id=str(ec.get("indicator_id") or ""),
                expected_xmin=ec.get("expected_xmin"),
                expected_goal_count=ec.get("expected_goal_count"),
                **audit_kwargs,
            )
        if capability == CAP_DEPARTMENT_DELETE:
            return self._client.delete_user_admin_department(
                authorization=authorization,
                department_id=str(ec.get("department_id") or ""),
                expected_xmin=ec.get("expected_xmin"),
                expected_indicator_count=ec.get("expected_indicator_count"),
                expected_goal_count=ec.get("expected_goal_count"),
                **audit_kwargs,
            )
        if capability == CAP_CONFIG_IMPORT_REPLACE:
            body = dict(ec.get("body") or {})
            if str(body.get("mode") or "") != "replace":
                raise _err(
                    "Sealed import payload is not mode='replace'; refusing ACT.",
                    code=VALIDATION,
                )
            return self._client.apply_user_admin_config_import(
                authorization=authorization,
                body=body,
                expected_counts=ec.get("expected_counts") or {},
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
        write_result: dict,
    ) -> dict[str, Any]:
        ec = dict(exact_change or {})
        if capability == CAP_GOAL_DELETE:
            goals = self._all_goals(authorization)
            still = any(
                str(g.get("id")) == str(ec.get("goal_id")) for g in goals
            )
            if still:
                raise _err(
                    "Postcondition failed: goal still present after delete.",
                    code=INTERNAL,
                    status_code=500,
                )
            return {
                "verified": True,
                "postcondition": "goal_absent",
                "goal_id": ec.get("goal_id"),
            }
        if capability == CAP_INDICATOR_DELETE:
            export = self._export(authorization)
            still = any(
                str(i.get("indicator_id")) == str(ec.get("indicator_id"))
                for i in export.get("department_indicators") or []
            )
            goals = self._indicator_goals(
                authorization, str(ec.get("indicator_id"))
            )
            if still or goals:
                raise _err(
                    "Postcondition failed: indicator or its goals still present.",
                    code=INTERNAL,
                    status_code=500,
                )
            return {
                "verified": True,
                "postcondition": "indicator_and_goals_absent",
                "indicator_id": ec.get("indicator_id"),
            }
        if capability == CAP_DEPARTMENT_DELETE:
            export = self._export(authorization)
            still = any(
                str(d.get("department_id")) == str(ec.get("department_id"))
                for d in export.get("departments") or []
            )
            leftovers = [
                i
                for i in export.get("department_indicators") or []
                if str(i.get("department_id"))
                == str(ec.get("department_id"))
            ]
            if still or leftovers:
                raise _err(
                    "Postcondition failed: department or its indicators still present.",
                    code=INTERNAL,
                    status_code=500,
                )
            return {
                "verified": True,
                "postcondition": "department_and_indicators_absent",
                "department_id": ec.get("department_id"),
            }
        if capability == CAP_CONFIG_IMPORT_REPLACE:
            expected = (expected_postcondition or {}).get("catalog_counts") or {}
            export = self._export(authorization)
            actual = {
                "departments": len(export.get("departments") or []),
                "department_indicators": len(
                    export.get("department_indicators") or []
                ),
                "indicator_goals": len(export.get("indicator_goals") or []),
            }
            mismatched = {
                k: {"expected": expected.get(k), "actual": actual.get(k)}
                for k in expected
                if expected.get(k) is not None
                and actual.get(k) != expected.get(k)
            }
            sealed_settings = (ec.get("body") or {}).get("module_settings") or {}
            if (export.get("module_settings") or {}) != sealed_settings:
                mismatched["module_settings"] = {
                    "expected": _canonical_bundle_digest(sealed_settings),
                    "actual": _canonical_bundle_digest(
                        export.get("module_settings") or {}
                    ),
                }
            if mismatched:
                raise _err(
                    f"Postcondition failed: catalog counts diverge {mismatched}.",
                    code=INTERNAL,
                    status_code=500,
                )
            return {
                "verified": True,
                "postcondition": "catalog_counts_match_plan",
                "catalog_counts": actual,
            }
        raise _err(
            f"Verify not implemented for '{capability}'.",
            code=INTERNAL,
            status_code=500,
        )
