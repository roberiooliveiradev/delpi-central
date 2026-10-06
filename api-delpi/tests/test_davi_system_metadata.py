"""DAVI System Metadata — governed READ promotion (TASK SYSTEM-METADATA-IMPLEMENTATION-001).

Proves:
- exactly 5 /system metadata operations promoted via generic BOUNDED_METADATA_READ opt-in;
- restricted-path opt-in is fail-closed (marker + allowlist + GET + projections);
- frozen external argument names (table_name/text) bound to owner tableName/q;
- responseBindings results[] -> data[] for the frozen column-search contract;
- fail-closed projections (no X2_CHAVE in search, no ranking fields, no X2.*/X3.* wildcard);
- flat-list truncation completeness (>50 -> truncated/is_complete);
- retrieval positives and data-access/SQL negatives;
- candidate-token actor binding;
- MCP surface stays at exactly 2 tools.
"""

from __future__ import annotations

import json
from contextlib import ExitStack, contextmanager
from pathlib import Path
from types import SimpleNamespace
from typing import Any, Iterator
from unittest.mock import MagicMock, patch

import pytest

from app.application.external_capabilities.dynamic_information.action_index import (
    reset_action_index_for_tests,
    set_actions_for_tests,
)
from app.application.external_capabilities.dynamic_information.argument_validator import (
    ArgumentValidationError,
    bind_owner_arguments,
    build_argument_json_schema,
    validate_arguments,
)
from app.application.external_capabilities.dynamic_information.candidate_token import (
    mint_candidate_token,
)
from app.application.external_capabilities.dynamic_information.catalog_builder import (
    TechnicalAction,
    build_technical_actions_from_baseline,
)
from app.application.external_capabilities.dynamic_information.content_loader import (
    load_dynamic_read_budgets,
    load_external_read_allowlist,
)
from app.application.external_capabilities.dynamic_information.discover_service import (
    discover_delpi_information,
)
from app.application.external_capabilities.dynamic_information.eligibility import (
    classify_operation,
)
from app.application.external_capabilities.dynamic_information.execute_service import (
    execute_delpi_information,
)
from app.application.external_capabilities.dynamic_information.projection import (
    apply_approved_field_projection,
)
from app.application.external_capabilities.dynamic_information.read_only_intent_guard import (
    clear_read_only_intent_guard_cache,
)
from app.domain.ports.davi_catalog_action_executor_port import CatalogActionExecutionResult

_API_ROOT = Path(__file__).resolve().parents[1]
_SECRET = "test-secret-davi-system-metadata"
_ACTOR = "22222222-2222-4222-8222-222222222222"
_OTHER_ACTOR = "33333333-3333-4333-8333-333333333333"

_PROMOTED = (
    "search_tables_by_description",
    "search_protheus_columns_by_description",
    "search_protheus_columns_in_table",
    "get_protheus_table",
    "list_protheus_table_columns",
)

_EXCLUDED_SYSTEM = (
    "get_protheus_table_indexes",
    "get_protheus_table_relations",
    "get_protheus_table_schema",
    "get_query_cache_stats",
    "get_connection_pool_stats",
    "get_caller_stats",
    "get_observability_snapshot",
    "get_console_health",
    "get_console_alerts",
    "get_sql_health",
    "get_smoke_definitions",
    "get_openapi_diff",
    "get_envelope_contracts",
    "evaluate_console_alerts",
    "notify_console_smoke_alerts",
)


@pytest.fixture(autouse=True)
def _reset_index():
    reset_action_index_for_tests()
    load_external_read_allowlist.cache_clear()
    load_dynamic_read_budgets.cache_clear()
    clear_read_only_intent_guard_cache()
    yield
    reset_action_index_for_tests()
    load_external_read_allowlist.cache_clear()
    load_dynamic_read_budgets.cache_clear()
    clear_read_only_intent_guard_cache()


def _actions() -> list[TechnicalAction]:
    baseline = json.loads(
        (_API_ROOT / "app/content/openapi_baseline.json").read_text(encoding="utf-8")
    )
    return build_technical_actions_from_baseline(
        baseline, allowlist=load_external_read_allowlist()
    )


