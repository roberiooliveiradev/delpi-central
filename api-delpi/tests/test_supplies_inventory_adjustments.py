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
from app.infrastructure.persistence.totvs.supplies_repositories.inventory_adjustments_repository import (
    InventoryAdjustmentsRepository,
    _summary_select,
)

_API_ROOT = Path(__file__).resolve().parents[1]


# ---------------------------------------------------------------------------
# Domain classifier — classify_internal_movement
# ---------------------------------------------------------------------------


def test_inventory_adjustment_surplus_de0_invent() -> None:
    """DE0/TM 499 = entrada (sobra) — comprovado contra o relatório."""
    result = classify_internal_movement(
        cf="DE0", tm="499", document="INVENT", production_order=""
    )
    assert result.category == MOVEMENT_CATEGORY_INVENTORY_ADJUSTMENT
    assert result.direction == "inbound"
    assert result.inventory_adjustment_nature == "surplus"
    assert result.label


def test_inventory_adjustment_shortage_re0_invent() -> None:
    """RE0/TM 999 = saída (furo) — comprovado contra o relatório."""
    result = classify_internal_movement(
        cf="RE0", tm="999", document="INVENT", production_order=""
    )
    assert result.category == MOVEMENT_CATEGORY_INVENTORY_ADJUSTMENT
    assert result.direction == "outbound"
    assert result.inventory_adjustment_nature == "shortage"


def test_inventory_adjustment_cf_is_consistent_with_tm_sign() -> None:
    """CF e TM concordam no INVENT: DE0/499 entrada; RE0/999 saída."""
    surplus = classify_internal_movement(
        cf="DE0", tm="499", document="INVENT", production_order="000123"
    )
    shortage = classify_internal_movement(
        cf="RE0", tm="999", document="INVENT", production_order="000123"
    )
    assert surplus.inventory_adjustment_nature == "surplus"
    assert surplus.direction == movement_direction("499")
    assert shortage.inventory_adjustment_nature == "shortage"
    assert shortage.direction == movement_direction("999")


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


@pytest.mark.parametrize("nature", ["shortage", "surplus"])
def test_summary_use_case_forwards_nature_filter(nature: str) -> None:
    repo = _FakeAdjustmentsRepo()
    GetInventoryAdjustmentsSummaryUseCase(repo).execute(_request(nature=nature))
    assert repo.summary_call is not None
    assert repo.summary_call["nature"] == nature


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
    # Aggregate/item presentation must not duplicate the raw CF rule here.
    # D3_CF belongs only to the canonical domain classifier.
    assert "D3_CF" not in source


def test_summary_sql_enforces_gross_and_net_value_identities() -> None:
    sql = _summary_select("")
    assert "ABS(SD3.D3_CUSTO1)" in sql
    assert "-ABS(SD3.D3_CUSTO1)" in sql
    assert "AS gross_adjustment_value" in sql
    assert "AS net_adjustment_value" in sql
    # The generated SQL contains the canonical domain classifier, not an
    # independently authored repository mapping.
    assert "THEN 'surplus'" in sql
    assert "THEN 'shortage'" in sql


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


class _RegressionInventoryAdjustmentsRepository(InventoryAdjustmentsRepository):
    def __init__(self, totals: dict) -> None:
        super().__init__()
        self._totals = totals
        self.calls: list[tuple[str, tuple]] = []

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        return None

    def execute_one(self, query: str, params: tuple = ()) -> dict:
        self.calls.append((query, params))
        return dict(self._totals)

    def execute_query(self, query: str, params: tuple = ()) -> list[dict]:
        self.calls.append((query, params))
        return []


def test_repository_regression_summary_maps_net_gross_and_nature_totals() -> None:
    repo = _RegressionInventoryAdjustmentsRepository(
        {
            "adjustment_count": 1451,
            "shortage_count": 474,
            "surplus_count": 977,
            "gross_adjustment_quantity": 1039642.353,
            "net_adjustment_quantity": 59690.229,
            "gross_adjustment_value": 3991042.739,
            "net_adjustment_value": 173164.323,
            "shortage_quantity": 489976.062,
            "shortage_value": 1908939.208,
            "surplus_quantity": 549666.291,
            "surplus_value": 2082103.531,
        }
    )
    result = repo.fetch_adjustment_summary(
        date_start="20260101",
        date_end_exclusive="20261008",
        branch="01",
        product_code=None,
        warehouse=None,
        nature=None,
    )
    summary = result["summary"]
    assert summary["adjustment_count"] == 1451
    assert summary["shortage_count"] == 474
    assert summary["surplus_count"] == 977
    assert summary["shortage_quantity"] == pytest.approx(489976.062)
    assert summary["surplus_quantity"] == pytest.approx(549666.291)
    assert summary["net_quantity"] == pytest.approx(
        summary["surplus_quantity"] - summary["shortage_quantity"]
    )
    assert summary["shortage_value"] == pytest.approx(1908939.208)
    assert summary["surplus_value"] == pytest.approx(2082103.531)
    assert summary["net_value"] == pytest.approx(
        summary["surplus_value"] - summary["shortage_value"]
    )
    assert summary["gross_value"] == pytest.approx(
        summary["surplus_value"] + summary["shortage_value"]
    )


