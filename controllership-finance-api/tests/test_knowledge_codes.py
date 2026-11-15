"""Extração de códigos da pergunta — sem banco."""

from controllership_finance_app.domain.knowledge.search_codes import (
    extract_search_codes,
)
from clara_golden_set_r01_r15 import GOLDEN_SET, NEGATIVE_SET


def test_extract_tes_cfop_and_group_codes():
    assert extract_search_codes("TES 525") == ["525"]
    assert extract_search_codes("o que é a TES 3A8") == ["3A8"]
    assert extract_search_codes("o que é a TES 3a8") == ["3A8"]
    assert extract_search_codes("quais TES usam o CFOP 5124") == ["5124"]
    assert extract_search_codes("grupo 9035") == ["9035"]
    assert extract_search_codes("a TES 036 credita ICMS?") == ["036"]
    assert extract_search_codes("A seleção 9035 e TES 594 do R11") == [
        "9035",
        "594",
    ]


def test_extract_ignores_years_reports_and_dates():
    assert extract_search_codes("outubro 2026") == []
    assert extract_search_codes("status do fechamento de outubro 2026") == []
    assert extract_search_codes("o que é o relatório R10") == []
    assert extract_search_codes("R05 e R10") == []
    assert extract_search_codes("competência 2026-10") == []
    assert extract_search_codes("14/11") == []
    assert extract_search_codes("10/2026") == []
    assert extract_search_codes("quais as pendências da competência") == []
    assert extract_search_codes("") == []
    assert extract_search_codes(None) == []


def test_golden_questions_with_a_code_are_only_the_known_case():
    """Pergunta com código muda a ordem de propósito. O conjunto
    conhecido é R11-D6 (9035 e 594). Qualquer outra é STOP 1."""
    coded = [
        (case["id"], extract_search_codes(case["q"]))
        for case in [*GOLDEN_SET, *NEGATIVE_SET]
        if extract_search_codes(case["q"])
    ]
    assert coded == [("R11-D6", ["9035", "594"])]
    plain = [
        case for case in GOLDEN_SET if not extract_search_codes(case["q"])
    ]
    assert len(plain) >= 20
