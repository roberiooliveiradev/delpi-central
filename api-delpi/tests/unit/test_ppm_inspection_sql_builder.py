from app.infrastructure.persistence.totvs.ppm_repositories.ppm_inspection_sql_builder import (
    build_inspection_apont_ctes,
)


def test_build_inspection_apont_ctes_without_filters() -> None:
    bundle = build_inspection_apont_ctes()
    assert "ct_inspecao_final AS" in bundle.ct_inspecao_cte
    assert "apont_inspecao AS" in bundle.apont_inspecao_cte
    assert "INSPE" in bundle.ct_inspecao_cte
    assert "FINAL" in bundle.ct_inspecao_cte
    assert "B1_TIPO IN ('PA', 'PI')" in bundle.apont_inspecao_cte
    assert bundle.params == []


def test_build_inspection_apont_ctes_with_branch_and_products() -> None:
    bundle = build_inspection_apont_ctes(
        branch="01",
        product_codes=["50232465", "50233615"],
    )
    assert "AND HB.HB_FILIAL = ?" in bundle.ct_inspecao_cte
    assert "AND SH6.H6_FILIAL = ?" in bundle.apont_inspecao_cte
    assert "AND SH6.H6_PRODUTO IN (?, ?)" in bundle.apont_inspecao_cte
    assert bundle.params == ["01", "01", "50232465", "50233615"]


def test_build_inspection_apont_ctes_with_product_prefix() -> None:
    bundle = build_inspection_apont_ctes(product_prefix="9048")
    assert "AND SH6.H6_PRODUTO LIKE ?" in bundle.apont_inspecao_cte
    assert bundle.params == ["9048%"]