def _action(oid: str) -> TechnicalAction:
    return next(a for a in _actions() if a.operation_id == oid)


def _allowlist_entry(oid: str) -> dict[str, Any]:
    for entry in (load_external_read_allowlist().get("operations") or []):
        if entry.get("operationId") == oid:
            return entry
    raise AssertionError(f"missing allowlist entry {oid}")


def _patch_token_secret(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "app.application.external_capabilities.dynamic_information.discover_service.candidate_token_secret",
        lambda: _SECRET,
    )
    monkeypatch.setattr(
        "app.application.external_capabilities.dynamic_information.execute_service.candidate_token_secret",
        lambda: _SECRET,
    )


def _fake_executor(payload: Any, *, captured: dict[str, Any] | None = None):
    class _Exec:
        def execute(self, *, action_id: str, validated_arguments: dict[str, Any]):
            if captured is not None:
                captured["action_id"] = action_id
                captured["validated_arguments"] = dict(validated_arguments)
            return CatalogActionExecutionResult(outcome="ok", payload=payload)

    return _Exec()


def _execute(
    oid: str,
    arguments: dict[str, Any],
    *,
    payload: Any,
    actor: str = _ACTOR,
    captured: dict[str, Any] | None = None,
) -> dict[str, Any]:
    token = mint_candidate_token(
        action_id=oid, actor_id=actor, secret=_SECRET, ttl_seconds=300
    )
    return execute_delpi_information(
        candidate_token=token,
        arguments=arguments,
        actor_id=actor,
        catalog_action_executor=_fake_executor(payload, captured=captured),
    )


def _envelope(inner: Any) -> dict[str, Any]:
    return {"success": True, "message": "ok", "data": inner}


# ---------------------------------------------------------------------------
# Promotion set / counts
# ---------------------------------------------------------------------------


def test_allowlist_v17_and_exactly_five_promoted():
    allow = load_external_read_allowlist()
    assert allow["version"] == 17
    ops = {o["operationId"] for o in allow["operations"]}
    assert len(allow["operations"]) == 77
    assert set(_PROMOTED) <= ops
    for oid in _EXCLUDED_SYSTEM:
        assert oid not in ops
    assert "execute_readonly_sql" not in ops


def test_exactly_five_system_ops_executable():
    eligible = {a.operation_id for a in _actions() if a.executable}
    assert set(_PROMOTED) <= eligible
    for oid in _EXCLUDED_SYSTEM:
        assert _action(oid).executable is False


@pytest.mark.parametrize("oid", _PROMOTED)
def test_promoted_entries_have_restricted_opt_in_and_projections(oid: str):
    entry = _allowlist_entry(oid)
    assert entry.get("executionMode") == "catalog_action"
    assert entry.get("restrictedPathRead") == "BOUNDED_METADATA_READ"
    assert entry.get("approvedInputFields")
    assert entry.get("approvedResponseFields")
    assert all("*" not in f for f in entry["approvedResponseFields"])
    assert all(not f.endswith(".*") for f in entry["approvedResponseFields"])


# ---------------------------------------------------------------------------
# Restricted-path opt-in fail-closed matrix
# ---------------------------------------------------------------------------


def _allowlist_with(entry: dict[str, Any] | None) -> dict[str, Any]:
    ops = [entry] if entry else []
    return {"operations": ops}


def test_system_get_allowlisted_without_marker_stays_admin():
    entry = {
        "operationId": "search_tables_by_description",
        "approvedInputFields": ["description"],
        "approvedResponseFields": ["page"],
    }
    status = classify_operation(
        method="GET",
        path="/system/tables/search",
        operation_id="search_tables_by_description",
        allowlisted_operation_ids={"search_tables_by_description"},
        allowlist=_allowlist_with(entry),
    )
    assert status == "ADMIN_OUT_OF_SCOPE"


def test_system_get_marked_but_not_allowlisted_stays_admin():
    entry = {
        "operationId": "search_tables_by_description",
        "restrictedPathRead": "BOUNDED_METADATA_READ",
        "approvedInputFields": ["description"],
        "approvedResponseFields": ["page"],
    }
    status = classify_operation(
        method="GET",
        path="/system/tables/search",
        operation_id="search_tables_by_description",
        allowlisted_operation_ids=set(),
        allowlist=_allowlist_with(entry),
    )
    assert status == "ADMIN_OUT_OF_SCOPE"


