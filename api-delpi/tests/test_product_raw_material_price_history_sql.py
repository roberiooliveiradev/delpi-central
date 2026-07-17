from __future__ import annotations

from unittest.mock import MagicMock, patch

from app.infrastructure.persistence.totvs.product_repositories.product_raw_material_price_repository import (
    ProductRawMaterialPriceRepository,
)


@patch.object(ProductRawMaterialPriceRepository, "execute_batch_query")
def test_fetch_purchase_price_history_default_keeps_issue_basis(
    mock_execute: MagicMock,
) -> None:
    mock_execute.return_value = []
    repo = ProductRawMaterialPriceRepository()
    with repo:
        repo.fetch_purchase_price_history(
            "10010005",
            "20250701",
            "20260701",
            branch="01",
            limit=24,
        )

    sql, params = mock_execute.call_args.args
    assert "D1_EMISSAO >=" in sql
    assert "D1_TIPO = 'N'" not in sql
    assert "D1_FORNECE) = ?" not in sql
    assert params[0] == 24
    assert "10010005" in params
    assert "01" in params


@patch.object(ProductRawMaterialPriceRepository, "execute_batch_query")
def test_fetch_purchase_price_history_supplier_entry_basis(
    mock_execute: MagicMock,
) -> None:
    mock_execute.return_value = []
    repo = ProductRawMaterialPriceRepository()
    with repo:
        repo.fetch_purchase_price_history(
            "10010005",
            "20250701",
            "20260701",
            branch="01",
            limit=500,
            supplier_code="F001",
            supplier_store="01",
            date_basis="entry",
        )

    sql, params = mock_execute.call_args.args
    assert "D1_DTDIGIT >=" in sql
    assert "D1_TIPO = 'N'" in sql
    assert "D1_FORNECE) = ?" in sql
    assert "D1_LOJA) = ?" in sql
    assert "D1_VUNIT" in sql
    assert "R_E_C_N_O_ DESC" in sql
    order_by_clause = sql.split("ORDER BY", 1)[1]
    order_columns = [part.strip() for part in order_by_clause.split(",")]
    assert len(order_columns) == len(set(order_columns)), (
        "ORDER BY não pode repetir colunas (SQL Server erro 169)"
    )
    assert params == (
        500,
        "10010005",
        "20250701",
        "20260701",
        "000019",
        "001149",
        "01",
        "F001",
        "01",
    )
