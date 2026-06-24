from app.infrastructure.persistence.totvs.supplies_repositories.stock_value_query_repository import (
    StockValueQueryRepository,
)


def test_build_estimation_meta_aggregates_branches() -> None:
    repo = StockValueQueryRepository()
    meta = repo._build_estimation_meta(
        [
            {
                "branch": "01",
                "closing_base_date": "20260228",
                "closing_base_value": 100.0,
                "bridge_value": -20.0,
                "period_net_value": -10.0,
                "official_closure_date": "20260228",
                "official_closure_value": 100.0,
                "official_closure_available": 1,
                "official_closure_on_period_end": 0,
            },
            {
                "branch": "02",
                "closing_base_date": "20260228",
                "closing_base_value": 200.0,
                "bridge_value": -30.0,
                "period_net_value": -15.0,
                "official_closure_date": "20260228",
                "official_closure_value": 200.0,
                "official_closure_available": 1,
                "official_closure_on_period_end": 0,
            },
        ]
    )

    assert meta["closing_base_value"] == 300.0
    assert meta["bridge_value"] == -50.0
    assert meta["period_net_value"] == -25.0
    assert meta["official_closure_available"] is True
    assert meta["official_closure_value"] == 300.0
    assert len(meta["by_branch_breakdown"]) == 2


def test_merge_branch_with_breakdown_attaches_fields() -> None:
    repo = StockValueQueryRepository()
    merged = repo._merge_branch_with_breakdown(
        [
            {
                "branch": "01",
                "total_stock_value": 70.0,
                "total_stock_quantity": 1.0,
                "total_records": 1,
                "total_products": 1,
                "total_locations": 1,
            }
        ],
        [
            {
                "branch": "01",
                "closing_base_date": "20260228",
                "closing_base_value": 100.0,
                "bridge_value": -20.0,
                "period_net_value": -10.0,
                "official_closure_date": "20260228",
                "official_closure_value": 100.0,
                "official_closure_available": True,
                "official_closure_on_period_end": False,
            }
        ],
    )

    assert merged[0]["total_stock_value"] == 70.0
    assert merged[0]["closing_base_value"] == 100.0
    assert merged[0]["bridge_value"] == -20.0
