"""Qualidade, explain, cache e telemetria seguros do M DELPI v1."""

from __future__ import annotations

import hashlib
import json
import logging
import math
import time
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from typing import Any, Mapping

from tv_app.application.services.branch_policy_service import resolve_branch_access_scope
from tv_app.application.services.data.m_query.m_function_registry import get_function_registry
from tv_app.application.services.tv_dashboard_content_service import m_query_setting
from tv_app.domain.data_query.transform_plan import CompiledMPlanStep, TransformPlan
from tv_app.infrastructure.cache.bounded_ttl_lru_cache import BoundedTtlLruCache

_logger = logging.getLogger("tv_dashboard.m_query")


def _stable_hash(value: Any) -> str:
    encoded = json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        default=str,
    ).encode("utf-8")
    return f"sha256:{hashlib.sha256(encoded).hexdigest()}"


_compile_cache: BoundedTtlLruCache[Any] = BoundedTtlLruCache(
    ttl_seconds=float(m_query_setting("compileCacheTtlSeconds", 300)),
    max_entries=int(m_query_setting("compileCacheMaxEntries", 256)),
)
_preview_cache: BoundedTtlLruCache[dict[str, Any]] = BoundedTtlLruCache(
    ttl_seconds=float(m_query_setting("previewCacheTtlSeconds", 30)),
    max_entries=int(m_query_setting("previewCacheMaxEntries", 128)),
)


def compile_cache_key(request: Any) -> str:
    registry = get_function_registry()
    return _stable_hash(
        {
            "profile": request.profile,
            "registryVersion": registry.version,
            "scriptHash": _stable_hash(request.script),
            "sourceSchema": request.source_schema,
            "queryBindings": request.query_bindings,
            "targetStepName": request.target_step_name,
            "culture": request.culture,
        }
    )


def get_cached_compile(key: str) -> Any | None:
    if not bool(m_query_setting("compileCacheEnabled", False)):
        return None
    return _compile_cache.get(key)


def compile_cache_enabled() -> bool:
    return bool(m_query_setting("compileCacheEnabled", False))


def set_cached_compile(key: str, value: Any) -> None:
    if bool(m_query_setting("compileCacheEnabled", False)):
        _compile_cache.set(key, value)


def _principal_fingerprint(user: Any | None, authorization: str | None) -> str:
    identity = next(
        (
            str(value).strip()
            for value in (
                getattr(user, "id", None),
                getattr(user, "sub", None),
                getattr(user, "user_id", None),
                getattr(user, "email", None),
                getattr(user, "username", None),
            )
            if value is not None and str(value).strip()
        ),
        "",
    )
    permissions = sorted(
        str(item).strip()
        for item in (getattr(user, "permissions", None) or ())
        if str(item).strip()
    )
    credential_digest = (
        _stable_hash(authorization)
        if authorization and not identity
        else ""
    )
    return _stable_hash(
        {
            "identity": identity,
            "permissions": permissions,
            "superadmin": bool(getattr(user, "is_superadmin", False)),
            "branchScope": resolve_branch_access_scope(user).meta(),
            "credentialDigest": credential_digest,
        }
    )


def preview_cache_key(
    *,
    block: Mapping[str, Any],
    native_config: Mapping[str, Any],
    playlist_defaults: Mapping[str, Any] | None,
    target_step_name: str | None,
    preview_options: Mapping[str, Any] | None,
    user: Any | None,
    authorization: str | None,
) -> tuple[str, str]:
    transform = block.get("dataTransform")
    script = transform.get("script") if isinstance(transform, Mapping) else ""
    sources: list[dict[str, Any]] = []
    candidates = native_config.get("blocks")
    source_candidates = [block, *(candidates if isinstance(candidates, list) else [])]
    seen_source_ids: set[str] = set()
    for item in source_candidates:
        if not isinstance(item, Mapping):
            continue
        source_id = str(item.get("id") or "")
        if source_id and source_id in seen_source_ids:
            continue
        if source_id:
            seen_source_ids.add(source_id)
        binding = item.get("dataBinding")
        item_transform = item.get("dataTransform")
        sources.append(
            {
                "sourceId": source_id,
                "operationId": binding.get("operationId") if isinstance(binding, Mapping) else None,
                "params": binding.get("params") if isinstance(binding, Mapping) else None,
                "revision": item.get("revision") or item.get("updatedAt"),
                "scriptHash": _stable_hash(item_transform.get("script", ""))
                if isinstance(item_transform, Mapping)
                else None,
            }
        )
    principal = _principal_fingerprint(user, authorization)
    key = _stable_hash(
        {
            "profile": (
                transform.get("language", "m-delpi-v1")
                if isinstance(transform, Mapping)
                else "m-delpi-v1"
            ),
            "registryVersion": get_function_registry().version,
            "scriptHash": _stable_hash(script or ""),
            "sourceSchema": block.get("sourceSchema"),
            "targetStepName": target_step_name,
            "culture": m_query_setting("defaultCulture", "pt-BR"),
            "principalFingerprint": principal,
            "branchAndParams": {
                "playlistDefaults": playlist_defaults or {},
                "dataFilters": native_config.get("dataFilters") or {},
            },
            "sources": sources,
            "revisions": {
                "nativeConfig": native_config.get("revision")
                or native_config.get("updatedAt"),
                "block": block.get("revision") or block.get("updatedAt"),
            },
            "previewOptions": preview_options or {},
        }
    )
    return key, principal


