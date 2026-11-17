"""Strategic Indicators W014 capabilities for DAVI execute.

Bulk / operational surface — same sealed-proposal contract as the W012
goal stack and the W013 admin stack: every call carries the caller's own
JWT and the owner API stays the final authority on authorization and
domain validation.

Capability surface (closed set — nothing else is executable):

  si.goal.bulk_create      PREPARE+ACT — batch-create goals (≤500 items)
  si.goal.duplicate_year   PREPARE+ACT — copy goals year → year
  si.goal.fill_missing     PREPARE+ACT — fill indicators missing a goal
  si.config.import_apply   PREPARE+ACT — apply config bundle (merge only)
  si.cache.refresh         PREPARE+ACT — schedule materialized refresh
  si.cache.invalidate      PREPARE+ACT — wipe snapshots + schedule refresh
  si.job.tree_load         PREPARE+ACT — dispatch async tree load job

Concurrency model: PREPARE reproduces the owner's read set and seals a
deterministic digest (``_goals_rows_digest`` — sha256 over the sorted
``|``-joined field tuples, ``goal_value`` coerced through ``float``; the
contract is byte-identical to the owner implementation). ACT re-verifies
the fingerprint AND forwards the sealed digests / per-scope
``expected_max_version`` / ``expected_counts`` as query preconditions the
owner enforces atomically inside the mutation transaction (advisory
xact locks + guarded inserts). The destructive ``mode="replace"`` import
variant remains deferred to W015 and is rejected at PREPARE.
"""

from __future__ import annotations

import hashlib
import logging
from typing import Any

from strategic_indicators_client import (
    StrategicIndicatorsApiClient,
)

