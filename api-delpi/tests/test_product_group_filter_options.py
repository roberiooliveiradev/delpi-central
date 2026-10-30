"""Cobertura da extensão aditiva do filtro por grupo (CSV → IN) e do
endpoint oficial de opções de filtro do catálogo de produtos."""

from __future__ import annotations

import json
from unittest.mock import MagicMock, patch

from app.infrastructure.persistence.totvs.product_repositories.product_repository import (
    ProductRepository,
)


def _body(response) -> dict:
    return json.loads(response.body.decode())


# ---------------------------------------------------------------------------
# Repository — group_code único (compat) e lista (OR)
# ---------------------------------------------------------------------------


def test_search_products_repository_single_group_backward_compat() -> None:
    repo = ProductRepository()
    repo.execute_one = MagicMock(return_value={"total": 0})
    repo.execute_query = MagicMock(return_value=[])

    with patch.object(ProductRepository, "_connect"):
        repo.search_products(group="3019", page=1, page_size=10)

    sql = repo.execute_one.call_args[0][0]
    params = repo.execute_one.call_args[0][1]
    assert "SB1.B1_GRUPO = ?" in sql
    assert "IN" not in sql.split("B1_GRUPO")[1][:20]
    assert "3019" in params


def test_search_products_repository_group_list_uses_in() -> None:
    repo = ProductRepository()
    repo.execute_one = MagicMock(return_value={"total": 0})
    repo.execute_query = MagicMock(return_value=[])

    with patch.object(ProductRepository, "_connect"):
        repo.search_products(groups=["3019", "3020", "3050"], page=1, page_size=10)

    sql = repo.execute_one.call_args[0][0]
    params = repo.execute_one.call_args[0][1]
    assert "SB1.B1_GRUPO IN (?, ?, ?)" in sql
    for code in ("3019", "3020", "3050"):
        assert code in params


def test_search_products_repository_group_list_single_value() -> None:
    repo = ProductRepository()
    repo.execute_one = MagicMock(return_value={"total": 0})
    repo.execute_query = MagicMock(return_value=[])

    with patch.object(ProductRepository, "_connect"):
        repo.search_products(groups=["3019"], page=1, page_size=10)

    sql = repo.execute_one.call_args[0][0]
    assert "SB1.B1_GRUPO = ?" in sql


def test_search_products_repository_ignores_blank_groups() -> None:
    repo = ProductRepository()
    repo.execute_one = MagicMock(return_value={"total": 0})
    repo.execute_query = MagicMock(return_value=[])

    with patch.object(ProductRepository, "_connect"):
        repo.search_products(groups=["", "  "], page=1, page_size=10)

    sql = repo.execute_one.call_args[0][0]
    assert "B1_GRUPO" not in sql


# ---------------------------------------------------------------------------
# Repository — fetch_product_filter_options
# ---------------------------------------------------------------------------


def test_fetch_product_filter_options_returns_distinct_sorted() -> None:
    repo = ProductRepository()
    repo.execute_query = MagicMock(
        return_value=[
            {"group_code": "3020", "product_type": "PA"},
            {"group_code": "3019", "product_type": "MP"},
            {"group_code": "3020", "product_type": "PI"},
            {"group_code": None, "product_type": None},
        ]
    )

    with patch.object(ProductRepository, "_connect"):
        options = repo.fetch_product_filter_options()

    assert options["groups"] == ["3019", "3020"]
    assert options["types"] == ["MP", "PA", "PI"]


def test_fetch_product_filter_options_empty_source() -> None:
    repo = ProductRepository()
    repo.execute_query = MagicMock(return_value=[])

    with patch.object(ProductRepository, "_connect"):
        options = repo.fetch_product_filter_options()

    assert options == {"groups": [], "types": []}


# ---------------------------------------------------------------------------
# Rota — parsing CSV do group_code
# ---------------------------------------------------------------------------


def _run_search_route(**overrides):
    from app.interface.http.routes.product_routes import search_products_route

    captured: dict = {}

    use_case = MagicMock()
    result = MagicMock()
    result.to_dict.return_value = {"items": [], "total": 0, "page": 1, "page_size": 50}
    use_case.execute.side_effect = lambda dto: captured.setdefault("dto", dto) or result

    params = dict(
        code=None,
        group_code=None,
        subgroup=None,
        product_type=None,
        description=None,
        customer_reference=None,
        view="engineering",
        page=1,
        page_size=50,
        sort=None,
        direction=None,
    )
    params.update(overrides)

    with patch(
        "app.interface.http.routes.product_routes.build_search_products_use_case",
        return_value=use_case,
    ):
        response = search_products_route(**params)

    return response, captured


def test_search_route_parses_group_code_csv_into_list() -> None:
    _, captured = _run_search_route(group_code="3019, 3020")
    dto = captured["dto"]
    assert dto.group_codes == ["3019", "3020"]
    assert dto.group_code is None


def test_search_route_single_group_code_keeps_scalar_compat() -> None:
    _, captured = _run_search_route(group_code="3019")
    dto = captured["dto"]
    assert dto.group_code == "3019"
    assert dto.group_codes == ["3019"]


def test_search_route_rejects_invalid_group_code() -> None:
    response, captured = _run_search_route(group_code="A" * 11)
    assert "dto" not in captured
    body = _body(response)
    assert response.status_code == 400
    assert body["success"] is False


# ---------------------------------------------------------------------------
# Rota — /products/filter-options
# ---------------------------------------------------------------------------


def test_filter_options_route_returns_envelope_with_groups_and_types() -> None:
    from app.interface.http.routes.product_routes import get_product_filter_options_route

    use_case = MagicMock()
    use_case.execute.return_value = {"groups": ["3019"], "types": ["PA", "MP"]}

    with patch(
        "app.interface.http.routes.product_routes.build_product_filter_options_use_case",
        return_value=use_case,
    ):
        response = get_product_filter_options_route()

    body = _body(response)
    assert body["success"] is True
    assert body["data"]["groups"] == ["3019"]
    assert body["data"]["types"] == ["PA", "MP"]
