import pytest

from app.domain.services.ppm_inspection_denominator import (
    CT_INSPECAO_NOME_SQL_LIKE,
    PPM_PRODUCED_B1_TIPOS,
    is_eligible_product_type,
)


@pytest.mark.parametrize(
    ("tipo", "expected"),
    [
        ("PA", True),
        ("PI", True),
        ("pa", True),
        ("MP", False),
        ("", False),
        (None, False),
    ],
)
def test_is_eligible_product_type(tipo: str | None, expected: bool) -> None:
    assert is_eligible_product_type(tipo) is expected


def test_ppm_includes_pa_and_pi() -> None:
    assert PPM_PRODUCED_B1_TIPOS == frozenset({"PA", "PI"})


def test_ct_filter_matches_playbook() -> None:
    assert "INSPE" in CT_INSPECAO_NOME_SQL_LIKE
    assert "FINAL" in CT_INSPECAO_NOME_SQL_LIKE


def test_sql_b1_tipo_in_clause() -> None:
    from app.domain.services.ppm_inspection_denominator import sql_b1_tipo_in_clause

    assert sql_b1_tipo_in_clause() == "('PA', 'PI')"