def test_system_get_marked_allowlisted_without_projections_not_executable():
    entry = {
        "operationId": "search_tables_by_description",
        "restrictedPathRead": "BOUNDED_METADATA_READ",
    }
    status = classify_operation(
        method="GET",
        path="/system/tables/search",
        operation_id="search_tables_by_description",
        allowlisted_operation_ids={"search_tables_by_description"},
        allowlist=_allowlist_with(entry),
    )
    assert status != "DAVI_ELIGIBLE_READ"


def test_system_get_full_opt_in_eligible():
    entry = {
        "operationId": "search_tables_by_description",
        "restrictedPathRead": "BOUNDED_METADATA_READ",
        "approvedInputFields": ["description"],
        "approvedResponseFields": ["page"],
    }
    status = classify_operation(
        method="GET",
        path="/system/tables/search",
        operation_id="search_tables_by_description",
        allowlisted_operation_ids={"search_tables_by_description"},
        allowlist=_allowlist_with(entry),
    )
    assert status == "DAVI_ELIGIBLE_READ"


def test_marker_does_not_open_system_post():
    entry = {
        "operationId": "notify_console_smoke_alerts",
        "restrictedPathRead": "BOUNDED_METADATA_READ",
        "approvedInputFields": ["x"],
        "approvedResponseFields": ["y"],
    }
    status = classify_operation(
        method="POST",
        path="/system/console-alerts/smoke",
        operation_id="notify_console_smoke_alerts",
        allowlisted_operation_ids={"notify_console_smoke_alerts"},
        allowlist=_allowlist_with(entry),
    )
    assert status != "DAVI_ELIGIBLE_READ"


def test_generic_sql_forbidden_precedence_over_marker():
    entry = {
        "operationId": "execute_readonly_sql",
        "restrictedPathRead": "BOUNDED_METADATA_READ",
        "approvedInputFields": ["x"],
        "approvedResponseFields": ["y"],
    }
    status = classify_operation(
        method="POST",
        path="/data/sql",
        operation_id="execute_readonly_sql",
        allowlisted_operation_ids={"execute_readonly_sql"},
        allowlist=_allowlist_with(entry),
    )
    assert status == "GENERIC_SQL_FORBIDDEN"


# ---------------------------------------------------------------------------
# External argument schema / bindings
# ---------------------------------------------------------------------------


def test_table_name_external_schema_get_table():
    schema = build_argument_json_schema(_action("get_protheus_table"))
    assert set(schema["properties"]) == {"table_name"}
    assert schema["required"] == ["table_name"]
    assert schema["additionalProperties"] is False


def test_text_and_table_name_external_schema_in_table_search():
    schema = build_argument_json_schema(_action("search_protheus_columns_in_table"))
    assert set(schema["properties"]) == {"table_name", "text"}
    assert set(schema["required"]) == {"table_name", "text"}
    assert schema["properties"]["text"]["minLength"] == 2


def test_list_columns_schema_and_limit_bound():
    schema = build_argument_json_schema(_action("list_protheus_table_columns"))
    assert set(schema["properties"]) == {"table_name", "page", "limit"}
    assert schema["properties"]["limit"]["maximum"] == 50


@pytest.mark.parametrize(
    "bad_args",
    [
        {"tableName": "SB1010"},
        {"table_name": "SB1010", "extra": "x"},
        {"table_name": "SB1010", "url": "http://x"},
        {"table_name": "SB1010", "sql": "select 1"},
        {"table_name": "SB1010", "Authorization": "Bearer x"},
        {"table_name": "SB1010", "path": "/x"},
        {"table_name": "SB1010", "method": "POST"},
        {"table_name": "SB1010", "operationId": "execute_readonly_sql"},
    ],
)
def test_get_table_rejects_owner_and_transport_args(bad_args: dict[str, Any]):
    with pytest.raises(ArgumentValidationError):
        validate_arguments(_action("get_protheus_table"), bad_args)


