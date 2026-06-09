"""Regressão H1–H13 — contrato Onda 14 (fixtures commitadas)."""

from tests.fixtures.drawing_hierarchical_regression_cases import (
    DRAWING_HIERARCHICAL_REGRESSION_CASES,
    case_ids,
    pdf_regression_cases,
    synthetic_regression_cases,
)


def test_h_cases_cover_playbook_matrix():
    ids = set(case_ids())

    for required in (
        "H1",
        "H2",
        "H3",
        "H4",
        "H6",
        "H7",
        "H8",
        "H9",
        "H10",
        "H11",
        "H12",
    ):
        assert required in ids or any(item.startswith(required) for item in ids)


def test_pdf_cases_have_expected_codes():
    for case in pdf_regression_cases():
        assert case.pdf
        assert case.expected_product_code
        assert case.pdf.endswith(".pdf")


def test_synthetic_cases_flags():
    h8 = next(item for item in synthetic_regression_cases() if item.id == "H8")
    h9 = next(item for item in synthetic_regression_cases() if item.id == "H9")
    h10 = next(item for item in synthetic_regression_cases() if item.id == "H10")

    assert h8.expected_product_code == "50232222"
    assert h8.fixture and "stampText" in h8.fixture
    assert h9.expect_conflict
    assert h10.expect_unresolved
    assert h10.expected_product_code is None


def test_regression_case_count():
    assert len(DRAWING_HIERARCHICAL_REGRESSION_CASES) >= 13
