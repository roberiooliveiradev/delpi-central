"""DAVI-INVENTORY-MATERIAL-FLOW-CORRECTIVE-001 — governance closure tests.

Pins the four targeted corrections (SB7 provenance fail-closed, DAVI
page_size bound 50, raw movement_type removal, batch defer) plus
governance evidence (counts, coverageDecision chain, AuthZ, MCP=2,
generic-SQL forbidden). Owner API contracts are intentionally
preserved — owner page_size<=500, batch route, internal fields.
"""

from __future__ import annotations

import json
import re
from contextlib import ExitStack, contextmanager
from pathlib import Path
from types import SimpleNamespace
from typing import Any, Iterator
from unittest.mock import MagicMock, patch

import pytest

_API_ROOT = Path(__file__).resolve().parent.parent
_REPO_SOURCE = (
    _API_ROOT
    / "app/infrastructure/persistence/totvs/supplies_repositories/"
    / "inventory_adjustments_repository.py"
).read_text(encoding="utf-8")

from app.application.external_capabilities.dynamic_information.argument_validator import (  # noqa: E402
    ArgumentValidationError,
    validate_arguments,
)
from app.application.external_capabilities.dynamic_information.catalog_builder import (  # noqa: E402
    build_technical_actions_from_baseline,
    build_technical_actions_from_openapi,
)
from app.application.external_capabilities.dynamic_information.action_index import (  # noqa: E402
    set_actions_for_tests,
)
from app.application.external_capabilities.dynamic_information.eligibility import (  # noqa: E402
    STATUS_DAVI_ELIGIBLE_READ,
)
from app.application.external_capabilities.dynamic_information.projection import (  # noqa: E402
    apply_approved_field_projection,
)
from app.application.external_capabilities.dynamic_information.execute_service import (  # noqa: E402
    execute_delpi_information,
)
from app.application.external_capabilities.dynamic_information.candidate_token import (  # noqa: E402
    mint_candidate_token,
    parse_candidate_token,
)
from app.application.external_capabilities.dynamic_information.content_loader import (  # noqa: E402
    load_dynamic_read_budgets,
    load_external_read_allowlist,
)
from app.application.external_capabilities.dynamic_information.action_index import (  # noqa: E402
    reset_action_index_for_tests,
)
from app.application.external_capabilities.dynamic_information.discover_service import (  # noqa: E402
    discover_delpi_information,
)
from app.application.external_capabilities.dynamic_information.retrieval import (  # noqa: E402
    retrieve_eligible_actions,
)
from app.application.external_capabilities.dynamic_information.errors import (  # noqa: E402
    GovernedExecutionError,
)
from app.domain.ports.davi_catalog_action_executor_port import (  # noqa: E402
    CatalogActionExecutionResult,
)
from app.domain.services.pagination_tier_service import PaginationTierService  # noqa: E402
from app.domain.services.supplies.inventory_adjustment_service import (  # noqa: E402
    resolve_inventory_provenance,
)
from app.infrastructure.persistence.totvs.supplies_repositories.inventory_adjustments_repository import (  # noqa: E402
    InventoryAdjustmentsRepository,
)

_BATCH_ID = "list_production_order_operation_materials_batch"
_ACTOR = "user-inventory-corrective"


@pytest.fixture(autouse=True)
def _reset_index():
    reset_action_index_for_tests()
    load_external_read_allowlist.cache_clear()
    load_dynamic_read_budgets.cache_clear()


def _allow():
    return json.loads(
        (_API_ROOT / "app/content/davi_external_read_allowlist.json").read_text(
            encoding="utf-8"
        )
    )


def _ops():
    return {o["operationId"]: o for o in _allow()["operations"]}


def _actions():
    from functools import lru_cache

    @lru_cache(maxsize=1)
    def _live():
        from app.main import app

        return build_technical_actions_from_openapi(
            app.openapi(), allowlist=load_external_read_allowlist()
        )

    return _live()


def _baseline_actions():
    baseline = json.loads(
        (_API_ROOT / "app/content/openapi_baseline.json").read_text(encoding="utf-8")
    )
    return build_technical_actions_from_baseline(
        baseline, allowlist=load_external_read_allowlist()
    )


def _action(oid: str):
    return next(a for a in _actions() if a.operation_id == oid)


