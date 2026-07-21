from __future__ import annotations

from unittest.mock import MagicMock, patch

from app.infrastructure.persistence.totvs.supplies_repositories.safety_stock_query_repository import (
    SafetyStockQueryRepository,
)


def test_map_item_row_includes_warehouse_99_and_blocked_flag() -> None:
    row = {
        "product_code": " 90000001 ",
        "product_description": "Parafuso",
        "product_type": "MP",
        "unit": "PC",
        "product_group": "GRP",
        "blocked_raw": "1",
        "safety_stock": 100.0,
        "primary_stock": 50.0,
        "work_in_process_stock": 20.0,
        "warehouse_50_stock": 5.0,
        "warehouse_98_stock": 5.0,
        "warehouse_99_stock": 10.0,
        "work_in_process_committed": 3.0,
        "work_in_process_available": 17.0,
        "deficit_quantity": 50.0,
        "status": "below_safety_stock",
    }

    mapped = SafetyStockQueryRepository._map_item_row(row, "01")

    assert mapped["product_code"] == "90000001"
    assert mapped["blocked"] is True
    assert mapped["warehouse_99_stock"] == 10.0
    assert mapped["status"] == "below_safety_stock"
    assert mapped["branch"] == "01"


@patch.object(SafetyStockQueryRepository, "execute_query")
def test_fetch_items_uses_parametrized_query(mock_execute_query: MagicMock) -> None:
    mock_execute_query.return_value = []

    repo = SafetyStockQueryRepository()
    with repo:
        repo.fetch_items(
            branch="01",
            include_blocked=False,
            product_group=None,
            unit=None,
            search="abc",
            status="below_safety_stock",
            include_without_safety_stock=True,
            sort_by="product_code",
            sort_direction="asc",
            offset=0,
            page_size=10,
        )

    sql, params = mock_execute_query.call_args.args
    assert "OFFSET ? ROWS FETCH NEXT ? ROWS ONLY" in sql
    assert "B1_TIPO = 'MP'" in sql
    assert "%abc%" in params
    assert "below_safety_stock" in params
    assert params[-2:] == [0, 10]


@patch.object(SafetyStockQueryRepository, "execute_one")
@patch.object(SafetyStockQueryRepository, "execute_query")
def test_fetch_summary_returns_deficit_by_unit(
    mock_execute_query: MagicMock,
    mock_execute_one: MagicMock,
) -> None:
    mock_execute_one.return_value = {
        "total_materials": 2,
        "with_safety_stock": 1,
        "without_safety_stock": 1,
        "below_safety_stock": 1,
        "at_safety_stock": 0,
        "above_safety_stock": 0,
        "with_primary_stock": 1,
        "without_primary_stock": 1,
        "with_work_in_process_stock": 0,
    }
    mock_execute_query.return_value = [
        {"unit": "PC", "material_count": 1, "deficit_quantity": 10.0},
    ]

    repo = SafetyStockQueryRepository()
    with repo:
        result = repo.fetch_summary(
            branch="01",
            include_blocked=False,
            product_group=None,
            unit=None,
            search=None,
            status=None,
            include_without_safety_stock=True,
        )

    assert result["below_safety_stock"] == 1
    assert result["deficit_by_unit"] == [
        {"unit": "PC", "material_count": 1, "deficit_quantity": 10.0},
    ]


def test_map_open_commitment_formats_date_and_uses_qtdeori_fields() -> None:
    mapped = SafetyStockQueryRepository._map_open_commitment(
        {
            "branch": "01",
            "product_code": "10020113",
            "product_description": "Cabo",
            "warehouse": "01",
            "production_order": "OP001",
            "origin_production_order": "OP000",
            "commitment_date": "20260720",
            "unit": "M",
            "original_quantity": 100.0,
            "open_quantity": 40.0,
            "consumed_quantity": 60.0,
            "lot": "L1",
            "commitment_sequence": "001",
            "preserved_balance": 0.0,
            "finished_production_order": "OP00101001",
            "finished_product_code": "90261255",
            "finished_order_observation": "PED CLIENTE XYZ",
        }
    )

    assert mapped["commitment_date"] == "2026-07-20"
    assert mapped["original_quantity"] == 100.0
    assert mapped["open_quantity"] == 40.0
    assert mapped["consumed_quantity"] == 60.0
    assert mapped["production_order"] == "OP001"
    assert mapped["finished_production_order"] == "OP00101001"
    assert mapped["finished_product_code"] == "90261255"
    assert mapped["finished_order_observation"] == "PED CLIENTE XYZ"


