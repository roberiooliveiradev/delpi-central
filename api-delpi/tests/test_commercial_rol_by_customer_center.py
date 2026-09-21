"""ROL por centro do cliente — SQL canônico + mapeamento das regras de classificação."""

from __future__ import annotations

from unittest.mock import patch

import pytest

from app.application.dto.commercial.get_rol_by_customer_center_request import (
    GetRolByCustomerCenterRequest,
)
from app.application.use_cases.commercial.get_commercial_rol_by_customer_center_use_case import (
    GetCommercialRolByCustomerCenterUseCase,
)
from app.domain.totvs.protheus_customer_center import (
    UNCLASSIFIED_CUSTOMER_CENTER_NAME,
)
from app.infrastructure.persistence.totvs.commercial_repositories.commercial_rol_by_customer_center_repository import (
    CommercialRolByCustomerCenterRepository,
)


def _capture_sql(
    request: GetRolByCustomerCenterRequest, rows=None
) -> tuple[str, tuple, object]:
    repository = CommercialRolByCustomerCenterRepository()
    captured: dict[str, object] = {}

    def fake_execute_query(sql, params):
        captured["sql"] = sql
        captured["params"] = params
        return list(rows or [])

    with patch.object(
        CommercialRolByCustomerCenterRepository, "__enter__", return_value=repository
    ):
        with patch.object(
            CommercialRolByCustomerCenterRepository, "__exit__", return_value=False
        ):
            with patch.object(
                repository, "execute_query", side_effect=fake_execute_query
            ):
                result = repository.get_rol_by_customer_center(request)
    return str(captured["sql"]), tuple(captured["params"]), result


def test_sql_classifies_with_left_sa7_and_zc0_keys() -> None:
    sql, params, _ = _capture_sql(
        GetRolByCustomerCenterRequest(
            start_date="2026-08-01",
            end_date="2026-08-31",
        )
    )
    assert sql.count("SA7010") == 2
    assert sql.count("ZC0010") == 2
    assert "LEFT JOIN (" in sql
    assert "ZC0.customer_code = SA7C.customer_code" in sql
    assert "ZC0.customer_store = SA7C.customer_store" in sql
    assert "ZC0.customer_center = SA7C.customer_center" in sql
    assert "A7_FILIAL" not in sql
    assert "ZC0_FILIAL" not in sql
    assert "D_E_L_E_T_ = ''" in sql
    assert "ISNULL(D2.D2_TIPO, '') <> 'D'" in sql
    assert "D1_CF IN ('1201', '2201')" in sql
    assert UNCLASSIFIED_CUSTOMER_CENTER_NAME in sql
    assert "D2.D2_EMISSAO BETWEEN" in sql or "D2.D2_EMISSAO" in sql
    assert "FULL OUTER JOIN DEVOLUCOES" in sql
    assert "20260801" in params
    assert "20260831" in params


def test_sql_always_joins_classification_even_without_center_filter() -> None:
    sql, _, _ = _capture_sql(
        GetRolByCustomerCenterRequest(
            start_date="2026-08-01",
            end_date="2026-08-31",
        )
    )
    assert "SA7010" in sql
    assert "INNER JOIN (" not in sql


def test_filter_customer_store_center_and_product() -> None:
    sql, params, _ = _capture_sql(
        GetRolByCustomerCenterRequest(
            start_date="2026-08-01",
            end_date="2026-08-31",
            customer_codes=["000001"],
            customer_stores=["01"],
            customer_centers=["1304"],
            product_codes=["90264255"],
        )
    )
    assert "D2.D2_CLIENTE IN" in sql
    assert "D2.D2_LOJA IN" in sql
    assert "D1.D1_LOJA IN" in sql
    assert "SA7C.customer_center IN" in sql
    assert "D2.D2_COD IN" in sql
    assert "000001" in params
    assert "01" in params
    assert "1304" in params
    assert "90264255" in params
    assert "1700" not in params


def test_empty_period_returns_zero_totals() -> None:
    _, _, result = _capture_sql(
        GetRolByCustomerCenterRequest(
            start_date="2026-01-01",
            end_date="2026-01-31",
        ),
        rows=[],
    )
    assert result.items == ()
    assert result.total_rol == 0.0
    assert result.unclassified_rol == 0.0
    assert result.items_count == 0


def _row(**overrides):
    base = {
        "CUSTOMER_CODE": "000001",
        "CUSTOMER_STORE": "01",
        "CUSTOMER_NAME": "WEG",
        "CUSTOMER_CENTER": "1304",
        "CUSTOMER_CENTER_NAME": "CENTRO WEG 1304",
        "CENTER_ACTIVE": 1,
        "PRODUCT_CODE": "90264255",
        "PRODUCT_NAME": "PRODUTO A",
        "ROL_ITEM": 100.0,
        "GROSS_ITEM": 120.0,
        "QTY_ITEM": 10.0,
        "UNIT": "MI",
        "MIXED_UNITS": 0,
        "TOTAL_ROL": 100.0,
        "TOTAL_GROSS": 120.0,
        "TOTAL_QTY": 10.0,
        "ITEMS_COUNT": 1,
        "UNCLASSIFIED_ROL": 0.0,
        "UNCLASSIFIED_QTY": 0.0,
        "RNK": 1,
    }
    base.update(overrides)
    return base


