"""Tests for DAVI dynamic governed READ broker."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import MagicMock

import pytest
from pydantic import ValidationError

from app.application.external_capabilities.dynamic_information.action_index import (
    reset_action_index_for_tests,
    set_actions_for_tests,
)
from app.application.external_capabilities.dynamic_information.candidate_token import (
    CandidateTokenError,
    mint_candidate_token,
    parse_candidate_token,
)
from app.application.external_capabilities.dynamic_information.catalog_builder import (
    TechnicalAction,
    build_technical_actions_from_baseline,
)
from app.application.external_capabilities.dynamic_information.constants import (
    STATUS_DAVI_ELIGIBLE_READ,
    STATUS_GENERIC_SQL_FORBIDDEN,
    STATUS_NEEDS_BRANCH_AUTHZ_EVIDENCE,
    STATUS_WRITE_OUT_OF_SCOPE,
)
from app.application.external_capabilities.dynamic_information.content_loader import (
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
from app.application.external_capabilities.dynamic_information.governed_http_executor import (
    GovernedExecutionError,
    build_internal_request,
)
from app.application.external_capabilities.dynamic_information.retrieval import (
    retrieve_eligible_actions,
)
from app.interface.mcp.schemas import (
    DiscoverDelpiInformationInput,
    ExecuteDelpiInformationInput,
)


@pytest.fixture(autouse=True)
def _reset_index():
    reset_action_index_for_tests()
    yield
    reset_action_index_for_tests()


def _action(
    *,
    oid: str,
    path: str,
    method: str = "GET",
    status: str = STATUS_DAVI_ELIGIBLE_READ,
    summary: str = "",
) -> TechnicalAction:
    return TechnicalAction(
        action_id=oid,
        operation_id=oid,
        method=method,
        path=path,
        summary=summary or oid.replace("_", " "),
        description="",
        tags=("products",),
        davi_status=status,
        entity="product",
        shape="paged_list",
        parameters=(),
        searchable_text=f"{oid} {summary} {path} products".lower(),
    )


def test_classify_hard_blocks():
    allow = {"search_products"}
    assert (
        classify_operation(
            method="GET",
            path="/data/sql",
            operation_id="run_sql",
            allowlisted_operation_ids=allow,
        )
        == STATUS_GENERIC_SQL_FORBIDDEN
    )
    assert (
        classify_operation(
            method="POST",
            path="/products",
            operation_id="create_product",
            allowlisted_operation_ids=allow,
        )
        == STATUS_WRITE_OUT_OF_SCOPE
    )
    assert (
        classify_operation(
            method="GET",
            path="/products/{code}/stock",
            operation_id="get_product_stock",
            allowlisted_operation_ids=allow,
        )
        == STATUS_NEEDS_BRANCH_AUTHZ_EVIDENCE
    )
    assert (
        classify_operation(
            method="GET",
            path="/products/search",
            operation_id="search_products",
            allowlisted_operation_ids=allow,
        )
        == STATUS_DAVI_ELIGIBLE_READ
    )


def test_inventory_covers_baseline_100_percent():
    root = Path(__file__).resolve().parents[1]
    baseline = json.loads(
        (root / "app/content/openapi_baseline.json").read_text(encoding="utf-8")
    )
    actions = build_technical_actions_from_baseline(
        baseline, allowlist=load_external_read_allowlist()
    )
    assert len(actions) == int(baseline.get("operation_count") or 0)
    assert all(a.davi_status for a in actions)


def test_discover_rejects_transport_smuggling_in_schema():
    with pytest.raises(ValidationError):
        DiscoverDelpiInformationInput.model_validate(
            {"query": "estoque", "path": "/products/x/stock"}
        )
    with pytest.raises(ValidationError):
        ExecuteDelpiInformationInput.model_validate(
            {"candidate_token": "x", "url": "https://evil"}
        )


def test_discover_and_execute_happy_path(monkeypatch):
    set_actions_for_tests(
        [
            _action(
                oid="search_products",
                path="/products/search",
                summary="search products master",
            ),
            _action(
                oid="get_product_detail",
                path="/products/{code}",
                summary="product detail",
            ),
        ]
    )
    monkeypatch.setattr(
        "app.application.external_capabilities.dynamic_information.discover_service.candidate_token_secret",
        lambda: "test-secret-davi",
    )
    monkeypatch.setattr(
        "app.application.external_capabilities.dynamic_information.execute_service.candidate_token_secret",
        lambda: "test-secret-davi",
    )
    discovered = discover_delpi_information(query="search products", top_k=5, actor_id="u1")
    assert discovered["candidate_count"] >= 1
    token = discovered["candidates"][0]["candidate_token"]

    client = MagicMock()
    resp = MagicMock()
    resp.status_code = 200
    resp.json.return_value = {
        "success": True,
        "data": {"items": [{"product_code": "A"}], "page": 1, "page_size": 50, "total": 1},
    }
    client.get.return_value = resp

    result = execute_delpi_information(
        candidate_token=token,
        arguments={"code": "A"},
        actor_id="u1",
        authorization="Bearer test",
        http_client=client,
    )
    assert result["http_status"] == 200
    assert result["truncated"] is False
    client.get.assert_called()
    called_path = client.get.call_args.args[0]
    assert called_path.startswith("/products")


def test_execute_rejects_forged_token_and_arbitrary_args(monkeypatch):
    action = _action(oid="search_products", path="/products/search")
    set_actions_for_tests([action])
    secret = "sec"
    monkeypatch.setattr(
        "app.application.external_capabilities.dynamic_information.execute_service.candidate_token_secret",
        lambda: secret,
    )
    token = mint_candidate_token(
        action_id="search_products", actor_id="u1", secret=secret, ttl_seconds=60
    )
    with pytest.raises(CandidateTokenError):
        parse_candidate_token(token + "x", secret=secret, expected_actor_id="u1")
    with pytest.raises(GovernedExecutionError):
        build_internal_request(action, {"url": "https://evil.example"})
    with pytest.raises(GovernedExecutionError):
        build_internal_request(action, {"operationId": "get_product_stock"})
    with pytest.raises(PermissionError):
        execute_delpi_information(
            candidate_token=token,
            arguments={},
            actor_id="u1",
            authorization=None,
            http_client=MagicMock(),
        )


def test_metamorphic_rename_preserves_retrieval():
    a1 = _action(
        oid="search_products",
        path="/products/search",
        summary="buscar produtos cadastro",
    )
    a2 = _action(
        oid="product_master_lookup_v2",
        path="/v2/catalog/items",
        summary="buscar produtos cadastro",
    )
    hits1 = retrieve_eligible_actions("buscar produtos", [a1], top_k=3)
    hits2 = retrieve_eligible_actions("buscar produtos", [a2], top_k=3)
    assert hits1 and hits2
    assert hits1[0][0].operation_id != hits2[0][0].operation_id
    assert hits1[0][0].path != hits2[0][0].path


def test_dynamic_information_application_does_not_import_composition():
    root = (
        Path(__file__).resolve().parents[1]
        / "app/application/external_capabilities/dynamic_information"
    )
    for path in root.glob("*.py"):
        text = path.read_text(encoding="utf-8")
        assert "app.composition" not in text, path.name
