from app.infrastructure.persistence.totvs.ppm_repositories.ppm_nc_query import (
    build_nc_where_clause,
)


def test_build_nc_where_clause_returns_tuple_params() -> None:
    where, params = build_nc_where_clause(
        ppm_type="internal",
        branch=None,
        date_start="20260601",
        date_end_exclusive="20260610",
    )

    assert isinstance(params, tuple)
    assert "QI2_OCORRE" in where

    prod_params = ["20260601", "20260610"]
    merged = tuple(list(params) + prod_params)

    assert merged == ("20260601", "20260610", "20260601", "20260610")


def test_build_nc_where_clause_filters_by_product_prefix() -> None:
    where, params = build_nc_where_clause(
        ppm_type="external",
        branch=None,
        date_start="20260601",
        date_end_exclusive="20260610",
        product_prefix="9048",
    )

    assert "QI2_ITEM LIKE ?" in where
    assert params[-1] == "9048%"