def test_maps_classified_center() -> None:
    _, _, result = _capture_sql(
        GetRolByCustomerCenterRequest(
            start_date="2026-08-01",
            end_date="2026-08-31",
            group_by="center_product",
        ),
        rows=[_row()],
    )
    item = result.items[0]
    assert item.customer_center == "1304"
    assert item.customer_center_name == "CENTRO WEG 1304"
    assert item.center_active is True
    assert item.product_code == "90264255"
    assert item.rol == 100.0


def test_same_customer_store_different_centers() -> None:
    _, _, result = _capture_sql(
        GetRolByCustomerCenterRequest(
            start_date="2026-08-01",
            end_date="2026-08-31",
            group_by="center_product",
        ),
        rows=[
            _row(
                CUSTOMER_CENTER="1200",
                CUSTOMER_CENTER_NAME="CENTRO WEG 1200",
                PRODUCT_CODE="90200000",
                ROL_ITEM=50,
                TOTAL_ROL=80,
                ITEMS_COUNT=2,
                RNK=1,
            ),
            _row(
                CUSTOMER_CENTER="1304",
                CUSTOMER_CENTER_NAME="CENTRO WEG 1304",
                PRODUCT_CODE="90264255",
                ROL_ITEM=30,
                TOTAL_ROL=80,
                ITEMS_COUNT=2,
                RNK=2,
            ),
        ],
    )
    centers = {item.customer_center for item in result.items}
    assert centers == {"1200", "1304"}
    assert result.items_count == 2


def test_same_product_different_customers_keep_distinct_centers() -> None:
    _, _, result = _capture_sql(
        GetRolByCustomerCenterRequest(
            start_date="2026-08-01",
            end_date="2026-08-31",
            group_by="center_product",
        ),
        rows=[
            _row(CUSTOMER_CODE="000001", CUSTOMER_CENTER="1200", RNK=1, ITEMS_COUNT=2),
            _row(
                CUSTOMER_CODE="000002",
                CUSTOMER_CENTER="1505",
                CUSTOMER_CENTER_NAME="CENTRO 1505",
                RNK=2,
                ITEMS_COUNT=2,
            ),
        ],
    )
    by_customer = {
        item.customer_code: item.customer_center for item in result.items
    }
    assert by_customer == {"000001": "1200", "000002": "1505"}


def test_empty_a7_xcent_is_unclassified() -> None:
    _, _, result = _capture_sql(
        GetRolByCustomerCenterRequest(
            start_date="2026-08-01",
            end_date="2026-08-31",
        ),
        rows=[
            _row(
                CUSTOMER_CENTER=None,
                CUSTOMER_CENTER_NAME=UNCLASSIFIED_CUSTOMER_CENTER_NAME,
                CENTER_ACTIVE=None,
                UNCLASSIFIED_ROL=40.0,
                UNCLASSIFIED_QTY=4.0,
                ROL_ITEM=40.0,
                TOTAL_ROL=40.0,
            )
        ],
    )
    item = result.items[0]
    assert item.customer_center is None
    assert item.customer_center_name == UNCLASSIFIED_CUSTOMER_CENTER_NAME
    assert item.center_active is None
    assert result.unclassified_rol == 40.0


def test_missing_sa7_is_unclassified() -> None:
    _, _, result = _capture_sql(
        GetRolByCustomerCenterRequest(
            start_date="2026-08-01",
            end_date="2026-08-31",
        ),
        rows=[
            _row(
                CUSTOMER_CENTER="",
                CUSTOMER_CENTER_NAME="",
                CENTER_ACTIVE=None,
                UNCLASSIFIED_ROL=10.0,
            )
        ],
    )
    item = result.items[0]
    assert item.customer_center is None
    assert item.customer_center_name == UNCLASSIFIED_CUSTOMER_CENTER_NAME


def test_missing_or_inactive_zc0_keeps_center_code() -> None:
    _, _, result = _capture_sql(
        GetRolByCustomerCenterRequest(
            start_date="2026-08-01",
            end_date="2026-08-31",
        ),
        rows=[
            _row(
                CUSTOMER_CENTER="1304",
                CUSTOMER_CENTER_NAME="1304",
                CENTER_ACTIVE=0,
            )
        ],
    )
    item = result.items[0]
    assert item.customer_center == "1304"
    assert item.center_active is False
    assert item.customer_center_name == "1304"


def test_use_case_rejects_missing_dates() -> None:
    use_case = GetCommercialRolByCustomerCenterUseCase(repository=None)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="start_date"):
        use_case.execute(GetRolByCustomerCenterRequest())


def test_use_case_rejects_invalid_group_by() -> None:
    use_case = GetCommercialRolByCustomerCenterUseCase(repository=None)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="group_by"):
        use_case.execute(
            GetRolByCustomerCenterRequest(
                start_date="2026-08-01",
                end_date="2026-08-31",
                group_by="family",
            )
        )