class _FakeAdjustmentsRepository(InventoryAdjustmentsRepository):
    """Executes the real fetch_adjustment_items mapping without a DB."""

    def __init__(self, rows):
        self._rows = rows
        self.executed: list[str] = []
        self.connection = None
        self.cursor = None

    def _connect(self):  # noqa: D102
        return None

    def execute_one(self, query, params=()):
        self.executed.append(query)
        return {"total": len(self._rows)}

    def execute_query(self, query, params=()):
        self.executed.append(query)
        return list(self._rows)


def _adjustment_row(**over):
    row = {
        "issue_date": "20261001",
        "branch": "01",
        "product_code": "P1",
        "product_description": "Item",
        "unit": "UN",
        "warehouse": "01",
        "document": "INVENT",
        "movement_direction": "inbound",
        "inventory_adjustment_nature": "surplus",
        "quantity": 5.0,
        "signed_quantity": 5.0,
        "movement_value": 10.0,
        "signed_value": 10.0,
        "provenance_candidate_count": 1,
        "provenance_document": "INV-9",
        "provenance_counted_quantity": 12.0,
    }
    row.update(over)
    return row


def _fetch(rows):
    repo = _FakeAdjustmentsRepository(rows)
    return repo.fetch_adjustment_items(
        date_start="20250101",
        date_end_exclusive="20260101",
        branch=None,
        product_code=None,
        warehouse=None,
        nature=None,
        page=1,
        page_size=50,
    )


# ---------------------------------------------------------------------------
# PROV — SB7 provenance fail-closed (behavior, not only source grep)
# ---------------------------------------------------------------------------


def test_prov01_single_document_exposes_document_and_quantity():
    doc, qty = resolve_inventory_provenance(1, "INV-9", 12.0)
    assert doc == "INV-9" and qty == 12.0


def test_prov02_zero_documents_fails_closed():
    assert resolve_inventory_provenance(0, None, None) == (None, None)


def test_prov03_multiple_documents_fails_closed():
    assert resolve_inventory_provenance(2, "INV-9", 12.0) == (None, None)
    assert resolve_inventory_provenance(3, "INV-9", 12.0) == (None, None)


def test_prov04_end_to_end_same_document_aggregation():
    result = _fetch(
        [_adjustment_row(provenance_candidate_count=1,
                         provenance_document="INV-9",
                         provenance_counted_quantity=17.5)]
    )
    item = result["items"][0]
    assert item["inventory_document"] == "INV-9"
    assert item["counted_quantity"] == 17.5


def test_prov05_end_to_end_ambiguous_or_absent_fails_closed():
    ambiguous = _fetch(
        [_adjustment_row(provenance_candidate_count=2,
                         provenance_document="INV-9",
                         provenance_counted_quantity=30.0)]
    )["items"][0]
    assert ambiguous["inventory_document"] is None
    assert ambiguous["counted_quantity"] is None
    absent = _fetch(
        [_adjustment_row(provenance_candidate_count=0,
                         provenance_document=None,
                         provenance_counted_quantity=None)]
    )["items"][0]
    assert absent["inventory_document"] is None
    assert absent["counted_quantity"] is None


def test_prov06_no_cross_document_quantity_sum():
    # When >1 candidate documents exist, quantity must not be the
    # aggregate across different B7_DOC values — it must be None.
    item = _fetch(
        [_adjustment_row(provenance_candidate_count=2,
                         provenance_document="INV-A",
                         provenance_counted_quantity=99.0)]
    )["items"][0]
    assert item["counted_quantity"] != 99.0
    assert item["counted_quantity"] is None


def test_prov07_provenance_sql_is_set_based_no_top1_authority():
    block = re.search(
        r"_PROVENANCE_OUTER_APPLY = \"\"\"(.*?)\"\"\"", _REPO_SOURCE, re.S
    )
    assert block, "provenance OUTER APPLY not found"
    sql = block.group(1)
    assert "TOP 1" not in sql
    assert "ORDER BY S.B7_DOC" not in sql
    assert "OUTER APPLY" in sql
    assert "COUNT(*) AS candidate_document_count" in sql
    assert "GROUP BY NULLIF(LTRIM(RTRIM(S.B7_DOC)), '')" in sql
    assert "NULLIF(LTRIM(RTRIM(S.B7_DOC)), '') IS NOT NULL" in sql
    assert "S.D_E_L_E_T_ = ''" in sql
    assert "SUM(S.B7_QUANT) AS counted_quantity" in sql
    # outer count operates on distinct documents, not physical rows
    assert "CASE WHEN COUNT(*) = 1" in sql
    # no arbitrary TOP1-based provenance anywhere in the repository
    assert "TOP 1 RTRIM(LTRIM(S.B7_DOC))" not in _REPO_SOURCE
    # runtime mapping goes through the domain fail-closed resolver
    assert "resolve_inventory_provenance(" in _REPO_SOURCE