@pytest.mark.parametrize(
    "bad_args",
    [
        {"table_name": "SC7010", "q": "fornecedor"},
        {"tableName": "SC7010", "text": "fornecedor"},
        {"table_name": "SC7010"},
        {"table_name": "SC7010", "text": "a"},
        {"table_name": "SC7010", "text": "ok", "where": "1=1"},
        {"table_name": "SC7010", "text": "ok", "fields": ["*"]},
    ],
)
def test_in_table_search_rejects_owner_and_sql_args(bad_args: dict[str, Any]):
    with pytest.raises(ArgumentValidationError):
        validate_arguments(_action("search_protheus_columns_in_table"), bad_args)


def test_owner_binding_translation():
    action = _action("search_protheus_columns_in_table")
    validated = validate_arguments(
        action, {"table_name": "SC7010", "text": "fornecedor"}
    )
    bound = bind_owner_arguments(action, validated)
    assert bound == {"tableName": "SC7010", "q": "fornecedor"}


def test_binding_target_not_declared_fails_closed():
    action = _action("get_protheus_table")
    evil = action.__class__(
        **{**action.__dict__, "argument_bindings": {"table_name": "not_a_param"}}
    )
    validated = validate_arguments(action, {"table_name": "SB1010"})
    with pytest.raises(ArgumentValidationError):
        bind_owner_arguments(evil, validated)


def test_duplicate_binding_targets_fail_closed():
    action = _action("search_protheus_columns_in_table")
    evil = action.__class__(
        **{
            **action.__dict__,
            "argument_bindings": {"table_name": "tableName", "text": "tableName"},
        }
    )
    validated = validate_arguments(
        action, {"table_name": "SC7010", "text": "fornecedor"}
    )
    with pytest.raises(ArgumentValidationError):
        bind_owner_arguments(evil, validated)


def test_binding_to_forbidden_transport_name_impossible():
    action = _action("get_protheus_table")
    evil = action.__class__(
        **{**action.__dict__, "argument_bindings": {"table_name": "Authorization"}}
    )
    validated = validate_arguments(action, {"table_name": "SB1010"})
    with pytest.raises(ArgumentValidationError):
        bind_owner_arguments(evil, validated)


def test_description_min_length_and_limit_bounds():
    action = _action("search_tables_by_description")
    with pytest.raises(ArgumentValidationError):
        validate_arguments(action, {"description": "x"})
    with pytest.raises(ArgumentValidationError):
        validate_arguments(action, {"description": "produtos", "limit": 200})
    ok = validate_arguments(action, {"description": "produtos", "limit": 50, "page": 2})
    assert ok == {"description": "produtos", "limit": 50, "page": 2}


# ---------------------------------------------------------------------------
# Response projection / response bindings / minimization matrix
# ---------------------------------------------------------------------------


def test_table_search_projection_drops_key_and_ranking():
    payload = _envelope(
        {
            "success": True,
            "message": "ok",
            "page": 1,
            "page_size": 20,
            "total_records": 1,
            "total_pages": 1,
            "results": [
                {
                    "X2_ARQUIVO": "SB1010",
                    "X2_NOME": "Produtos",
                    "X2_CHAVE": "000123",
                    "similarity_ratio": 0.9,
                    "coverage_ratio": 0.8,
                    "order_ratio": 0.7,
                    "length_ratio": 0.6,
                    "total_score": 3.0,
                    "X2_FUTURE_SECRET": "x",
                }
            ],
        }
    )
    fields = tuple(_allowlist_entry("search_tables_by_description")["approvedResponseFields"])
    projected = apply_approved_field_projection(payload, approved_fields=fields)
    row = projected["results"][0]
    assert row == {"X2_ARQUIVO": "SB1010", "X2_NOME": "Produtos"}
    for forbidden in (
        "X2_CHAVE",
        "similarity_ratio",
        "coverage_ratio",
        "order_ratio",
        "length_ratio",
        "total_score",
        "X2_FUTURE_SECRET",
    ):
        assert forbidden not in row
    assert projected["page"] == 1
    assert projected["total_records"] == 1
    assert projected["total_pages"] == 1


