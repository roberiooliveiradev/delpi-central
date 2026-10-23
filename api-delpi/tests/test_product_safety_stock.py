"""Consulta geral de estoque de segurança (GET /products/{code}/safety-stock).

Cobre DTO, use case, SQL, rota e regressão de escopo (a análise de
Suprimentos é MP ou prefixo 3019 — este read geral não tem filtro de tipo).
"""

from __future__ import annotations

import json
from unittest.mock import MagicMock, patch

import pytest

from app.application.dto.product.get_product_safety_stock_request import (
    GetProductSafetyStockRequest,
)
from app.application.use_cases.product.get_product_safety_stock_use_case import (
    GetProductSafetyStockUseCase,
    ProductTypeMismatchError,
)
from app.infrastructure.persistence.totvs.product_repositories.product_safety_stock_sql import (
    product_safety_stock_sql,
)


def _record(*, product_type: str = "MC", by_branch: dict | None = None) -> dict:
    return {
        "product_code": "20060063",
        "description": "LAMPADA LED T8 18W",
        "product_type": product_type,
        "unit": "PC",
        "blocked": False,
        "safety_stock_by_branch": by_branch if by_branch is not None else {"01": 6.0, "02": 0.0},
    }


def _use_case(record) -> GetProductSafetyStockUseCase:
    repo = MagicMock()
    repo.fetch_safety_stock.return_value = record
    return GetProductSafetyStockUseCase(repository=repo)


# --------------------------------------------------------------------------
# DTO
# --------------------------------------------------------------------------


def test_dto_normalizes_product_type_uppercase() -> None:
    dto = GetProductSafetyStockRequest(code="20060063", product_type="mc")
    assert dto.product_type == "MC"


def test_dto_accepts_absent_product_type() -> None:
    dto = GetProductSafetyStockRequest(code="20060063")
    assert dto.product_type is None
    assert dto.branch is None


@pytest.mark.parametrize("bad", ["M", "MCP", "!", "M ", "mp1"])
def test_dto_rejects_invalid_product_type(bad: str) -> None:
    with pytest.raises(ValueError):
        GetProductSafetyStockRequest(code="20060063", product_type=bad)


def test_dto_rejects_empty_code() -> None:
    with pytest.raises(ValueError):
        GetProductSafetyStockRequest(code="  ")


# --------------------------------------------------------------------------
# SQL builder
# --------------------------------------------------------------------------


def test_sql_has_no_product_type_predicate() -> None:
    """Read geral não pode carregar a restrição MP de Suprimentos."""
    sql, _ = product_safety_stock_sql("20060063", ("01", "02"))
    assert "B1_TIPO" in sql  # projetado, mas nunca filtrado
    assert "B1_TIPO = 'MP'" not in sql
    assert "B1_TIPO = ?" not in sql


def test_sql_is_parameterized_and_scoped() -> None:
    sql, params = product_safety_stock_sql("20060063", ("01", "02"))
    assert "IN (?, ?)" in sql
    assert "B1_COD)) = ?" in sql
    assert "LTRIM(RTRIM(SBZ.BZ_FILIAL)) <> ''" in sql
    assert "D_E_L_E_T_ = ''" in sql
    assert params == ("01", "02", "20060063")


def test_sql_single_branch_scope() -> None:
    sql, params = product_safety_stock_sql("20060063", ("02",))
    assert "IN (?)" in sql and "IN (?, ?)" not in sql
    assert params == ("02", "20060063")


# --------------------------------------------------------------------------
# Use case
# --------------------------------------------------------------------------


def test_uc_returns_none_when_product_missing() -> None:
    uc = _use_case(None)
    assert uc.execute(GetProductSafetyStockRequest(code="99999999")) is None


def test_uc_registered_value_and_zero_distinguished() -> None:
    uc = _use_case(_record(by_branch={"01": 6.0, "02": 0.0}))
    result = uc.execute(GetProductSafetyStockRequest(code="20060063"))
    by_branch = {b["branch"]: b for b in result["branches"]}
    assert by_branch["01"]["safety_stock"] == 6.0
    assert by_branch["01"]["safety_stock_data_state"] == "registered"
    assert by_branch["02"]["safety_stock"] == 0.0
    assert by_branch["02"]["safety_stock_data_state"] == "registered"


def test_uc_missing_sbz_record_is_not_zero() -> None:
    uc = _use_case(_record(by_branch={"01": 6.0}))
    result = uc.execute(GetProductSafetyStockRequest(code="20060063"))
    by_branch = {b["branch"]: b for b in result["branches"]}
    assert by_branch["02"]["safety_stock"] is None
    assert by_branch["02"]["safety_stock_data_state"] == "missing"


def test_uc_branch_filter_limits_scope() -> None:
    uc = _use_case(_record(by_branch={"01": 6.0, "02": 0.0}))
    dto = GetProductSafetyStockRequest(code="20060063", branch="01")
    result = uc.execute(dto)
    assert [b["branch"] for b in result["branches"]] == ["01"]
    uc._repository.fetch_safety_stock.assert_called_once_with("20060063", ("01",))


def test_uc_default_scope_covers_both_branches() -> None:
    uc = _use_case(_record())
    uc.execute(GetProductSafetyStockRequest(code="20060063"))
    assert uc._repository.fetch_safety_stock.call_args.args[1] == ("01", "02")