# ---------------------------------------------------------------------------
# PAGE — DAVI bound 50 vs owner API bound 500
# ---------------------------------------------------------------------------


def test_page01_owner_tier_remains_500():
    tier = PaginationTierService.get("page_50_500")
    assert tier.le == 500 and tier.default == 50


def test_page02_davi_page_size_50_valid_and_default():
    action = _action("list_supplies_inventory_adjustments")
    ok = validate_arguments(
        action, {"start_date": "2026-01-01", "end_date": "2026-01-31",
                 "page_size": 50}
    )
    assert ok["page_size"] == 50
    defaulted = validate_arguments(
        action, {"start_date": "2026-01-01", "end_date": "2026-01-31"}
    )
    assert defaulted["page_size"] == 50


def test_page03_davi_page_size_51_rejected_owner_never_called(monkeypatch):
    action = _action("list_supplies_inventory_adjustments")
    with pytest.raises(ArgumentValidationError):
        validate_arguments(
            action, {"start_date": "2026-01-01", "end_date": "2026-01-31",
                     "page_size": 51}
        )

    class _Spy:
        def __init__(self):
            self.calls = []

        def execute(self, *, action_id, validated_arguments):
            self.calls.append(validated_arguments)
            return CatalogActionExecutionResult(outcome="ok", payload={})

    set_actions_for_tests(_actions())
    secret = "sec"
    monkeypatch.setattr(
        "app.application.external_capabilities.dynamic_information."
        "execute_service.candidate_token_secret",
        lambda: secret,
    )
    token = mint_candidate_token(
        action_id=action.action_id, actor_id="u1", secret=secret,
        ttl_seconds=60,
    )
    spy = _Spy()
    with pytest.raises(GovernedExecutionError):
        execute_delpi_information(
            candidate_token=token,
            arguments={
                "start_date": "2026-01-01",
                "end_date": "2026-01-31",
                "page_size": 51,
            },
            actor_id="u1",
            catalog_action_executor=spy,
        )
    assert spy.calls == []


# ---------------------------------------------------------------------------
# TM — raw movement_type/cf/user_name not model-visible
# ---------------------------------------------------------------------------


def test_tm01_raw_fields_absent_after_projection():
    fields = tuple(
        _ops()["get_product_internal_movements"]["approvedResponseFields"]
    )
    raw = {
        "items": [
            {
                "branch": "01",
                "location": "01",
                "document": "INVENT",
                "issue_date": "20261001",
                "product_code": "P1",
                "product_description": "Item",
                "unit": "UN",
                "movement_type": "999",
                "cf": "RE0",
                "user_name": "joao.silva",
                "quantity": 5.0,
                "production_order": "",
                "movement_category": "inventory_adjustment",
                "movement_direction": "inbound",
                "movement_label": "Ajuste de inventário",
                "inventory_adjustment_nature": "surplus",
            }
        ],
        "page": 1,
        "page_size": 50,
        "total": 1,
        "total_pages": 1,
    }
    projected = apply_approved_field_projection(raw, approved_fields=fields)
    dumped = json.dumps(projected)
    for forbidden in ("movement_type", "cf", "user_name"):
        assert f'"{forbidden}"' not in dumped
    assert "999" not in dumped
    assert "joao.silva" not in dumped


def test_tm02_semantic_fields_remain_projected():
    fields = tuple(
        _ops()["get_product_internal_movements"]["approvedResponseFields"]
    )
    raw = {
        "items": [
            {
                "movement_category": "inventory_adjustment",
                "movement_direction": "inbound",
                "movement_label": "Ajuste de inventário",
                "inventory_adjustment_nature": "surplus",
                "branch": "01",
                "document": "INVENT",
                "issue_date": "20261001",
                "product_code": "P1",
                "product_description": "Item",
                "unit": "UN",
                "location": "01",
                "quantity": 5.0,
                "production_order": "",
            }
        ],
        "page": 1,
        "page_size": 50,
        "total": 1,
        "total_pages": 1,
    }
    projected = apply_approved_field_projection(raw, approved_fields=fields)
    item = projected["items"][0]
    for required in (
        "movement_category",
        "movement_direction",
        "movement_label",
        "inventory_adjustment_nature",
    ):
        assert required in item


# ---------------------------------------------------------------------------
# BATCH — deferred from DAVI, owner API untouched
# ---------------------------------------------------------------------------