def get_cached_preview(key: str) -> dict[str, Any] | None:
    if not bool(m_query_setting("previewCacheEnabled", False)):
        return None
    return _preview_cache.get(key)


def preview_cache_enabled() -> bool:
    return bool(m_query_setting("previewCacheEnabled", False))


def set_cached_preview(key: str, value: dict[str, Any]) -> None:
    if bool(m_query_setting("previewCacheEnabled", False)):
        _preview_cache.set(key, value)


def reset_phase7_caches() -> None:
    _compile_cache.clear()
    _preview_cache.clear()


def cache_stats() -> dict[str, Any]:
    return {
        "compile": _compile_cache.stats(),
        "preview": _preview_cache.stats(),
    }


def explain_transform_plan(plan: TransformPlan | None) -> dict[str, Any]:
    if plan is None:
        return {"version": 1, "output": None, "steps": [], "warnings": []}
    expensive = {
        "Table.Sort",
        "Table.Group",
        "Table.Pivot",
        "Table.NestedJoin",
        "Table.ExpandTableColumn",
        "Table.Combine",
        "Table.Distinct",
        "Table.Transpose",
    }
    steps = []
    warnings = []
    for index, step in enumerate(plan.steps):
        operation = (
            step.function_name
            if isinstance(step, CompiledMPlanStep)
            else str(step.operation)
        )
        cost = "potentially_expensive" if operation in expensive else "bounded"
        if cost == "potentially_expensive":
            warnings.append(
                {
                    "code": "m.expensive_operation",
                    "stepName": step.name,
                    "operation": operation,
                }
            )
        steps.append(
            {
                "index": index,
                "name": step.name,
                "input": step.input_name,
                "operation": operation,
                "cost": cost,
                "cancelable": True,
            }
        )
    return {
        "version": 1,
        "profile": plan.profile,
        "output": plan.output,
        "referencedQueries": list(plan.referenced_queries),
        "steps": steps,
        "warnings": warnings,
    }


def _is_error(value: Any) -> bool:
    return isinstance(value, Mapping) and isinstance(value.get("error"), Mapping)


def _is_empty(value: Any) -> bool:
    return value is None or (isinstance(value, str) and not value.strip())


def _safe_ordered(values: list[Any]) -> bool:
    if not values:
        return False
    kinds = {type(value) for value in values}
    if any(isinstance(value, float) and not math.isfinite(value) for value in values):
        return False
    return len(kinds) == 1 and next(iter(kinds)) in {
        int,
        float,
        str,
        date,
        datetime,
        timedelta,
    }


def profile_table(
    table: Mapping[str, Any],
    *,
    requested: bool,
    deadline_ms: int | None = None,
) -> dict[str, Any] | None:
    """Perfil opt-in amostrado; não produz top-values nem serializa linhas."""

    if not requested or not bool(m_query_setting("profilingEnabled", False)):
        return None
    sample_limit = int(m_query_setting("profileSampleRows", 500))
    column_limit = int(m_query_setting("profileMaxColumns", 100))
    timeout_ms = min(
        max(1, int(deadline_ms or m_query_setting("profileTimeoutMs", 750))),
        int(m_query_setting("profileTimeoutMs", 750)),
    )
    deadline = time.monotonic() + timeout_ms / 1000
    rows = [item for item in (table.get("rows") or []) if isinstance(item, Mapping)]
    columns = [str(item) for item in (table.get("columns") or [])][:column_limit]
    sample = rows[:sample_limit]
    profiles: list[dict[str, Any]] = []
    for column in columns:
        if time.monotonic() > deadline:
            raise TimeoutError("m.profile_timeout")
        values = [row.get(column) for row in sample]
        empty = sum(1 for value in values if _is_empty(value))
        errors = sum(1 for value in values if _is_error(value))
        valid_values = [
            value for value in values if not _is_empty(value) and not _is_error(value)
        ]
        fingerprints = {
            _stable_hash(value)
            for value in valid_values
            if not (isinstance(value, float) and not math.isfinite(value))
        }
        ordered = _safe_ordered(valid_values)
        profiles.append(
            {
                "key": column,
                "quality": {
                    "valid": len(valid_values),
                    "empty": empty,
                    "error": errors,
                },
                "distribution": {
                    "distinct": len(fingerprints),
                    "repeated": max(0, len(valid_values) - len(fingerprints)),
                    "distinctRatio": (
                        round(len(fingerprints) / len(valid_values), 4)
                        if valid_values
                        else 0
                    ),
                },
                "min": min(valid_values) if ordered else None,
                "max": max(valid_values) if ordered else None,
                "minMaxAvailable": ordered,
            }
        )
    return {
        "sampled": len(sample) < len(rows),
        "sampleRows": len(sample),
        "availableRows": len(rows),
        "columns": profiles,
    }


@dataclass(frozen=True, slots=True)
class SafeTelemetry:
    code: str
    duration_ms: int
    cache: str
    rows: int = 0
    columns: int = 0
    errors: int = 0
    artifact_hash: str = ""

    def emit(self) -> None:
        if not bool(m_query_setting("phase7TelemetryEnabled", False)):
            return
        _logger.info(
            "m_query_event",
            extra={
                "eventCode": self.code,
                "durationMs": self.duration_ms,
                "cache": self.cache,
                "rows": self.rows,
                "columns": self.columns,
                "errors": self.errors,
                "artifactHash": self.artifact_hash,
            },
        )