@patch.object(SafetyStockQueryRepository, "execute_query")
def test_fetch_open_commitments_binds_branch_and_product(
    mock_execute_query: MagicMock,
) -> None:
    mock_execute_query.return_value = []
    repo = SafetyStockQueryRepository()
    with repo:
        repo.fetch_open_commitments(branch="01", product_code="10020113")

    sql, params = mock_execute_query.call_args.args
    assert "SD4010" in sql
    assert "D4_QTDEORI" in sql
    assert params == ["01", "10020113"]


def test_map_linked_supplier_formats_date_and_keeps_null_purchase_fields() -> None:
    with_purchase = SafetyStockQueryRepository._map_linked_supplier(
        {
            "product_code": "10010005",
            "supplier_code": "F001",
            "supplier_store": "01",
            "supplier_part_number": " PN-ACME-001 ",
            "trade_name": "ACME",
            "legal_name": "ACME LTDA",
            "document": "12345678000199",
            "has_last_purchase": 1,
            "last_purchase_date": "20260710",
            "last_unit_price": 12.5,
            "last_quantity": 10.0,
            "last_total_value": 125.0,
            "last_invoice_number": "000123",
            "last_invoice_series": "1",
        }
    )
    without_purchase = SafetyStockQueryRepository._map_linked_supplier(
        {
            "product_code": "10010005",
            "supplier_code": "F002",
            "supplier_store": "01",
            "trade_name": "BETA",
            "legal_name": "BETA SA",
            "document": "99887766000155",
            "has_last_purchase": 0,
            "last_purchase_date": None,
            "last_unit_price": None,
            "last_quantity": None,
            "last_total_value": None,
            "last_invoice_number": None,
            "last_invoice_series": None,
        }
    )

    assert with_purchase["last_purchase_date"] == "2026-07-10"
    assert with_purchase["last_unit_price"] == 12.5
    assert with_purchase["has_last_purchase"] is True
    assert with_purchase["supplier_part_number"] == "PN-ACME-001"
    assert without_purchase["supplier_part_number"] == ""
    assert without_purchase["has_last_purchase"] is False
    assert without_purchase["last_purchase_date"] is None
    assert without_purchase["last_unit_price"] is None
    assert without_purchase["last_total_value"] is None


@patch.object(SafetyStockQueryRepository, "execute_query")
def test_fetch_linked_suppliers_binds_branch_and_product(
    mock_execute_query: MagicMock,
) -> None:
    mock_execute_query.return_value = []
    repo = SafetyStockQueryRepository()
    with repo:
        repo.fetch_linked_suppliers(branch="01", product_code="10010005")

    sql, params = mock_execute_query.call_args.args
    assert "SA5010" in sql
    assert "SD1010" in sql
    assert "D1_VUNIT" in sql
    assert params == ["01", "10010005", "01", "10010005", "01"]