def test_batch01_owner_route_and_openapi_still_exist():
    spec = json.loads(
        (_API_ROOT / "app/content/openapi_baseline.json").read_text(encoding="utf-8")
    )
    op_ids = {o["operationId"] for o in spec["operations"]}
    assert _BATCH_ID in op_ids


def test_batch02_absent_from_davi_operations():
    assert _BATCH_ID not in _ops()


def test_batch03_present_once_in_explicitly_not_approved():
    entries = [
        e
        for e in _allow()["explicitlyNotApproved"]
        if e["operationId"] == _BATCH_ID
    ]
    assert len(entries) == 1
    assert entries[0]["coverageDisposition"] == "DEFER"
    assert entries[0]["primaryBlocker"] == (
        "CAPABILITY_NOT_PRODUCT_FROZEN_FOR_DAVI"
    )


def test_batch05_retrieval_never_returns_batch():
    # Batch intent phrase previously bound to its semanticAliases.
    hits = retrieve_eligible_actions(
        "materiais de várias OPs", _actions(), top_k=10
    )
    assert all(a.operation_id != _BATCH_ID for a, _ in hits)
    # Sibling positive: the single-OP operation remains retrievable.
    single = retrieve_eligible_actions(
        "empenhos da OP", _actions(), top_k=10
    )
    assert any(
        a.operation_id == "list_production_order_operation_materials"
        for a, _ in single
    )


def test_batch06_discover_mints_no_candidate_token_for_batch(monkeypatch):
    set_actions_for_tests(_actions())
    secret = "sec"
    monkeypatch.setattr(
        "app.application.external_capabilities.dynamic_information."
        "discover_service.candidate_token_secret",
        lambda: secret,
    )
    discovered = discover_delpi_information(
        query="materiais de várias OPs", top_k=10, actor_id=_ACTOR
    )
    candidates = discovered.get("candidates") or []
    assert all(c["action_id"] != _BATCH_ID for c in candidates)
    # governed invariant: discovery never mints a token for the batch —
    # decode every emitted token and pin the bound action.
    for c in candidates:
        payload = parse_candidate_token(
            c["candidate_token"], secret=secret, expected_actor_id=_ACTOR
        )
        assert payload["action_id"] != _BATCH_ID


def test_batch04_not_eligible_and_not_executable_through_broker(monkeypatch):
    actions = _actions()
    batch = next(a for a in actions if a.operation_id == _BATCH_ID)
    assert batch.davi_status != STATUS_DAVI_ELIGIBLE_READ
    assert not batch.executable

    set_actions_for_tests(actions)
    secret = "sec"
    monkeypatch.setattr(
        "app.application.external_capabilities.dynamic_information."
        "execute_service.candidate_token_secret",
        lambda: secret,
    )
    token = mint_candidate_token(
        action_id=batch.action_id, actor_id="u1", secret=secret,
        ttl_seconds=60,
    )
    with pytest.raises(GovernedExecutionError, match="not DAVI-eligible"):
        execute_delpi_information(
            candidate_token=token,
            arguments={"branch": "01", "production_orders": ["OP1"]},
            actor_id="u1",
            catalog_action_executor=object(),
        )


# ---------------------------------------------------------------------------
# COUNT — governance counts (allowlist / baseline / live are distinct)
# ---------------------------------------------------------------------------


def test_count01_allowlist_delta_exactly_expected():
    allow = _allow()
    assert allow["version"] == 21
    assert len(allow["operations"]) == 89
    ops = _ops()
    for kept in (
        "list_supplies_inventory_adjustments",
        "get_supplies_inventory_adjustments_summary",
        "list_production_order_operation_materials",
        "get_product_raw_material_set_shortages",
        "get_production_consumption_by_item",
        "get_production_consumption_top_items",
        "get_production_allocation_gaps",
        "get_production_orders_finished_without_consumption",
        "get_production_losses_records",
        "get_production_losses_top_materials",
        "get_supplies_safety_stock_item_details",
        "get_supplies_safety_stock_consumption_analysis_item_details",
    ):
        assert kept in ops
    for deferred in (
        "get_production_consumption_top_items_by_work_center",
        "get_production_consumption_top_items_validated",
        "get_supplies_purchase_requests_open_coverage",
        _BATCH_ID,
    ):
        assert deferred not in ops


def test_count02_baseline_and_live_counts_recomputed():
    baseline_eligible = {
        a.operation_id for a in _baseline_actions() if a.executable
    }
    assert len(baseline_eligible) == 87
    live_eligible = {a.operation_id for a in _actions() if a.executable}
    assert len(live_eligible) == 89