def test_column_search_response_binding_results_to_data():
    action = _action("search_protheus_columns_by_description")
    payload = _envelope(
        {
            "page": 1,
            "page_size": 20,
            "total_records": 1,
            "total_pages": 1,
            "results": [
                {
                    "table_name": "SC7010",
                    "table_description": "Pedidos de Compra",
                    "column_name": "C7_FORNECE",
                    "column_description": "Fornecedor",
                    "similarity_ratio": 0.9,
                    "total_score": 3.0,
                    "unmapped_field": "x",
                }
            ],
            "unmapped_root": "drop-me",
        }
    )
    projected = apply_approved_field_projection(
        payload,
        approved_fields=action.approved_response_fields,
        response_bindings=action.response_bindings,
    )
    assert "results" not in projected
    assert projected["data"][0] == {
        "table_name": "SC7010",
        "table_description": "Pedidos de Compra",
        "column_name": "C7_FORNECE",
        "column_description": "Fornecedor",
    }
    assert "unmapped_root" not in projected


def test_response_binding_missing_source_fails_closed():
    projected = apply_approved_field_projection(
        _envelope({"page": 1, "other": []}),
        approved_fields=("data[].table_name",),
        response_bindings={"data": "results"},
    )
    assert "data" not in projected
    assert "results" not in projected


def test_in_table_search_projection_six_fields_only():
    payload = _envelope(
        [
            {
                "X3_CAMPO": "C7_FORNECE",
                "X3_DESCRIC": "Fornecedor",
                "X3_ORDEM": "10",
                "X3_TIPO": "C",
                "X3_TAMANHO": 6,
                "X3_DECIMAL": 0,
                "X3_FUTURE_FIELD": "drop",
            }
        ]
    )
    fields = tuple(
        _allowlist_entry("search_protheus_columns_in_table")["approvedResponseFields"]
    )
    projected = apply_approved_field_projection(payload, approved_fields=fields)
    assert projected == [
        {
            "X3_CAMPO": "C7_FORNECE",
            "X3_DESCRIC": "Fornecedor",
            "X3_ORDEM": "10",
            "X3_TIPO": "C",
            "X3_TAMANHO": 6,
            "X3_DECIMAL": 0,
        }
    ]


def test_get_table_projection_allows_x2_chave_only_here():
    fields = tuple(_allowlist_entry("get_protheus_table")["approvedResponseFields"])
    projected = apply_approved_field_projection(
        _envelope(
            {
                "TableName": "SB1010",
                "X2_ARQUIVO": "SB1010",
                "X2_NOME": "Produtos",
                "X2_CHAVE": "000123",
                "X2_MODO": "X",
                "X2_FUTURE_SECRET": "drop",
            }
        ),
        approved_fields=fields,
    )
    assert projected == {
        "TableName": "SB1010",
        "X2_ARQUIVO": "SB1010",
        "X2_NOME": "Produtos",
        "X2_CHAVE": "000123",
    }


def test_list_columns_projection_six_fields_drops_extra_meta():
    fields = tuple(
        _allowlist_entry("list_protheus_table_columns")["approvedResponseFields"]
    )
    projected = apply_approved_field_projection(
        _envelope(
            {
                "total": 60,
                "page": 1,
                "pageSize": 50,
                "totalPages": 2,
                "results": [
                    {
                        "X3_CAMPO": "B1_COD",
                        "X3_DESCRIC": "Codigo",
                        "X3_ORDEM": "01",
                        "X3_TIPO": "C",
                        "X3_TAMANHO": 15,
                        "X3_DECIMAL": 0,
                        "X3_RELACAO": "drop",
                    }
                ],
            }
        ),
        approved_fields=fields,
    )
    row = projected["results"][0]
    assert set(row) == {
        "X3_CAMPO",
        "X3_DESCRIC",
        "X3_ORDEM",
        "X3_TIPO",
        "X3_TAMANHO",
        "X3_DECIMAL",
    }
    assert "pageSize" not in projected
    assert "totalPages" not in projected


def test_no_business_row_or_sql_text_in_projection():
    fields = tuple(_allowlist_entry("get_protheus_table")["approvedResponseFields"])
    projected = apply_approved_field_projection(
        _envelope(
            {
                "TableName": "SB1010",
                "X2_ARQUIVO": "SB1010",
                "X2_NOME": "Produtos",
                "X2_CHAVE": "1",
                "rows": [{"B1_COD": "X"}],
                "sql": "SELECT * FROM SB1010",
            }
        ),
        approved_fields=fields,
    )
    assert "rows" not in projected
    assert "sql" not in projected


