from app.domain.services.chat_department_kpi_intent_service import (
    ChatDepartmentKpiIntentService,
)


def test_resolve_ebitda_with_typo():
    match = ChatDepartmentKpiIntentService.resolve("qual o ebita do trimestre")

    assert match is not None
    assert "ebitda" in match.path_token
    assert match.domain_prefix == "/financial/"


def test_resolve_commercial_closing_rate():
    match = ChatDepartmentKpiIntentService.resolve("taxa de conversao de vendas")

    assert match is not None
    assert "closing-rate" in match.path_token


def test_resolve_quality_kaizen_typo():
    match = ChatDepartmentKpiIntentService.resolve("resumo de kaisen")

    assert match is not None
    assert "kaizens" in match.path_token


def test_skips_when_product_code_present():
    match = ChatDepartmentKpiIntentService.resolve("ebitda do produto 10080047")

    assert match is None


def test_skips_supplies_cpv():
    match = ChatDepartmentKpiIntentService.resolve("qual o cpv da filial")

    assert match is None