def test_coverage_decision_chain_records_corrective():
    coverage = _allow()["coverageDecision"]
    assert coverage["taskId"] == "DAVI-INVENTORY-MATERIAL-FLOW-CORRECTIVE-001"
    assert coverage["decision"] == (
        "DEFER_OP_MATERIALS_BATCH_AND_TIGHTEN_DAVI_PROJECTIONS"
    )
    prev = coverage["previousDecision"]
    assert prev["taskId"] == "DAVI-INVENTORY-MATERIAL-FLOW-IMPLEMENTATION-001"
    assert prev["decision"] == "PROMOTE_INVENTORY_MATERIAL_FLOW_READS"


# ---------------------------------------------------------------------------
# AUTHZ / SQL / MCP — surfaces unchanged
# ---------------------------------------------------------------------------


def test_authz01_routes_keep_api_delpi_access():
    source = (
        _API_ROOT
        / "app/interface/http/routes/supplies/inventory_adjustments_router.py"
    ).read_text(encoding="utf-8")
    assert source.count("require_permission(API_DELPI_ACCESS)") == 2


def test_sql01_generic_sql_not_promoted():
    ops = _ops()
    for oid in ops:
        assert oid != "execute_readonly_sql"
        assert "data/sql" not in oid


def test_mcp01_tool_count_exactly_two():
    import asyncio

    from app.interface.mcp.server import create_mcp_server

    tools = asyncio.run(create_mcp_server().list_tools())
    assert [t.name for t in tools] == [
        "discover_delpi_information",
        "execute_delpi_information",
    ]


# ---------------------------------------------------------------------------
# AUTHZ-02 — real FastAPI/TestClient runtime evidence (real middleware +
# require_permission; only identity/RBAC and use cases are faked, per the
# system-metadata convention in test_davi_system_metadata.py).
# ---------------------------------------------------------------------------


@contextmanager
def _inventory_route_authz(*, permissions: list[str]) -> Iterator[Any]:
    """Real app + real auth middleware; non-superadmin user with `permissions`."""
    from fastapi.testclient import TestClient

    import app.interface.http.routes.supplies.inventory_adjustments_router as inv_router

    claims = {
        "sub": _ACTOR,
        "email": "invcorr@example.com",
        "aud": "delpi-central",
        "name": "Inventory Corrective Test",
    }
    user = SimpleNamespace(is_superadmin=False, permissions=permissions)

    async def _rbac(_token: str) -> dict[str, Any]:
        return {
            "id": _ACTOR,
            "email": "invcorr@example.com",
            "name": "Inventory Corrective Test",
            "roles": [],
            "groups": [],
            "permissions": permissions,
            "is_superadmin": False,
            "rbac_unavailable": False,
        }

    list_uc = MagicMock()
    list_uc.execute.return_value = {
        "items": [],
        "page": 1,
        "page_size": 50,
        "total": 0,
        "total_pages": 0,
    }
    summary_uc = MagicMock()
    summary_uc.execute.return_value = {
        "summary": {},
        "by_month": [],
        "by_branch": [],
        "by_nature": [],
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
                inv_router,
                "build_list_inventory_adjustments_use_case",
                return_value=list_uc,
            )
        )
        stack.enter_context(
            patch.object(
                inv_router,
                "build_get_inventory_adjustments_summary_use_case",
                return_value=summary_uc,
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
        # once-only (same convention as the system-metadata authz tests).
        yield TestClient(app)


_INVENTORY_ROUTES = (
    "/supplies/inventory-adjustments?start_date=2026-01-01&end_date=2026-01-31",
    "/supplies/inventory-adjustments/summary?start_date=2026-01-01&end_date=2026-01-31",
)


@pytest.mark.parametrize(
    ("permissions", "expected"),
    [
        (["api-delpi.access"], 200),
        ([], 403),
        (["dashboard-supplies.view"], 403),
    ],
)
def test_authz02_inventory_adjustment_routes_runtime_matrix(
    permissions, expected
):
    """Real middleware + require_permission: API_DELPI_ACCESS holder → 200;
    no permission → 403; dashboard-supplies.view alone → 403 (pins that the
    routes use API_DELPI_ACCESS directly, not KPI_SUPPLIES_ACCESS)."""
    with _inventory_route_authz(permissions=permissions) as client:
        for path in _INVENTORY_ROUTES:
            response = client.get(
                path,
                headers={"Authorization": "Bearer end-user-token"},
            )
            assert response.status_code == expected, (
                path,
                permissions,
                expected,
            )