def test_map_consumption_analysis_row() -> None:
    mapped = SafetyStockQueryRepository._map_consumption_analysis_row(
        {
            "product_code": "10020113",
            "product_description": "Material",
            "product_type": "MP",
            "unit": "PC",
            "product_group": "GRP",
            "blocked_raw": "",
            "safety_stock": 80,
            "lead_time_days": 12,
            "primary_stock": 10,
            "work_in_process_stock": 5,
            "warehouse_50_stock": 1,
            "warehouse_98_stock": 2,
            "warehouse_99_stock": 3,
            "available_stock": 15,
            "work_in_process_committed": 0,
            "work_in_process_available": 5,
            "deficit_quantity": 65,
            "status": "below_safety_stock",
            "period_consumption": 1300,
            "movement_count": 8,
            "first_movement_date": "20250720",
            "last_movement_date": "20260710",
        },
        "01",
    )
    assert mapped["lead_time_days"] == 12.0
    assert mapped["period_consumption"] == 1300.0
    assert mapped["first_movement_date"] == "2025-07-20"
    assert mapped["last_movement_date"] == "2026-07-10"


@patch.object(SafetyStockQueryRepository, "execute_query")
def test_fetch_consumption_analysis_rows_binds_period(
    mock_execute_query: MagicMock,
) -> None:
    mock_execute_query.return_value = []
    repo = SafetyStockQueryRepository()
    with repo:
        repo.fetch_consumption_analysis_rows(
            branch="01",
            period_start="20250718",
            include_blocked=False,
            product_group=None,
            unit=None,
            search=None,
            product_code="10020113",
        )

    sql, params = mock_execute_query.call_args.args
    assert "SD3010" in sql
    assert "BZ_PE" in sql
    assert "safety_stock <> 0" in sql
    assert params[:4] == ["01", "01", "01", "20250718"]
    assert "10020113" in params


@patch.object(SafetyStockQueryRepository, "execute_query")
def test_fetch_open_purchase_orders_for_branch_omits_product_param(
    mock_execute_query: MagicMock,
) -> None:
    mock_execute_query.return_value = []
    repo = SafetyStockQueryRepository()
    with repo:
        repo.fetch_open_purchase_orders_for_branch(branch="01")

    sql, params = mock_execute_query.call_args.args
    assert "SC7010" in sql
    assert "C7_PRODUTO) =" not in sql
    assert params == ["01"]


@patch.object(SafetyStockQueryRepository, "execute_query")
def test_fetch_open_commitments_for_branch_omits_product_param(
    mock_execute_query: MagicMock,
) -> None:
    mock_execute_query.return_value = []
    repo = SafetyStockQueryRepository()
    with repo:
        repo.fetch_open_commitments_for_branch(branch="02")

    sql, params = mock_execute_query.call_args.args
    assert "SD4010" in sql
    assert "D4_COD =" not in sql
    assert params == ["02"]


@patch.object(SafetyStockQueryRepository, "execute_query")
def test_fetch_materials_for_projection_batch_binds_branch_twice(
    mock_execute_query: MagicMock,
) -> None:
    mock_execute_query.return_value = [
        {
            "product_code": "10020113",
            "product_description": "MP TESTE",
            "product_type": "MP",
            "unit": "PC",
            "product_group": "GRP",
            "blocked_raw": "",
            "safety_stock": 10,
            "primary_stock": 5,
            "work_in_process_stock": 0,
            "warehouse_50_stock": 0,
            "warehouse_98_stock": 0,
            "warehouse_99_stock": 0,
            "available_stock": 5,
            "work_in_process_committed": 0,
            "work_in_process_available": 0,
            "deficit_quantity": 5,
            "status": "below_safety_stock",
            "secondary_unit": "CX",
            "conversion_factor": 12,
            "conversion_type": "M",
        }
    ]
    repo = SafetyStockQueryRepository()
    with repo:
        rows = repo.fetch_materials_for_projection_batch(
            branch="01",
            include_blocked=False,
            product_group=None,
            unit=None,
            search=None,
            include_without_safety_stock=True,
        )

    sql, params = mock_execute_query.call_args.args
    assert "B1_SEGUM" in sql
    assert "OFFSET" not in sql.upper()
    assert params == ["01", "01"]
    assert len(rows) == 1
    assert rows[0]["available_stock"] == 5.0
    assert rows[0]["secondary_unit"] == "CX"
    assert rows[0]["conversion_factor"] == 12.0
