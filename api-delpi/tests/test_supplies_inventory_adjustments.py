"""DAVI-INVENTORY-MATERIAL-FLOW-IMPLEMENTATION-001 — ajustes de inventário.

Cobre a classificação canônica de movimentações internas SD3
(domain-owned), o serviço de natureza furo/sobra, a validação do
período fechado (<=366 dias), os use cases, os contratos de rota e a
geração de SQL do repositório — positive + sibling + negative.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

from app.application.dto.supplies.inventory_adjustments_request import (
    InventoryAdjustmentsRequest,
)
from app.application.use_cases.supplies.get_inventory_adjustments_summary_use_case import (
    GetInventoryAdjustmentsSummaryUseCase,
)
from app.application.use_cases.supplies.inventory_adjustments_shared import (
    MAX_PERIOD_DAYS,
    resolve_required_period,
)
from app.application.use_cases.supplies.list_inventory_adjustments_use_case import (
    ListInventoryAdjustmentsUseCase,
)
from app.domain.services.supplies.inventory_adjustment_service import (
    KNOWN_NATURES,
    InventoryAdjustmentClassification,
    nature_label,
    normalize_nature,
)
from app.domain.totvs.protheus_internal_movements import (
    MOVEMENT_CATEGORY_INVENTORY_ADJUSTMENT,
    MOVEMENT_CATEGORY_PRODUCTION_CONSUMPTION,
    MOVEMENT_CATEGORY_PRODUCTION_RECEIPT,
    MOVEMENT_CATEGORY_UNCLASSIFIED,
    MOVEMENT_CATEGORY_WAREHOUSE_TRANSFER,
    classify_internal_movement,
    movement_direction,
    movement_kind_filters,
)
from app.infrastructure.persistence.totvs.product_repositories.product_internal_movements_sql import (
    bind_internal_movement_filters,
)
from app.infrastructure.persistence.totvs.query_builder import QueryBuilder

_API_ROOT = Path(__file__).resolve().parents[1]


# ---------------------------------------------------------------------------
# Domain classifier — classify_internal_movement
# ---------------------------------------------------------------------------


def test_inventory_adjustment_surplus_re0_invent() -> None:
    result = classify_internal_movement(
        cf="RE0", tm="999", document="INVENT", production_order=""
    )
    assert result.category == MOVEMENT_CATEGORY_INVENTORY_ADJUSTMENT
    assert result.direction == "inbound"
    assert result.inventory_adjustment_nature == "surplus"
    assert result.label


def test_inventory_adjustment_shortage_de0_invent() -> None:
    result = classify_internal_movement(
        cf="DE0", tm="499", document="INVENT", production_order=""
    )
    assert result.category == MOVEMENT_CATEGORY_INVENTORY_ADJUSTMENT
    assert result.direction == "outbound"
    assert result.inventory_adjustment_nature == "shortage"


def test_inventory_adjustment_tm_is_not_nature_authority() -> None:
    """TM 999 também aparece no consumo; a natureza vem do CF, não do TM."""
    result = classify_internal_movement(
        cf="RE0", tm="999", document="INVENT", production_order="000123"
    )
    assert result.category == MOVEMENT_CATEGORY_INVENTORY_ADJUSTMENT
    assert result.inventory_adjustment_nature == "surplus"


def test_invent_doc_with_unknown_cf_stays_adjustment_without_nature() -> None:
    result = classify_internal_movement(
        cf="XXX", tm="100", document="INVENT", production_order=""
    )
    assert result.category == MOVEMENT_CATEGORY_INVENTORY_ADJUSTMENT
    assert result.inventory_adjustment_nature is None


def test_warehouse_transfer_excludes_invent_document() -> None:
    """DE0/RE0 fora do doc INVENT é transferência; dentro é ajuste."""
    transfer = classify_internal_movement(
        cf="RE0", tm="499", document="TRANSF", production_order=""
    )
    assert transfer.category == MOVEMENT_CATEGORY_WAREHOUSE_TRANSFER
    assert transfer.direction == "inbound"
    adjustment = classify_internal_movement(
        cf="RE0", tm="499", document="INVENT", production_order=""
    )
    assert adjustment.category == MOVEMENT_CATEGORY_INVENTORY_ADJUSTMENT


def test_warehouse_transfer_outbound_de0() -> None:
    result = classify_internal_movement(
        cf="DE0", tm="499", document="", production_order=""
    )
    assert result.category == MOVEMENT_CATEGORY_WAREHOUSE_TRANSFER
    assert result.direction == "outbound"


def test_production_receipt_pr0() -> None:
    result = classify_internal_movement(
        cf="PR0", tm="100", document="", production_order="000123"
    )
    assert result.category == MOVEMENT_CATEGORY_PRODUCTION_RECEIPT
    assert result.direction == "inbound"


def test_production_consumption_tm999_with_op() -> None:
    result = classify_internal_movement(
        cf="RE5", tm="999", document="", production_order="000123"
    )
    assert result.category == MOVEMENT_CATEGORY_PRODUCTION_CONSUMPTION
    assert result.direction == "outbound"


def test_tm999_without_op_is_unclassified() -> None:
    result = classify_internal_movement(
        cf="RE5", tm="999", document="", production_order=""
    )
    assert result.category == MOVEMENT_CATEGORY_UNCLASSIFIED


def test_unknown_combination_is_unclassified() -> None:
    result = classify_internal_movement(
        cf="ZZZ", tm="300", document="XYZ", production_order=""
    )
    assert result.category == MOVEMENT_CATEGORY_UNCLASSIFIED
    assert result.direction == "inbound"
    assert result.inventory_adjustment_nature is None


def test_movement_direction_sign_rule() -> None:
    assert movement_direction("100") == "inbound"
    assert movement_direction("499") == "inbound"
    assert movement_direction("500") == "outbound"
    assert movement_direction("999") == "outbound"
    assert movement_direction("") is None
    assert movement_direction(None) is None


# ---------------------------------------------------------------------------
# movement_kind_filters — specs declarativas consumidas pelo SQL
# ---------------------------------------------------------------------------


def test_kind_none_returns_none() -> None:
    assert movement_kind_filters(None) is None
    assert movement_kind_filters("") is None
    assert movement_kind_filters("  ") is None


def test_kind_warehouse_transfer_excludes_invent() -> None:
    spec = movement_kind_filters("warehouse_transfer")
    assert spec is not None
    assert set(spec["cf_in"]) == {"DE0", "RE0"}
    assert spec["doc_ne"] == "INVENT"


def test_kind_inventory_adjustment_filters_doc() -> None:
    spec = movement_kind_filters("inventory_adjustment")
    assert spec == {"doc_eq": "INVENT"}


def test_kind_production_receipt() -> None:
    spec = movement_kind_filters("production_receipt")
    assert spec == {"cf_eq": "PR0"}


def test_kind_production_consumption() -> None:
    spec = movement_kind_filters("production_consumption")
    assert spec is not None
    assert spec["tm_eq"] == "999"
    assert spec["doc_ne"] == "INVENT"
    assert spec["requires_production_order"] is True


def test_kind_invalid_raises() -> None:
    with pytest.raises(ValueError):
        movement_kind_filters("fiscal_invoice")


# ---------------------------------------------------------------------------
# SQL binder — o predicado kind sai da fonte canônica (sem INVENT leak)
# ---------------------------------------------------------------------------


def _movement_where(kind: str | None) -> tuple[str, tuple]:
    qb = QueryBuilder()
    bind_internal_movement_filters(
        qb,
        code="10090482",
        date_start=None,
        date_end=None,
        branch=None,
        location=None,
        tm=None,
        op=None,
        kind=kind,
    )
    return qb.build()


def test_warehouse_transfer_sql_excludes_invent() -> None:
    where, params = _movement_where("warehouse_transfer")
    assert "RTRIM(LTRIM(SD3.D3_CF)) IN" in where
    assert "RTRIM(LTRIM(SD3.D3_DOC)) <> ?" in where
    assert "INVENT" in params


def test_inventory_adjustment_sql_filters_doc() -> None:
    where, params = _movement_where("inventory_adjustment")
    assert "RTRIM(LTRIM(SD3.D3_DOC)) = ?" in where
    assert "INVENT" in params


def test_production_consumption_sql_requires_op() -> None:
    where, params = _movement_where("production_consumption")
    assert "RTRIM(LTRIM(SD3.D3_TM)) = ?" in where
    assert "RTRIM(LTRIM(SD3.D3_OP)) <> ''" in where
    assert "RTRIM(LTRIM(SD3.D3_DOC)) <> ?" in where
    assert "999" in params
    assert "INVENT" in params


# ---------------------------------------------------------------------------
# Nature — domain service
# ---------------------------------------------------------------------------


def test_known_natures() -> None:
    assert KNOWN_NATURES == frozenset({"shortage", "surplus"})


def test_normalize_nature_accepts_case_and_spaces() -> None:
    assert normalize_nature("shortage") == "shortage"
    assert normalize_nature(" Surplus ") == "surplus"
    assert normalize_nature("SURPLUS") == "surplus"
    assert normalize_nature(None) is None
    assert normalize_nature("") is None


def test_normalize_nature_rejects_unknown() -> None:
    with pytest.raises(ValueError):
        normalize_nature("adjustment")


def test_nature_label() -> None:
    assert nature_label("shortage") == "Furo de inventário"
    assert nature_label("surplus") == "Sobra de inventário"
    assert nature_label("other") == "Ajuste de inventário"
    assert nature_label(None) == "Ajuste de inventário"


def test_request_dto_normalizes_nature_and_branch() -> None:
    request = InventoryAdjustmentsRequest(nature=" Surplus ", branch="all")
    assert request.nature == "surplus"
    assert request.branch is None
    concrete = InventoryAdjustmentsRequest(branch="01")
    assert concrete.branch == "01"


def test_request_dto_rejects_unknown_nature() -> None:
    with pytest.raises(ValueError):
        InventoryAdjustmentsRequest(nature="perda")


# ---------------------------------------------------------------------------
# Período obrigatório — 366 dias, closed-open interno
# ---------------------------------------------------------------------------


def _request(**overrides) -> InventoryAdjustmentsRequest:
    base = {"start_date": "2026-01-01", "end_date": "2026-01-31"}
    base.update(overrides)
    return InventoryAdjustmentsRequest(**base)


def test_period_requires_both_dates() -> None:
    with pytest.raises(ValueError):
        resolve_required_period(_request(end_date=None))
    with pytest.raises(ValueError):
        resolve_required_period(_request(start_date=None))


def test_period_rejects_inverted_range() -> None:
    with pytest.raises(ValueError):
        resolve_required_period(
            _request(start_date="2026-02-01", end_date="2026-01-01")
        )


def test_period_rejects_invalid_date() -> None:
    with pytest.raises(ValueError):
        resolve_required_period(_request(start_date="not-a-date"))


def test_period_accepts_max_366_inclusive_days() -> None:
    """2026-01-01 .. 2026-12-31 = 365 dias; 366 = limite inclusivo."""
    start, end, end_exclusive = resolve_required_period(
        _request(start_date="2025-01-01", end_date="2026-01-01")
    )
    assert start == "20250101"
    assert end == "20260101"
    assert end_exclusive == "20260102"


def test_period_over_366_days_rejected() -> None:
    with pytest.raises(ValueError):
        resolve_required_period(
            _request(start_date="2025-01-01", end_date="2026-01-02")
        )


def test_period_end_is_exclusive_for_sql() -> None:
    _start, _end, end_exclusive = resolve_required_period(_request())
    assert end_exclusive == "20260201"


def test_max_period_days_constant() -> None:
    assert MAX_PERIOD_DAYS == 366


# ---------------------------------------------------------------------------
# Use cases — composição, paginação e datas ISO
# ---------------------------------------------------------------------------


class _FakeAdjustmentsRepo:
    def __init__(self) -> None:
        self.items_call: dict | None = None
        self.summary_call: dict | None = None

    def fetch_adjustment_items(self, **kwargs):
        self.items_call = kwargs
        return {
            "total": 2,
            "items": [
                {"issue_date": "20260115", "signed_quantity": -3.0},
                {"issue_date": "20260120", "signed_quantity": 5.0},
            ],
        }

    def fetch_adjustment_summary(self, **kwargs):
        self.summary_call = kwargs
        return {"summary": {"adjustment_count": 2}, "by_month": []}


def test_list_use_case_forwards_closed_open_period() -> None:
    repo = _FakeAdjustmentsRepo()
    result = ListInventoryAdjustmentsUseCase(repo).execute(
        _request(page=2, page_size=50)
    )
    assert repo.items_call is not None
    assert repo.items_call["date_start"] == "20260101"
    assert repo.items_call["date_end_exclusive"] == "20260201"
    assert repo.items_call["page"] == 2
    assert result["period_start"] == "2026-01-01"
    assert result["period_end"] == "2026-01-31"
    assert result["total"] == 2
    assert result["total_pages"] == 1


def test_list_use_case_caps_page_size_at_500() -> None:
    repo = _FakeAdjustmentsRepo()
    result = ListInventoryAdjustmentsUseCase(repo).execute(
        _request(page_size=9999)
    )
    assert repo.items_call is not None
    assert repo.items_call["page_size"] == 500
    assert result["page_size"] == 500


def test_list_use_case_page_size_500_allowed() -> None:
    """page_50_500 tier: 500 é máximo válido, não clamp silencioso a 50."""
    repo = _FakeAdjustmentsRepo()
    ListInventoryAdjustmentsUseCase(repo).execute(_request(page_size=500))
    assert repo.items_call is not None
    assert repo.items_call["page_size"] == 500


def test_list_use_case_normalizes_item_dates_to_iso() -> None:
    repo = _FakeAdjustmentsRepo()
    result = ListInventoryAdjustmentsUseCase(repo).execute(_request())
    assert result["items"][0]["issue_date"] == "2026-01-15"
    assert result["items"][1]["issue_date"] == "2026-01-20"


def test_summary_use_case_normalizes_period_dates_to_iso() -> None:
    repo = _FakeAdjustmentsRepo()
    result = GetInventoryAdjustmentsSummaryUseCase(repo).execute(_request())
    assert repo.summary_call is not None
    assert repo.summary_call["date_start"] == "20260101"
    assert repo.summary_call["date_end_exclusive"] == "20260201"
    assert result["period_start"] == "2026-01-01"
    assert result["period_end"] == "2026-01-31"
    assert result["summary"]["adjustment_count"] == 2


# ---------------------------------------------------------------------------
# Contratos de rota + OpenAPI
# ---------------------------------------------------------------------------


def test_routes_use_api_delpi_access_and_contract_builder() -> None:
    source = (
        _API_ROOT
        / "app/interface/http/routes/supplies/inventory_adjustments_router.py"
    ).read_text(encoding="utf-8")
    assert source.count("@require_permission(API_DELPI_ACCESS)") == 2
    assert "get_supplies_inventory_adjustments_summary" in source
    assert "list_supplies_inventory_adjustments" in source
    assert 'PAGE_SIZE_QUERY("page_50_500")' in source
    assert "resolve_period_dates" in source


def test_operation_ids_registered_in_route_contract_registry() -> None:
    source = (
        _API_ROOT / "app/interface/http/route_contract_registry.py"
    ).read_text(encoding="utf-8")
    assert '"get_supplies_inventory_adjustments_summary"' in source
    assert '"list_supplies_inventory_adjustments"' in source


def test_operations_present_in_live_openapi() -> None:
    from app.main import app

    paths = app.openapi()["paths"]
    summary = paths["/supplies/inventory-adjustments/summary"]["get"]
    listing = paths["/supplies/inventory-adjustments"]["get"]
    assert summary["operationId"] == "get_supplies_inventory_adjustments_summary"
    assert listing["operationId"] == "list_supplies_inventory_adjustments"


# ---------------------------------------------------------------------------
# Repositório — SQL canônico, sem regra duplicada fora do domínio
# ---------------------------------------------------------------------------


def test_repository_uses_domain_sql_expressions_not_adhoc() -> None:
    source = (
        _API_ROOT
        / "app/infrastructure/persistence/totvs/supplies_repositories/"
        / "inventory_adjustments_repository.py"
    ).read_text(encoding="utf-8")
    # As expressões de natureza/sinal vêm do domínio — não podem ser
    # reescritas inline no repositório.
    assert "InventoryAdjustmentClassification" in source
    assert "_NATURE = InventoryAdjustmentClassification" in source
    assert "_SIGNED_QTY = InventoryAdjustmentClassification" in source
    assert "_SIGNED_VAL = InventoryAdjustmentClassification" in source


def test_repository_filters_invent_doc_and_estorno() -> None:
    source = (
        _API_ROOT
        / "app/infrastructure/persistence/totvs/supplies_repositories/"
        / "inventory_adjustments_repository.py"
    ).read_text(encoding="utf-8")
    assert "RTRIM(LTRIM(SD3.D3_DOC)) = 'INVENT'" in source
    assert "D3_ESTORNO" in source
    assert "SD3.D_E_L_E_T_ = ''" in source
    # Proveniência SB7 fail-closed (documento+quantidade só quando inequívoco).
    assert "SB7010" in source
    for key in ("B7_FILIAL", "B7_COD", "B7_LOCAL", "B7_DATA"):
        assert key in source


def test_repository_binds_all_filters_as_parameters() -> None:
    source = (
        _API_ROOT
        / "app/infrastructure/persistence/totvs/supplies_repositories/"
        / "inventory_adjustments_repository.py"
    ).read_text(encoding="utf-8")
    bind = re.search(r"def _bind_filters\(.*?\) -> None:\n(.*?)def ", source, re.S)
    assert bind, "_bind_filters não localizado"
    body = bind.group(1)
    assert "?" in body
    # filtros por usuário nunca interpolados na SQL
    for field in ("branch", "product_code", "warehouse", "nature"):
        assert f'SD3." + {field}' not in body
        assert f"% {field}" not in body
        assert f".format({field}" not in body


def test_domain_nature_sql_matches_proven_cf_semantics() -> None:
    nature = InventoryAdjustmentClassification.NATURE_SQL_EXPRESSION
    assert "'RE0'" in nature and "surplus" in nature
    assert "'DE0'" in nature and "shortage" in nature
    signed_qty = InventoryAdjustmentClassification.SIGNED_QUANTITY_SQL_EXPRESSION
    assert "-SD3.D3_QUANT" in signed_qty
    signed_val = InventoryAdjustmentClassification.SIGNED_VALUE_SQL_EXPRESSION
    assert "-SD3.D3_CUSTO1" in signed_val


# ---------------------------------------------------------------------------
# Allowlist + DAVI wiring
# ---------------------------------------------------------------------------


def test_inventory_adjustment_ops_allowlisted_with_bounded_inputs() -> None:
    import json

    allow = json.loads(
        (_API_ROOT / "app/content/davi_external_read_allowlist.json").read_text(
            encoding="utf-8"
        )
    )
    ops = {o["operationId"]: o for o in allow["operations"]}
    for oid in (
        "get_supplies_inventory_adjustments_summary",
        "list_supplies_inventory_adjustments",
    ):
        entry = ops[oid]
        assert entry.get("executionMode") == "catalog_action"
        assert entry.get("approvedInputFields")
        assert "start_date" in entry["approvedInputFields"]
        assert "end_date" in entry["approvedInputFields"]
        assert "nature" in entry["approvedInputFields"]
        assert entry.get("approvedResponseFields")
        assert all("*" not in f for f in entry["approvedResponseFields"])
        assert entry.get("semanticAliases")