# ---------------------------------------------------------------------------
# Truncation / completeness
# ---------------------------------------------------------------------------


def test_flat_list_over_50_truncated_and_incomplete(monkeypatch):
    set_actions_for_tests(_actions())
    _patch_token_secret(monkeypatch)
    rows = [
        {
            "X3_CAMPO": f"C{i:03d}",
            "X3_DESCRIC": "d",
            "X3_ORDEM": "01",
            "X3_TIPO": "C",
            "X3_TAMANHO": 1,
            "X3_DECIMAL": 0,
        }
        for i in range(60)
    ]
    result = _execute(
        "search_protheus_columns_in_table",
        {"table_name": "SB1010", "text": "cod"},
        payload=_envelope(rows),
    )
    assert result["status"] == "ok"
    assert len(result["data"]) == 50
    assert result["truncated"] is True
    assert result["is_complete"] is False


def test_flat_list_exactly_50_complete(monkeypatch):
    set_actions_for_tests(_actions())
    _patch_token_secret(monkeypatch)
    rows = [
        {
            "X3_CAMPO": f"C{i:03d}",
            "X3_DESCRIC": "d",
            "X3_ORDEM": "01",
            "X3_TIPO": "C",
            "X3_TAMANHO": 1,
            "X3_DECIMAL": 0,
        }
        for i in range(50)
    ]
    result = _execute(
        "search_protheus_columns_in_table",
        {"table_name": "SB1010", "text": "cod"},
        payload=_envelope(rows),
    )
    assert len(result["data"]) == 50
    assert result["truncated"] is False
    assert result["is_complete"] is True


def test_flat_list_empty_valid_no_match(monkeypatch):
    set_actions_for_tests(_actions())
    _patch_token_secret(monkeypatch)
    result = _execute(
        "search_protheus_columns_in_table",
        {"table_name": "SB1010", "text": "zz"},
        payload=_envelope([]),
    )
    assert result["status"] == "ok"
    assert result["data"] == []
    assert result["truncated"] is False


# ---------------------------------------------------------------------------
# End-to-end execute (fake executor boundary)
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("oid", "args", "payload", "check"),
    [
        (
            "search_tables_by_description",
            {"description": "produtos"},
            _envelope(
                {
                    "page": 1,
                    "page_size": 20,
                    "total_records": 1,
                    "total_pages": 1,
                    "results": [
                        {
                            "X2_ARQUIVO": "SB1010",
                            "X2_NOME": "Produtos",
                            "X2_CHAVE": "secret",
                            "total_score": 9.9,
                        }
                    ],
                }
            ),
            lambda d: d["data"]["results"][0]
            == {"X2_ARQUIVO": "SB1010", "X2_NOME": "Produtos"},
        ),
        (
            "search_protheus_columns_by_description",
            {"description": "fornecedor"},
            _envelope(
                {
                    "page": 1,
                    "page_size": 20,
                    "total_records": 1,
                    "total_pages": 1,
                    "results": [
                        {
                            "table_name": "SC7010",
                            "table_description": "PC",
                            "column_name": "C7_FORNECE",
                            "column_description": "Fornecedor",
                            "total_score": 9.9,
                        }
                    ],
                }
            ),
            lambda d: set(d["data"]["data"][0])
            == {
                "table_name",
                "table_description",
                "column_name",
                "column_description",
            },
        ),
        (
            "search_protheus_columns_in_table",
            {"table_name": "SC7010", "text": "fornecedor"},
            _envelope(
                [
                    {
                        "X3_CAMPO": "C7_FORNECE",
                        "X3_DESCRIC": "Fornecedor",
                        "X3_ORDEM": "10",
                        "X3_TIPO": "C",
                        "X3_TAMANHO": 6,
                        "X3_DECIMAL": 0,
                    }
                ]
            ),
            lambda d: set(d["data"][0]) == {
                "X3_CAMPO",
                "X3_DESCRIC",
                "X3_ORDEM",
                "X3_TIPO",
                "X3_TAMANHO",
                "X3_DECIMAL",
            },
        ),
        (
            "get_protheus_table",
            {"table_name": "SB1010"},
            _envelope(
                {
                    "TableName": "SB1010",
                    "X2_ARQUIVO": "SB1010",
                    "X2_NOME": "Produtos",
                    "X2_CHAVE": "000123",
                    "X2_FUTURE_SECRET": "drop",
                }
            ),
            lambda d: set(d["data"]) == {"TableName", "X2_ARQUIVO", "X2_NOME", "X2_CHAVE"},
        ),
        (
            "list_protheus_table_columns",
            {"table_name": "SB1010"},
            _envelope(
                {
                    "total": 1,
                    "page": 1,
                    "pageSize": 50,
                    "totalPages": 1,
                    "results": [
                        {
                            "X3_CAMPO": "B1_COD",
                            "X3_DESCRIC": "Codigo",
                            "X3_ORDEM": "01",
                            "X3_TIPO": "C",
                            "X3_TAMANHO": 15,
                            "X3_DECIMAL": 0,
                            "X3_RELACAO": "drop",
                        }
                    ],
                }
            ),
            lambda d: set(d["data"]["results"][0])
            == {"X3_CAMPO", "X3_DESCRIC", "X3_ORDEM", "X3_TIPO", "X3_TAMANHO", "X3_DECIMAL"},
        ),
    ],
)
def test_positive_execute_each_promoted(monkeypatch, oid, args, payload, check):
    set_actions_for_tests(_actions())
    _patch_token_secret(monkeypatch)
    result = _execute(oid, args, payload=payload)
    assert result["status"] == "ok"
    assert result["projection"] == "approved_fields"
    assert check(result)


