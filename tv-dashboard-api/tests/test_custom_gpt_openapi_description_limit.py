"""Custom GPT Builder import safety — operation.description length gate."""

from __future__ import annotations

from tv_app.application.gpt_actions.openapi_builder import (
    CUSTOM_GPT_OPERATION_DESCRIPTION_MAX_CHARS,
    build_gpt_actions_openapi,
    count_operations,
)
from tv_app.application.gpt_actions import GPT_ACTIONS_OPERATION_IDS

_HTTP_METHODS = frozenset({"get", "post", "put", "patch", "delete"})


def _operation_description_rows(doc: dict) -> list[tuple[str, str, str, int]]:
    rows: list[tuple[str, str, str, int]] = []
    for path, item in (doc.get("paths") or {}).items():
        if not isinstance(item, dict):
            continue
        for method, operation in item.items():
            if method not in _HTTP_METHODS or not isinstance(operation, dict):
                continue
            description = operation.get("description") or ""
            rows.append(
                (
                    str(operation.get("operationId") or "?"),
                    str(path),
                    str(method),
                    len(description),
                )
            )
    return rows


def test_all_operation_descriptions_within_custom_gpt_builder_limit():
    doc = build_gpt_actions_openapi()
    limit = CUSTOM_GPT_OPERATION_DESCRIPTION_MAX_CHARS
    failures: list[str] = []
    for operation_id, path, method, length in _operation_description_rows(doc):
        if length > limit:
            failures.append(
                f"{operation_id} {method.upper()} {path}: length={length} limit={limit}"
            )
    assert not failures, "operation.description exceeds Custom GPT Builder limit:\n" + "\n".join(
        failures
    )


def test_vista_read_description_under_limit_with_margin():
    doc = build_gpt_actions_openapi()
    for path, item in (doc.get("paths") or {}).items():
        if not isinstance(item, dict):
            continue
        op = item.get("post")
        if not isinstance(op, dict):
            continue
        if op.get("operationId") != "vista_read":
            continue
        description = op.get("description") or ""
        assert len(description) <= 260, (
            f"vista_read description length={len(description)} "
            f"(prefer <=260 margin under Builder 300)"
        )
        # Contract keywords preserved (concise).
        blob = description.lower()
        assert "blockindex" in blob.replace(" ", "") or "block index" in blob
        assert "datasources" in blob.replace(" ", "") or "data sources" in blob
        schema = (
            op.get("requestBody", {})
            .get("content", {})
            .get("application/json", {})
            .get("schema", {})
        )
        props = set((schema.get("properties") or {}).keys())
        assert {"entity", "action"} <= props
        return
    raise AssertionError("vista_read not found in OpenAPI")


def test_action_count_and_operation_ids_stable():
    doc = build_gpt_actions_openapi()
    assert count_operations(doc) == len(GPT_ACTIONS_OPERATION_IDS)
    found: list[str] = []
    for _path, item in (doc.get("paths") or {}).items():
        if not isinstance(item, dict):
            continue
        for method, operation in item.items():
            if method not in _HTTP_METHODS or not isinstance(operation, dict):
                continue
            oid = operation.get("operationId")
            if oid:
                found.append(str(oid))
    assert found == list(GPT_ACTIONS_OPERATION_IDS)