from app.application.external_capabilities.governed_writes.errors import (
    INTERNAL,
    NOT_FOUND,
    OUTCOME_VERIFICATION_FAILED,
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

CAP_GOAL_BULK_CREATE = "si.goal.bulk_create"
CAP_GOAL_DUPLICATE_YEAR = "si.goal.duplicate_year"
CAP_GOAL_FILL_MISSING = "si.goal.fill_missing"
CAP_CONFIG_IMPORT_APPLY = "si.config.import_apply"
CAP_CACHE_REFRESH = "si.cache.refresh"
CAP_CACHE_INVALIDATE = "si.cache.invalidate"
CAP_JOB_TREE_LOAD = "si.job.tree_load"

SI_W014_WRITE_CAPABILITIES = frozenset(
    {
        CAP_GOAL_BULK_CREATE,
        CAP_GOAL_DUPLICATE_YEAR,
        CAP_GOAL_FILL_MISSING,
        CAP_CONFIG_IMPORT_APPLY,
        CAP_CACHE_REFRESH,
        CAP_CACHE_INVALIDATE,
        CAP_JOB_TREE_LOAD,
    }
)

_MAX_BULK_ITEMS = 500
_MAX_BUNDLE_BYTES = 2 * 1024 * 1024
_MAX_TEXT_LENGTH = 2000
_VALID_PERIODICITIES = frozenset({"monthly", "annual", "quarterly", "weekly"})
_VALID_GOAL_MODES = frozenset({"standard", "monthly_curve"})
_VALID_SCOPE_BRANCHES = frozenset({"", "01", "02"})
_VALID_VIEW_MODES = frozenset({"consolidated", "per_unit"})

_BULK_CREATE_ARGS = frozenset({"goal_year", "items"})
_BULK_ITEM_ARGS = frozenset(
    {
        "indicator_id",
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
_DUPLICATE_YEAR_ARGS = frozenset(
    {"source_year", "target_year", "department_ids", "overwrite_existing"}
)
_FILL_MISSING_ARGS = frozenset({"goal_year", "department_ids", "copy_from_year"})
_IMPORT_APPLY_ARGS = frozenset({"bundle", "include_goals"})
_CACHE_REFRESH_ARGS = frozenset({"competence", "trends_months"})
_CACHE_INVALIDATE_ARGS: frozenset = frozenset()
_JOB_TREE_LOAD_ARGS = frozenset(
    {"view_mode", "branch", "competence", "start_date", "end_date", "months"}
)

# Shared digest contract with
# PostgresStrategicIndicatorsIndicatorGoalsRepository._goals_rows_digest —
# any drift here turns every ACT into a spurious 409, so both sides must
# normalize identically (goal_value through float, None → "").
_BULK_SOURCE_DIGEST_FIELDS = (
    "indicator_id",
    "goal_scope_branch",
    "goal_label",
    "goal_value",
    "goal_periodicity",
    "goal_mode",
)
_BULK_EXISTING_DIGEST_FIELDS = (
    "indicator_id",
    "goal_scope_branch",
    "goal_year",
)


def _goals_rows_digest(rows: list[dict], fields: tuple[str, ...]) -> str:
    def _norm(field: str, value) -> str:
        if value is None:
            return ""
        if field == "goal_value":
            try:
                return str(float(value))
            except (TypeError, ValueError):
                return str(value)
        return str(value)

    tuples = sorted(
        "|".join(_norm(field, row.get(field)) for field in fields)
        for row in rows
    )
    return hashlib.sha256("\n".join(tuples).encode("utf-8")).hexdigest()


def _require_int(args: dict, key: str, *, minimum: int, maximum: int) -> int:
    value = args.get(key)
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        raise _err(f"{key} must be an integer.", code=VALIDATION)
    if parsed < minimum or parsed > maximum:
        raise _err(
            f"{key} must be between {minimum} and {maximum}.",
            code=VALIDATION,
        )
    return parsed


def _require_year(args: dict, key: str) -> int:
    return _require_int(args, key, minimum=2020, maximum=2100)


def _require_department_ids(args: dict) -> list[str]:
    raw = args.get("department_ids")
    if raw is None:
        return []
    if not isinstance(raw, list):
        raise _err("department_ids must be an array.", code=VALIDATION)
    ids = [str(item).strip() for item in raw if str(item).strip()]
    if len(ids) > 200:
        raise _err("department_ids exceeds the limit of 200.", code=VALIDATION)
    return ids


class SiW014WriteStack:
    """PREPARE/ACT implementation for the W014 operational surface."""

    def __init__(self, client: StrategicIndicatorsApiClient | None = None) -> None:
        self._client = client or StrategicIndicatorsApiClient()

    # ------------------------------------------------------- owner reads

    def _list_goals(
        self, authorization: str, *, goal_year: int, active_only: bool
    ) -> list[dict]:
        page = self._client.list_user_indicator_goals(
            authorization=authorization,
            goal_year=goal_year,
            active_only=active_only,
        )
        return [dict(item) for item in (page or {}).get("items") or []]

    def _resolve_indicator_ids(
        self, authorization: str, department_ids: list[str]
    ) -> set[str] | None:
        """Map department_ids → the indicator set the owner will use.

        ``None`` mirrors the owner contract: an empty department filter
        means "every indicator". The owner's
        ``list_indicator_ids_by_departments`` filters ``is_active = TRUE``
        while the admin listing endpoint also returns inactive rows —
        keep only active ones so the sealed digests match byte-for-byte.
        """
        if not department_ids:
            return None
        ids: set[str] = set()
        for department_id in department_ids:
            page = self._client.list_user_admin_department_indicators(
                authorization=authorization,
                department_id=department_id,
            )
            for item in (page or {}).get("items") or []:
                if not item.get("is_active"):
                    continue
                indicator_id = str(item.get("indicator_id") or "").strip()
                if indicator_id:
                    ids.add(indicator_id)
        return ids

    def _cache_status(self, authorization: str) -> dict:
        return self._client.get_user_cache_refresh_status(
            authorization=authorization
        )

    # -------------------------------------------------------------- PREPARE

    def prepare(self, authorization: str, capability: str, args: dict) -> dict:
        args = dict(args or {})
        if capability == CAP_GOAL_BULK_CREATE:
            return self._prepare_bulk_create(authorization, args)
        if capability == CAP_GOAL_DUPLICATE_YEAR:
            return self._prepare_duplicate_year(authorization, args)
        if capability == CAP_GOAL_FILL_MISSING:
            return self._prepare_fill_missing(authorization, args)
        if capability == CAP_CONFIG_IMPORT_APPLY:
            return self._prepare_import_apply(authorization, args)
        if capability == CAP_CACHE_REFRESH:
            return self._prepare_cache_refresh(authorization, args)
        if capability == CAP_CACHE_INVALIDATE:
            return self._prepare_cache_invalidate(authorization, args)
        if capability == CAP_JOB_TREE_LOAD:
            return self._prepare_job_tree_load(authorization, args)
        raise _err(f"Unknown write capability '{capability}'.", code=VALIDATION)

    # --------------------------------------------------- bulk goals family

    def _normalize_bulk_items(self, args: dict) -> list[dict]:
        items = args.get("items")
        if not isinstance(items, list) or not items:
            raise _err("items must be a non-empty array.", code=VALIDATION)
        if len(items) > _MAX_BULK_ITEMS:
            raise _err(
                f"items exceeds the limit of {_MAX_BULK_ITEMS} goals per batch.",
                code=VALIDATION,
            )
        normalized: list[dict] = []
        for index, item in enumerate(items):
            if not isinstance(item, dict):
                raise _err(f"items[{index}] must be an object.", code=VALIDATION)
            _reject_unknown_args(
                f"{CAP_GOAL_BULK_CREATE}.items[{index}]", item, _BULK_ITEM_ARGS
            )
            indicator_id = _require_str(item, "indicator_id")
            goal_label = _require_str(item, "goal_label")
            goal_periodicity = str(item.get("goal_periodicity") or "").strip()
            if goal_periodicity not in _VALID_PERIODICITIES:
                raise _err(
                    f"items[{index}].goal_periodicity must be one of "
                    f"{sorted(_VALID_PERIODICITIES)}.",
                    code=VALIDATION,
                )
            goal_mode = str(item.get("goal_mode") or "standard").strip()
            if goal_mode not in _VALID_GOAL_MODES:
                raise _err(
                    f"items[{index}].goal_mode must be 'standard' or "
                    "'monthly_curve'.",
                    code=VALIDATION,
                )
            branch = str(item.get("goal_scope_branch") or "").strip()
            if branch not in _VALID_SCOPE_BRANCHES:
                raise _err(
                    f"items[{index}].goal_scope_branch must be '', '01' or '02'.",
                    code=VALIDATION,
                )
            monthly_targets = item.get("monthly_targets") or []
            if goal_mode == "monthly_curve":
                if not isinstance(monthly_targets, list) or len(monthly_targets) != 12:
                    raise _err(
                        f"items[{index}].monthly_targets must contain exactly "
                        "12 months for goal_mode=monthly_curve.",
                        code=VALIDATION,
                    )
            elif monthly_targets:
                raise _err(
                    f"items[{index}].monthly_targets is only allowed with "
                    "goal_mode=monthly_curve.",
                    code=VALIDATION,
                )
            for text_key in ("goal_label", "notes"):
                value = item.get(text_key)
                if value is not None and len(str(value)) > _MAX_TEXT_LENGTH:
                    raise _err(
                        f"items[{index}].{text_key} exceeds {_MAX_TEXT_LENGTH} chars.",
                        code=VALIDATION,
                    )
            normalized.append(
                {
                    "indicator_id": indicator_id,
                    "goal_label": goal_label,
                    "goal_value": float(item.get("goal_value") or 0),
                    "goal_periodicity": goal_periodicity,
                    "goal_mode": goal_mode,
                    "goal_scope_branch": branch,
                    "monthly_targets": monthly_targets,
                    "valid_from": item.get("valid_from"),
                    "valid_to": item.get("valid_to"),
                    "notes": item.get("notes"),
                }
            )
        return normalized

    def _scope_version_map(
        self, authorization: str, goal_year: int
    ) -> dict[tuple[str, str], int]:
        """MAX(version) per (indicator_id, goal_scope_branch) — includes
        inactive rows, matching the owner's guarded insert."""
        versions: dict[tuple[str, str], int] = {}
        for row in self._list_goals(
            authorization, goal_year=goal_year, active_only=False
        ):
            key = (
                str(row.get("indicator_id") or ""),
                str(row.get("goal_scope_branch") or ""),
            )
            versions[key] = max(
                versions.get(key, 0), int(row.get("version") or 0)
            )
        return versions

    def _prepare_bulk_create(self, authorization: str, args: dict) -> dict:
        _reject_unknown_args(CAP_GOAL_BULK_CREATE, args, _BULK_CREATE_ARGS)
        goal_year = _require_year(args, "goal_year")
        items = self._normalize_bulk_items(args)

        versions = self._scope_version_map(authorization, goal_year)
        active_rows = self._list_goals(
            authorization, goal_year=goal_year, active_only=True
        )
        active_scopes = {
            (str(row.get("indicator_id") or ""), str(row.get("goal_scope_branch") or ""))
            for row in active_rows
        }

        sealed_items: list[dict] = []
        supersede_count = 0
        for item in items:
            key = (item["indicator_id"], item["goal_scope_branch"])
            sealed = dict(item)
            sealed["expected_max_version"] = versions.get(key, 0)
            if key in active_scopes:
                supersede_count += 1
            sealed_items.append(sealed)

        fp = fingerprint(
            {
                "goal_year": goal_year,
                "scope_versions": sorted(
                    f"{i}|{b}|{v}" for (i, b), v in versions.items()
                ),
            }
        )
        return {
            "resource_type": "si_indicator_goal_bulk",
            "resource_id": f"year:{goal_year}",
            "current_state_fingerprint": fp,
            "exact_change": {
                "body": {"goal_year": goal_year, "items": sealed_items},
            },
            "validation_result": {
                "ready": True,
                "checks": ["args", "items", "scope_versions"],
            },
            "consequential_impact": {
                "scope": f"goal_year={goal_year}",
                "items_total": len(sealed_items),
                "supersedes_active_goals": supersede_count,
                "note": (
                    "Each item inserts a new active goal version; scopes "
                    "with an existing active goal are superseded "
                    "(previous active is deactivated, not deleted). "
                    "Monthly curves are copied atomically per item."
                ),
            },
            "confirmation_requirement": {
                "kind": "confirm_before_act",
                "summary": {
                    "action": "bulk_create_goals",
                    "goal_year": goal_year,
                    "items_total": len(sealed_items),
                    "supersedes_active_goals": supersede_count,
                },
            },
            "expected_postcondition": {
                "goal_year": goal_year,
                "items": [
                    {
                        "indicator_id": item["indicator_id"],
                        "goal_scope_branch": item["goal_scope_branch"],
                        "goal_label": item["goal_label"],
                    }
                    for item in sealed_items
                ],
            },
        }

    def _prepare_duplicate_year(self, authorization: str, args: dict) -> dict:
        _reject_unknown_args(
            CAP_GOAL_DUPLICATE_YEAR, args, _DUPLICATE_YEAR_ARGS
        )
        source_year = _require_year(args, "source_year")
        target_year = _require_year(args, "target_year")
        if source_year == target_year:
            raise _err(
                "source_year and target_year must differ.", code=VALIDATION
            )
        department_ids = _require_department_ids(args)
        overwrite_existing = bool(args.get("overwrite_existing", False))

        indicator_ids = self._resolve_indicator_ids(authorization, department_ids)
        source_rows = self._list_goals(
            authorization, goal_year=source_year, active_only=True
        )
        if indicator_ids is not None:
            source_rows = [
                row for row in source_rows if row.get("indicator_id") in indicator_ids
            ]
        existing_rows = self._list_goals(
            authorization, goal_year=target_year, active_only=True
        )
        existing_keys = {
            (row.get("indicator_id"), row.get("goal_scope_branch") or "")
            for row in existing_rows
        }

        source_digest = _goals_rows_digest(source_rows, _BULK_SOURCE_DIGEST_FIELDS)
        existing_digest = _goals_rows_digest(
            existing_rows, _BULK_EXISTING_DIGEST_FIELDS
        )

        would_skip = sum(
            1
            for row in source_rows
            if (row.get("indicator_id"), row.get("goal_scope_branch") or "")
            in existing_keys
            and not overwrite_existing
        )
        would_overwrite = sum(
            1
            for row in source_rows
            if (row.get("indicator_id"), row.get("goal_scope_branch") or "")
            in existing_keys
            and overwrite_existing
        )
        would_create = len(source_rows) - would_skip - would_overwrite

        fp = fingerprint(
            {
                "source_digest": source_digest,
                "existing_digest": existing_digest,
                "source_year": source_year,
                "target_year": target_year,
            }
        )
        return {
            "resource_type": "si_indicator_goal_bulk",
            "resource_id": f"{source_year}->{target_year}",
            "current_state_fingerprint": fp,
            "exact_change": {
                "body": {
                    "source_year": source_year,
                    "target_year": target_year,
                    "department_ids": department_ids,
                    "overwrite_existing": overwrite_existing,
                },
                "expected_source_digest": source_digest,
                "expected_existing_digest": existing_digest,
                "source_scopes": sorted(
                    f"{row.get('indicator_id')}|{row.get('goal_scope_branch') or ''}"
                    for row in source_rows
                ),
            },
            "validation_result": {
                "ready": True,
                "checks": ["args", "source_digest", "existing_digest"],
            },
            "consequential_impact": {
                "scope": f"{source_year}→{target_year}",
                "source_goals": len(source_rows),
                "creates": would_create,
                "overwrites": would_overwrite,
                "preserved_conflicts": would_skip,
                "overwrite_existing": overwrite_existing,
                "note": (
                    "Creates one new active version per source goal in the "
                    "target year, copying monthly curves. With "
                    "overwrite_existing the current active target goal is "
                    "deactivated (not deleted)."
                ),
            },
            "confirmation_requirement": {
                "kind": "confirm_before_act",
                "summary": {
                    "action": "duplicate_goals_year",
                    "source_year": source_year,
                    "target_year": target_year,
                    "source_goals": len(source_rows),
                    "creates": would_create,
                    "overwrites": would_overwrite,
                    "preserved_conflicts": would_skip,
                    "overwrite_existing": overwrite_existing,
                },
            },
            "expected_postcondition": {
                "goal_year": target_year,
                "must_have_active_scopes": sorted(
                    f"{row.get('indicator_id')}|{row.get('goal_scope_branch') or ''}"
                    for row in source_rows
                ),
            },
        }

    def _prepare_fill_missing(self, authorization: str, args: dict) -> dict:
        _reject_unknown_args(CAP_GOAL_FILL_MISSING, args, _FILL_MISSING_ARGS)
        goal_year = _require_year(args, "goal_year")
        department_ids = _require_department_ids(args)
        copy_from_year = args.get("copy_from_year")
        if copy_from_year is not None:
            copy_from_year = _require_year(args, "copy_from_year")

        indicator_ids = self._resolve_indicator_ids(authorization, department_ids)

        existing_rows = self._list_goals(
            authorization, goal_year=goal_year, active_only=True
        )
        if indicator_ids is not None:
            existing_rows = [
                row
                for row in existing_rows
                if row.get("indicator_id") in indicator_ids
            ]

        # Reproduce the owner DISTINCT ON (indicator_id) reduce: newest
        # active source row per indicator by (version, updated_at).
        source_rows: list[dict] = []
        if copy_from_year is not None:
            candidates = self._list_goals(
                authorization, goal_year=copy_from_year, active_only=True
            )
            if indicator_ids is not None:
                candidates = [
                    row
                    for row in candidates
                    if row.get("indicator_id") in indicator_ids
                ]
            best: dict[str, dict] = {}
            for row in candidates:
                indicator_id = row.get("indicator_id")
                key = (
                    int(row.get("version") or 0),
                    str(row.get("updated_at") or ""),
                )
                current = best.get(indicator_id)
                if current is None or key > (
                    int(current.get("version") or 0),
                    str(current.get("updated_at") or ""),
                ):
                    best[indicator_id] = row
            source_rows = list(best.values())

        target_digest = _goals_rows_digest(
            existing_rows, _BULK_EXISTING_DIGEST_FIELDS
        )
        # The owner digest for fill_missing uses goal_scope_branch="" — the
        # source query does not select that column.
        source_digest = _goals_rows_digest(
            [
                {
                    "indicator_id": row.get("indicator_id"),
                    "goal_scope_branch": "",
                    "goal_label": row.get("goal_label"),
                    "goal_value": row.get("goal_value"),
                    "goal_periodicity": row.get("goal_periodicity"),
                    "goal_mode": row.get("goal_mode"),
                }
                for row in source_rows
            ],
            _BULK_SOURCE_DIGEST_FIELDS,
        )

        existing_indicator_ids = {row.get("indicator_id") for row in existing_rows}
        would_create = sum(
            1
            for row in source_rows
            if row.get("indicator_id") not in existing_indicator_ids
        )

        fp = fingerprint(
            {
                "target_digest": target_digest,
                "source_digest": source_digest,
                "goal_year": goal_year,
            }
        )
        return {
            "resource_type": "si_indicator_goal_bulk",
            "resource_id": f"fill-missing:{goal_year}",
            "current_state_fingerprint": fp,
            "exact_change": {
                "body": {
                    "goal_year": goal_year,
                    "department_ids": department_ids,
                    "copy_from_year": copy_from_year,
                },
                "expected_target_digest": target_digest,
                "expected_source_digest": source_digest,
            },
            "validation_result": {
                "ready": True,
                "checks": ["args", "target_digest", "source_digest"],
            },
            "consequential_impact": {
                "scope": f"goal_year={goal_year}",
                "creates": would_create,
                "source_year": copy_from_year,
                "note": (
                    "Creates a goal only for indicators that have none in "
                    "the target year, copying the newest active goal from "
                    "copy_from_year (including monthly curves). Existing "
                    "goals are never touched."
                ),
            },
            "confirmation_requirement": {
                "kind": "confirm_before_act",
                "summary": {
                    "action": "fill_missing_goals",
                    "goal_year": goal_year,
                    "copy_from_year": copy_from_year,
                    "creates": would_create,
                },
            },
            "expected_postcondition": {
                "goal_year": goal_year,
                "must_have_active_indicator_ids": sorted(
                    {
                        row.get("indicator_id")
                        for row in source_rows
                        if row.get("indicator_id") not in existing_indicator_ids
                    }
                ),
            },
        }

    # ---------------------------------------------------------- import family

    def _prepare_import_apply(self, authorization: str, args: dict) -> dict:
        _reject_unknown_args(CAP_CONFIG_IMPORT_APPLY, args, _IMPORT_APPLY_ARGS)
        bundle = args.get("bundle")
        if not isinstance(bundle, dict):
            raise _err("bundle must be an object.", code=VALIDATION)
        # Explicit guard: a smuggled mode=replace inside the bundle is
        # still a destructive W015-class variant — never forwarded.
        requested_mode = str(bundle.get("mode") or "").strip()
        if requested_mode and requested_mode != "merge":
            raise _err(
                "Only merge imports are exposed. mode='replace' is a "
                "destructive variant reserved for a future governed wave.",
                code=VALIDATION,
            )
        include_goals = bool(args.get("include_goals", True))
        bundle = dict(bundle)
        bundle["mode"] = "merge"
        bundle["include_goals"] = include_goals

        from app.application.external_capabilities.governed_writes.proposal import (
            canonical_json,
        )

        if len(canonical_json(bundle).encode("utf-8")) > _MAX_BUNDLE_BYTES:
            raise _err(
                f"bundle exceeds the {_MAX_BUNDLE_BYTES}-byte limit.",
                code=VALIDATION,
            )

        preview = self._client.preview_user_admin_config_import(
            authorization=authorization,
            body=bundle,
        )
        valid = bool((preview or {}).get("valid"))
        errors = (preview or {}).get("errors") or []
        current_counts = (preview or {}).get("current_counts") or {}
        planned = (preview or {}).get("planned") or {}

        fp = fingerprint(
            {
                "current_counts": current_counts,
                "bundle_sha256": hashlib.sha256(
                    canonical_json(bundle).encode("utf-8")
                ).hexdigest(),
            }
        )
        return {
            "resource_type": "si_admin_config",
            "resource_id": "catalog",
            "current_state_fingerprint": fp,
            "exact_change": {
                "body": bundle,
                "expected_counts": current_counts,
            },
            "validation_result": {
                "ready": valid,
                "checks": ["args", "bundle_preview"],
                "errors": [str(item) for item in errors][:20],
            },
            "consequential_impact": {
                "mode": "merge",
                "current_counts": current_counts,
                "planned": planned,
                "note": (
                    "Merge upserts departments, indicators and goals from "
                    "the bundle — it never deletes rows absent from the "
                    "file. The destructive replace mode is not exposed."
                ),
            },
            "confirmation_requirement": {
                "kind": "confirm_before_act",
                "summary": {
                    "action": "import_config_merge",
                    "include_goals": include_goals,
                    "current_counts": current_counts,
                    "planned": planned,
                },
            },
            "expected_postcondition": {
                "expected_counts": {
                    table: int(current_counts.get(table) or 0)
                    + int((planned.get(table) or {}).get("insert") or 0)
                    for table in (
                        "departments",
                        "department_indicators",
                        "indicator_goals",
                    )
                },
                "include_goals": include_goals,
            },
        }

    # ----------------------------------------------------------- cache family

    def _prepare_cache_refresh(self, authorization: str, args: dict) -> dict:
        _reject_unknown_args(CAP_CACHE_REFRESH, args, _CACHE_REFRESH_ARGS)
        competence = args.get("competence")
        if competence is not None:
            competence = _require_str(args, "competence")
        trends_months = args.get("trends_months")
        if trends_months is not None:
            trends_months = _require_int(
                args, "trends_months", minimum=1, maximum=24
            )

        status = self._cache_status(authorization)
        running = bool(status.get("running"))
        fp = fingerprint(
            {
                "running": running,
                "last_started_at": status.get("last_started_at"),
                "last_completed_at": status.get("last_completed_at"),
            }
        )
        body: dict[str, Any] = {}
        if competence is not None:
            body["competence"] = competence
        if trends_months is not None:
            body["trends_months"] = trends_months
        return {
            "resource_type": "si_cache",
            "resource_id": "period_scores",
            "current_state_fingerprint": fp,
            "exact_change": {
                "body": body,
                "previous_last_started_at": status.get("last_started_at"),
            },
            "validation_result": {"ready": True, "checks": ["args", "status"]},
            "consequential_impact": {
                "already_running": running,
                "note": (
                    "Schedules a full materialized refresh of "
                    "period_scores (TOTVS recompute). Current data stays "
                    "servable until the new clean version lands; a second "
                    "request while one is running is a no-op."
                ),
            },
            "confirmation_requirement": {
                "kind": "confirm_before_act",
                "summary": {
                    "action": "cache_refresh",
                    "competence": competence,
                    "trends_months": trends_months,
                    "already_running": running,
                },
            },
            "expected_postcondition": {
                "previous_last_started_at": status.get("last_started_at"),
            },
        }

    def _prepare_cache_invalidate(self, authorization: str, args: dict) -> dict:
        _reject_unknown_args(
            CAP_CACHE_INVALIDATE, args, _CACHE_INVALIDATE_ARGS
        )
        status = self._cache_status(authorization)
        fp = fingerprint(
            {
                "running": bool(status.get("running")),
                "last_started_at": status.get("last_started_at"),
                "last_completed_at": status.get("last_completed_at"),
            }
        )
        return {
            "resource_type": "si_cache",
            "resource_id": "period_scores",
            "current_state_fingerprint": fp,
            "exact_change": {
                "previous_last_started_at": status.get("last_started_at"),
            },
            "validation_result": {"ready": True, "checks": ["status"]},
            "consequential_impact": {
                "already_running": bool(status.get("running")),
                "note": (
                    "Wipes materialized period_scores and calculation "
                    "snapshots, clears in-process caches and schedules a "
                    "recompute. Until the refresh lands, dashboards may "
                    "serve stale-then-recomputed data (availability is "
                    "preserved by the versioned-read contract)."
                ),
            },
            "confirmation_requirement": {
                "kind": "confirm_before_act",
                "summary": {
                    "action": "cache_invalidate",
                    "already_running": bool(status.get("running")),
                },
            },
            "expected_postcondition": {
                "previous_last_started_at": status.get("last_started_at"),
            },
        }

    # ------------------------------------------------------------ job family

    def _prepare_job_tree_load(self, authorization: str, args: dict) -> dict:
        _reject_unknown_args(CAP_JOB_TREE_LOAD, args, _JOB_TREE_LOAD_ARGS)
        view_mode = str(args.get("view_mode") or "consolidated").strip()
        if view_mode not in _VALID_VIEW_MODES:
            raise _err(
                "view_mode must be 'consolidated' or 'per_unit'.",
                code=VALIDATION,
            )
        months = _require_int(args, "months", minimum=2, maximum=12)
        body: dict[str, Any] = {"view_mode": view_mode, "months": months}
        for key in ("branch", "competence", "start_date", "end_date"):
            value = args.get(key)
            if value is not None:
                value = str(value).strip()
                if len(value) > 64:
                    raise _err(f"{key} exceeds 64 chars.", code=VALIDATION)
                body[key] = value
        # No bindable owner state — admission (per-actor/global caps) is
        # enforced by the owner job registry at dispatch time.
        fp = fingerprint({"capability": CAP_JOB_TREE_LOAD, "body": body})
        return {
            "resource_type": "si_tree_load_job",
            "resource_id": None,
            "current_state_fingerprint": fp,
            "exact_change": {"body": body},
            "validation_result": {"ready": True, "checks": ["args"]},
            "consequential_impact": {
                "note": (
                    "Dispatches an asynchronous tree-load job (snapshot + "
                    "trends). 'job accepted' is not 'job completed' — poll "
                    "the job status read until it reaches succeeded."
                ),
            },
            "confirmation_requirement": {
                "kind": "confirm_before_act",
                "summary": {"action": "dispatch_tree_load_job", **body},
            },
            "expected_postcondition": {"job_registered": True},
        }

    # ------------------------------------------------------- fingerprint re-read

    def recompute_fingerprint(
        self, authorization: str, capability: str, exact_change: dict
    ) -> str:
        body = (exact_change or {}).get("body") or {}
        if capability == CAP_GOAL_BULK_CREATE:
            versions = self._scope_version_map(
                authorization, int(body.get("goal_year") or 0)
            )
            return fingerprint(
                {
                    "goal_year": body.get("goal_year"),
                    "scope_versions": sorted(
                        f"{i}|{b}|{v}" for (i, b), v in versions.items()
                    ),
                }
            )
        if capability == CAP_GOAL_DUPLICATE_YEAR:
            indicator_ids = self._resolve_indicator_ids(
                authorization, body.get("department_ids") or []
            )
            source_rows = self._list_goals(
                authorization,
                goal_year=int(body.get("source_year") or 0),
                active_only=True,
            )
            if indicator_ids is not None:
                source_rows = [
                    row
                    for row in source_rows
                    if row.get("indicator_id") in indicator_ids
                ]
            existing_rows = self._list_goals(
                authorization,
                goal_year=int(body.get("target_year") or 0),
                active_only=True,
            )
            return fingerprint(
                {
                    "source_digest": _goals_rows_digest(
                        source_rows, _BULK_SOURCE_DIGEST_FIELDS
                    ),
                    "existing_digest": _goals_rows_digest(
                        existing_rows, _BULK_EXISTING_DIGEST_FIELDS
                    ),
                    "source_year": body.get("source_year"),
                    "target_year": body.get("target_year"),
                }
            )
        if capability == CAP_GOAL_FILL_MISSING:
            indicator_ids = self._resolve_indicator_ids(
                authorization, body.get("department_ids") or []
            )
            existing_rows = self._list_goals(
                authorization,
                goal_year=int(body.get("goal_year") or 0),
                active_only=True,
            )
            if indicator_ids is not None:
                existing_rows = [
                    row
                    for row in existing_rows
                    if row.get("indicator_id") in indicator_ids
                ]
            copy_from_year = body.get("copy_from_year")
            source_rows: list[dict] = []
            if copy_from_year is not None:
                candidates = self._list_goals(
                    authorization,
                    goal_year=int(copy_from_year),
                    active_only=True,
                )
                if indicator_ids is not None:
                    candidates = [
                        row
                        for row in candidates
                        if row.get("indicator_id") in indicator_ids
                    ]
                best: dict[str, dict] = {}
                for row in candidates:
                    key = (
                        int(row.get("version") or 0),
                        str(row.get("updated_at") or ""),
                    )
                    current = best.get(row.get("indicator_id"))
                    if current is None or key > (
                        int(current.get("version") or 0),
                        str(current.get("updated_at") or ""),
                    ):
                        best[row.get("indicator_id")] = row
                source_rows = list(best.values())
            return fingerprint(
                {
                    "target_digest": _goals_rows_digest(
                        existing_rows, _BULK_EXISTING_DIGEST_FIELDS
                    ),
                    "source_digest": _goals_rows_digest(
                        [
                            {
                                "indicator_id": row.get("indicator_id"),
                                "goal_scope_branch": "",
                                "goal_label": row.get("goal_label"),
                                "goal_value": row.get("goal_value"),
                                "goal_periodicity": row.get("goal_periodicity"),
                                "goal_mode": row.get("goal_mode"),
                            }
                            for row in source_rows
                        ],
                        _BULK_SOURCE_DIGEST_FIELDS,
                    ),
                    "goal_year": body.get("goal_year"),
                }
            )
        if capability == CAP_CONFIG_IMPORT_APPLY:
            preview = self._client.preview_user_admin_config_import(
                authorization=authorization, body=body
            )
            from app.application.external_capabilities.governed_writes.proposal import (
                canonical_json,
            )

            return fingerprint(
                {
                    "current_counts": (preview or {}).get("current_counts") or {},
                    "bundle_sha256": hashlib.sha256(
                        canonical_json(body).encode("utf-8")
                    ).hexdigest(),
                }
            )
        if capability in (CAP_CACHE_REFRESH, CAP_CACHE_INVALIDATE):
            status = self._cache_status(authorization)
            return fingerprint(
                {
                    "running": bool(status.get("running")),
                    "last_started_at": status.get("last_started_at"),
                    "last_completed_at": status.get("last_completed_at"),
                }
            )
        if capability == CAP_JOB_TREE_LOAD:
            return fingerprint({"capability": capability, "body": body})
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
        audit_kwargs = {
            "write_origin": "davi-mcp",
            "correlation_id": correlation_id,
        }
        body = dict((exact_change or {}).get("body") or {})
        if capability == CAP_GOAL_BULK_CREATE:
            return self._client.bulk_create_user_indicator_goals(
                authorization=authorization,
                body=body,
                **audit_kwargs,
            )
        if capability == CAP_GOAL_DUPLICATE_YEAR:
            return self._client.duplicate_user_indicator_goals_year(
                authorization=authorization,
                body=body,
                expected_source_digest=exact_change.get("expected_source_digest"),
                expected_existing_digest=exact_change.get(
                    "expected_existing_digest"
                ),
                **audit_kwargs,
            )
        if capability == CAP_GOAL_FILL_MISSING:
            return self._client.fill_missing_user_indicator_goals(
                authorization=authorization,
                body=body,
                expected_target_digest=exact_change.get("expected_target_digest"),
                expected_source_digest=exact_change.get("expected_source_digest"),
                **audit_kwargs,
            )
        if capability == CAP_CONFIG_IMPORT_APPLY:
            # Final client-side guard: the sealed body is what was previewed.
            if str(body.get("mode") or "") != "merge":
                raise _err(
                    "Sealed import payload is not mode='merge'; refusing ACT.",
                    code=VALIDATION,
                )
            return self._client.apply_user_admin_config_import(
                authorization=authorization,
                body=body,
                expected_counts=exact_change.get("expected_counts") or {},
                **audit_kwargs,
            )
        if capability == CAP_CACHE_REFRESH:
            return self._client.refresh_user_cache(
                authorization=authorization,
                body=body or None,
            )
        if capability == CAP_CACHE_INVALIDATE:
            return self._client.invalidate_user_cache(
                authorization=authorization,
            )
        if capability == CAP_JOB_TREE_LOAD:
            return self._client.create_user_tree_load_job(
                authorization=authorization,
                body=body,
            )
        raise _err(
            f"ACT not implemented for '{capability}'.",
            code=INTERNAL,
            status_code=500,
        )

    # ------------------------------------------------------------ verify

    def _goal_index(
        self, authorization: str, goal_year: int
    ) -> dict[tuple[str, str], list[dict]]:
        index: dict[tuple[str, str], list[dict]] = {}
        for row in self._list_goals(
            authorization, goal_year=goal_year, active_only=True
        ):
            key = (
                str(row.get("indicator_id") or ""),
                str(row.get("goal_scope_branch") or ""),
            )
            index.setdefault(key, []).append(row)
        return index

    def verify(
        self,
        authorization: str,
        capability: str,
        exact_change: dict,
        expected_postcondition: dict,
        write_result: dict[str, Any] | None,
    ) -> dict[str, Any]:
        """Authoritative read-back against the owner API."""
        if capability == CAP_GOAL_BULK_CREATE:
            goal_year = int(expected_postcondition.get("goal_year") or 0)
            index = self._goal_index(authorization, goal_year)
            missing: list[str] = []
            for item in expected_postcondition.get("items") or []:
                key = (
                    str(item.get("indicator_id") or ""),
                    str(item.get("goal_scope_branch") or ""),
                )
                rows = index.get(key) or []
                if not any(
                    str(row.get("goal_label") or "") == str(item.get("goal_label") or "")
                    for row in rows
                ):
                    missing.append("|".join(key))
            if missing:
                raise GovernedWriteError(
                    "Postcondition failed: expected active goals not found "
                    f"after bulk create ({missing[:5]}).",
                    code=OUTCOME_VERIFICATION_FAILED,
                    status_code=409,
                )
            created = (write_result or {}).get("items") or []
            return {
                "bulk_create": {
                    "goal_year": goal_year,
                    "created_count": len(created),
                }
            }

        if capability == CAP_GOAL_DUPLICATE_YEAR:
            goal_year = int(expected_postcondition.get("goal_year") or 0)
            index = self._goal_index(authorization, goal_year)
            missing = [
                scope
                for scope in expected_postcondition.get("must_have_active_scopes")
                or []
                if tuple(scope.split("|")) not in index
            ]
            if missing:
                raise GovernedWriteError(
                    "Postcondition failed: duplicated scopes missing in "
                    f"target year ({missing[:5]}).",
                    code=OUTCOME_VERIFICATION_FAILED,
                    status_code=409,
                )
            created = (write_result or {}).get("items") or []
            return {
                "duplicate_year": {
                    "goal_year": goal_year,
                    "created_count": len(created),
                }
            }

        if capability == CAP_GOAL_FILL_MISSING:
            goal_year = int(expected_postcondition.get("goal_year") or 0)
            index = self._goal_index(authorization, goal_year)
            present_indicator_ids = {key[0] for key in index}
            missing = [
                indicator_id
                for indicator_id in expected_postcondition.get(
                    "must_have_active_indicator_ids"
                )
                or []
                if indicator_id not in present_indicator_ids
            ]
            if missing:
                raise GovernedWriteError(
                    "Postcondition failed: filled goals missing in target "
                    f"year ({missing[:5]}).",
                    code=OUTCOME_VERIFICATION_FAILED,
                    status_code=409,
                )
            created = (write_result or {}).get("items") or []
            return {
                "fill_missing": {
                    "goal_year": goal_year,
                    "created_count": len(created),
                }
            }

        if capability == CAP_CONFIG_IMPORT_APPLY:
            bundle = self._client.export_user_admin_config(
                authorization=authorization
            )
            expected = expected_postcondition.get("expected_counts") or {}
            actual = {
                "departments": len((bundle or {}).get("departments") or []),
                "department_indicators": len(
                    (bundle or {}).get("department_indicators") or []
                ),
                "indicator_goals": len(
                    (bundle or {}).get("indicator_goals") or []
                ),
            }
            mismatched = {
                table: {"expected": expected.get(table), "actual": got}
                for table, got in actual.items()
                if expected.get(table) is not None and int(expected[table]) != got
            }
            if mismatched:
                raise GovernedWriteError(
                    "Postcondition failed: catalog counts diverge from the "
                    f"approved merge plan ({mismatched}).",
                    code=OUTCOME_VERIFICATION_FAILED,
                    status_code=409,
                )
            return {"import": {"mode": "merge", "counts": actual}}

        if capability in (CAP_CACHE_REFRESH, CAP_CACHE_INVALIDATE):
            status = self._cache_status(authorization)
            previous = expected_postcondition.get("previous_last_started_at")
            started = status.get("last_started_at")
            if not (
                status.get("running")
                or (started and started != previous)
                or (write_result or {}).get("status")
                in ("accepted", "already_running", "ok")
            ):
                raise GovernedWriteError(
                    "Postcondition failed: refresh status shows no evidence "
                    "the request was accepted.",
                    code=OUTCOME_VERIFICATION_FAILED,
                    status_code=409,
                )
            return {
                "cache": {
                    "running": bool(status.get("running")),
                    "last_started_at": started,
                    "last_completed_at": status.get("last_completed_at"),
                    "result": (write_result or {}).get("status"),
                }
            }

        if capability == CAP_JOB_TREE_LOAD:
            job_id = (write_result or {}).get("job_id")
            if not job_id:
                raise GovernedWriteError(
                    "Postcondition failed: dispatch returned no job_id.",
                    code=OUTCOME_VERIFICATION_FAILED,
                    status_code=409,
                )
            status = self._client.get_user_job_status(
                authorization=authorization, job_id=str(job_id)
            )
            state = str((status or {}).get("state") or "")
            if state not in ("queued", "running", "succeeded", "failed"):
                raise GovernedWriteError(
                    "Postcondition failed: job not tracked after dispatch.",
                    code=OUTCOME_VERIFICATION_FAILED,
                    status_code=409,
                )
            return {
                "job": {
                    "job_id": str(job_id),
                    "state": state,
                    "phase": (status or {}).get("phase"),
                    "progress_pct": (status or {}).get("progress_pct"),
                    "note": (
                        "Job dispatched — track completion via the job "
                        "status read; 'accepted' is not 'completed'."
                    ),
                }
            }

        raise _err(
            f"Verify not implemented for '{capability}'.",
            code=INTERNAL,
            status_code=500,
        )