def test_owner_binding_reaches_executor(monkeypatch):
    set_actions_for_tests(_actions())
    _patch_token_secret(monkeypatch)
    captured: dict[str, Any] = {}
    _execute(
        "search_protheus_columns_in_table",
        {"table_name": "SC7010", "text": "fornecedor"},
        payload=_envelope([]),
        captured=captured,
    )
    assert captured["validated_arguments"] == {
        "tableName": "SC7010",
        "q": "fornecedor",
    }


# ---------------------------------------------------------------------------
# Retrieval positives / collision negatives
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("query", "expected"),
    [
        ("qual tabela guarda produtos?", "search_tables_by_description"),
        ("qual tabela guarda pedidos de compra?", "search_tables_by_description"),
        ("qual campo representa referência do fornecedor?", "search_protheus_columns_by_description"),
        ("quais campos da SC7 têm fornecedor?", "search_protheus_columns_in_table"),
        ("o que é a SB1?", "get_protheus_table"),
        ("quais são os campos da SB1010?", "list_protheus_table_columns"),
    ],
)
def test_retrieval_positives(query, expected, monkeypatch):
    set_actions_for_tests(_actions())
    _patch_token_secret(monkeypatch)
    discovered = discover_delpi_information(query=query, top_k=5, actor_id=_ACTOR)
    ids = [c["action_id"] for c in discovered["candidates"]]
    assert ids, query
    assert ids[0] == expected, (query, ids)


@pytest.mark.parametrize(
    "query",
    [
        "me mostre os registros da SB1",
        "liste clientes da SA1",
        "execute um SELECT na SC7",
        "traga todos os dados da SC7",
        "select * from SB1",
    ],
)
def test_retrieval_negatives_no_metadata_or_sql_candidate(query, monkeypatch):
    set_actions_for_tests(_actions())
    _patch_token_secret(monkeypatch)
    discovered = discover_delpi_information(query=query, top_k=5, actor_id=_ACTOR)
    ids = [c["action_id"] for c in discovered["candidates"]]
    assert "execute_readonly_sql" not in ids
    assert not set(ids) & set(_PROMOTED), (query, ids)


# ---------------------------------------------------------------------------
# Candidate token actor binding
# ---------------------------------------------------------------------------


