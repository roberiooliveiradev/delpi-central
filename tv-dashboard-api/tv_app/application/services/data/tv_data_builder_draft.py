"""Mutações do rascunho DataModelDraft (assistente de dados TV)."""

from __future__ import annotations

import re
import uuid
from typing import Any


def _new_local_id() -> str:
    return f"src_{uuid.uuid4().hex[:10]}"


def empty_draft() -> dict[str, Any]:
    return {
        "sources": [],
        "primaryLocalId": "",
        "transform": None,
        "fieldLabels": {},
        "status": "draft",
    }


def slug_query_name(label: str, operation_id: str) -> str:
    base = re.sub(r"[^a-zA-Z0-9]+", "_", (label or operation_id or "fonte").strip())
    base = base.strip("_") or "fonte"
    return base[:48]


def find_source(draft: dict[str, Any], *, local_id: str | None = None, operation_id: str | None = None) -> dict[str, Any] | None:
    for source in draft.get("sources") or []:
        if not isinstance(source, dict):
            continue
        if local_id and str(source.get("localId") or "") == local_id:
            return source
        if operation_id and str(source.get("operationId") or "") == operation_id:
            return source
    return None


def add_source(
    draft: dict[str, Any],
    *,
    operation_id: str,
    label: str,
    params: dict[str, Any] | None = None,
    query_name: str | None = None,
) -> tuple[dict[str, Any], dict[str, Any] | None]:
    """Returns (draft, source) — source None if already present."""
    existing = find_source(draft, operation_id=operation_id)
    if existing:
        return draft, None

    source = {
        "localId": _new_local_id(),
        "queryName": query_name or slug_query_name(label, operation_id),
        "operationId": operation_id,
        "params": dict(params or {}),
        "label": label,
    }
    sources = list(draft.get("sources") or [])
    sources.append(source)
    draft = {**draft, "sources": sources}
    if not draft.get("primaryLocalId"):
        draft["primaryLocalId"] = source["localId"]
    if len(sources) >= 1:
        draft["status"] = "ready"
    return draft, source


def remove_source(draft: dict[str, Any], *, local_id: str | None = None, operation_id: str | None = None) -> tuple[dict[str, Any], dict[str, Any] | None]:
    target = find_source(draft, local_id=local_id, operation_id=operation_id)
    if not target:
        # fuzzy by label fragment in local_id param misuse — caller may pass label as operation_id
        needle = (local_id or operation_id or "").strip().lower()
        if needle:
            for source in draft.get("sources") or []:
                if needle in str(source.get("label") or "").lower() or needle in str(source.get("operationId") or "").lower():
                    target = source
                    break
    if not target:
        return draft, None

    removed_id = str(target.get("localId") or "")
    sources = [s for s in (draft.get("sources") or []) if str(s.get("localId") or "") != removed_id]
    draft = {**draft, "sources": sources}
    if draft.get("primaryLocalId") == removed_id:
        draft["primaryLocalId"] = str(sources[0].get("localId") or "") if sources else ""
    if not sources:
        draft["status"] = "draft"
        draft["transform"] = None
    return draft, target


def set_params(
    draft: dict[str, Any],
    *,
    params: dict[str, Any],
    local_id: str | None = None,
) -> tuple[dict[str, Any], dict[str, Any] | None]:
    sources = list(draft.get("sources") or [])
    if not sources:
        return draft, None

    target_id = local_id or str(draft.get("primaryLocalId") or sources[0].get("localId") or "")
    updated = None
    next_sources: list[dict[str, Any]] = []
    for source in sources:
        row = dict(source)
        if str(row.get("localId") or "") == target_id:
            merged = {**(row.get("params") or {}), **params}
            row["params"] = merged
            updated = row
        next_sources.append(row)
    return {**draft, "sources": next_sources}, updated


def set_columns(draft: dict[str, Any], columns: list[str]) -> dict[str, Any]:
    cols = [str(c).strip() for c in columns if str(c).strip()]
    transform = dict(draft.get("transform") or {})
    steps = [step for step in (transform.get("steps") or []) if isinstance(step, dict) and step.get("op") != "select"]
    if cols:
        steps.append({"op": "select", "columns": cols})
    transform["steps"] = steps
    draft = {**draft, "transform": transform if steps else None}
    if draft.get("sources"):
        draft["status"] = "ready"
    return draft


def propose_join(
    draft: dict[str, Any],
    *,
    left_local_id: str | None = None,
    right_local_id: str | None = None,
    left_key: str = "op",
    right_key: str | None = None,
) -> tuple[dict[str, Any], dict[str, Any] | None]:
    sources = list(draft.get("sources") or [])
    if len(sources) < 2:
        return draft, None

    primary = left_local_id or str(draft.get("primaryLocalId") or sources[0].get("localId") or "")
    right = right_local_id
    if not right:
        for source in sources:
            lid = str(source.get("localId") or "")
            if lid and lid != primary:
                right = lid
                break
    if not right:
        return draft, None

    right_source = find_source(draft, local_id=right)
    if not right_source:
        return draft, None

    rk = right_key or left_key
    transform = dict(draft.get("transform") or {})
    steps = [
        step
        for step in (transform.get("steps") or [])
        if isinstance(step, dict) and not (step.get("op") == "merge" and step.get("sourceId") == right)
    ]
    merge_step = {
        "op": "merge",
        "sourceId": right,
        "leftKey": left_key,
        "rightKey": rk,
        "join": "left",
    }
    steps.append(merge_step)
    transform["steps"] = steps
    draft = {
        **draft,
        "primaryLocalId": primary,
        "transform": transform,
        "status": "ready",
    }
    return draft, merge_step
