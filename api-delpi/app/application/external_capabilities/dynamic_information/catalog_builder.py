"""Technical Action Catalog derived from OpenAPI (not semantic capability authority)."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from app.application.external_capabilities.dynamic_information.eligibility import (
    classify_operation,
    is_dynamically_executable,
    load_allowlist_operation_ids,
)

_HTTP = frozenset({"get", "post", "put", "patch", "delete", "head", "options"})


@dataclass(frozen=True)
class TechnicalAction:
    action_id: str
    operation_id: str
    method: str
    path: str
    summary: str
    description: str
    tags: tuple[str, ...]
    davi_status: str
    entity: str | None = None
    shape: str | None = None
    parameters: tuple[dict[str, Any], ...] = field(default_factory=tuple)
    searchable_text: str = ""

    @property
    def executable(self) -> bool:
        return is_dynamically_executable(self.davi_status)


def _param_names(parameters: list[dict[str, Any]] | None) -> list[str]:
    names: list[str] = []
    for p in parameters or []:
        if isinstance(p, dict) and p.get("name"):
            names.append(str(p["name"]))
    return names


def build_technical_actions_from_openapi(
    openapi: dict[str, Any],
    *,
    allowlist: dict[str, Any],
) -> list[TechnicalAction]:
    allowlisted = load_allowlist_operation_ids(allowlist)
    actions: list[TechnicalAction] = []
    paths = openapi.get("paths") or {}
    for path, item in paths.items():
        if not isinstance(item, dict):
            continue
        for method, op in item.items():
            if method.lower() not in _HTTP or not isinstance(op, dict):
                continue
            oid = op.get("operationId") or f"{method.upper()}:{path}"
            summary = str(op.get("summary") or "")
            description = str(op.get("description") or "")
            tags = tuple(str(t) for t in (op.get("tags") or []) if t)
            x_delpi = op.get("x-delpi") or {}
            if not isinstance(x_delpi, dict):
                x_delpi = {}
            status = classify_operation(
                method=method,
                path=path,
                operation_id=op.get("operationId"),
                allowlisted_operation_ids=allowlisted,
                summary=summary,
                tags=list(tags),
            )
            params = tuple(p for p in (op.get("parameters") or []) if isinstance(p, dict))
            searchable = " ".join(
                [
                    oid,
                    summary,
                    description,
                    path,
                    " ".join(tags),
                    " ".join(_param_names(list(params))),
                    str(x_delpi.get("entity") or ""),
                ]
            ).lower()
            actions.append(
                TechnicalAction(
                    action_id=oid,
                    operation_id=oid,
                    method=method.upper(),
                    path=path,
                    summary=summary,
                    description=description,
                    tags=tags,
                    davi_status=status,
                    entity=x_delpi.get("entity"),
                    shape=x_delpi.get("shape"),
                    parameters=params,
                    searchable_text=searchable,
                )
            )
    return actions


def build_technical_actions_from_baseline(
    baseline: dict[str, Any],
    *,
    allowlist: dict[str, Any],
) -> list[TechnicalAction]:
    """Fallback when full OpenAPI is unavailable (tests / offline inventory)."""
    allowlisted = load_allowlist_operation_ids(allowlist)
    actions: list[TechnicalAction] = []
    for row in baseline.get("operations") or []:
        if not isinstance(row, dict):
            continue
        method = str(row.get("method") or "")
        path = str(row.get("path") or "")
        oid = row.get("operationId")
        summary = str(row.get("summary") or "")
        description = str(row.get("description") or "")
        tags = tuple(str(t) for t in (row.get("tags") or []) if t)
        x_delpi = row.get("xDelpi") or row.get("x-delpi") or {}
        if not isinstance(x_delpi, dict):
            x_delpi = {}
        status = classify_operation(
            method=method,
            path=path,
            operation_id=oid,
            allowlisted_operation_ids=allowlisted,
            summary=summary,
            tags=list(tags),
        )
        oid_s = str(oid or f"{method}:{path}")
        searchable = " ".join(
            [oid_s, summary, description, path, " ".join(tags), str(x_delpi.get("entity") or "")]
        ).lower()
        actions.append(
            TechnicalAction(
                action_id=oid_s,
                operation_id=oid_s,
                method=method.upper(),
                path=path,
                summary=summary,
                description=description,
                tags=tags,
                davi_status=status,
                entity=x_delpi.get("entity"),
                shape=x_delpi.get("shape"),
                parameters=tuple(),
                searchable_text=searchable,
            )
        )
    return actions