def test_candidate_token_user_b_denied(monkeypatch):
    set_actions_for_tests(_actions())
    _patch_token_secret(monkeypatch)
    token = mint_candidate_token(
        action_id="get_protheus_table",
        actor_id=_ACTOR,
        secret=_SECRET,
        ttl_seconds=300,
    )
    with pytest.raises(Exception):
        execute_delpi_information(
            candidate_token=token,
            arguments={"table_name": "SB1010"},
            actor_id=_OTHER_ACTOR,
            catalog_action_executor=_fake_executor(_envelope({})),
        )


# ---------------------------------------------------------------------------
# MCP surface / GPT Actions
# ---------------------------------------------------------------------------


def test_mcp_tools_remain_two():
    import asyncio

    from app.interface.mcp.server import create_mcp_server

    tools = asyncio.run(create_mcp_server().list_tools())
    assert [t.name for t in tools] == [
        "discover_delpi_information",
        "execute_delpi_information",
    ]


def test_gpt_actions_unchanged():
    gpt_path = _API_ROOT / "docs" / "gpt-actions" / "openapi-gpt-actions.json"
    if not gpt_path.exists():
        pytest.skip("gpt actions openapi not versioned here")
    spec = json.loads(gpt_path.read_text(encoding="utf-8"))
    assert not any("/system" in p for p in (spec.get("paths") or {}))


# ---------------------------------------------------------------------------
# AuthZ through canonical routes (real ASGI, faked auth/rbac/use-case)
# ---------------------------------------------------------------------------


@contextmanager
def _system_route_authz(*, permissions: list[str]) -> Iterator[Any]:
    """Spin up the real app with a non-superadmin user carrying `permissions`."""
    from fastapi.testclient import TestClient

    import app.interface.http.routes.system_routes as system_routes

    claims = {
        "sub": _ACTOR,
        "email": "sysmeta@example.com",
        "aud": "delpi-central",
        "name": "System Metadata Test",
    }
    user = SimpleNamespace(is_superadmin=False, permissions=permissions)

    async def _rbac(_token: str) -> dict[str, Any]:
        return {
            "id": _ACTOR,
            "email": "sysmeta@example.com",
            "name": "System Metadata Test",
            "roles": [],
            "groups": [],
            "permissions": permissions,
            "is_superadmin": False,
            "rbac_unavailable": False,
        }

    table_uc = MagicMock()
    table_uc.execute.return_value = {
        "TableName": "SB1010",
        "X2_ARQUIVO": "SB1010",
        "X2_NOME": "Produtos",
        "X2_CHAVE": "000123",
    }

    with ExitStack() as stack:
        stack.enter_context(
            patch("delpi_auth.jwt_validator.validate_token", return_value=claims)
        )
        stack.enter_context(
            patch(
                "delpi_auth.middleware.fastapi_auth.validate_token",
                return_value=claims,
            )
        )
        stack.enter_context(
            patch(
                "app.middleware.auth_middleware.validate_token",
                return_value=claims,
            )
        )
        stack.enter_context(
            patch("delpi_auth.authorization.resolve_user_context", return_value=user)
        )
        stack.enter_context(
            patch(
                "delpi_auth.middleware.fastapi_auth.load_user_rbac",
                side_effect=_rbac,
            )
        )
        stack.enter_context(
            patch.object(
                system_routes,
                "build_get_table_use_case",
                return_value=table_uc,
            )
        )
        stack.enter_context(
            patch(
                "app.startup.run_plugins_migrations_on_startup.run_plugins_migrations_on_startup",
                lambda: None,
            )
        )
        stack.enter_context(
            patch(
                "app.startup.schedule_openapi_consumer_notify.schedule_openapi_consumer_notify_on_startup",
                lambda: None,
            )
        )
        from app.main import app

        # No `with`: lifespan re-entry would re-run the MCP session manager
        # once-only (same convention as product-master security tests).
        yield TestClient(app)


@pytest.mark.parametrize(
    ("permissions", "expected"),
    [
        (["api-delpi.system"], 200),
        (["api-delpi.access.full"], 200),
        (["api-delpi.access"], 403),
        ([], 403),
    ],
)
def test_system_metadata_route_authz_matrix(permissions, expected):
    with _system_route_authz(permissions=permissions) as client:
        response = client.get(
            "/system/tables/SB1010",
            headers={"Authorization": "Bearer end-user-token"},
        )
    assert response.status_code == expected