@pytest.mark.parametrize("nature", ["shortage", "surplus"])
def test_repository_nature_filter_is_bound_as_parameter(nature: str) -> None:
    repo = InventoryAdjustmentsRepository()
    where, params = repo._filter_sql(
        date_start="20260101",
        date_end_exclusive="20261008",
        branch="01",
        product_code="10080034",
        warehouse="01",
        nature=nature,
    )
    assert "= ?" in where
    assert params[-1] == nature
    assert "20260101" in params
    assert "20261008" in params
    assert "01" in params
    assert "10080034" in params


def test_frozen_scenario_2026_09_semantics() -> None:
    """Regressão do recorte real: filial 02, 2026-09-04..2026-09-29,
    armazéns 01+99, doc INVENT — 45 movimentos provados contra o
    relatório Protheus (colunas ENTRADAS/SAÍDAS).

    Expectativa derivada da regra corrigida (DE0=entrada/sobra,
    RE0=saída/furo) sobre os totais de quantidade do relatório:

      surplus_quantity  = 28.798,380  (ENTRADAS, 13 linhas TM499/DE0)
      shortage_quantity = 147.248,364 (SAÍDAS, 32 linhas TM999/RE0)
      net_quantity      = -118.449,984
    """
    repo = _RegressionInventoryAdjustmentsRepository(
        {
            "adjustment_count": 45,
            "shortage_count": 32,
            "surplus_count": 13,
            "gross_adjustment_quantity": 176046.744,
            "net_adjustment_quantity": -118449.984,
            "gross_adjustment_value": 33336.889,
            "net_adjustment_value": -28376.193,
            "shortage_quantity": 147248.364,
            "shortage_value": 30856.541,
            "surplus_quantity": 28798.380,
            "surplus_value": 2480.348,
        }
    )
    result = repo.fetch_adjustment_summary(
        date_start="20260904",
        date_end_exclusive="20260930",
        branch="02",
        product_code=None,
        warehouse=None,
        nature=None,
    )
    summary = result["summary"]
    assert summary["adjustment_count"] == 45
    assert summary["surplus_count"] == 13
    assert summary["shortage_count"] == 32
    assert summary["surplus_quantity"] == pytest.approx(28798.380)
    assert summary["shortage_quantity"] == pytest.approx(147248.364)
    assert summary["net_quantity"] == pytest.approx(-118449.984)
    assert summary["net_value"] == pytest.approx(
        summary["surplus_value"] - summary["shortage_value"]
    )
    assert summary["net_value"] < 0


def test_domain_nature_sql_matches_proven_cf_semantics() -> None:
    """DE0 = sobra/entrada, RE0 = furo/saída (relatório Protheus)."""
    nature = InventoryAdjustmentClassification.NATURE_SQL_EXPRESSION
    assert "WHEN RTRIM(LTRIM(SD3.D3_CF)) = 'DE0' THEN 'surplus'" in nature
    assert "WHEN RTRIM(LTRIM(SD3.D3_CF)) = 'RE0' THEN 'shortage'" in nature
    signed_qty = InventoryAdjustmentClassification.SIGNED_QUANTITY_SQL_EXPRESSION
    assert "WHEN RTRIM(LTRIM(SD3.D3_CF)) = 'DE0' THEN SD3.D3_QUANT" in signed_qty
    assert "WHEN RTRIM(LTRIM(SD3.D3_CF)) = 'RE0' THEN -SD3.D3_QUANT" in signed_qty
    signed_val = InventoryAdjustmentClassification.SIGNED_VALUE_SQL_EXPRESSION
    assert "WHEN RTRIM(LTRIM(SD3.D3_CF)) = 'DE0' THEN SD3.D3_CUSTO1" in signed_val
    assert "WHEN RTRIM(LTRIM(SD3.D3_CF)) = 'RE0' THEN -SD3.D3_CUSTO1" in signed_val


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
