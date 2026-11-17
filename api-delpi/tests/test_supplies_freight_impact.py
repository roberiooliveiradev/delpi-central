from app.application.services.supplies.freight_impact_service import (
    compose_freight_impact,
)
from app.infrastructure.persistence.totvs.supplies_repositories.freight_impact_repository import (
    MAX_INVOICES,
    build_freight_impact_sql,
)


def row(doc: str, purchase: float, freight: float, month: str = "20261104") -> dict:
    return {
        "branch": "01",
        "invoice_document": doc,
        "invoice_series": "1",
        "supplier_code": "000001",
        "supplier_store": "01",
        "supplier_name": "Fornecedor BR",
        "issue_date": month,
        "purchase_cost": purchase,
        "freight_cost": freight,
        "cte_count": 1 if freight else 0,
    }


def test_sql_uses_all_national_purchases_as_denominator_and_links_cte_items():
    sql, params = build_freight_impact_sql(["01", "02"], "2026-11-01", "2026-11-30")
    assert "FROM SF1010 F1" in sql
    assert "INNER JOIN SD1010 D1" in sql
    assert "SA2.A2_EST IN" in sql
    assert "F1.F1_ESPECIE = 'SPED'" in sql
    assert "F1.F1_TIPO = 'N'" in sql
    assert "D1.D1_TIPO = 'N'" in sql
    assert "F8.F8_TIPO = 'F'" in sql
    assert "SELECT DISTINCT" in sql
    assert "CTI.D1_ITEMORI" in sql
    assert "LEFT JOIN FREIGHT_AGG" in sql
    assert "P.issue_date" in sql
    assert f"TOP ({MAX_INVOICES + 1})" in sql
    assert sql.count("?") == len(params)
    assert params[-4:] == ("20261101", "20261130", "01", "02")


def test_invalid_branches_are_rejected():
    for branches in ([], ["all"], ["01", "03"]):
        try:
            build_freight_impact_sql(branches, "2026-11-01", "2026-11-30")
        except ValueError:
            pass
        else:
            raise AssertionError("expected fail closed for branch")


def test_summary_denominator_includes_invoices_without_freight():
    result = compose_freight_impact(
        [row("001", 100, 10), row("002", 900, 0)],
        branches=["01"], date_from="2026-11-01", date_to="2026-11-30",
        page=1, page_size=1,
    )
    assert result["summary"]["purchases_total"] == 1000
    assert result["summary"]["freight_total"] == 10
    assert result["summary"]["freight_pct"] == 1
    assert result["summary"]["with_freight_count"] == 1
    assert result["summary"]["without_freight_count"] == 1
    assert result["total"] == 2
    assert len(result["items"]) == 1


def test_invalid_base_is_disclosed_not_used_in_percentage():
    result = compose_freight_impact(
        [row("001", 100, 5), row("002", 0, 20)],
        branches=["01"], date_from="2026-11-01", date_to="2026-11-30",
        page=1, page_size=25,
    )
    assert result["summary"]["freight_pct"] == 5
    assert result["summary"]["invalid_base_count"] == 1
    assert result["items"][-1]["freight_pct"] is None


def test_monthly_uses_weighted_ratio_and_matches_overall():
    result = compose_freight_impact(
        [
            row("001", 100, 10, "20261015"),
            row("002", 900, 0, "20261017"),
            row("003", 100, 20, "20261103"),
        ],
        branches=["01"], date_from="2026-10-01", date_to="2026-11-30",
        page=1, page_size=25,
    )
    assert result["monthly"][0]["freight_pct"] == 1
    assert result["monthly"][1]["freight_pct"] == 20
    assert result["summary"]["freight_pct"] == 2.73