def test_uc_product_type_filter_match() -> None:
    uc = _use_case(_record(product_type="MC"))
    result = uc.execute(
        GetProductSafetyStockRequest(code="20060063", product_type="MC")
    )
    assert result["product_type"] == "MC"


def test_uc_product_type_mismatch_raises() -> None:
    uc = _use_case(_record(product_type="MC"))
    with pytest.raises(ProductTypeMismatchError):
        uc.execute(GetProductSafetyStockRequest(code="20060063", product_type="MP"))


def test_uc_non_mp_product_is_served() -> None:
    """Caso original: II/MC devem responder — não é falta de autorização."""
    uc = _use_case(_record(product_type="II"))
    result = uc.execute(GetProductSafetyStockRequest(code="30191665"))
    assert result["product_type"] == "II"


# --------------------------------------------------------------------------
# Route
# --------------------------------------------------------------------------


def _call_route(**kwargs):
    from app.interface.http.routes.product_routes import safety_stock

    return safety_stock("20060063", **kwargs)


def _body(response) -> dict:
    return json.loads(response.body.decode())


@patch(
    "app.interface.http.routes.product_routes.build_get_product_safety_stock_use_case"
)
def test_route_success_envelope(mock_build) -> None:
    use_case = MagicMock()
    use_case.execute.return_value = {
        "product_code": "20060063",
        "description": "LAMPADA LED T8 18W",
        "product_type": "MC",
        "unit": "PC",
        "blocked": False,
        "branches": [
            {"branch": "01", "safety_stock": 6.0, "safety_stock_data_state": "registered"},
        ],
    }
    mock_build.return_value = use_case

    response = _call_route(branch=None, product_type=None)
    body = _body(response)

    assert response.status_code == 200
    assert body["meta"]["operationId"] == "get_product_safety_stock"
    assert body["meta"]["entity"] == "product_safety_stock"
    assert body["data"]["branches"][0]["safety_stock_data_state"] == "registered"


@patch(
    "app.interface.http.routes.product_routes.build_get_product_safety_stock_use_case"
)
def test_route_product_not_found_404(mock_build) -> None:
    use_case = MagicMock()
    use_case.execute.return_value = None
    mock_build.return_value = use_case

    response = _call_route(branch=None, product_type=None)
    body = _body(response)

    assert response.status_code == 404
    assert body["error"]["code"] == "PRODUCT_NOT_FOUND"
    assert "Matéria-prima" not in body["message"]


@patch(
    "app.interface.http.routes.product_routes.build_get_product_safety_stock_use_case"
)
def test_route_type_mismatch_is_404_not_403(mock_build) -> None:
    """Tipo incompatível é ausência semântica — nunca confundir com AuthZ."""
    use_case = MagicMock()
    use_case.execute.side_effect = ProductTypeMismatchError("tipo divergente")
    mock_build.return_value = use_case

    response = _call_route(branch=None, product_type="MP")
    body = _body(response)

    assert response.status_code == 404
    assert body["error"]["code"] == "PRODUCT_TYPE_MISMATCH"


def test_route_invalid_product_type_400() -> None:
    response = _call_route(branch=None, product_type="X")
    assert response.status_code == 400


# --------------------------------------------------------------------------
# AuthZ — backend é o único gate (API_DELPI_ACCESS, mesmo do /stock)
# --------------------------------------------------------------------------


def test_route_denies_user_without_api_delpi_access() -> None:
    from types import SimpleNamespace

    from app.interface.http.routes.product_routes import safety_stock

    user = SimpleNamespace(is_superadmin=False, permissions=[], rbac_unavailable=False)
    with patch(
        "delpi_auth.authorization.resolve_user_context", return_value=user
    ), pytest.raises(Exception, match="Forbidden"):
        safety_stock("20060063", branch=None, product_type=None)


def test_route_denies_unauthenticated() -> None:
    from app.interface.http.routes.product_routes import safety_stock

    with patch(
        "delpi_auth.authorization.resolve_user_context", return_value=None
    ), pytest.raises(Exception, match="Unauthorized"):
        safety_stock("20060063", branch=None, product_type=None)


# --------------------------------------------------------------------------
# Regressão MP — Suprimentos preserva a restrição
# --------------------------------------------------------------------------


def test_supplies_analysis_universe_is_not_the_unrestricted_product_read() -> None:
    from app.domain.totvs.protheus_product_types import (
        PRODUCT_TYPE_RAW_MATERIAL,
        SUPPLIES_OTD_PRODUCT_CODE_PREFIX,
    )
    from app.infrastructure.persistence.totvs.supplies_repositories.safety_stock_sql import (
        materials_base_cte,
        safety_stock_product_universe_clause,
    )

    clause, params = safety_stock_product_universe_clause()
    sql, cte_params = materials_base_cte(branch="all")
    assert " OR " in clause
    assert params == [PRODUCT_TYPE_RAW_MATERIAL, SUPPLIES_OTD_PRODUCT_CODE_PREFIX]
    assert clause in sql
    assert cte_params == params

    general_sql, _ = product_safety_stock_sql("20060063", ("01", "02"))
    assert "B1_TIPO = ?" not in general_sql
    assert SUPPLIES_OTD_PRODUCT_CODE_PREFIX not in general_sql
